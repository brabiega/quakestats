import logging
from typing import (
    Iterator,
    List,
    Optional,
    Tuple,
)

from quakestats.core.game.qlmatch import (
    FullMatchInfo,
)
from quakestats.core.q3parser.api import (
    Q3ParserAPI,
)
from quakestats.core.q3toql.api import (
    Q3toQLAPI,
    QuakeGame,
)
from quakestats.core.wh import (
    Warehouse,
    WarehouseItem,
)
from quakestats.dataprovider import (
    analyze,
)
from quakestats.dataprovider.analyze import (
    AnalysisResult,
)
from quakestats.datasource.entities import (
    Q3Match,
)
from quakestats.system.context import (
    SystemContext,
)

logger = logging.getLogger(__name__)


class QSSdk():
    def __init__(self, ctx: SystemContext):
        self.ctx = ctx
        self.q3parser = Q3ParserAPI()
        self.q3toql = Q3toQLAPI()
        self.warehouse = Warehouse(ctx.config.get("RAW_DATA_DIR", None))
        self.server_domain: str = ctx.config.get("SERVER_DOMAIN")

    def iter_matches(self, latest: Optional[int] = None) -> Iterator[Q3Match]:
        return self.ctx.ds.get_matches_n(latest=latest)

    def get_match(self, match_guid: str):
        # TODO what to return here?
        return self.ctx.ds.get_match(match_guid)

    # TODO This needs further refactoring so all games go through validation (is_valid, duration) condition
    def process_q3_log(self, raw_data: str, mod_hint: str) -> Tuple[List[FullMatchInfo], List[Exception]]:
        errors: List[Exception] = []
        final_results: List[FullMatchInfo] = []
        skips = 0

        for idx, game_log in enumerate(self.q3parser.split_games(raw_data, mod_hint)):
            logger.debug("Processing match %s, %s", idx, game_log.identifier)

            # TODO error handling
            q3_game = self.q3parser.parse_game_log(game_log)
            ql_game = self.q3toql.transform(q3_game)
            if not ql_game.is_valid or ql_game.metadata.duration < 60:
                logger.debug("Game %s ignored", q3_game.identifier)
                continue

            if self.get_match(ql_game.game_guid):
                logger.debug("Game %s already in DB", ql_game.game_guid)
                skips += 1
                continue

            if not self.warehouse.has_item(ql_game.game_guid):
                self.warehouse.save_match_log(ql_game.game_guid, game_log.serialize())

            try:
                fmi = self.analyze_and_store(ql_game)
                final_results.append(fmi)
            except Exception as e:
                logger.exception(e)
                errors.append(e)

        return final_results, errors, skips

    def analyze_and_store(self, game: QuakeGame) -> FullMatchInfo:
        if not game.is_valid:
            logger.info("Game %s ignored", game.game_guid)
            return

        fmi = FullMatchInfo(
            events=game.get_events(),
            match_guid=game.game_guid,
            duration=game.metadata.duration,
            start_date=game.metadata.start_date,
            finish_date=game.metadata.finish_date,
            server_domain=self.server_domain,
            source=game.source,
        )

        analyzer = analyze.Analyzer()
        report = analyzer.analyze(fmi)
        self.store_analysis_report(report)
        return fmi

    def store_analysis_report(self, report: AnalysisResult):
        self.ctx.ds.store_analysis_report(report)
        logger.info("Storing game %s in datastore", report.match_metadata.match_guid)

    def load_game_from_wh(self, wh_item: WarehouseItem) -> QuakeGame:
        if not wh_item.data:
            raise Exception("WH item was not read")

        lines = wh_item.data.splitlines()

        if wh_item.ext == 'log':
            # identifier and create date are needed for old warehouse items when only OSP was supported
            game = self.q3parser.load_game_log(lines, wh_item.identifier, wh_item.create_date)

        else:
            # TODO where to put this logic
            # TODO ql doesn't need transform
            raise NotImplementedError()

        return self.q3toql.transform(game)

    def rebuild_db(self):
        self.ctx.ds.prepare_for_rebuild()
        counter = 0

        for item in self.warehouse.iter_matches():
            self.warehouse.read_item(item)
            logger.info("Processing file %s", item.path)

            game = self.load_game_from_wh(item)
            self.analyze_and_store(game)
            counter += 1

        self.ctx.ds.post_rebuild()
        return counter

    def delete_match(self, match_guid: str):
        self.ctx.ds.drop_match_info(match_guid)
        self.warehouse.delete_item(match_guid)

    def warehouse_iter(self) -> Iterator[WarehouseItem]:
        return self.warehouse.iter_matches()

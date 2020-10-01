import logging
from typing import (
    Iterator,
    List,
    Optional,
    Tuple,
)

from quakestats import (
    dataprovider,
)
from quakestats.core.q3toql.parse import (
    QuakeGame,
    read_games,
)
from quakestats.core.wh import (
    Warehouse,
)
from quakestats.dataprovider import (
    analyze,
)
from quakestats.datasource.entities import (
    Q3Match,
)
from quakestats.system.context import (
    SystemContext,
)

logger = logging.getLogger(__name__)


class QSSdk:
    def __init__(self, ctx: SystemContext):
        self.ctx = ctx
        self.warehouse = Warehouse(ctx.config.get("RAW_DATA_DIR", None))
        self.server_domain: str = ctx.config.get("SERVER_DOMAIN")

    def iter_matches(self, latest: Optional[int] = None) -> Iterator[Q3Match]:
        return self.ctx.ds.get_matches_n(latest=latest)

    def get_match(self, matchid: str):
        pass

    # TODO This needs further refactoring so all games go through validation (is_valid, duration) condition
    def process_q3_log(self, raw_data: str, save_log=True) -> Tuple[List[dataprovider.FullMatchInfo], List[Exception]]:
        errors: List[Exception] = []
        final_results: List[dataprovider.FullMatchInfo] = []
        # TODO handle different mods
        for game_or_error, game_log in read_games(raw_data, 'osp'):
            if isinstance(game_or_error, Exception):
                error = game_or_error
                errors.append(error)
                continue
            else:
                game = game_or_error

            if not game.is_valid or game.metadata.duration < 60:
                continue

            if save_log:
                self.warehouse.save_match_log(game.game_guid, "\n".join(game_log.raw_lines))

            try:
                fmi = self.process_game(game)
                final_results.append(fmi)
            except Exception as e:
                logger.exception(e)
                errors.append(e)

        return final_results, errors

    # TODO FullMatchInfo should be in dataprovider?
    def process_game(self, game: QuakeGame) -> dataprovider.FullMatchInfo:
        if not game.is_valid:
            logger.info("Game %s ignored", game.game_guid)
            return

        fmi = dataprovider.FullMatchInfo(
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
        self.ctx.ds.store_analysis_report(report)
        return fmi

    def rebuild_db(self):
        self.ctx.ds.prepare_for_rebuild()
        counter = 0

        for item in self.warehouse.iter_matches():
            self.warehouse.read_item(item)
            logger.info("Processing file %s", item.path)

            results, errors = self.process_q3_log(item.data, save_log=False)
            if errors:
                logger.error("Got error, %s", errors)
            else:
                counter += 1

        self.ctx.ds.post_rebuild()
        return counter

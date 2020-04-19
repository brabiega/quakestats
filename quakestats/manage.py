import json
import logging
from os import (
    listdir,
    path,
)
from time import (
    time,
)
from typing import (
    Optional,
)

from passlib.hash import (
    pbkdf2_sha256,
)

from quakestats import (
    dataprovider,
)
from quakestats.core.q3toql.parse import (
    QuakeGame,
    read_games,
)
from quakestats.core.ql import (
    QLGame,
)
from quakestats.dataprovider import (
    analyze,
)

logger = logging.getLogger(__name__)


def set_admin_password(db, password):
    assert password
    assert len(password) > 3
    hashpass = pbkdf2_sha256.hash(password)
    result = db.user.update_one(
        {"username": "admin"},
        {"$set": {"username": "admin", "password": hashpass}},
        upsert=True,
    )
    return result


def rebuild_db(data_dir, server_domain, data_store):
    # TODO add tests
    data_store().prepare_for_rebuild()
    ds = data_store()
    counter = 0
    files = listdir(data_dir)
    for f in files:
        with open(path.join(data_dir, f)) as fh:
            data = fh.read()
            logger.info("Processing file %s", f)
            results, errors = process_q3_log(
                server_domain, None, data, 'osp', ds
            )
            if errors:
                logger.error("Got error, %s", errors)
            else:
                counter += 1

    data_store().post_rebuild()
    return counter


def process_q3_log(
    server_domain: str, data_dir: Optional[str],
    raw_game_log: str, q3mod: str, data_store,
):
    """
    Returns 2 lists
    - list of results
    - list of errors
    """
    errors = []
    final_results = []
    for game, game_log in read_games(raw_game_log, q3mod):
        if isinstance(game, Exception):
            errors.append(game)
            continue

        if not game.is_valid or game.metadata.duration < 60:
            continue

        if data_dir:
            p = path.join(data_dir, "{}.log".format(game.game_guid))
            with open(p, "w") as fh:
                for line in game_log.raw_lines:
                    fh.write(line)
                    fh.write("\n")

        try:
            fmi = process_game(server_domain, data_dir, game, data_store)
            final_results.append(fmi)
        except Exception as e:
            logger.exception(e)
            errors.append(e)
    return final_results, errors


def process_game(
    server_domain: str, data_dir: Optional[str], game: QuakeGame, data_store
):
    """
    Process single q3 game
    """
    # TODO QuakeGame should keep source type (Q3/QL)
    fmi = dataprovider.FullMatchInfo(
        events=game.get_events(),
        match_guid=game.game_guid,
        duration=game.metadata.duration,
        start_date=game.metadata.start_date,
        finish_date=game.metadata.finish_date,
        server_domain=server_domain,
        source=game.source,
    )

    analyzer = analyze.Analyzer()
    report = analyzer.analyze(fmi)
    data_store.store_analysis_report(report)
    return fmi


def store_game(game: QLGame, server_domain, store_dir):
    assert game.game_guid

    game_dict = {
        'metadata': game.metadata.__dict__,
        'game_guid': game.game_guid,
        'store_time': time(),
        'valid': game.is_valid,
        'events': [e for e in game.get_events()],
        'source': game.source,
        'server_domain': server_domain,
    }
    if not game_dict['events']:
        logger.info("Ignored game %s, no valid events", game.game_guid)

    file_path = path.join(store_dir, f'{game.game_guid}.json')
    with open(file_path, 'w') as fh:
        json.dump(game_dict, fh)

    logger.info(
        "Written game %s, with %s events",
        game.game_guid, len(game_dict['events'])
    )


def load_game(file_path: str):
    from datetime import datetime, timedelta
    with open(file_path) as fh:
        data = json.load(fh)

    game = QLGame()
    game.metadata.__dict__.update(data['metadata'])
    game.game_guid = data['game_guid']
    for ev in data['events']:
        game.add_event(ev)
    game.valid_start = game.valid_end = data['valid']
    game.source = data['source']

    store_time = data['store_time']
    game.metadata.game_received_ts = store_time
    game.metadata.finish_date = datetime.fromtimestamp(store_time)
    game.metadata.start_date = (
        game.metadata.finish_date - timedelta(seconds=game.metadata.duration)
    )

    server_domain = data['server_domain']

    return server_domain, game

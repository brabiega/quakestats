import json
import logging
import os
from time import (
    time,
)

from passlib.hash import (
    pbkdf2_sha256,
)

from quakestats.core.ql import (
    QLGame,
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


def store_game(game: QLGame, server_domain, store_dir):
    from copy import deepcopy
    from datetime import datetime
    assert game.game_guid

    metadata = deepcopy(game.metadata.__dict__)
    metadata['start_date'] = datetime.timestamp(metadata['start_date'])
    metadata['finish_date'] = datetime.timestamp(metadata['finish_date'])
    game_dict = {
        'metadata': metadata,
        'game_guid': game.game_guid,
        'store_time': time(),
        'valid': game.is_valid,
        'events': [e for e in game.get_events()],
        'source': game.source,
        'server_domain': server_domain,
    }
    if not game_dict['events']:
        logger.info("Ignored game %s, no valid events", game.game_guid)

    file_path = os.path.join(store_dir, f'{game.game_guid}.json')
    with open(file_path, 'w') as fh:
        json.dump(game_dict, fh)

    logger.info(
        "Written game %s, with %s events",
        game.game_guid, len(game_dict['events'])
    )


def load_game(file_path: str):
    from datetime import datetime, timedelta

    logger.info("Loading game %s", file_path)
    with open(file_path) as fh:
        data = json.load(fh)

    metadata = data['metadata']
    metadata['start_date'] = datetime.fromtimestamp(
        metadata['start_date'] or 0
    )
    metadata['finish_date'] = datetime.fromtimestamp(
        metadata['finish_date'] or 0
    )

    game = QLGame()
    game.metadata.__dict__.update(metadata)
    game.game_guid = data['game_guid']
    for ev in data['events']:
        game.add_event(0, ev)
    game.source = data['source']

    store_time = data['store_time']
    game.metadata.game_received_ts = store_time
    game.metadata.finish_date = datetime.fromtimestamp(store_time)
    game.metadata.start_date = (
        game.metadata.finish_date - timedelta(seconds=game.metadata.duration)
    )

    server_domain = data['server_domain']

    return server_domain, game

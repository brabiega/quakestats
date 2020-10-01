"""
Base module for Q3 game parser
"""

import logging
from typing import (
    Iterator,
    Tuple,
    Union,
)

from quakestats.core.q3toql.parsers.base import (
    Q3GameLog,
    Q3LogParserModOsp,
)
from quakestats.core.q3toql.transform import (
    Q3toQL,
    QuakeGame,
)

logger = logging.getLogger(__name__)


def read_games(
    raw_data: str, mod_hint: str
) -> Iterator[Tuple[Union[QuakeGame, Exception], Q3GameLog]]:
    """
    raw_data: raw string of quake log
    mod_name: name of game mod [baseq3, osp, cpma]

    Returns instance of QuakeGame and Q3GameLog
    """
    assert mod_hint == 'osp'
    parser = Q3LogParserModOsp(raw_data)
    for game_log in parser.games():
        tf = Q3toQL()
        try:
            game = tf.transform(game_log)
        except Exception as e:
            logger.error("Error in game %s", game_log.start_date)
            logger.exception(e)
            game = e

        yield game, game_log

"""
Base module for Q3 game parser
"""

from typing import (
    Iterator,
)

from quakestats.core.q3toql.parsers.base import (
    Q3LogParserModOsp,
)
from quakestats.core.q3toql.transform import (
    Q3toQL,
    QuakeGame,
)


def read_games(raw_data: str, mod_hint: str) -> Iterator[QuakeGame]:
    """
    raw_data: raw string of quake log
    mod_name: name of game mod [baseq3, osp, cpma]

    Returns instance of QuakeGame
    """
    assert mod_hint == 'osp'
    parser = Q3LogParserModOsp(raw_data)
    for game in parser.games():
        tf = Q3toQL()
        yield tf.transform(game)

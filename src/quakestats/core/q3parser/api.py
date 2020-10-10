"""
API module for q3parser
"""

import logging
from typing import (
    Iterator,
)

from .parser import (
    GameLogParserOsp,
    Q3Game,
)
from .splitter import (
    GameLogSplitter,
    Q3GameLog,
)

logger = logging.getLogger(__name__)


class Q3ParserAPI():
    def split_games(self, raw_data: str, mod_hint: str) -> Iterator[Q3GameLog]:
        splitter = GameLogSplitter(mod_hint)
        for game in splitter.iter_games(raw_data):
            yield game

    def parse_game_log(self, game_log: Q3GameLog) -> Q3Game:
        parser = GameLogParserOsp()
        return parser.parse(game_log)

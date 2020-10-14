"""
API module for q3parser
"""

import logging
from datetime import (
    datetime,
)
from typing import (
    Iterator,
    List,
)

from .parser import (
    GameLogParserEdawn,
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

        if game_log.mod == 'edawn':
            parser = GameLogParserEdawn()
        elif game_log.mod == 'osp':
            parser = GameLogParserOsp()
        else:
            raise Exception(f"Unsupported mod {game_log.mod}")
        return parser.parse(game_log)

    def load_game_log(self, data: List[str], identifier: str, create_date: datetime) -> Q3Game:
        game_log = Q3GameLog.deserialize(data, identifier, create_date)
        return self.parse_game_log(game_log)

from typing import (
    List,
)

from .splitter import (
    QLGameLog,
    QLGameLogSplitter,
)


class QLFeed():
    def __init__(self):
        self.splitter = QLGameLogSplitter()

    def feed(self, ev: dict) -> QLGameLog:
        return self.splitter.add_event(ev)


class QLParserAPI():
    def create_feed(self) -> QLFeed:
        return QLFeed()

    def is_log_from_ql(self, line: str) -> bool:
        return line == QLGameLog.TYPE

    def load_game_log(self, data: List[str]) -> QLGameLog:
        return QLGameLog.deserialize(data)

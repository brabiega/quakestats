from typing import (
    List,
)

from quakestats.core.q3toql.parsers.events import (
    Q3GameEvent,
)


class Q3GameLog():
    def __init__(self):
        self.events: List[Q3GameEvent] = []
        self.checksum = None
        self.finished = False
        self.start_time = None
        self.end_time = None

    def add_event(self, event: Q3GameEvent):
        if event:
            self.events.append(event)

    def is_empty(self) -> bool:
        return not bool(self.events)

    def set_finished(self):
        self.finished = True

    def set_checksum(self, checksum: str):
        self.checksum = checksum

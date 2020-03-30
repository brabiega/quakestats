import hashlib
from typing import (
    List,
)

from quakestats.core.q3toql.parsers.events import (
    Q3GameEvent,
)


class Q3GameLog():
    def __init__(self):
        self.events: List[Q3GameEvent] = []
        self.checksum = hashlib.md5()
        self.finished = False

    def add_event(self, event: Q3GameEvent, name, payload):
        # calculate game checksum, collisions should be very rare as
        # the hash depends on
        # - order of events
        # - event names and their payloads
        # if this ever becomes a problem we can include event.time
        # into the hash
        self.checksum.update(name.encode())
        if payload:
            self.checksum.update(payload.encode())
        self.events.append(event)

    def is_empty(self) -> bool:
        return not bool(self.events)

    def set_finished(self):
        self.finished = True

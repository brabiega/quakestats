import hashlib
from typing import Optional, List


class Q3MatchLogEvent():
    def __init__(
        self, time: int, name: str,
        payload: Optional[str] = None
    ):
        """
        time: game time in miliseconds
        """
        assert time >= 0
        self.time = time
        self.name = name
        self.payload = payload
        self.is_separator = False

    @classmethod
    def create_separator(cls, time: int):
        obj = cls(time, '__separator__')
        obj.is_separator = True
        return obj


class Q3GameLog():
    def __init__(self):
        self.events: List[Q3MatchLogEvent] = []
        self.checksum = hashlib.md5()

    def add_event(self, event: Q3MatchLogEvent):
        # calculate game checksum, collisions should be very rare as
        # the hash depends on
        # - order of events
        # - event names and their payloads
        # if this ever becomes a problem we can include event.time
        # into the hash
        self.checksum.update(event.name.encode())
        if event.payload:
            self.checksum.update(event.payload.encode())
        self.events.append(event)

    def is_empty(self) -> bool:
        return not bool(self.events)

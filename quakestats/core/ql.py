"""
Code to preprocess QL events
"""
from typing import (
    List,
)

from quakestats.core.game import (
    qlevents,
)
from quakestats.core.game.metadata import (
    QuakeGameMetadata,
)


class MatchMismatch(Exception):
    pass


class QLGame():
    """
    This should be a claas which represents
    single quake live match

    """
    def __init__(self):
        self.ql_events: List[qlevents.QLEvent] = []
        self.start_time: int = 0
        self.game_guid = None
        self.warmup = False
        self.metadata = QuakeGameMetadata()
        self.valid_start = False
        self.valid_end = False
        self.source = 'QL'

    @property
    def is_valid(self):
        return self.valid_start and self.valid_end

    def add_event(self, event: dict):
        ql_ev = qlevents.create_from_ql_dict(event)

        if self.game_guid is None:
            self.game_guid = ql_ev.match_guid
        elif self.game_guid != ql_ev.match_guid:
            raise MatchMismatch("Event guid mismatch")

        if isinstance(ql_ev, qlevents.MatchStarted):
            self.valid_start = True
        elif isinstance(ql_ev, qlevents.MatchReport):
            self.valid_end = True
            self.metadata.duration = ql_ev.data['GAME_LENGTH']

        # ignore warmup and non-meaningful events
        if not self.valid_start:
            return

        self.ql_events.append(ql_ev)
        return ql_ev

    def get_events(self):
        for ev in self.ql_events:
            yield ev

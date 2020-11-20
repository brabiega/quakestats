from datetime import (
    datetime,
)
from typing import (
    List,
    Optional,
)

from quakestats.core.game import (
    qlevents,
)


class QuakeGameMetadata():
    def __init__(self):
        self.start_date: Optional[datetime] = None
        self.finish_date: Optional[datetime] = None
        # timestamp when this game was received by the server
        self.game_received_ts: Optional[float] = None
        self.map = None
        self.timelimit = None
        self.fraglimit = None
        self.capturelimit = None
        self.hostname = None
        self.duration = 0


class QuakeGame():
    def __init__(self, source: str):
        self.ql_events: List[qlevents.QLEvent] = []
        self.start_time: int = 0
        self.game_guid = None
        self.warmup = False
        self.metadata = QuakeGameMetadata()
        self.valid_start = False
        self.valid_end = False
        self.source = source

    @property
    def is_valid(self):
        return self.valid_start and self.valid_end

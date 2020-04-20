from datetime import (
    datetime,
)
from typing import (
    Optional,
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

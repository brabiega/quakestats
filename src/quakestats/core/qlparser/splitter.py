import itertools
import json
import logging
from datetime import (
    datetime,
)
from typing import (
    List,
    Optional,
)

from quakestats.core.game.gamelog import (
    RawGameLog,
)

logger = logging.getLogger(__name__)


class QLGameLog(RawGameLog):
    """
    Represents raw QL game log
    """
    TYPE = 'QuakeLive'

    def __init__(self, received: datetime, identifier: str):
        self.events: List[dict] = []
        self.received: datetime = received
        self._identifier = identifier

    def add_event(self, event: dict):
        self.events.append(event)

    def serialize(self) -> str:
        assert self.received
        assert not self.is_empty
        base_header = super().serialize()
        header = f"{self.identifier} {self.received.timestamp()}"
        return "\n".join(itertools.chain([base_header, header, json.dumps(self.events)]))

    @classmethod
    def deserialize(cls, data: List[str]) -> 'QLGameLog':
        if data[0] != cls.TYPE:
            raise Exception(f"Invalid header, got '{data[0]}'")

        recv_identifier, recv_ts, = data[1].split(" ")
        received = datetime.fromtimestamp(float(recv_ts))

        obj = cls(received, recv_identifier)
        obj.events = json.loads(data[2])

        return obj

    @property
    def is_empty(self) -> bool:
        return not self.events

    @property
    def identifier(self) -> str:
        return self._identifier

    def __str__(self) -> str:
        return f"QLGameLog({self.identifier})"


class QLGameLogSplitter():
    """
    Class which splits events data (e.g. ql match events)
    into separate matches
    """
    def __init__(self):
        self.current_game = None

    def add_event(self, ql_event: dict) -> Optional[QLGameLog]:
        """
        Consumes ql events, produces QLGameLog when MATCH_REPORT reached
        """
        game_id = ql_event['DATA']['MATCH_GUID']
        event_type = ql_event['TYPE']

        if not self.current_game:
            logger.debug("Created new game %s", game_id)
            self.current_game = QLGameLog(datetime.now(), game_id)

        if event_type == "MATCH_REPORT":
            self.current_game.add_event(ql_event)
            logger.debug("Finished game %s", game_id)
            return self.current_game

        if self.current_game.identifier != game_id:
            # some events like "PLAYER_DISCONNECT" may be collected after MATCH_REPORT
            # ignore them
            self.current_game = QLGameLog(datetime.now(), game_id)

        self.current_game.add_event(ql_event)


import hashlib
import itertools
from datetime import (
    datetime,
)
from typing import (
    Iterator,
    List,
)

from quakestats.core.game.gamelog import (
    RawGameLog,
)


class Q3GameLog(RawGameLog):
    """
    Represents raw q3 game log
    """
    TYPE = 'Quake3'

    def __init__(self, received: datetime, mod: str):
        self.lines: List[str] = []
        self.mod = mod
        self.received: datetime = received
        self.__checksum: str = None

    def add_line(self, line: str):
        self.__checksum = None
        self.lines.append(line)

    def serialize(self) -> str:
        assert self.mod
        assert self.received
        assert not self.is_empty
        base_header = super().serialize()
        header = f"{self.identifier} {self.received.timestamp()} {self.mod}"
        return "\n".join(itertools.chain([base_header, header], self.lines))

    @classmethod
    def deserialize(cls, data: List[str], identifier: str, create_date: datetime) -> 'Q3GameLog':
        if data[0] == cls.TYPE:
            recv_identifier, recv_ts, mod = data[1].split(" ")
            received = datetime.fromtimestamp(float(recv_ts))

            obj = cls(received, mod)
            obj.lines = data[2:]
        else:
            recv_identifier = identifier
            received = create_date
            # assume it is an old item when only OSP was supported
            mod = 'osp'

            obj = cls(received, mod)
            obj.lines = data

        obj.__checksum = recv_identifier
        return obj

    @property
    def checksum(self) -> str:
        if self.__checksum:
            return self.__checksum

        checksum = hashlib.md5()
        for line in self.lines:
            checksum.update(line.encode())

        self.__checksum = checksum.hexdigest()
        return self.__checksum

    @property
    def is_empty(self) -> bool:
        return not bool(self.lines)

    @property
    def identifier(self):
        return self.checksum


class GameLogSplitter():
    """
    Class which splits text data (e.g. log file with multiple matches)
    into separate matches
    """
    # assume all mods use the same match separator
    SEPARATOR = '-----------'

    def __init__(self, mod: str):
        self.mod = mod

    def iter_games(self, raw_data: str) -> Iterator[Q3GameLog]:
        current_game = Q3GameLog(datetime.now(), self.mod)
        for line in raw_data.splitlines():
            if self.is_separator(line):
                if not current_game.is_empty:
                    yield current_game

                current_game = Q3GameLog(datetime.now(), self.mod)
                continue

            current_game.add_line(line)

        if not current_game.is_empty:
            yield current_game

    def is_separator(self, line: str) -> bool:
        return self.SEPARATOR in line

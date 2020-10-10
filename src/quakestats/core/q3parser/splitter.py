
import hashlib
import itertools
from datetime import (
    datetime,
)
from typing import (
    Iterator,
    List,
)


class RawGameLog():
    TYPE = None

    def serialize(self) -> str:
        return f"{self.TYPE}"

    @property
    def identifier(self) -> str:
        raise NotImplementedError()


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

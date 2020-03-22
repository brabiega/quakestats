from typing import Optional


class Q3MatchLog():
    pass


class Q3MatchLogEvent():
    def __init__(
        self, time: int, name: str,
        payload: Optional[str]=None
    ):
        """
        time: game time in miliseconds
        """
        assert time >=0
        self.time = time
        self.name = name
        self.payload = payload
        self.is_separator = False

    @classmethod
    def create_separator(cls, time: int):
        obj = cls(time, '__separator__')
        obj.is_separator = True
        return obj
class RawGameLog():
    """
    Base class for game log, should be used for q3 and ql
    """
    TYPE = None

    def serialize(self) -> str:
        return f"{self.TYPE}"

    @property
    def identifier(self) -> str:
        raise NotImplementedError()

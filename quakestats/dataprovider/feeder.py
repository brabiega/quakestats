class FeedFull(Exception):
    pass


class MatchFeeder():
    """
    Base class used to implement match detection (from start till end)
    from continuous stream of events/log entries.
    Feeding is done event by event or log entry by log entry, once match
    end is reached the Feed has to be consumed by `consume` method.
    Each log/event format has specific implementation:
        - quake3 - log entries processing
        - quake live - events processing
    """
    def __init__(self):
        self.events = []
        self.full = False

    def feed(self, event):
        """Raises FeedFull when ready to consume
        In QL the only way to determine change is to compare
        Previous and current match_guid, so whether feed is full
        or not, it's only known when next event is being processed
        """
        if self.full:
            raise FeedFull("Feed is full, please consume")
        self.inspect_event(event)

    def inspect_event(self, event):
        raise NotImplementedError("Abstract method")

    def consume(self):
        result = {
            "EVENTS": self.events,
        }
        self.events = []
        self.full = False
        return result

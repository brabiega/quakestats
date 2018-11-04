from datetime import datetime
from quakestats.dataprovider.preprocessor import MatchPreprocessor


__all__ = [
    'FeedFull',
    'MatchPreprocessor',
    'MatchFeeder',
    'FullMatchInfo',
]


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


class FeedFull(Exception):
    pass


class MatchFeeder():
    """
    Helper class to split stream of events/log entries
    into matches
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


class FullMatchInfo():
    """
    Object gathers all relevant info about the match.
    Only data stored here will be used for further processing
    """
    def __init__(
        self, events, match_guid,
        duration, start_date, finish_date,
        server_domain, source
    ):
        self.events = events
        self.match_guid = match_guid
        self.duration = duration
        self.start_date = start_date
        self.finish_date = finish_date
        self.server_domain = server_domain
        self.source = source

    def get_summary(self):
        return {
            "MATCH_GUID": self.match_guid,
            "DURATION": self.duration,
            "START_DATE": self.start_date,
            "FINISH_DATE": self.finish_date,
            "SERVER_DOMAIN": self.server_domain,
            "SOURCE": self.source,
        }

    def as_dict(self):
        res = self.get_summary()
        res['EVENTS'] = self.events
        return res

    @classmethod
    def from_dict(cls, raw):
        return cls(
            events=raw['EVENTS'],
            match_guid=raw['MATCH_GUID'],
            duration=raw['DURATION'],
            start_date=datetime.strptime(
                raw['START_DATE'].split('.')[0], DATE_FORMAT),
            finish_date=datetime.strptime(
                raw['FINISH_DATE'].split('.')[0], DATE_FORMAT),
            server_domain=raw['SERVER_DOMAIN'],
            source=raw['SOURCE'])

    @classmethod
    def from_preprocessor(
        cls, preprocessor, start_date, finish_date,
        server_domain, source
    ):
        return FullMatchInfo(
            events=preprocessor.events,
            match_guid=preprocessor.match_guid,
            duration=preprocessor.duration,
            start_date=start_date,
            finish_date=finish_date,
            server_domain=server_domain,
            source=source)

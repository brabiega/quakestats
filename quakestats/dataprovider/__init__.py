from datetime import datetime


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


class MatchPreprocessor():
    """Checks whether match was finished or not, etc"""
    def __init__(self):
        self.started = None
        self.match_guid = None
        self.aborted = None
        self.finished = None
        self.events = []
        self.duration = None

    def process_events(self, events):
        for event in events:
            ev_match_guid = event['DATA']['MATCH_GUID']
            if not self.match_guid:
                self.match_guid = ev_match_guid
            assert self.match_guid == ev_match_guid

            if event['TYPE'] == 'MATCH_STARTED':
                self.started = True

            if event['TYPE'] == 'MATCH_REPORT':
                self.finished = True
                self.duration = event['DATA']['GAME_LENGTH']
                self.aborted = event['DATA']['ABORTED']

            warmup_event = event['DATA'].get('WARMUP', False)
            # skip warmup events
            if not warmup_event:
                self.events.append(event)

    def is_valid(self):
        if (
            self.started
            and self.finished
            and not self.aborted
        ):
            return True
        else:
            return False


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

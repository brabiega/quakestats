from quakestats.dataprovider import MatchFeeder, FeedFull


class QLMatchFeeder(MatchFeeder):
    """
        Detection of different matches is done based on
        MATCH_GUID passed in events. If current event has different
        MATCH_GUID than previous one, raise an Exception
    """
    def __init__(self):
        super().__init__()
        self.current_match_guid = None

    def inspect_event(self, event):
        if self.current_match_guid:
            if self.current_match_guid != event['DATA']['MATCH_GUID']:
                self.full = True
                raise FeedFull('Feed is full, please consume')
        else:
            self.current_match_guid = event['DATA']['MATCH_GUID']

        self.events.append(event)

    def consume(self):
        self.current_match_guid = None
        return super().consume()

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

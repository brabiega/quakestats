import re
from quakestats.dataprovider.feeder import MatchFeeder, FeedFull


class Q3MatchFeeder(MatchFeeder):
    base_format = r"(\d+\.\d+) (.+?):(.*)"
    separator_format = r"(\d+\.\d+) ---*$"
    vq3_format = r"\s+(\d+)\:(\d+)(.*)"

    def normalize(self, data):
        """
        vq3 and osp have slightly different format
        we can translate vq3 log entry to osp
        """
        match = re.search(self.vq3_format, data)
        if match:
            mins = int(match.group(1))
            secs = int(match.group(2))
            rest = match.group(3)
            return "{}.0{}".format((mins * 60) + secs, rest)
        else:
            return data

    def inspect_event(self, data):
        """Sets self.full to True in consumption is needed"""
        if self.full:
            raise FeedFull("Feed is full, please consume")

        match = re.search(self.base_format, data)

        if match:
            # Special case if log is broken
            # (previous game wasnt finished properly)
            if self.events and match.group(2).startswith('InitGame'):
                self.full = True
                raise FeedFull('Broken log detected')

            self.events.append(data)
            return
        match = re.search(self.separator_format, data)
        if match:
            if self.events:
                self.full = True
                raise FeedFull("Feed is full, please consume")
            return

        raise Exception("Malformed line {}".format(data))

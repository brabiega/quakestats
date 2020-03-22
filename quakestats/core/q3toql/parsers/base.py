import re
import logging

from typing import Iterator

from quakestats.core.q3toql.parsers.result import Q3MatchLog, Q3MatchLogEvent


logger = logging.getLogger(__name__)


class Q3LogParser():
    """
    Should be a base class for all mod parsers:
    - [ ] baseq3
    - [ ] OSP
    - [ ] CPMA
    """
    def __init__(self, raw_data: str):
        self.raw_data = raw_data

    def games(self):
        pass

    def read_lines(self) -> Iterator[str]:
        for line in self.raw_data.splitlines():
            yield line

    def read_events(self):
        raise NotImplementedError()


class Q3LogParserModOsp(Q3LogParser):
    separator_format = r"(\d+\.\d+) ------*$"
    event_format = r"(\d+\.\d+) (.+?):(.*)"

    def read_events(self):
        for line in self.read_lines():
            yield self.line_to_event(line)
            
    def line_to_event(self, line: str) -> Q3MatchLogEvent:
        match = re.search(self.event_format, line)
        if match:
            ev_time = match.group(1)
            ev_name = match.group(2)
            ev_payload = match.group(3).strip()
            return Q3MatchLogEvent(
                self.mktime(ev_time),
                ev_name,
                ev_payload if ev_payload else None
            )

        separator_match = re.search(self.separator_format, line)
        if separator_match:
            ev_time = separator_match.group(1)
            return Q3MatchLogEvent.create_separator(
                self.mktime(ev_time)
            )

    @classmethod
    def mktime(cls, event_time: str) -> int:
        seconds, tenths = event_time.split('.')
        return int(seconds) * 1000 + int(tenths) * 100
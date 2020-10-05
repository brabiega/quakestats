import hashlib
import logging
import re
from datetime import (
    timedelta,
)
from typing import (
    Iterator,
)

from quakestats.core.q3toql.parsers import (
    events,
)
from quakestats.core.q3toql.parsers.baseq3 import (
    BaseQ3ParserMixin,
    RawEvent,
)
from quakestats.core.q3toql.parsers.osp import (
    OspParserMixin,
)
from quakestats.core.q3toql.parsers.result import (
    Q3GameLog,
)

logger = logging.getLogger(__name__)

SEPARATOR = '___SEPARATOR___'


class Q3LogParser():
    """
    Should be a base class for all mod parsers:
    - [x] baseq3
    - [x] OSP
    - [x] edawn
    - [ ] CPMA - it's probably the same as baseq3, need to check
    """
    def __init__(self, raw_data: str):
        self.raw_data = raw_data
        # game that is currently being parsed
        self._current_game = None

    def games(self) -> Iterator[Q3GameLog]:
        """
        Parse given data and return iterator
        over parsed games
        """
        game = self.new_game()
        for event in self.read_raw_events():
            if event.name == SEPARATOR:
                # this seems to mean that single q3 game has ended or started
                if not game.is_empty():
                    self.close_game(game)
                    yield game
                game = self.new_game()
                continue

            try:
                ev = self.build_event(event)
            except Exception:
                logger.exception("Failed to process event '%s'", event)
                raise

            if ev:
                # check to detect some inconsistent logs, just warn
                if ev.time < self.current_time:
                    logger.warning(
                        "Got out of time log line '%s', '%s'",
                        ev.time, event
                    )
                self.current_time = ev.time
            game.add_event(ev)

        # handle last game even if there is no separator
        if not game.is_empty():
            self.close_game(game)
            yield game

    def new_game(self) -> Q3GameLog:
        game = Q3GameLog()
        self._current_game = game
        self.current_time: int = 0
        return game

    def close_game(self, game: Q3GameLog):
        """
        Do some logic to close the game
        """
        raise NotImplementedError()

    def read_lines(self) -> Iterator[str]:
        for line in self.raw_data.splitlines():
            self._current_game.add_raw_line(line)
            yield line

    def build_event(self, raw_event: RawEvent) -> events.Q3GameEvent:
        raise NotImplementedError()

    def read_raw_events(self) -> RawEvent:
        raise NotImplementedError()


class Q3LogParserModOsp(
    Q3LogParser, BaseQ3ParserMixin, OspParserMixin
):
    separator_format = r"(\d+\.\d+) ------*$"
    event_format = r"(\d+\.\d+) (.+?):(.*)"

    def __init__(self, raw_data: str):
        self.raw_data = raw_data
        # time of game init event
        self.__init_time = 0
        self.__ev_exit = None
        self.game_hash = hashlib.md5()

    def read_raw_events(self) -> Iterator[RawEvent]:
        for line in self.read_lines():
            yield self.line_to_raw_event(line)

    def line_to_raw_event(self, line: str) -> RawEvent:
        match = re.search(self.event_format, line)
        if match:
            # calculate game checksum, collisions should be very rare as
            # the hash depends on log lines and their order
            # hash will be used as unique game identifier
            self.game_hash.update(line.encode())
            ev_time = match.group(1)
            ev_name = match.group(2)
            ev_payload = match.group(3).strip()
            return RawEvent(
                self.mktime(ev_time), ev_name,
                ev_payload if ev_payload else None
            )

        separator_match = re.search(self.separator_format, line)
        if separator_match:
            ev_time = separator_match.group(1)
            return RawEvent(
                self.mktime(ev_time), SEPARATOR, None
            )

        logger.warning("Ignored malformed line '%s'", line)

    def build_event(self, raw_event: RawEvent) -> events.Q3GameEvent:
        if raw_event.name == 'InitGame':
            ev = self.parse_init_game(raw_event)
            self.__init_time = ev.time
            return ev
        elif raw_event.name == 'ClientUserinfoChanged':
            return self.parse_user_info(raw_event)
        elif raw_event.name == 'Weapon_Stats':
            return self.parse_weapon_stat(raw_event)
        elif raw_event.name == 'Kill':
            return self.parse_kill(raw_event)
        elif raw_event.name == 'ClientDisconnect':
            return self.parse_client_disconnect(raw_event)
        elif raw_event.name == 'Exit':
            self.__ev_exit = self.parse_exit(raw_event)
        elif raw_event.name == 'ServerTime':
            self._current_game.start_date = self.parse_server_time(raw_event)

    @classmethod
    def mktime(cls, event_time: str) -> int:
        seconds, tenths = event_time.split('.')
        return int(seconds) * 1000 + int(tenths) * 100

    def close_game(self, game: Q3GameLog):
        game.set_checksum(self.game_hash.hexdigest())
        self.game_hash = hashlib.md5()
        if self.__ev_exit:
            game.add_event(self.__ev_exit)
            game.set_finished()

        if game.start_date and self.current_time:
            game.finish_date = (
                game.start_date +
                timedelta(milliseconds=self.current_time - self.__init_time)
            )
        self.__ev_exit = None


class Q3LogParserModEdawn(
    Q3LogParser, BaseQ3ParserMixin, OspParserMixin
):
    """
    Edawn has similar log format to OSP
    Enchanced logging (higher granularity) is planned for 1.6.3
    """
    separator_format = r"(\d+:\d+\.\d+) ------*$"
    event_format = r"(\d+:\d+\.\d+) (.+?):(.*)"
    time_format = r"(\d+):(\d+)\.(\d+)"

    def __init__(self, raw_data: str):
        self.raw_data = raw_data
        # time of game init event
        self.__init_time = 0
        self.__ev_exit = None
        self.game_hash = hashlib.md5()

    def read_raw_events(self) -> Iterator[RawEvent]:
        for line in self.read_lines():
            yield self.line_to_raw_event(line)

    def line_to_raw_event(self, line: str) -> RawEvent:
        match = re.search(self.event_format, line)
        if match:
            # calculate game checksum, collisions should be very rare as
            # the hash depends on log lines and their order
            # hash will be used as unique game identifier
            self.game_hash.update(line.encode())
            ev_time = match.group(1)
            ev_name = match.group(2)
            ev_payload = match.group(3).strip()
            return RawEvent(
                self.mktime(ev_time), ev_name,
                ev_payload if ev_payload else None
            )

        separator_match = re.search(self.separator_format, line)
        if separator_match:
            ev_time = separator_match.group(1)
            return RawEvent(
                self.mktime(ev_time), SEPARATOR, None
            )

        logger.warning("Ignored malformed line '%s'", line)

    def build_event(self, raw_event: RawEvent) -> events.Q3GameEvent:
        if raw_event.name == 'InitGame':
            ev = self.parse_init_game(raw_event)
            self.__init_time = ev.time
            return ev
        elif raw_event.name == 'ClientUserinfoChanged':
            return self.parse_user_info(raw_event)
        elif raw_event.name == 'Weapon_Stats':
            return self.parse_weapon_stat(raw_event)
        elif raw_event.name == 'Kill':
            return self.parse_kill(raw_event)
        elif raw_event.name == 'ClientDisconnect':
            return self.parse_client_disconnect(raw_event)
        elif raw_event.name == 'Exit':
            self.__ev_exit = self.parse_exit(raw_event)
        elif raw_event.name == 'ServerTime':
            self._current_game.start_date = self.parse_server_time(raw_event)

    @classmethod
    def mktime(cls, event_time: str) -> int:
        minutes, seconds, tenths = re.search(cls.time_format, event_time).groups()
        return int(minutes) * 60 * 1000 + int(seconds) * 1000 + int(tenths) * 100

    def close_game(self, game: Q3GameLog):
        game.set_checksum(self.game_hash.hexdigest())
        self.game_hash = hashlib.md5()
        if self.__ev_exit:
            game.add_event(self.__ev_exit)
            game.set_finished()

        if game.start_date and self.current_time:
            game.finish_date = (
                game.start_date +
                timedelta(milliseconds=self.current_time - self.__init_time)
            )
        self.__ev_exit = None

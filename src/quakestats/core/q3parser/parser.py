import logging
import re
from datetime import (
    timedelta,
)
from typing import (
    List,
)

from quakestats.core.q3parser import (
    events,
)
from quakestats.core.q3parser.modparse.baseq3 import (
    BaseQ3ParserMixin,
)
from quakestats.core.q3parser.modparse.edawn import (
    EdawnParserMixin,
)
from quakestats.core.q3parser.modparse.osp import (
    OspParserMixin,
)
from quakestats.core.q3parser.splitter import (
    Q3GameLog,
)

logger = logging.getLogger(__name__)


class Q3Game():
    """
    Represents parsed Q3 game
    """
    def __init__(self, identifier: str, mod: str):
        self.events: List[events.Q3GameEvent] = []
        self.mod = mod
        self.identifier = identifier
        self.finished = False
        self.start_date = None
        self.finish_date = None

    def add_event(self, event: events.Q3GameEvent):
        assert event
        self.events.append(event)

    def is_empty(self) -> bool:
        return not bool(self.events)

    def set_finished(self):
        self.finished = True


class GameLogParser():
    """
    Should be a base class for all mod parsers:
    - [x] baseq3
    - [x] OSP
    - [x] edawn
    - [ ] CPMA - it's probably the same as baseq3, need to check
    """
    def __init__(self):
        pass

    def parse(self, game_log: Q3GameLog) -> Q3Game:
        assert not game_log.is_empty
        game = Q3Game(game_log.identifier, game_log.mod)

        last_event: events.Q3GameEvent = None
        for line in game_log.lines:
            event: events.Q3GameEvent = self.parse_line(line)

            # some of the log entries are ignored at the moment
            if not event:
                continue

            if last_event and last_event.time > event.time:
                raise Exception(f"Flow error on line '{line}'")

            game.add_event(event)

        self.populate_dates(game)
        return game

    def parse_line(self, line: str) -> events.RawEvent:
        raise NotImplementedError()

    def populate_dates(self, game: Q3Game) -> Q3Game:
        """
        Do initial analysis of the game, look for SeverTime event
        Fill game start and finish dates if possible
        This is needed to validate the game, not valid games (e.g. not finished)
        will be ignored in further processing
        """
        raise NotImplementedError()


class GameLogParserOsp(GameLogParser, BaseQ3ParserMixin, OspParserMixin):
    event_format = r"^(\d+\.\d+) (.+?):(.*)"

    def __init__(self):
        # time of game init event
        super().__init__()

    def parse_line(self, line: str):
        raw_event = self.line_to_raw_event(line)
        event = self.parse_event(raw_event)
        return event

    def line_to_raw_event(self, line: str) -> events.RawEvent:
        match = re.search(self.event_format, line)
        if match:
            ev_time = match.group(1)
            ev_name = match.group(2)
            ev_payload = match.group(3).strip()
            return events.RawEvent(
                self.mktime(ev_time), ev_name,
                ev_payload if ev_payload else None
            )
        else:
            raise Exception(f"Malformed line, {line}")

    def populate_dates(self, game: Q3Game) -> Q3Game:
        init_ev: events.Q3EVInitGame = None
        exit_ev: events.Q3EventExit = None
        server_time_ev: events.Q3EVServerTime = None
        for event in game.events:
            if isinstance(event, events.Q3EVInitGame):
                assert not init_ev
                init_ev = event
            elif isinstance(event, events.Q3EVServerTime):
                assert not server_time_ev
                server_time_ev = event
            elif isinstance(event, events.Q3EventExit):
                assert not exit_ev
                exit_ev = event

        if server_time_ev:
            game.start_date = server_time_ev.dt
        if all([init_ev, server_time_ev, exit_ev]):
            game_length = exit_ev.time - init_ev.time
            game.finish_date = game.start_date + timedelta(milliseconds=game_length)

        return game

    def mktime(self, event_time: str) -> int:
        seconds, tenths = event_time.split('.')
        return int(seconds) * 1000 + int(tenths) * 100

    def parse_event(self, raw_event: events.RawEvent) -> events.Q3GameEvent:
        if raw_event.name == 'InitGame':
            return self.parse_init_game(raw_event)
        elif raw_event.name == 'ClientUserinfoChanged':
            return self.parse_user_info(raw_event)
        elif raw_event.name == 'Weapon_Stats':
            return self.parse_weapon_stat(raw_event)
        elif raw_event.name == 'Kill':
            return self.parse_kill(raw_event)
        elif raw_event.name == 'ClientDisconnect':
            return self.parse_client_disconnect(raw_event)
        elif raw_event.name == 'Exit':
            return self.parse_exit(raw_event)
        elif raw_event.name == 'ServerTime':
            return self.parse_server_time(raw_event)


class GameLogParserEdawn(GameLogParser, BaseQ3ParserMixin, EdawnParserMixin):
    """
    Edawn has similar log format to OSP
    Enchanced logging (higher granularity) is planned for 1.6.3
    """
    event_format = r"^\s+(\d+:\d+\.\d+) (.+?):(.*)"
    time_format = r"(\d+):(\d+)\.(\d+)"

    def __init__(self):
        super().__init__()

    def parse_line(self, line: str):
        raw_event = self.line_to_raw_event(line)
        event = self.parse_event(raw_event)
        return event

    def line_to_raw_event(self, line: str) -> events.RawEvent:
        match = re.search(self.event_format, line)
        if match:
            ev_time = match.group(1)
            ev_name = match.group(2)
            ev_payload = match.group(3).strip()
            return events.RawEvent(
                self.mktime(ev_time), ev_name,
                ev_payload if ev_payload else None
            )
        else:
            raise Exception(f"Malformed line, {line}")

    def populate_dates(self, game: Q3Game) -> Q3Game:
        init_ev: events.Q3EVInitGame = None
        exit_ev: events.Q3EventExit = None
        server_time_ev: events.Q3EVServerTime = None
        for event in game.events:
            if isinstance(event, events.Q3EVInitGame):
                assert not init_ev
                init_ev = event
            elif isinstance(event, events.Q3EVServerTime):
                assert not server_time_ev
                server_time_ev = event
            elif isinstance(event, events.Q3EventExit):
                assert not exit_ev
                exit_ev = event

        if server_time_ev:
            game.start_date = server_time_ev.dt
        if all([init_ev, server_time_ev, exit_ev]):
            game_length = exit_ev.time - init_ev.time
            game.finish_date = game.start_date + timedelta(milliseconds=game_length)

        return game

    def parse_event(self, raw_event: events.RawEvent) -> events.Q3GameEvent:
        if raw_event.name == 'InitGame':
            return self.parse_init_game(raw_event)
        elif raw_event.name == 'ClientUserinfoChanged':
            return self.parse_user_info(raw_event)
        elif raw_event.name == 'Weapon_Stats':
            return self.parse_weapon_stat(raw_event)
        elif raw_event.name == 'Kill':
            return self.parse_kill(raw_event)
        elif raw_event.name == 'ClientDisconnect':
            return self.parse_client_disconnect(raw_event)
        elif raw_event.name == 'Exit':
            return self.parse_exit(raw_event)
        elif raw_event.name == 'ServerTime':
            return self.parse_server_time(raw_event)

    @classmethod
    def mktime(cls, event_time: str) -> int:
        minutes, seconds, tenths = re.search(cls.time_format, event_time).groups()
        return int(minutes) * 60 * 1000 + int(seconds) * 1000 + int(tenths) * 100

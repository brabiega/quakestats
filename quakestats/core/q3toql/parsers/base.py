import collections
import logging
import re
from typing import (
    Iterator,
)

from quakestats.core.q3toql.parsers import (
    events,
)
from quakestats.core.q3toql.parsers.result import (
    Q3GameLog,
)

logger = logging.getLogger(__name__)

SEPARATOR = '___SEPARATOR___'
RawEvent = collections.namedtuple(
    'RawEvent', ['time', 'name', 'payload']
)


class Q3LogParser():
    """
    Should be a base class for all mod parsers:
    - [ ] baseq3
    - [x] OSP
    - [ ] CPMA - it's probably the same as baseq3, need to check
    """
    def __init__(self, raw_data: str):
        self.raw_data = raw_data

    def games(self):
        game = Q3GameLog()
        for event in self.read_raw_events():
            if event.name == SEPARATOR:
                # this seems to mean that single q3 game has ended or started
                if not game.is_empty():
                    yield game
                game = Q3GameLog()
                continue

            ev = self.build_event(event)
            game.add_event(ev, event.name, event.payload)

    def read_lines(self) -> Iterator[str]:
        for line in self.raw_data.splitlines():
            yield line

    def build_event(self, raw_event: RawEvent) -> events.Q3GameEvent:
        raise NotImplementedError()

    def read_raw_events(self) -> RawEvent:
        raise NotImplementedError()


class DefaultParserMixin():
    GAMETYPE_MAP = {
        "0": "FFA", "1": "DUEL",
        "3": "TDM", "4": "CTF",
    }
    TEAM_MAP = {"0": "FREE", "1": "RED", "2": "BLUE", "3": "SPECTATOR"}

    def parse_init_game(self, ev: RawEvent) -> events.Q3EVInitGame:
        """
        The data coming here usually looks like:
        '\sv_allowDownload\1\sv_maxclients\32\timelimit\15\fraglimit\200
        \dmflags\0\sv_maxPing\0\sv_minPing\0\sv_hostname\Host Q3\sv_maxRate\0
        \sv_floodProtect\0\capturelimit\8\sv_punkbuster\0
        \version\Q3 1.32b linux-i386 Nov 14 2002\g_gametype\0
        \protocol\68\mapname\ospdm1\sv_privateClients\0\server_ospauth\0
        \gamename\osp\gameversion\OSP v1.03a\server_promode\0
        \g_needpass\0\server_freezetag\0'
        (no new line chars)
        Some parsing of this info is done here
        """  # noqa
        game_info = ev.payload.split("\\")[1:]
        game_info_dict = {}
        for key, value in zip(game_info[0::2], game_info[1::2]):
            game_info_dict[key] = value

        game_info_dict["gametype"] = self.GAMETYPE_MAP[
            game_info_dict["g_gametype"]
        ]  # noqa

        gi = game_info_dict
        return events.Q3EVInitGame(
            ev.time, gi['sv_hostname'], gi['gametype'],
            gi['mapname'], gi['fraglimit'],
            gi['capturelimit'], gi['timelimit'],
            gi['gamename']
        )

    def parse_user_info(self, ev: RawEvent) -> events.Q3EVUpdateClient:
        """
        4 n\n0npax\t\0\model\sarge\hmodel\sarge
        \c1\1\c2\5\hc\100\w\0\l\0\rt\0\st\0
        """  # noqa
        match = re.match(r'^(\d+) (.*)$', ev.payload)
        client_id, user_info = match.groups()
        client_id = int(client_id)
        user_data = user_info.split("\\")
        user_info = {}
        for key, value in zip(user_data[0::2], user_data[1::2]):
            user_info[key] = value

        result = events.Q3EVUpdateClient(
            ev.time, client_id, user_info['n'],
            self.TEAM_MAP[user_info['t']],
        )
        return result

    def parse_kill(self, raw_event: RawEvent) -> events.Q3EVPlayerKill:
        match = re.search(r"(\d+) (\d+) (\d+): .* by (\w+)", raw_event.payload)
        killer_id, victim_id, weapon_id, reason = match.groups()
        return events.Q3EVPlayerKill(
            raw_event.time, int(killer_id), int(victim_id), reason
        )


class OspParserMixin():
    STAT_WEAPON_MAP = {
        'MachineGun': 'MACHINEGUN',
        'Shotgun': 'SHOTGUN',
        'G.Launcher': 'GRENADE',
        'R.Launcher': 'ROCKET',
        'LightningGun': 'LIGHTNING',
        'Plasmagun': 'PLASMA',
        'Gauntlet': 'GAUNTLET'
    }

    def parse_weapon_stat(self, ev: RawEvent) -> events.Q3EVPlayerStats:
        """
        Example:
            2 MachineGun:1367:267:0:0 Shotgun:473:107:23:8 G.Launcher:8:1:8:3 R.Launcher:30:11:9:5 LightningGun:403:68:15:10 Plasmagun:326:45:13:8 Given:5252 Recvd:7836 Armor:620 Health:545
        """  # noqa
        payload = ev.payload
        client_id = int(re.search(r'^\d+', payload).group())
        weapons = re.findall(r'([a-zA-Z\.]+):(\d+):(\d+):(\d+):(\d+)', payload)
        # given received armor health
        grah = re.findall(r'([a-zA-Z\.]+):(\d+)', payload)

        event = events.Q3EVPlayerStats(ev.time, client_id)
        for weapon_name, shot, hit, pick, drop in weapons:
            event.add_weapon(
                self.STAT_WEAPON_MAP[weapon_name],
                int(shot), int(hit),
            )

        grah_stats = {
            k: int(v) for k, v in grah
            if k in ['Given', 'Recvd', 'Armor', 'Health']
        }
        event.set_damage(grah_stats['Given'], grah_stats['Recvd'])
        event.set_pickups(grah_stats['Health'], grah_stats['Armor'])
        return event


class Q3LogParserModOsp(
    Q3LogParser, DefaultParserMixin, OspParserMixin
):
    separator_format = r"(\d+\.\d+) ------*$"
    event_format = r"(\d+\.\d+) (.+?):(.*)"

    def read_raw_events(self) -> Iterator[RawEvent]:
        for line in self.read_lines():
            yield self.line_to_raw_event(line)

    def line_to_raw_event(self, line: str) -> RawEvent:
        match = re.search(self.event_format, line)
        if match:
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
            return self.parse_init_game(raw_event)
        elif raw_event.name == 'ClientUserinfoChanged':
            return self.parse_user_info(raw_event)
        elif raw_event.name == 'Weapon_Stats':
            return self.parse_weapon_stat(raw_event)
        elif raw_event.name == 'Kill':
            return self.parse_kill(raw_event)

    @classmethod
    def mktime(cls, event_time: str) -> int:
        seconds, tenths = event_time.split('.')
        return int(seconds) * 1000 + int(tenths) * 100

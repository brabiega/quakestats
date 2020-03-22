import logging
from typing import (
    List,
)

from quakestats.core.q3toql.parsers.result import (
    Q3GameLog,
    Q3MatchLogEvent,
)

logger = logging.getLogger(__name__)
UNKNOWN = -255


class QuakeGame():
    """
    This should be a claas which represents
    single quake match (compatible with Quake Live)
    """
    def __init__(self):
        self.ql_events: List[dict] = []
        self.start_time: int = 0

    def add_match_started(
        self, start_time: int, event: dict
    ):
        self.start_time = start_time
        assert event['TYPE'] == 'MATCH_STARTED'
        self.ql_events.append(event)


class Q3toQL():
    """
    Process Quake3 game log events,
    Produces QuakeLive compatible events
    """
    GAMETYPE_MAP = {
        "0": "FFA",
        "1": "DUEL",
        "3": "TDM",
        "4": "CTF",
    }
    TEAM_MAP = {"0": "FREE", "1": "RED", "2": "BLUE", "3": "SPECTATOR"}

    def __init__(self):
        self.game = None
        self.gamelog = None

    def transform(self, gamelog: Q3GameLog):
        self.game = QuakeGame()
        self.gamelog = gamelog
        time, ev_started = self.build_match_start()
        self.game.add_match_started(time, ev_started)
        return self.game

    def find_event(self, name: str) -> Q3MatchLogEvent:
        ev = [e for e in self.gamelog.events if e.name == name]
        if not ev:
            raise Exception("No such event")

        assert len(ev) == 1
        return ev[0]

    def build_match_start(self):
        ev = self.find_event('InitGame')
        info = self.parse_init_game(ev.payload)
        result = {
            "DATA": {
                "INSTAGIB": 0,
                "FACTORY": "quake3",
                "FACTORY_TITLE": "quake3",
                "INFECTED": 0,
                "TIME_LIMIT": info["timelimit"],
                "TRAINING": 0,
                "FRAG_LIMIT": info["fraglimit"],
                "CAPTURE_LIMIT": info["capturelimit"],
                "SERVER_TITLE": info["sv_hostname"],
                "GAME_TYPE": info["gametype"],
                "QUADHOG": 0,
                "ROUND_LIMIT": 0,
                "MERCY_LIMIT": 0,
                "SCORE_LIMIT": 0,
                "MATCH_GUID": self.gamelog.checksum.hexdigest(),
                "MAP": info['mapname'],
                "PLAYERS": {}  # I think we can live without it
            },
            "TYPE": "MATCH_STARTED",
        }
        return ev.time, result

    def parse_init_game(self, payload):
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
        game_info = payload.split("\\")[1:]
        game_info_dict = {}
        for key, value in zip(game_info[0::2], game_info[1::2]):
            game_info_dict[key] = value

        game_info_dict["gametype"] = self.GAMETYPE_MAP[
            game_info_dict["g_gametype"]
        ]  # noqa

        return game_info_dict

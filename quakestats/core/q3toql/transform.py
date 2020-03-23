import hashlib
import logging
import re
from typing import (
    List,
)

from quakestats.core.q3toql.parsers.result import (
    Q3GameLog,
    Q3MatchLogEvent,
)

logger = logging.getLogger(__name__)
UNKNOWN = -255


class ClientIdentity():
    def __init__(self):
        self.id = None

    def update(self, id: str):
        self.id = id


class QuakeGame():
    """
    This should be a claas which represents
    single quake match (compatible with Quake Live)
    """
    def __init__(self):
        self.ql_events: List[dict] = []
        self.start_time: int = 0
        self.game_guid = None
        self.warmup = False

        # keeps track of current clients
        self.clients = {}
        self.identities = {}

    def add_event(self, time: int, ev_type: str, data: dict):
        game_time = time - self.start_time
        ev = {
            'TYPE': ev_type,
            'DATA': {
                'MATCH_GUID': self.game_guid,
                'TIME': game_time,
                'WARMUP': self.warmup,
            }
        }
        ev['DATA'].update(data)
        self.ql_events.append(ev)
        return ev

    def add_match_started(
        self, time: int, game_guid: str, game_info: dict
    ):
        self.start_time = time
        self.game_guid = game_guid
        self.add_event(time, "MATCH_STARTED", {
            "INSTAGIB": 0,
            "FACTORY": "quake3",
            "FACTORY_TITLE": "quake3",
            "INFECTED": 0,
            "TIME_LIMIT": game_info["timelimit"],
            "TRAINING": 0,
            "FRAG_LIMIT": game_info["fraglimit"],
            "CAPTURE_LIMIT": game_info["capturelimit"],
            "SERVER_TITLE": game_info["sv_hostname"],
            "GAME_TYPE": game_info["gametype"],
            "QUADHOG": 0,
            "ROUND_LIMIT": 0,
            "MERCY_LIMIT": 0,
            "SCORE_LIMIT": 0,
            "MAP": game_info['mapname'],
            "PLAYERS": {}  # I think we can live without it
        })

    def user_info_changed(
        self, time: int, client_id: int, user_info: dict
    ):
        if client_id not in self.clients:
            # create new client identity
            identity = ClientIdentity()
            self.identities[client_id] = identity
            # even if client_id is reused old events will keep
            # references to old client identity

            self.add_event(time, "PLAYER_CONNECT", {
                "NAME": user_info["name"],
                "STEAM_ID": identity,
            })

        old_user_info = self.clients.get(client_id, None)
        identity = self.identities[client_id]
        if (
            old_user_info is None
            or old_user_info['team'] != user_info['team']
        ):
            self.add_event(
                time, 'PLAYER_SWITCHTEAM', {
                    "KILLER": {
                        "STEAM_ID": identity,
                        "OLD_TEAM": (
                            old_user_info['team'] if old_user_info
                            else 'SPECTATOR'
                        ),
                        "TEAM": user_info['team'],
                        "NAME": user_info['name'],
                    },
                }
            )

        self.clients[client_id] = user_info
        # update identity in case of name change during game
        self.identities[client_id].update(
            self.create_steam_id(user_info['name'])
        )

    def create_steam_id(self, name):
        server_domain = "Q3"
        raw_name = re.sub(r"\^\d", "", name).capitalize()
        raw_name = "q3-{}-{}".format(server_domain, raw_name)
        h = hashlib.sha256()
        h.update(raw_name.encode("utf-8"))
        steam_id = h.hexdigest()[:24]
        return steam_id

    def get_events(self):
        for ev in self.ql_events:
            if ev['TYPE'] == 'PLAYER_SWITCHTEAM':
                ev['DATA']['KILLER']['STEAM_ID'] = (
                    ev['DATA']['KILLER']['STEAM_ID'].id
                )
            elif ev['TYPE'] == 'PLAYER_CONNECT':
                ev['DATA']['STEAM_ID'] = ev['DATA']['STEAM_ID'].id
            yield ev


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

        time, game_info = self.build_match_start()
        self.game.add_match_started(
            time, self.gamelog.checksum.hexdigest(), game_info
        )

        for event in self.gamelog.events:
            if event.name == 'ClientUserinfoChanged':
                client_id, user_info = self.parse_user_info_changed(
                    event.payload
                )
                self.game.user_info_changed(event.time, client_id, user_info)

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
        return ev.time, info

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

    def parse_user_info_changed(self, payload):
        """
        4 n\n0npax\t\0\model\sarge\hmodel\sarge
        \c1\1\c2\5\hc\100\w\0\l\0\rt\0\st\0
        """  # noqa
        match = re.match(r'^(\d+) (.*)$', payload)
        client_id, user_info = match.groups()
        client_id = int(client_id)
        user_data = user_info.split("\\")
        user_info = {}
        for key, value in zip(user_data[0::2], user_data[1::2]):
            user_info[key] = value

        result = {
            'name': user_info['n'],
            'team': self.TEAM_MAP[user_info['t']],
            'model': user_info['model']
        }
        return client_id, result

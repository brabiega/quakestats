from copy import (
    deepcopy,
)

from quakestats.core.q3toql import (
    entities,
)

EV_CLS_MAP = {}


def __register(ql_event_cls):
    # I'm too lazy to write metaclass
    EV_CLS_MAP[ql_event_cls.name] = ql_event_cls
    return ql_event_cls


class QLEvent(dict):
    name = None
    payload = {}

    def __init__(self):
        self['TYPE'] = self.name
        self['DATA'] = {}

    def initialize(self, time: int, match_guid: str, warmup: bool = False):
        self['DATA'] = deepcopy(self.payload)
        self['DATA'].update({
            'TIME': time,
            'WARMUP': warmup,
            'MATCH_GUID': match_guid,
        })

    def update_payload(self, data: dict):
        self["DATA"].update(data)

    @property
    def data(self) -> dict:
        return self['DATA']

    @property
    def type(self) -> str:
        return self['TYPE']

    @property
    def match_guid(self) -> str:
        return self.data['MATCH_GUID']


@__register
class MatchStarted(QLEvent):
    name = "MATCH_STARTED"
    payload = {
        "INSTAGIB": 0,
        "FACTORY": "quake3",
        "FACTORY_TITLE": "quake3",
        "INFECTED": 0,
        "TIME_LIMIT": 0,
        "TRAINING": 0,
        "FRAG_LIMIT": 0,
        "CAPTURE_LIMIT": 0,
        "SERVER_TITLE": None,
        "GAME_TYPE": None,
        "QUADHOG": 0,
        "ROUND_LIMIT": 0,
        "MERCY_LIMIT": 0,
        "SCORE_LIMIT": 0,
        "MAP": None,
        "PLAYERS": []  # I think we can live without it
    }

    def set_limits(self, fraglimit: int, timelimit: int, capturelimit: int):
        self.data['FRAG_LIMIT'] = fraglimit
        self.data['TIME_LIMIT'] = timelimit
        self.data['CAPTURE_LIMIT'] = capturelimit

    def set_game_info(self, server_title: str, map_name: str, game_type: str):
        # other modes are not yet supported
        assert game_type in ['FFA', 'CA', 'DUEL']
        self.data['SERVER_TITLE'] = server_title
        self.data['GAME_TYPE'] = game_type
        self.data['MAP'] = map_name

    def add_player(self, steam_id, player_name):
        self.data['PLAYERS'].append({
            "STEAM_ID": steam_id,
            "NAME": player_name,
            "TEAM": 0,
        })


@__register
class PlayerConnect(QLEvent):
    name = "PLAYER_CONNECT"
    payload = {
        'NAME': None,
        'STEAM_ID': None,
    }

    def set_data(self, name: str, steam_id):
        self.data['NAME'] = name
        self.data['STEAM_ID'] = steam_id


@__register
class PlayerDisconnect(PlayerConnect):
    name = "PLAYER_DISCONNECT"


@__register
class PlayerSwitchteam(QLEvent):
    name = 'PLAYER_SWITCHTEAM'
    payload = {
        'KILLER': {
            "STEAM_ID": None,
            "OLD_TEAM": None,
            "TEAM": None,
            "NAME": None,
        }
    }

    def set_data(
        self, steam_id, player_name: str, team_name: str, old_team_name: str
    ):
        inner = self.data['KILLER']
        inner['STEAM_ID'] = steam_id
        inner['NAME'] = player_name
        inner['TEAM'] = team_name
        inner['OLD_TEAM'] = old_team_name

    @property
    def steam_id(self):
        return self.data['KILLER']['STEAM_ID']

    @steam_id.setter
    def steam_id(self, val: str):
        self.data['KILLER']['STEAM_ID'] = val


@__register
class PlayerStats(QLEvent):
    name = "PLAYER_STATS"
    payload = {
        "TIED_TEAM_RANK": None,
        "QUIT": None,
        "WEAPONS": {},
        "MODEL": None,
        "PICKUPS": {},
        "LOSE": 0,
        "DAMAGE": {
            "DEALT": 0,
            "TAKEN": 0
        },
        "RED_FLAG_PICKUPS": 0,
        "SCORE": 0,
        "MAX_STREAK": 0,
        "DEATHS": 0,  # not implemented
        "PLAY_TIME": 0,  # not implemented
        "BLUE_FLAG_PICKUPS": 0,
        "NAME": None,
        "ABORTED": False,
        "HOLY_SHITS": 0,
        "TEAM_RANK": None,
        "KILLS": 0,  # not implemented
        "MEDALS": {},
        "NEUTRAL_FLAG_PICKUPS": 0,
        "TIED_RANK": None,
        "WIN": 0,
        "TEAM_JOIN_TIME": 0,
        "TEAM": None,  # not implemented
        "RANK": 0,
        "STEAM_ID": None
    }
    """
    Many of not implemented fields are determined later
    during game analysis (e.g. total kills or play time)
    """

    def initialize(self, time: int, match_guid: str, warmup: bool = False):
        super().initialize(time, match_guid, warmup)

        # init pickups
        for key in entities.PICKUPS:
            self.data['PICKUPS'][key] = 0

        # init medals
        for key in entities.MEDALS:
            self.data['MEDALS'][key] = 0

    def set_data(self, name: str, steam_id):
        self.data['NAME'] = name
        self.data['STEAM_ID'] = steam_id

    def set_pickups(self, health: int, armor: int):
        self.data['PICKUPS']['TOTAL_HEALTH'] = health
        self.data['PICKUPS']['TOTAL_ARMOR'] = armor

    def set_damage(self, dealt: int, taken: int):
        self.data['DAMAGE']['DEALT'] = dealt
        self.data['DAMAGE']['TAKEN'] = taken

    def add_weapon(self, weapon: str, shots: int, hits: int):
        if weapon not in entities.WEAPONS:
            raise ValueError(f"Invalid weapon '{weapon}'")

        try:
            weapon_stat = self.data['WEAPONS'][weapon]
        except KeyError:
            weapon_stat = {
                'K': None, 'P': None, 'DR': None, 'H': None,
                'D': None, 'DG': None, 'T': None, 'S': None,
            }
            self.data['WEAPONS'][weapon] = weapon_stat

        weapon_stat['H'] = hits
        weapon_stat['S'] = shots


@__register
class PlayerKill(QLEvent):
    name = 'PLAYER_KILL'
    payload = {
        "MOD": None,
        "SUICIDE": None,
        "TEAMKILL": None,
        "ROUND": None,
        "KILLER": {},
        "VICTIM": {},
        "TEAM_ALIVE": None,
        "TEAM_DEAD": None,
        "OTHER_TEAM_ALIVE": None,
        "OTHER_TEAM_DEAD": None,
    }

    def _user_info(self, steam_id) -> dict:
        return {
            "POSITION": {"X": None, "Y": None, "Z": None, },
            "VIEW": {"X": None, "Y": None, "Z": None, },
            "BOT": None,
            "BOT_SKILL": None,
            "WEAPON": None,
            "AMMO": None,
            "AIRBORNE": None,
            "ARMOR": None,
            "SUBMERGED": None,
            "STEAM_ID": steam_id,
            "TEAM": None,
            "POWERUPS": None,
            "SPEED": None,
            "HOLDABLE": None,
            "HEALTH": None,
            "NAME": None,
        }

    def set_data(self, mod: str):
        if mod not in entities.MODS:
            raise ValueError(f"Invalid mod, '{mod}'")
        self.data['MOD'] = mod

    def add_killer(self, steam_id):
        self.data['KILLER'] = self._user_info(steam_id)

    def add_victim(self, steam_id):
        self.data['VICTIM'] = self._user_info(steam_id)

    @property
    def time(self):
        return self.data['TIME']


@__register
class PlayerDeath(PlayerKill):
    name = 'PLAYER_DEATH'


@__register
class MatchReport(QLEvent):
    name = 'MATCH_REPORT'
    payload = {
        "LAST_TEAMSCORER": None,
        "MERCY_LIMIT": None,
        "EXIT_MSG": None,
        "MAP": None,
        "TSCORE1": None,
        "INSTAGIB": None,
        "LAST_SCORER": None,
        "TIME_LIMIT": None,
        "TRAINING": None,
        "FRAG_LIMIT": None,
        "CAPTURE_LIMIT": None,
        "GAME_LENGTH": None,
        "SERVER_TITLE": None,
        "RESTARTED": None,
        "FACTORY": None,
        "MATCH_GUID": None,  # set in constructor
        "ABORTED": None,
        "INFECTED": None,
        "SCORE_LIMIT": None,
        "LAST_LEAD_CHANGE_TIME": None,
        "FIRST_SCORER": None,
        "FACTORY_TITLE": None,
        "TSCORE0": None,
        "GAME_TYPE": None,
        "QUADHOG": None,
        "ROUND_LIMIT": None,
    }

    def set_data(
        self, exit_msg: str, game_length: int, map: str, hostname: str
    ):
        self.data['SERVER_TITLE'] = hostname
        self.data['EXIT_MSG'] = exit_msg
        self.data['GAME_LENGTH'] = game_length
        self.data['MAP'] = map

    def set_limits(self, fraglimit: int, capturelimit: int, timelimit: int):
        self.data['FRAG_LIMIT'] = fraglimit
        self.data['CAPTURE_LIMIT'] = capturelimit
        self.data['TIME_LIMIT'] = timelimit


@__register
class PlayerMedal(QLEvent):
    name = 'PLAYER_MEDAL'


@__register
class RoundOver(QLEvent):
    name = 'ROUND_OVER'


def create_from_ql_dict(data: dict) -> QLEvent:
    cls = EV_CLS_MAP[data['TYPE']]
    obj = cls()
    obj.update(data)
    return obj

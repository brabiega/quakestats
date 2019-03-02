import hashlib
import logging
import re
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class ParsingError(Exception):
    pass


class PlayerId():
    """
    Helper class to keep proper fake steam_id
    when client connects with different name
    """
    def __init__(self):
        self.steam_id = None


class Q3toQL():
    """
    Transforms quake 3 event stream into quake live events
    The transformation result is a dict
    result = {
            "unknown_entries": [],
            "events": [],
            "server_info": {},
            "warmup": False,
            "start_date": None,
            "finish_date": None,
        }

    """
    base_format = r"(\d+\.\d+) (.+?):(.*)"
    NOT_IMPLEMENTED = 'NotImplemented'
    GAMETYPE_MAP = {
        "0": "FFA",
        "1": "DUEL",
        "3": "TDM",
        "4": "CTF",
    }
    TEAM_MAP = {
        '0': 'FREE',
        '1': 'RED',
        '2': 'BLUE',
        '3': 'SPECTATOR'
    }

    def __init__(self, raw_events):
        self.raw_events = raw_events
        self.match_guid = None
        self.server_time = None
        self.time_offset = None
        # need server domain to support
        # unique players with the same name
        # playing on completely different servers
        self.server_domain = None
        self.match_report_event = None
        self.players = {}
        self.player_world = {
            'name': '__world__',
            'team': '0',
            'player_id': 'q3-world',
        }
        self.client_player_map = {}
        self.result = {
            "unknown_entries": [],
            "events": [],
            "server_info": {},
            "warmup": False,
            "start_date": None,
            "finish_date": None,
        }
        self.debug_events = []
        self.hook_processors()

    def hook_processors(self):
        self.event_processors = {
            "InitGame": self.on_init,
            "ServerTime": self.on_server_time,
            "Warmup": self.on_warmup,
            "ClientUserinfoChanged": self.on_client_info_changed,
            "ClientBegin": self.on_client_begin,
            "Kill": self.on_kill,
            "Exit": self.on_exit,
            "ClientDisconnect": self.on_client_disconnect,
            "Weapon_Stats": self.on_weapon_stats,
        }

    def extract(self, data):
        match = re.search(self.base_format, data)
        ts, name, args = match.groups()
        args = args.strip()
        ts = float(ts)
        return ts, name, args

    def process(self):
        assert not self.result['events']
        for raw_event in self.raw_events:
            events = self.process_raw_event(raw_event)
            self.debug_events.append(
                (raw_event, events))
            if type(events) is list:
                self.result['events'].extend(events)
            elif events:
                self.result['events'].append(events)
        if self.match_report_event:
            self.result['events'].append(self.match_report_event)

        self.materialize_ids()

    def materialize_ids(self):
        """
        Player unique ID is built from server domain and player name.
        Because of that we need to overcome such bizzare stuff like:
        - player changing name ingame
        - player connecting with default name then set proper name once connected
        - probably more
        Function extracts unique player ID from PlayerId object and static id for all events
        Should be executed at the end of a match.
        """  # noqa
        for ev in self.result['events']:
            try:
                if isinstance(ev['DATA']['STEAM_ID'], PlayerId):
                    ev['DATA']['STEAM_ID'] = ev['DATA']['STEAM_ID'].steam_id
            except KeyError:
                pass
            try:
                if isinstance(ev['DATA']['KILLER']['STEAM_ID'], PlayerId):
                    ev['DATA']['KILLER']['STEAM_ID'] = ev['DATA']['KILLER']['STEAM_ID'].steam_id  # noqa
            except KeyError:
                pass
            try:
                if isinstance(ev['DATA']['VICTIM']['STEAM_ID'], PlayerId):
                    ev['DATA']['VICTIM']['STEAM_ID'] = ev['DATA']['VICTIM']['STEAM_ID'].steam_id  # noqa
            except KeyError:
                pass

    def process_raw_event(self, raw_event):
        ts, name, args = self.extract(raw_event)
        try:
            process_func = self.event_processors[name]
        except KeyError:
            self.result['unknown_entries'].append((ts, name, args))
        else:
            return process_func(ts, name, args)

    def ts2match_time(self, ts):
        assert self.time_offset is not None
        assert self.time_offset >= 0
        result = round(ts - self.time_offset, 2)
        assert result >= 0
        return result

    def get_player(self, client_id, allow_disconnected=False):
        if client_id == '1022':
            return self.player_world
        player_id = self.client_player_map[client_id]
        player = self.players[player_id]
        if not allow_disconnected and player['is_disconnected']:
            raise KeyError("Player disconnected")
        return player

    def set_player_team(self, client_id, team_id):
        """Returns True if changed, False if no change"""
        pass

    def build_guid(self):
        server = self.result['server_info']['sv_hostname']
        server_time = self.result['start_date']
        if not server or not server_time:
            return None
        h = hashlib.sha256()
        h.update("q3".encode('utf-8'))
        h.update(str(server).encode('utf-8'))
        h.update(str(server_time).encode('utf-8'))
        return h.hexdigest()[:32]

    # ----------------------------------------PROCESSORS ->
    def on_init(self, ts, name, args):
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
        self.time_offset = ts
        data = args
        game_info = data.split("\\")[1:]
        game_info_dict = {}
        for key, value in zip(game_info[0::2], game_info[1::2]):
            game_info_dict[key] = value

        game_info_dict["gametype"] = self.GAMETYPE_MAP[game_info_dict["g_gametype"]]  # noqa
        logger.debug("Game type '{}' map '{}'".format(
            game_info_dict['gametype'], game_info_dict["mapname"]))

        self.result['server_info'].update(game_info_dict)

    def on_server_time(self, ts, name, args):
        """Usual data
        '20170404123334 12:33:34 (04 Apr 2017)'
        All events have timsetamp relative to server start time
        Thus the real time of an event has to be calculated
        This is OSP specific :/ and can't be used to build guid with vq3
        """
        data = args

        start_date = datetime.strptime(
            data.split()[0].strip(), "%Y%m%d%H%M%S")

        self.result['start_date'] = start_date

        logger.debug("Game started at {}, server timestamp {}".format(
            start_date, ts))

        si = self.result['server_info']
        self.match_guid = self.build_guid()
        event = {
            'TYPE': 'MATCH_STARTED',
            'DATA': {
                'MATCH_GUID': self.match_guid,
                'GAME_TYPE': si['gametype'],
                'MAP': si['mapname'],
                'TIME_LIMIT': si['timelimit'],
                'FRAG_LIMIT': si['fraglimit'],
                'CAPTURE_LIMIT': si['capturelimit'],
                'SERVER_TITLE': si['sv_hostname'],
                'PLAYERS': [{
                    'STEAM_ID': self.player_world['player_id'],
                    'NAME': self.player_world['name'],
                    'TEAM': 0,
                }]
            }
        }
        return event

    def on_warmup(self, ts, name, args):
        self.result["warmup"] = True

    def create_steam_id(self, name):
        raw_name = re.sub(r"\^\d", "", name).capitalize()
        raw_name = "q3-{}-{}".format(self.server_domain, raw_name)
        h = hashlib.sha256()
        h.update(raw_name.encode('utf-8'))
        steam_id = h.hexdigest()[:24]
        return steam_id

    def on_client_info_changed(self, ts, name, args):
        """
        Finally some client identification, looks like:
        '4 n\n0npax\t\0\model\sarge\hmodel\sarge\c1\1\c2\5\hc\100\w\0\l\0\rt\0\st\0'
        """  # noqa
        time = self.ts2match_time(ts)
        data = args
        match = re.search(r"(\d+) (.*)", data)
        client_id, user_info = match.groups()
        user_data = user_info.split("\\")
        user_info = {}
        for key, value in zip(user_data[0::2], user_data[1::2]):
            user_info[key] = value

        user_info['name'] = user_info['n']
        user_info['team'] = user_info['t']
        del user_info['n']
        del user_info['t']

        # We can get multiple messages during the match
        # Client may connect with temporary name as well :C
        new_connection = False
        result = []
        try:
            player = self.get_player(client_id)

            # handle name change (update steam ID)
            # workaround for missing consistent player id
            # TODO possible clash? player disconnect + new player connect?
            if user_info['name'] != player['name']:
                new_id = self.create_steam_id(
                    user_info['name'])
                logger.info(
                    "Player name change detected. "
                    "'{}' -> '{}'"
                    .format(player['name'], user_info['name']))
                player['name'] = user_info['name']
                player['player_id'].steam_id = new_id

            assert player['team']
            assert user_info['team']
            assert player['player_id']
            assert player['name']
            assert int(player['team']) <= 3
            if player['team'] != user_info['team']:
                ev_switch_team = {
                    'TYPE': 'PLAYER_SWITCHTEAM',
                    'DATA': {
                        'MATCH_GUID': self.match_guid,
                        'TIME': time,
                        'WARMUP': self.result['warmup'],
                        'KILLER': {
                            'STEAM_ID': player['player_id'],
                            'OLD_TEAM': self.TEAM_MAP[player['team']],
                            'TEAM': self.TEAM_MAP[user_info['team']],
                            'NAME': player['name'],
                        }
                    }
                }
                result.append(ev_switch_team)

            player.update(user_info)
        except KeyError:
            # Create new player
            new_connection = True
            steam_id = self.create_steam_id(user_info['name'])
            player_id = PlayerId()
            player_id.steam_id = steam_id

            self.players[player_id] = user_info
            self.client_player_map[client_id] = player_id
            user_info['player_id'] = player_id
            player = user_info
            player['is_disconnected'] = False

        if new_connection:
            ev_connected = {
                'TYPE': 'PLAYER_CONNECT',
                'DATA': {
                    'MATCH_GUID': self.match_guid,
                    'TIME': time,
                    'WARMUP': self.result['warmup'],
                    'NAME': player['name'],
                    'STEAM_ID': player['player_id'],
                }
            }
            ev_switch_team = {
                'TYPE': 'PLAYER_SWITCHTEAM',
                'DATA': {
                    'MATCH_GUID': self.match_guid,
                    'TIME': time,
                    'WARMUP': self.result['warmup'],
                    'KILLER': {
                        'STEAM_ID': player['player_id'],
                        'OLD_TEAM': 'SPECTATOR',
                        'TEAM': self.TEAM_MAP[user_info['team']],
                        'NAME': player['name'],
                    }
                }
            }
            result.append(ev_connected)
            result.append(ev_switch_team)

        return result

    def on_client_begin(self, ts, name, args):
        # nothing to do here
        pass

    def on_kill(self, ts, name, args):
        time = self.ts2match_time(ts)
        match = re.search(r"(\d+) (\d+) (\d+): .* by (\w+)", args)
        killer_id, victim_id, weapon_id, weapon_name = match.groups()
        killer = self.get_player(killer_id)
        victim = self.get_player(victim_id)

        if not weapon_name.startswith('MOD_'):
            raise ParsingError(
                "Invalid weapon '{}' at event '{}'"
                .format(weapon_name, (ts, name, args)))

        killer_info = {
            "WEAPON": self.NOT_IMPLEMENTED,
            "HEALTH": self.NOT_IMPLEMENTED,
            "HOLDABLE": self.NOT_IMPLEMENTED,
            "AMMO": self.NOT_IMPLEMENTED,
            "VIEW": self.NOT_IMPLEMENTED,
            "NAME": killer['name'],
            "POWERUPS": self.NOT_IMPLEMENTED,
            "SUBMERGED": self.NOT_IMPLEMENTED,
            "STEAM_ID": killer['player_id'],
            "AIRBORNE": self.NOT_IMPLEMENTED,
            "TEAM": killer['team'],
            "POSITION": self.NOT_IMPLEMENTED,
            "SPEED": self.NOT_IMPLEMENTED,
            "BOT_SKILL": self.NOT_IMPLEMENTED,
            "ARMOR": self.NOT_IMPLEMENTED,
            "BOT": self.NOT_IMPLEMENTED,
        }
        victim_info = {
            "WEAPON": self.NOT_IMPLEMENTED,
            "HEALTH": self.NOT_IMPLEMENTED,
            "HOLDABLE": self.NOT_IMPLEMENTED,
            "AMMO": self.NOT_IMPLEMENTED,
            "VIEW": self.NOT_IMPLEMENTED,
            "NAME": victim['name'],
            "POWERUPS": self.NOT_IMPLEMENTED,
            "SUBMERGED": self.NOT_IMPLEMENTED,
            "STEAM_ID": victim['player_id'],
            "AIRBORNE": self.NOT_IMPLEMENTED,
            "TEAM": victim['team'],
            "POSITION": self.NOT_IMPLEMENTED,
            "SPEED": self.NOT_IMPLEMENTED,
            "BOT_SKILL": self.NOT_IMPLEMENTED,
            "ARMOR": self.NOT_IMPLEMENTED,
            "BOT": self.NOT_IMPLEMENTED,
        }
        data = {
            'TEAMKILL': self.NOT_IMPLEMENTED,
            'MATCH_GUID': self.match_guid,
            'MOD': weapon_name.split('MOD_')[1],
            'TEAM_ALIVE': self.NOT_IMPLEMENTED,
            'TEAM_DEAD': self.NOT_IMPLEMENTED,
            'TIME': time,
            'ROUND': self.NOT_IMPLEMENTED,
            'KILLER': killer_info,
            'VICTIM': victim_info,
            'SUICIDE': self.NOT_IMPLEMENTED,
            'OTHER_TEAM_ALIVE': self.NOT_IMPLEMENTED,
            'OTHER_TEAM_DEAD': 'NotImlemented',
            'WARMUP': self.result['warmup'],
        }

        ev_death = {
            'TYPE': 'PLAYER_DEATH',
            'DATA': data
        }
        ev_kill = {
            'TYPE': 'PLAYER_KILL',
            'DATA': data
        }

        return [ev_kill, ev_death]

    def on_exit(self, ts, name, args):
        reason = args
        time = self.ts2match_time(ts)

        if self.result["start_date"]:
            self.result["finish_date"] = \
                self.result["start_date"] + timedelta(seconds=time)

        self.match_report_event = {
            'TYPE': 'MATCH_REPORT',
            'DATA': {
                "EXIT_MSG": reason,
                "FIRST_SCORER": self.NOT_IMPLEMENTED,
                "SCORE_LIMIT": self.NOT_IMPLEMENTED,
                "FRAG_LIMIT": int(self.result['server_info']['fraglimit']),
                "ROUND_LIMIT": self.NOT_IMPLEMENTED,
                "MAP": self.result['server_info']['mapname'],
                "TRAINING": self.NOT_IMPLEMENTED,
                "LAST_TEAMSCORER": self.NOT_IMPLEMENTED,
                "SERVER_TITLE": self.result['server_info']['sv_hostname'],
                "GAME_LENGTH": time,
                "TIME_LIMIT": int(self.result['server_info']['timelimit']),
                "CAPTURE_LIMIT": int(self.result['server_info']['capturelimit']),  # noqa
                "LAST_SCORER": self.NOT_IMPLEMENTED,
                "RESTARTED": self.NOT_IMPLEMENTED,
                "TSCORE1": self.NOT_IMPLEMENTED,
                "MATCH_GUID": self.match_guid,
                "GAME_TYPE": self.result['server_info']['gametype'],
                "QUADHOG": self.NOT_IMPLEMENTED,
                "LAST_LEAD_CHANGE_TIME": self.NOT_IMPLEMENTED,
                "ABORTED": False,
                "TSCORE0": self.NOT_IMPLEMENTED,
                "FACTORY": self.NOT_IMPLEMENTED,
                "INFECTED": self.NOT_IMPLEMENTED,
                "FACTORY_TITLE": self.NOT_IMPLEMENTED,
                "INSTAGIB": self.NOT_IMPLEMENTED,
                "MERCY_LIMIT": self.NOT_IMPLEMENTED,
            }
        }
        # Can't produce the event here, need to preserve the order and
        # this should be the last event
        # in q3 after this message there were additional logs with client
        # weapon stats

    def on_client_disconnect(self, ts, name, args):
        time = self.ts2match_time(ts)
        client_id = args
        player = self.get_player(client_id)
        player['is_disconnected'] = True
        # Can't remove client here since there are additional log entries
        # indicating client stats

        event = {
            'TYPE': 'PLAYER_DISCONNECT',
            'DATA': {
                'STEAM_ID': player['player_id'],
                'MATCH_GUID': self.match_guid,
                'WARMUP': self.result['warmup'],
                'TIME': time,
                'NAME': player['name']
            }
        }
        return event

    stat_weapon_map = {
        "Gauntlet": "GAUNTLET",
        "MachineGun": "MACHINEGUN",
        "Shotgun": "SHOTGUN",
        "G.Launcher": "GRENADE",
        "R.Launcher": "ROCKET",
        "LightningGun": "LIGHTNING",
        "Plasmagun": "PLASMA",
        "Railgun": "RAILGUN",
    }

    def on_weapon_stats(self, ts, name, args):
        """
        Example:
            963.5 Weapon_Stats: 2 MachineGun:1367:267:0:0 Shotgun:473:107:23:8 G.Launcher:8:1:8:3 R.Launcher:30:11:9:5 LightningGun:403:68:15:10 Plasmagun:326:45:13:8 Given:5252 Recvd:7836 Armor:620 Health:545
        """  # noqa

        items = args.split(' ')
        client_id = items[0]
        player = self.get_player(client_id, allow_disconnected=True)

        stats = {}
        weapon_stats = {
        }

        for item in items[1:]:
            subitems = item.split(':')
            stats[subitems[0]] = subitems[1:]

        damage_stats = {
            "DEALT": int(stats.get("Given", [0])[0]),
            "TAKEN": int(stats.get("Recvd", [0])[0]),
        }
        pickups = {
            "TOTAL_ARMOR": int(stats.get("Armor", [0])[0]),
            "TOTAL_HEALTH": int(stats.get("Health", [0])[0]),
        }

        for key, value in stats.items():
            try:
                weapon_name = self.stat_weapon_map[key]
            except KeyError:
                continue

            weapon_stats[weapon_name] = {
                # shoot
                "S": int(value[0]),
                # hit
                "H": int(value[1]),
                # kill
                "K": 0,
                # death
                "D": 0,
            }

        # TODO
        # following event is not fully compatible with quake live as quake 3
        # stats from OSP have much less details
        # e.g. there is no damage given per weapon
        # R.Launcher:30:11:9:5 - seems to be SHOOT:HIT:KILL:DEATH?
        # dunno, ignore for now.
        ev = {
            "DATA": {
                "ABORTED": False,
                'STEAM_ID': player['player_id'],
                'NAME': player['name'],
                'MATCH_GUID': self.match_guid,
                'DAMAGE': damage_stats,
                'WARMUP': self.result['warmup'],
                # pickups have additional fields (TOTAL_HEALTH, TOTAL_ARMOR)
                'PICKUPS': pickups,
                "WEAPONS": self.NOT_IMPLEMENTED,

            },
            "TYPE": "PLAYER_STATS",
        }

        return ev

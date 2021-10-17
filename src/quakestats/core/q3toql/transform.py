import hashlib
import logging
import re

from quakestats.core.game import (
    qlevents,
)
from quakestats.core.game.base import (
    QuakeGame,
)
from quakestats.core.q3parser import events as q3_events
from quakestats.core.q3parser.parser import (
    Q3Game,
)

logger = logging.getLogger(__name__)


class ClientQ3World():
    def __init__(self):
        self.id = 1022
        self.name = '__world__'
        self.is_connected = True

    @property
    def lazy_identity(self):
        return self

    def resolve(self) -> str:
        return 'q3-world'


class Client():
    def __init__(self, id: int, name: str, team: str):
        self.id = id
        self.name = name
        self.team = team
        self.is_connected = True

    def disconnect(self) -> bool:
        self.is_connected = False

    def update(self, name: str, team: str):
        self.name = name
        self.team = team

    @property
    def lazy_identity(self):
        return self

    def resolve(self) -> str:
        """
        resolve identity
        """
        server_domain = "Q3"
        raw_name = re.sub(r"\^\d", "", self.name).capitalize()
        raw_name = "q3-{}-{}".format(server_domain, raw_name)
        h = hashlib.sha256()
        h.update(raw_name.encode("utf-8"))
        steam_id = h.hexdigest()[:24]
        return steam_id


class Quake3Game(QuakeGame):
    """
    This should be a class which represents
    single quake match (compatible with Quake Live)

    QL event support:
    [+] - MATCH_STARTED
    [+] - PLAYER_CONNECT
    [+] - PLAYER_SWITCHTEAM - FREE/RED/BLUE/SPECTATOR
    [*] - PLAYER_STATS team is 0,1,2, partial implementation
    [*] - PLAYER_KILL, partial implementation
    [*] - PLAYER_DEATH, partial implementation
    [+] - PLAYER_DISCONNECT
    [-] - PLAYER_MEDAL, not supported no such info in Quake3 logs
    [*] - MATCH_REPORT, partial implementation
    [ ] - ROUND_OVER
    [?] - Q3_PLAYER_QUAD - Is there an event for taking an item?
    """
    def __init__(self):
        super().__init__("Q3")

        # keeps track of current clients
        self.clients = {
            1022: ClientQ3World()
        }

    def add_event(self, time: int, ev_cls) -> qlevents.QLEvent:
        game_time = (time - self.start_time) / 1000
        ev = ev_cls()
        ev.initialize(game_time, self.game_guid, self.warmup)
        self.ql_events.append(ev)
        return ev

    def add_match_started(
        self, game_guid: str, ev: q3_events.Q3EVInitGame
    ):
        self.start_time = ev.time
        self.game_guid = game_guid
        event: qlevents.MatchStarted = self.add_event(
            ev.time, qlevents.MatchStarted
        )
        event.set_game_info(ev.hostname, ev.mapname, ev.gametype)
        event.set_limits(ev.fraglimit, ev.timelimit, ev.capturelimit)
        event.add_player("q3-world", '__world__')
        self.metadata.map = ev.mapname
        self.metadata.timelimit = ev.timelimit
        self.metadata.fraglimit = ev.fraglimit
        self.metadata.capturelimit = ev.capturelimit
        self.metadata.hostname = ev.hostname
        self.valid_start = True

    def user_info_changed(
        self, ev: q3_events.Q3EVUpdateClient
    ):
        client = self.clients.get(ev.client_id, None)
        just_connected = False
        if not client or not client.is_connected:
            # create new client identity
            client = Client(ev.client_id, ev.name, ev.team)
            self.clients[ev.client_id] = client
            just_connected = True

        if just_connected:
            ql_ev: qlevents.PlayerConnect = self.add_event(
                ev.time, qlevents.PlayerConnect
            )
            ql_ev.set_data(client.name, client.lazy_identity)

        if (
            just_connected or
            client.team != ev.team
        ):
            ql_ev: qlevents.PlayerSwitchteam = self.add_event(
                ev.time, qlevents.PlayerSwitchteam
            )
            ql_ev.set_data(
                client.lazy_identity, ev.name, ev.team,
                'SPECTATOR' if just_connected else client.team
            )

        client.update(ev.name, ev.team)

    def get_client(self, client_id: int) -> Client:
        return self.clients[client_id]

    def get_events(self):
        for ev in self.ql_events:
            if ev.type == 'PLAYER_SWITCHTEAM':
                ev.data['KILLER']['STEAM_ID'] = (
                    ev.data['KILLER']['STEAM_ID'].resolve()
                )
            elif ev.type in [
                'PLAYER_CONNECT', 'PLAYER_STATS', 'PLAYER_DISCONNECT', 'PLAYER_QUAD'
            ]:
                ev.data['STEAM_ID'] = ev.data['STEAM_ID'].resolve()

            elif ev.type == 'PLAYER_KILL':
                ev.data['KILLER']['STEAM_ID'] = (
                    ev.data['KILLER']['STEAM_ID'].resolve()
                )
                ev.data['VICTIM']['STEAM_ID'] = (
                    ev.data['VICTIM']['STEAM_ID'].resolve()
                )
            yield ev

    def weapon_stats(self, ev: q3_events.Q3EVPlayerStats):
        ql_ev: qlevents.PlayerStats = self.add_event(
            ev.time, qlevents.PlayerStats
        )
        client = self.get_client(ev.client_id)
        for name, stats in ev.weapons.items():
            stats: q3_events.Q3EVPlayerStats.WeaponStat = stats
            ql_ev.add_weapon(name, stats.shots, stats.hits)

        ql_ev.set_data(client.name, client.lazy_identity)
        ql_ev.set_pickups(ev.pickups.health, ev.pickups.armor)
        ql_ev.set_damage(ev.damage.given, ev.damage.received)

    def kill(self, ev: q3_events.Q3EVPlayerKill):
        ql_ev: qlevents.PlayerKill = self.add_event(
            ev.time, qlevents.PlayerKill
        )
        ql_ev_death: qlevents.PlayerDeath = self.add_event(
            ev.time, qlevents.PlayerDeath
        )

        killer = self.get_client(ev.client_id)
        victim = self.get_client(ev.victim_id)
        ql_ev.add_killer(killer.lazy_identity)
        ql_ev.add_victim(victim.lazy_identity)
        mod = ev.reason.split("MOD_")[1]
        ql_ev.set_data(mod)

        # same event different 'type'
        ql_ev_death['DATA'] = ql_ev['DATA']

    def client_disconnect(self, ev: q3_events.Q3EVClientDisconnect):
        ql_ev: qlevents.PlayerDisconnect = self.add_event(
            ev.time, qlevents.PlayerDisconnect
        )
        client = self.get_client(ev.client_id)
        ql_ev.set_data(client.name, client.lazy_identity)
        client.disconnect()

    def exit(self, ev: q3_events.Q3EventExit):
        ql_ev: qlevents.MatchReport = self.add_event(
            ev.time, qlevents.MatchReport
        )
        duration = ev.time - self.start_time
        ql_ev.set_data(
            ev.reason, duration, self.metadata.map,
            self.metadata.hostname
        )
        ql_ev.set_limits(
            self.metadata.fraglimit,
            self.metadata.capturelimit,
            self.metadata.timelimit,
        )
        self.valid_end = True
        self.metadata.duration = (ev.time - self.start_time) / 1000

    def item(self, ev: q3_events.Q3EVItem):
        if ev.item_name != 'item_quad':
            return

        ql_ev: qlevents.PlayerQuad = self.add_event(ev.time, qlevents.PlayerQuad)
        client = self.get_client(ev.client_id)
        ql_ev.set_data(client.lazy_identity)


class Q3toQL():
    """
    Process Quake3 game log events,
    Produces QuakeLive compatible events
    """

    def __init__(self):
        self.game = None
        self.gamelog = None

    def transform(self, gamelog: Q3Game):
        self.game = Quake3Game()
        self.gamelog = gamelog
        self.game.metadata.start_date = gamelog.start_date
        self.game.metadata.finish_date = gamelog.finish_date

        init_game = [
            e for e in self.gamelog.events
            if isinstance(e, q3_events.Q3EVInitGame)
        ][0]
        self.game.add_match_started(
            self.gamelog.identifier, init_game
        )

        ev_exit = None
        for event in self.gamelog.events:
            if isinstance(event, q3_events.Q3EVUpdateClient):
                self.game.user_info_changed(event)
            elif isinstance(event, q3_events.Q3EVPlayerStats):
                self.game.weapon_stats(event)
            elif isinstance(event, q3_events.Q3EVPlayerKill):
                self.game.kill(event)
            elif isinstance(event, q3_events.Q3EVClientDisconnect):
                self.game.client_disconnect(event)
            elif isinstance(event, q3_events.Q3EVItem):
                self.game.item(event)

            # Exit event can be produced before player stats in q3
            # for compatibility with QL we will always emmit
            # MATCH_REPORT as a last event
            elif isinstance(event, q3_events.Q3EventExit):
                ev_exit = event

        if ev_exit:
            self.game.exit(ev_exit)

        return self.game

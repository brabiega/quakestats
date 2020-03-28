"""
Parsed, structurized Quake3 events
"""
from collections import (
    namedtuple,
)

from quakestats.core.q3toql import (
    entities,
)


class Q3GameEvent():
    def __init__(self, ev_time: int):
        assert ev_time >= 0
        self.time = ev_time


class Q3EVInitGame(Q3GameEvent):
    def __init__(
        self, ev_time: int,
        hostname: str, gametype: str, mapname: str,
        fraglimit: int, capturelimit: int, timelimit: int,
        modname: str
    ):
        super().__init__(ev_time)
        if gametype not in ['FFA', 'CA', 'DUEL']:
            raise ValueError("Invalid gametype, got {}".format(gametype))
        self.hostname = hostname
        self.gametype = gametype
        self.mapname = mapname
        self.fraglimit = fraglimit
        self.timelimit = timelimit
        self.capturelimit = capturelimit
        self.modname = modname


class Q3EVUpdateClient(Q3GameEvent):
    def __init__(
        self, ev_time: int, client_id: int, name: str, team: str
    ):
        super().__init__(ev_time)
        if team not in ["RED", "BLUE", "SPECTATOR", "FREE"]:
            raise ValueError("Invalid team, got {}".format(team))

        self.client_id = client_id
        self.name = name
        self.team = team


class Q3EVPlayerStats(Q3GameEvent):
    WeaponStat = namedtuple('WeaponStat', ['shots', 'hits'])
    DamageStat = namedtuple('DamageStat', ['given', 'received'])
    PickupStats = namedtuple('PickupStats', ['health', 'armor'])

    def __init__(
        self, ev_time: int, client_id: int
    ):
        super().__init__(ev_time)
        self.client_id = client_id
        self.weapons = {}
        self.pickups = self.PickupStats(0, 0)
        self.damage = self.DamageStat(0, 0)

    def add_weapon(self, name: str, shots: int, hits: int):
        assert name in entities.WEAPONS, f"Got {name}"
        self.weapons[name] = self.WeaponStat(shots, hits)

    def set_damage(self, given: int, received: int):
        self.damage = self.DamageStat(given, received)

    def set_pickups(self, health: int, armor: int):
        self.pickups = self.PickupStats(health, armor)
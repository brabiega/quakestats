import re
from datetime import (
    datetime,
)

from quakestats.core.q3parser import (
    events,
)

RawEvent = events.RawEvent


class OspParserMixin():
    STAT_WEAPON_MAP = {
        'MachineGun': 'MACHINEGUN',
        'Machinegun': 'MACHINEGUN',
        'Shotgun': 'SHOTGUN',
        'G.Launcher': 'GRENADE',
        'R.Launcher': 'ROCKET',
        'LightningGun': 'LIGHTNING',
        'Plasmagun': 'PLASMA',
        'Gauntlet': 'GAUNTLET',
        'Railgun': 'RAILGUN',
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
            # seems like some bug in OSP
            if weapon_name == 'None':
                continue
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

    def parse_server_time(self, ev: RawEvent) -> datetime:
        """
        Example: 20170622112609  11:26:09 (22 Jun 2017)
        """
        data = ev.payload
        server_date = datetime.strptime(
            data.split()[0].strip(), "%Y%m%d%H%M%S"
        )
        event = events.Q3EVServerTime(ev.time, server_date)
        return event

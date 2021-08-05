import re

from quakestats.core.q3parser import (
    events,
)

RawEvent = events.RawEvent


class BaseQ3ParserMixin():
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
            gi['mapname'], int(gi.get('fraglimit', 0)),
            int(gi.get('capturelimit', 0)), int(gi.get('timelimit', 0)),
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

    def parse_client_disconnect(
        self, raw_event: RawEvent
    ) -> events.Q3EVClientDisconnect:
        match = re.search(r"(\d+)", raw_event.payload)
        client_id = int(match.groups()[0])
        return events.Q3EVClientDisconnect(raw_event.time, client_id)

    def parse_exit(self, raw_event: RawEvent) -> events.Q3EventExit:
        match = re.search(r"(.*)", raw_event.payload)
        reason = match.groups()[0]
        return events.Q3EventExit(raw_event.time, reason)

    def parse_item(self, raw_event: RawEvent) -> events.Q3EVItem:
        """
        3 item_quad
        """
        match = re.search(r"(\d+) (\w+)", raw_event.payload)
        client_id, item_name = match.groups()
        return events.Q3EVItem(raw_event.time, int(client_id), item_name)

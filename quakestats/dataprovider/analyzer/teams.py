"""
Logic related to keeping track of teams
"""


class TeamLifecycle():
    """
    holds history of joins/leaves/changes
    holds teams at current moment
    """
    def __init__(self):
        self.match_guid = None  # [fmi]
        # list of team switches
        # [ts, steam_id, from, to]
        self.switches = []  # [MATCH_STARTED][PLAYER_SWITCHTEAM]

        # initial values from [MATCH_STARTED]
        self.spectator = set()
        self.free = set()
        self.red = set()
        self.blue = set()

        self.team_map = {
            "SPECTATOR": self.spectator,
            "RED": self.red,
            "BLUE": self.blue,
            "FREE": self.free,
        }
        self.team_id_to_name = {
            0: "FREE",
            1: "RED",
            2: "BLUE",
            3: "SPECTATOR",
        }
        self.team_id_map = {
            0: self.free,
            1: self.red,
            2: self.blue,
            3: self.spectator}

    def from_full_match_info(self, fmi):
        self.match_guid = fmi.match_guid

    def from_match_started(self, match_started):
        for player in match_started['PLAYERS']:
            team_id = int(player['TEAM'])
            player_id = player['STEAM_ID']

            if team_id == 0:
                self.free.add(player_id)
            elif team_id == 1:
                self.red.add(player_id)
            elif team_id == 2:
                self.blue.add(player_id)
            elif team_id == 3:
                self.spectator.add(player_id)
            else:
                raise Exception("Unexpected team {} {}".format(
                    player_id, team_id))

            self.switches.append(
                (0, player_id, None, self.team_id_to_name[team_id]))

    def from_player_switchteam(self, switch_team):
        player_id = switch_team.player_id
        old_team = switch_team.old_team
        new_team = switch_team.new_team
        self.switches.append((
            switch_team.time,
            player_id, old_team, new_team))

        try:
            self.team_map[old_team].remove(player_id)
        except KeyError:
            pass

        self.team_map[new_team].add(player_id)

    def from_player_disconnect(self, player_disconnect):
        player_id = player_disconnect['STEAM_ID']
        game_time = player_disconnect['TIME']
        if int(game_time) >= int(self.match_duration):
            # ignore events after match end
            return
        self.red.discard(player_id)
        self.blue.discard(player_id)
        self.free.discard(player_id)
        self.spectator.discard(player_id)
        self.switches.append((
            player_disconnect['TIME'],
            player_id, None, 'DISCONNECTED'))

    def get_team_by_id(self, team_id):
        return self.team_id_map[team_id]

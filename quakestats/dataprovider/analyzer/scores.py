from collections import defaultdict


class PlayerScores():
    def __init__(self):
        # store events history
        # the format is (ts, killer_id, victim_id, mod)
        self.kills = []
        self.deaths = []

        # store score events
        # the format is (ts, killer_id, score, mod)
        self.scores = []

        self.kdr = defaultdict(lambda: KDR())
        # store (score, timestamp) per player
        self.player_score = defaultdict(lambda: [0, 0])

    def get_final_kdr(self):
        return [
            (player_id, kdr.r) for player_id, kdr in self.kdr.items()]

    def players_sorted_by_score(self, reverse=True, skip_world=False):
        """
        Active players sorted by score
        """
        sorted_players = sorted(
            self.player_score.keys(),
            reverse=reverse,
            key=lambda k: (self.player_score[k]))

        if skip_world:
            sorted_players = [
                pid for pid in sorted_players if pid != 'q3-world']
        return sorted_players

    def from_match_started(self, report):
        for entry in report['PLAYERS']:
            # use defaultdict to set init values
            self.player_score[entry['STEAM_ID']]

    def from_player_kill(self, player_kill):
        game_time = player_kill.time
        killer_id = player_kill.killer_id
        victim_id = player_kill.victim_id
        mod = player_kill.mod

        self.kills.append((
            game_time,
            killer_id, victim_id,
            mod))

        # not self kill
        if killer_id != victim_id:
            self.player_score[killer_id][0] += 1
            self.player_score[killer_id][1] = game_time
            self.scores.append((
                game_time,
                killer_id,
                self.player_score[killer_id][0],
                mod))
            self.kdr[killer_id].add_kill()

        # TODO add friendlyfire for teamplay

    def from_player_death(self, player_death):
        game_time = player_death.time
        killer_id = player_death.killer_id
        victim_id = player_death.victim_id
        mod = player_death.mod

        self.deaths.append((
            game_time,
            killer_id, victim_id,
            mod))

        self.kdr[victim_id].add_death()
        if killer_id == victim_id or killer_id == 'q3-world':
            self.player_score[victim_id][0] -= 1
            self.scores.append((
                game_time, victim_id,
                self.player_score[victim_id][0], mod))

    def from_player_switchteam(self, player_switchteam):
        game_time = player_switchteam['TIME']
        player_id = player_switchteam['KILLER']['STEAM_ID']
        # well to be 100% accurate the score should be deleted
        # when switch is done TO team FREE (Spectator)
        # otherwise it would be better to set it to [0, 0]
        try:
            del self.player_score[player_id]
        except KeyError:
            pass
        self.scores.append((
            game_time, player_id, 0, 'SWITCHTEAM'))

    def from_player_disconnect(self, player_disconnect):
        game_time = player_disconnect['TIME']
        if int(game_time) >= int(self.match_duration):
            # ignore events after match end
            return
        player_id = player_disconnect['STEAM_ID']
        try:
            del self.player_score[player_id]
        except KeyError:
            pass
        self.scores.append((
            game_time, player_id, 0, 'DISCONNECTED'))

    def from_match_report(self, match_report):
        # any disconnections after match end are not counted
        game_length = match_report['GAME_LENGTH']
        self.scores = [
            s for s in self.scores
            if s[0] < game_length]


class KDR():
    """
    Helper class for easy handling of kill/death ratio
    """
    def __init__(self):
        self.k = 1
        self.d = 1
        self.r = None
        self._recalc()

    def add_kill(self):
        self.k += 1
        self._recalc()

    def add_death(self):
        self.d += 1
        self._recalc()

    def _recalc(self):
        self.r = round((self.k / self.d) - 1, 3)

    def __repr__(self):
        return "kdr={}".format(self.r)

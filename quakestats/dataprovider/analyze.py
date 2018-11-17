"""
Quake match analyzer, analyzes Quake Live events

Produces Match info:
    [x] server info
    [x] player info
    [x] teams info
    [x] match metadata
    [x] team scores
    [ ] medals - standard Q3/QL medals, q3 doesn't send such info :/
    [x] special scores
    [x] badges
    [x] kill / death info
"""

from collections import defaultdict
from quakestats.dataprovider.analyzer.specials import SpecialScores
from quakestats.dataprovider.analyzer.badges import Badger
from quakestats.dataprovider.analyzer.teams import TeamLifecycle


class AnalysisResult():
    """
    Match analysis object
    """
    def __init__(self):
        self.server_info = None

        self.players = None
        self.scores = None
        self.final_scores = None
        self.special_scores = None
        self.team_scores = None
        self.team_switches = None
        self.teams = None
        self.match_metadata = None
        self.kills = None
        self.badges = None


class ServerInfo():
    def __init__(self):
        self.server_name = None  # [MATCH_REPORT]
        self.server_domain = None  # [fmi]
        self.server_type = None  # [fmi] q3 or ql

    def from_full_match_info(self, fmi):
        self.server_domain = fmi.server_domain
        self.server_type = fmi.source

    def from_match_report(self, report):
        self.server_name = report['SERVER_TITLE']


class PlayerInfo():
    def __init__(self):
        self.steam_id = None
        self.name = None
        self.model = None

    def __repr__(self):
        return "PlayerInfo({}, {}, {})".format(
            self.steam_id, self.name, self.model)


class KDR():
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
        game_time = player_kill['TIME']
        killer_id = player_kill['KILLER']['STEAM_ID']
        victim_id = player_kill['VICTIM']['STEAM_ID']
        mod = player_kill['MOD']

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
        game_time = player_death['TIME']
        killer_id = player_death['KILLER']['STEAM_ID']
        victim_id = player_death['VICTIM']['STEAM_ID']
        mod = player_death['MOD']

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


class MatchMetadata():
    def __init__(self):
        self.match_guid = None  # [fmi]
        self.game_type = None  # [MATCH_STARTED]
        self.start_date = None  # [fmi]
        self.finish_date = None  # [fmi]
        self.duration = None  # [fmi]
        self.map_name = None  # [MATCH_REPORT]
        self.time_limit = None  # [MATCH_REPORT]
        self.frag_limit = None  # [MATCH_REPORT]
        self.score_limit = None  # [MATCH_REPORT]
        self.capture_limit = None  # [MATCH_REPORT]

        self.server_name = None  # [MATCH_REPORT]
        self.server_domain = None  # [fmi]
        self.exit_message = None  # [MATCH_REPORT]

    def from_full_match_info(self, fmi):
        self.match_guid = fmi.match_guid
        self.start_date = fmi.start_date
        self.finish_date = fmi.finish_date
        self.duration = fmi.duration
        self.server_domain = fmi.server_domain

    def from_match_started(self, match_started):
        self.game_type = match_started['GAME_TYPE']

    def from_match_report(self, report):
        self.map_name = report['MAP']
        self.server_name = report['SERVER_TITLE']
        self.exit_message = report['EXIT_MSG']

        self.time_limit = report['TIME_LIMIT']
        self.frag_limit = report['FRAG_LIMIT']
        self.score_limit = report['SCORE_LIMIT']
        self.capture_limit = report['CAPTURE_LIMIT']


class Analyzer():
    def __init__(self):
        self.match_metadata = MatchMetadata()
        self.server_info = ServerInfo()
        self.team_lifecycle = TeamLifecycle()
        self.player_scores = PlayerScores()
        self.players = {}
        self.special_scores = SpecialScores(self.player_scores)
        self.badger = Badger(self.player_scores, self.special_scores)
        self.specific_analyzer = None

    def analyze(self, full_match_info):
        """
        :param full_match_info: FullMatchInfo
        :return: AnalysisResult
        """
        self.full_match_info = full_match_info
        self.match_guid = full_match_info.match_guid
        self.player_scores.match_duration = self.full_match_info.duration
        self.team_lifecycle.match_duration = self.full_match_info.duration

        self.match_metadata.from_full_match_info(full_match_info)
        self.server_info.from_full_match_info(full_match_info)

        for event in full_match_info.events:
            self.analyze_event(event)

        self.badger.assign()
        # report generation
        report = AnalysisResult()
        report.server_info = self.server_info

        report.players = self.players
        report.scores = self.player_scores.scores
        report.final_scores = self.player_scores.player_score
        report.special_scores = self.special_scores.scores
        report.team_scores = "NOT IMPLEMENTED"
        report.team_switches = self.team_lifecycle.switches
        report.teams = self.team_lifecycle.team_map
        report.match_metadata = self.match_metadata
        report.kills = self.player_scores.kills
        report.badges = self.badger.badges
        return report

    def analyze_event(self, event):
        dispatcher = {
            'MATCH_REPORT': self.on_match_report,
            'MATCH_STARTED': self.on_match_start,
            'PLAYER_DEATH': self.on_player_death,
            'PLAYER_DISCONNECT': self.on_player_disconnect,
            'PLAYER_KILL': self.on_player_kill,
            'PLAYER_SWITCHTEAM': self.on_player_switchteam,
        }

        try:
            handler = dispatcher[event['TYPE']]
        except KeyError:
            return

        handler(event)

    def add_player_if_needed(self, player_id, player_name):
        if player_id not in self.players:
            player_info = PlayerInfo()
            player_info.steam_id = player_id
            player_info.name = player_name
            self.players[player_id] = player_info

    def on_match_report(self, event):
        self.match_metadata.from_match_report(event['DATA'])
        self.server_info.from_match_report(event['DATA'])
        self.player_scores.from_match_report(event['DATA'])
        self.special_scores.from_match_report(event['DATA'])

    def on_match_start(self, event):
        self.match_metadata.from_match_started(event['DATA'])
        if 'PLAYERS' in event['DATA']:
            self.team_lifecycle.from_match_started(event['DATA'])
            self.player_scores.from_match_started(event['DATA'])

            for player in event['DATA']['PLAYERS']:
                self.add_player_if_needed(
                    player['STEAM_ID'], player['NAME'])

        if self.match_metadata.game_type == 'CA':
            self.specific_analyzer = CA_Analyzer(
                 self.players, self.team_lifecycle)
        else:
            self.specific_analyzer = SpecializedAnalyzer(
                self.players, self.team_lifecycle)

    def on_player_switchteam(self, event):
        self.team_lifecycle.from_player_switchteam(event['DATA'])
        player_id = event['DATA']['KILLER']['STEAM_ID']
        player_name = event['DATA']['KILLER']['NAME']
        self.add_player_if_needed(player_id, player_name)
        self.player_scores.from_player_switchteam(event['DATA'])

    def on_player_disconnect(self, event):
        self.player_scores.from_player_disconnect(event['DATA'])
        self.team_lifecycle.from_player_disconnect(event['DATA'])

    def on_player_kill(self, event):
        # in q3 player can change his nickname. the generated id is
        # properly preserved between events but the name is not
        player_id = event['DATA']['KILLER']['STEAM_ID']
        player_name = event['DATA']['KILLER']['NAME']
        self.players[player_id].name = player_name
        self.player_scores.from_player_kill(event['DATA'])
        self.special_scores.from_player_kill(event['DATA'])

    def on_player_death(self, event):
        # nice to have it here
        self.player_scores.from_player_death(event['DATA'])
        self.specific_analyzer.on_player_death(event)
        self.special_scores.from_player_death(event['DATA'])


# This could probably be done with some fancy subclassing
# or mixins but this way 'seems' easier

class SpecializedAnalyzer():
    def __init__(self, players, team_lifecycle):
        self.players = players
        self.team_lifecycle = team_lifecycle
        self.team_scores = None

    def on_player_death(self, event):
        pass


# gametype specific analyzers
class CA_Analyzer(SpecializedAnalyzer):
    def __init__(self, players, team_lifecycle):
        super().__init__(players, team_lifecycle)

        self.player_state = {}
        self.team_scores = []

        self.red_score = 0
        self.blue_score = 0
        self.pre_round_time = 0

        class PlayerState():
            def __init__(self):
                self.alive = True

        for player_id in self.players.keys():
            self.player_state[player_id] = PlayerState()

    def on_player_death(self, event):
        game_time = int(event['DATA']['TIME'])
        player_id = event['DATA']['VICTIM']['STEAM_ID']
        dead_team_id = int(event['DATA']['VICTIM']['TEAM'])
        self.player_state[player_id].alive = False
        team = self.team_lifecycle.get_team_by_id(dead_team_id)

        # in case of CA there is a telefrag/lava kill
        # possible in X sec between rounds period
        if game_time - self.pre_round_time < 8:
            return

        if self.is_team_dead(team):
            self.pre_round_time = game_time
            self.team_dead(dead_team_id)

            if dead_team_id == 1:
                self.blue_score += 1
                self.add_score(game_time, 2, self.blue_score)
            elif dead_team_id == 2:
                self.red_score += 1
                self.add_score(game_time, 1, self.red_score)
            else:
                raise Exception("Unexpected team id")

    def is_team_dead(self, team):
        for player_id in team:
            if self.player_state[player_id].alive:
                return False
        return True

    def team_dead(self, dead_team_id):
        for player_state in self.player_state.values():
            player_state.alive = True

    def add_score(self, game_time, team_id, score):
        self.team_scores.append((
            game_time,
            self.team_lifecycle.team_id_to_name[team_id],
            score))

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

from quakestats.dataprovider.analyzer.specials import SpecialScores
from quakestats.dataprovider.analyzer.badges import Badger
from quakestats.dataprovider.analyzer.teams import TeamLifecycle
from quakestats.dataprovider.analyzer.events import Event
from quakestats.dataprovider.analyzer.scores import PlayerScores


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
        self.player_stats = None


class ServerInfo():
    def __init__(self):
        self.server_name = None  # [MATCH_REPORT]
        self.server_domain = None  # [fmi]
        self.server_type = None  # [fmi] q3 or ql

    def from_full_match_info(self, fmi):
        self.server_domain = fmi.server_domain
        self.server_type = fmi.source

    def from_match_report(self, report):
        self.server_name = report.data['SERVER_TITLE']


class PlayerInfo():
    def __init__(self):
        self.steam_id = None
        self.name = None
        self.model = None

    def __repr__(self):
        return "PlayerInfo({}, {}, {})".format(
            self.steam_id, self.name, self.model)


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

    def from_match_started(self, event):
        self.game_type = event.data['GAME_TYPE']

    def from_match_report(self, event):
        report = event.data
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
        self.player_stats = {}
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

        for raw_event in full_match_info.events:
            self.analyze_event(raw_event)

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
        report.player_stats = list(self.player_stats.values())
        return report

    def analyze_event(self, raw_event):
        event = Event.from_dict(raw_event)
        dispatcher = {
            'MATCH_REPORT': self.on_match_report,
            'MATCH_STARTED': self.on_match_start,
            'PLAYER_DEATH': self.on_player_death,
            'PLAYER_DISCONNECT': self.on_player_disconnect,
            'PLAYER_KILL': self.on_player_kill,
            'PLAYER_SWITCHTEAM': self.on_player_switchteam,
            'PLAYER_STATS': self.on_player_stats,
        }

        try:
            handler = dispatcher[event.type]
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
        self.match_metadata.from_match_report(event)
        self.server_info.from_match_report(event)
        self.player_scores.from_match_report(event)
        self.special_scores.from_match_report(event)

    def on_match_start(self, event):
        self.match_metadata.from_match_started(event)
        for player in event.iter_players():
            self.add_player_if_needed(player.id, player.name)

        self.team_lifecycle.from_match_started(event)
        self.player_scores.from_match_started(event)

        if self.match_metadata.game_type == 'CA':
            self.specific_analyzer = CA_Analyzer(
                 self.players, self.team_lifecycle)
        else:
            self.specific_analyzer = SpecializedAnalyzer(
                self.players, self.team_lifecycle)

    def on_player_switchteam(self, event):
        self.team_lifecycle.from_player_switchteam(event)
        player_id = event.player_id
        player_name = event.player_name
        self.add_player_if_needed(player_id, player_name)
        self.player_scores.from_player_switchteam(event)

    def on_player_disconnect(self, event):
        self.player_scores.from_player_disconnect(event)
        self.team_lifecycle.from_player_disconnect(event)

    def on_player_kill(self, event):
        # in q3 player can change his nickname. the generated id is
        # properly preserved between events but the name is not
        player_id = event.killer_id
        self.players[player_id].name = event.killer_name
        self.player_scores.from_player_kill(event)
        self.special_scores.from_player_kill(event)

    def on_player_death(self, event):
        # nice to have it here
        self.player_scores.from_player_death(event)
        self.specific_analyzer.on_player_death(event)
        self.special_scores.from_player_death(event)

    def on_player_stats(self, event):
        # if player has multiple stats events just use the last one
        # TODO consider merging stats (e.g. player reconnects/rejoins match)
        # ordinary stats sum grouped by player_id would be sufficient
        self.player_stats[event.player_id] = {
            'player_id': event.player_id,
            'total_armor_pickup': event.total_armor,
            'total_health_pickup': event.total_health,
            'damage_dealt': event.damage_dealt,
            'damage_taken': event.damage_taken,
        }


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
        game_time = int(event.time)
        player_id = event.victim_id
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

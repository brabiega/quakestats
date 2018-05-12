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
import pandas as pd


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


special_handlers = defaultdict(lambda: [])


class SpecialScores():

    def __init__(self, player_scores):
        self.scores = defaultdict(lambda: [])
        self.player_state = defaultdict(lambda: {})

        # we need player scores at given time
        # to score HEADHUNTER and DUCKHUNTER
        self.player_scores = player_scores

    def on_event(event_name):
        def wrapper(func):
            special_handlers[event_name].append(func)
            return func
        return wrapper

    def dispatch(self, event_name, event):
        for h in special_handlers[event_name]:
            h(self, event)

    def from_player_death(self, player_death):
        self.dispatch('PLAYER_DEATH', player_death)

    def from_player_kill(self, player_kill):
        self.dispatch('PLAYER_KILL', player_kill)

    def from_match_report(self, report):
        self.dispatch('REPORT', report)

    def add_score(self, name, event, swap_kv=False, weight=1):
        killer_id = event['KILLER']['STEAM_ID']
        victim_id = event['VICTIM']['STEAM_ID']
        game_time = event['TIME']
        if not swap_kv:
            self.scores[name].append(
                (game_time, killer_id, victim_id, weight))
        else:
            self.scores[name].append(
                (game_time, victim_id, killer_id, weight))

    @on_event('PLAYER_KILL')
    def score_gauntlet(self, player_kill):
        mod = player_kill['MOD']
        if mod == 'GAUNTLET':
            self.add_score('GAUNTLET_KILL', player_kill)
            self.add_score('GAUNTLET_DEATH', player_kill, swap_kv=True)

    @on_event('PLAYER_KILL')
    def score_spree(self, player_kill):
        """
        At least 2 players in 2 seconds
        """
        # TODO So it's not spree, its EXCELLENT
        game_time = player_kill['TIME']
        killer_id = player_kill['KILLER']['STEAM_ID']
        victim_id = player_kill['VICTIM']['STEAM_ID']
        if killer_id == victim_id:
            return

        state = self.player_state[killer_id]
        last_spree = state.setdefault('last_killing_spree', [])

        if not last_spree:
            last_spree.append((game_time, 1, player_kill))
            return

        last_time, last_score, last_kill = last_spree[-1]
        if (game_time - last_time) <= 2:
            current_spree = last_score + 1
            last_spree.append((game_time, current_spree, player_kill))

        else:
            current_spree = 1
            last_spree.append((game_time, current_spree, player_kill))

        if current_spree == 2:
            self.add_score('KILLING_SPREE', last_kill)
            self.add_score('KILLING_SPREE', player_kill, weight=2)
        elif current_spree > 2:
            self.add_score('KILLING_SPREE', player_kill, weight=current_spree)

    @on_event('PLAYER_KILL')
    def score_headduckhunter(self, player_kill):
        killer_id = player_kill['KILLER']['STEAM_ID']
        victim_id = player_kill['VICTIM']['STEAM_ID']
        mod = player_kill['MOD']

        if killer_id == victim_id:
            return

        if mod != 'GAUNTLET':
            return

        sorted_players = self.player_scores.players_sorted_by_score(
            skip_world=True)

        if len(sorted_players) < 2:
            return

        if victim_id == sorted_players[0]:
            self.add_score('HEADHUNTER', player_kill)
        elif victim_id == sorted_players[-1]:
            self.add_score('DUCKHUNTER', player_kill)

    @on_event('PLAYER_KILL')
    def score_death(self, player_kill):
        self.add_score('DEATH', player_kill, swap_kv=True)

    def _is_selfkill(self, player_kill):
        killer_id = player_kill['KILLER']['STEAM_ID']
        victim_id = player_kill['VICTIM']['STEAM_ID']
        if killer_id == victim_id or killer_id == 'q3-world':
            return True
        else:
            return False

    @on_event('PLAYER_KILL')
    def score_selfkill(self, player_kill):
        if self._is_selfkill(player_kill):
            self.add_score('SELFKILL', player_kill, swap_kv=True)

    @on_event('PLAYER_KILL')
    def score_killing_spree(self, player_kill):
        killer_id = player_kill['KILLER']['STEAM_ID']
        victim_id = player_kill['VICTIM']['STEAM_ID']

        killer_state = self.player_state[killer_id]
        victim_state = self.player_state[victim_id]

        last_spree = killer_state.setdefault(
            'killing_spree', {'max': [], 'current': []})
        if not self._is_selfkill(player_kill):
            last_spree['current'].append(player_kill)
            if len(last_spree['current']) > len(last_spree['max']):
                last_spree['max'] = last_spree['current']

        last_spree = victim_state.setdefault(
            'killing_spree', {'max': [], 'current': []})
        last_spree['current'] = []

    @on_event('REPORT')
    def postprocess_killing_spree(self, report):
        for state in self.player_state.values():
            try:
                spree = state['killing_spree']
                for kill in spree['max']:
                    self.add_score('KILLING_SPREE_R', kill)
            except KeyError:
                pass

    @on_event('PLAYER_KILL')
    def score_dying_spree(self, player_kill):
        killer_id = player_kill['KILLER']['STEAM_ID']
        victim_id = player_kill['VICTIM']['STEAM_ID']

        killer_state = self.player_state[killer_id]
        victim_state = self.player_state[victim_id]

        last_spree = killer_state.setdefault(
            'dying_spree', {'max': [], 'current': []})
        if not self._is_selfkill(player_kill):
            last_spree['current'] = []

        last_spree = victim_state.setdefault(
            'dying_spree', {'max': [], 'current': []})
        last_spree['current'].append(player_kill)
        if len(last_spree['current']) > len(last_spree['max']):
            last_spree['max'] = last_spree['current']

    @on_event('REPORT')
    def postprocess_dying_spree(self, report):
        for state in self.player_state.values():
            try:
                spree = state['dying_spree']
                for kill in spree['max']:
                    self.add_score('DYING_SPREE', kill, swap_kv=True)
            except KeyError:
                pass

    @on_event('PLAYER_KILL')
    def score_lavasaurus(self, player_kill):
        if player_kill['MOD'] == 'LAVA':
            self.add_score('LAVASAURUS', player_kill, swap_kv=True)


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
        self.kills = []
        self.deaths = []
        self.scores = []

        self.kdr = defaultdict(lambda: KDR())
        # store score, timestamp
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
        player_id = switch_team['KILLER']['STEAM_ID']
        old_team = switch_team['KILLER']['OLD_TEAM']
        new_team = switch_team['KILLER']['TEAM']
        self.switches.append((
            switch_team['TIME'],
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


badger_handlers = []


class Badger():
    def __init__(self, scores, special_scores):
        self.scores = scores
        self.special_scores = special_scores
        self.badges = []
        self.handlers = []

    def add_badge(self, name, player_id, count):
        self.badges.append((name, player_id, count))

    def assign(self):
        for h in badger_handlers:
            h(self)

    def badge():
        def wrapper(func):
            badger_handlers.append(func)
            return func
        return wrapper

    def from_special_score(self, name, aggregate, count, head):
        """
        Group special score (:name) by player_id, :aggregate, sort
        Take :count head or tail
        """
        try:
            scores = self.special_scores.scores[name]
        except KeyError:
            return []

        df = pd.DataFrame(scores, columns=['ts', 'to', 'from', 'value'])
        series = (
            df.groupby(['to'])
            .agg({'value': aggregate, 'ts': 'max'})
            .sort_values(by=['value', 'ts'])
        )
        if head:
            res = series.head(count)
        else:
            res = series.tail(count)

        return [
            (index, row.ts, row.value) for index, row in res.iterrows()]

    @badge()
    def winners(self):
        players = self.scores.players_sorted_by_score()
        try:
            self.add_badge('WIN_GOLD', players[0], 1)
            self.add_badge('WIN_SILVER', players[1], 1)
            self.add_badge('WIN_BRONZE', players[2], 1)
            self.add_badge('WIN_ALMOST', players[3], 1)
        except IndexError:
            pass

    @badge()
    def kdr_stars(self):
        kdrs = [
            (ratio, player_id) for player_id, ratio
            in self.scores.get_final_kdr()]
        rising_star = filter(lambda v: 0 <= v[0] <= 0.1, kdrs)
        try:
            self.add_badge('RISING_STAR', sorted(rising_star)[0][1], 1)
        except IndexError:
            pass

    @badge()
    def deaths(self):
        scores = self.from_special_score('DEATH', 'sum', 3, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('DEATH', index, count)

    @badge()
    def gauntlet_kill(self):
        scores = self.from_special_score('GAUNTLET_KILL', 'sum', 3, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('GAUNTLET_KILL', index, count)

    @badge()
    def excellent(self):
        scores = self.from_special_score('KILLING_SPREE', 'count', 3, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('KILLING_SPREE', index, count)

    @badge()
    def gauntlet_death(self):
        scores = self.from_special_score('GAUNTLET_DEATH', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('GAUNTLET_DEATH', index, count)

    @badge()
    def headhunter(self):
        scores = self.from_special_score('HEADHUNTER', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('HEADHUNTER', index, count)

    @badge()
    def duckhunter(self):
        scores = self.from_special_score('DUCKHUNTER', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('DUCKHUNTER', index, count)

    @badge()
    def selfkill(self):
        scores = self.from_special_score('SELFKILL', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('SELFKILL', index, count)

    @badge()
    def dying_spree(self):
        scores = self.from_special_score('DYING_SPREE', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('DYING_SPREE', index, count)

    @badge()
    def lavasaurus(self):
        scores = self.from_special_score('LAVASAURUS', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('LAVASAURUS', index, count)


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

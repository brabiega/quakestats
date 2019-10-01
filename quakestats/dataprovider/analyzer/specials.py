from collections import defaultdict


special_handlers = defaultdict(lambda: [])


class SpecialScores():

    def __init__(self, player_scores):
        self.scores = defaultdict(lambda: [])
        self.player_state = defaultdict(lambda: {})
        self.lifespan = {}
        self.states = {}

        # we need player scores at given time
        # to score HEADHUNTER and DUCKHUNTER
        self.player_scores = player_scores

    def on_event(event_name):
        def wrapper(func):
            special_handlers[event_name].append(func)
            return func
        return wrapper

    def on_stateful_event(event_name, state_id, default=None):
        def wrapper(func):
            def enchanced(self, *args, **kwargs):
                defval = default if default is not None else {}
                state = self.states.setdefault(
                    state_id, defaultdict(lambda: defval)
                )
                return func(self, state, *args, **kwargs)

            special_handlers[event_name].append(enchanced)
            return enchanced
        return wrapper

    def dispatch(self, event_name, event):
        for h in special_handlers[event_name]:
            h(self, event)

    def from_player_death(self, player_death):
        self.dispatch('PLAYER_DEATH', player_death)

    def from_player_kill(self, player_kill):
        self.dispatch('PLAYER_KILL', player_kill)

    def from_match_report(self, event):
        self.dispatch('REPORT', event.data)

    def add_score(self, name, event, swap_kv=False, weight=1):
        killer_id = event.killer_id
        victim_id = event.victim_id
        game_time = event.time
        if not swap_kv:
            self.scores[name].append(
                (game_time, killer_id, victim_id, weight))
        else:
            self.scores[name].append(
                (game_time, victim_id, killer_id, weight))

    @on_event('PLAYER_KILL')
    def score_gauntlet(self, player_kill):
        mod = player_kill.mod
        if mod == 'GAUNTLET':
            self.add_score('GAUNTLET_KILL', player_kill)
            self.add_score('GAUNTLET_DEATH', player_kill, swap_kv=True)

    @on_event('PLAYER_KILL')
    def score_spree(self, player_kill):
        """
        At least 2 players in 2 seconds
        """
        # TODO So it's not spree, its EXCELLENT
        game_time = player_kill.time
        killer_id = player_kill.killer_id
        victim_id = player_kill.victim_id
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
        killer_id = player_kill.killer_id
        victim_id = player_kill.victim_id
        mod = player_kill.mod
        should_calculate = True

        if killer_id == victim_id:
            should_calculate = False

        if mod != 'GAUNTLET':
            should_calculate = False

        sorted_players = self.player_state[None].get(
            'previous_players_by_score', [])

        if len(sorted_players) < 2:
            should_calculate = False

        # two extra cases to consider
        # scores are assigned before special scores are calculated so:
        # A is first B second score 1:1, B kills A, B should get headhunter
        # A is second B first score 0:1, A kills B, A should get headhunter
        # so we need to take a look into history

        if should_calculate:
            if victim_id == sorted_players[0]:
                self.add_score('HEADHUNTER', player_kill)
                self.add_score('HEADLESS_KNIGHT', player_kill, swap_kv=True)
            elif victim_id == sorted_players[-1]:
                self.add_score('DUCKHUNTER', player_kill)

        # global state
        self.player_state[None]['previous_players_by_score'] = \
            self.player_scores.players_sorted_by_score(skip_world=True)

    @on_event('PLAYER_KILL')
    def score_death(self, player_kill):
        self.add_score('DEATH', player_kill, swap_kv=True)

    def _is_selfkill(self, player_kill):
        killer_id = player_kill.killer_id
        victim_id = player_kill.victim_id
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
        killer_id = player_kill.killer_id
        victim_id = player_kill.victim_id

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
        killer_id = player_kill.killer_id
        victim_id = player_kill.victim_id

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

    @on_event('PLAYER_DEATH')
    def process_lifespan(self, report):
        # Currently no info when player joined so let's
        # count lifespan from first death
        victim_id = report.victim_id
        ts = report.time

        state = self.player_state[victim_id].setdefault(
            'lifespan', {'last_death': ts, 'max': 0})

        if (ts - state['last_death']) > state['max']:
            state['max'] = ts - state['last_death']

        if 0 < (ts - state['last_death']) <= 5:
            self.add_score('MOSQUITO', report, swap_kv=True)

        state['last_death'] = ts

    @on_event('REPORT')
    def postprocess_lifespan(self, report):
        sorted_players = self.player_scores.players_sorted_by_score(
            skip_world=True)

        for player_id in sorted_players:
            try:
                lifespan = self.player_state[player_id]['lifespan']
            except KeyError:
                continue
            self.lifespan[player_id] = lifespan['max']
            self.scores['DREADNOUGHT'].append(
                (0, player_id, player_id, lifespan['max'])
            )

    @on_event('PLAYER_KILL')
    def score_lavasaurus(self, player_kill):
        if player_kill.mod == 'LAVA':
            self.add_score('LAVASAURUS', player_kill, swap_kv=True)

    @on_event('PLAYER_DEATH')
    def vengeance_start(self, player_kill):
        killer_id = player_kill.killer_id
        victim_id = player_kill.victim_id
        if self._is_selfkill(player_kill):
            self.player_state[victim_id]['vengeance_target'] = None
        else:
            self.player_state[victim_id]['vengeance_target'] = killer_id

    @on_event('PLAYER_KILL')
    def score_vengeance(self, player_death):
        killer_id = player_death.killer_id
        victim_id = player_death.victim_id

        try:
            vengeance_target = self.player_state[killer_id]['vengeance_target']
        except KeyError:
            return

        if victim_id == vengeance_target:
            self.add_score('VENGEANCE', player_death)

    @on_event('PLAYER_KILL')
    def score_kamikaze(self, kill):
        if kill.killer_id == kill.victim_id:
            try:
                previous_kill = (
                    self.player_state[kill.killer_id]['kamikaze_last_kill']
                )

            except KeyError:
                pass

            else:
                if previous_kill.time == kill.time:
                    self.add_score('KAMIKAZE', previous_kill)

        self.player_state[kill.killer_id]['kamikaze_last_kill'] = kill

    @on_event('PLAYER_DEATH')
    def save_ghost_kill(self, death):
        self.player_state[death.victim_id]['ghost_kill'] = death.time

    @on_event('PLAYER_KILL')
    def score_ghost_kill(self, kill):
        # self kills shouldn't be possible and aren't counted
        if self._is_selfkill(kill):
            return

        try:
            death_ts = self.player_state[kill.killer_id]['ghost_kill']
        except KeyError:
            return

        # player killed killer right after death
        # (e.g. player died but launched rocket and killed someone)
        if 0 < kill.time - death_ts <= 3:
            self.add_score('GHOST_KILL', kill)

    @on_stateful_event('PLAYER_KILL', 'LUMBERJACK', 0)
    def score_gauntlet_serial_killer(self, state, kill):
        if kill.mod == 'GAUNTLET':
            state[kill.killer_id] += 1
        else:
            state[kill.killer_id] = 0

        if state[kill.killer_id] > 1:
            self.add_score('LUMBERJACK', kill)

    @on_stateful_event('PLAYER_DEATH', 'LUMBERJACK', 0)
    def score_gauntlet_serial_killer_reset(self, state, event):
        state[event.victim_id] = 0

    @on_event('PLAYER_KILL')
    def score_marauder(self, player_kill):
        killer_id = player_kill.killer_id
        victim_id = player_kill.victim_id
        should_calculate = True

        if killer_id == victim_id:
            should_calculate = False

        sorted_players = self.player_state[None].get(
            'previous_players_by_score', [])

        if len(sorted_players) < 2:
            should_calculate = False

        # two extra cases to consider
        # scores are assigned before special scores are calculated so:
        # A is first B second score 1:1, B kills A, B should get marauder
        # so we need to take a look into history again

        if should_calculate:
            try:
                killer_idx = sorted_players.index(killer_id)
                victim_idx = sorted_players.index(victim_id)
            except ValueError:
                pass
            else:
                # player is behind victim
                if killer_idx > victim_idx:
                    self.add_score('MARAUDER', player_kill)

        # global state
        self.player_state[None]['previous_players_by_score'] = \
            self.player_scores.players_sorted_by_score(skip_world=True)

    @on_stateful_event('PLAYER_KILL', 'CONSECUTIVE_RAIL_KILL', 0)
    def score_consecutive_rail_kill(self, state, kill):
        if kill.mod == 'RAILGUN':
            state[kill.killer_id] += 1
            if state[kill.killer_id] > 1:
                self.add_score('CONSECUTIVE_RAIL_KILL', kill)

        else:
            state[kill.killer_id] = 0

    @on_stateful_event('PLAYER_DEATH', 'CONSECUTIVE_RAIL_KILL', 0)
    def score_consecutive_rail_kill_reset(self, state, event):
        state[event.victim_id] = 0

    @on_stateful_event('PLAYER_KILL', 'SUICIDE_BOMBER', (0, 0, 0, None))
    def score_suicide_bomber(self, state, event):
        last_ts, score, has_selfkill, history = state[event.killer_id]
        history = history if history is not None else []

        if event.time == last_ts:
            history.append(event)
            state[event.killer_id] = (
                event.time,
                score + 1,
                has_selfkill or self._is_selfkill(event),
                history,
            )

        else:
            # the badge isn't 100% accurate as player has to kill
            # someone or himself to actually earn the scores
            # E.g. won't be assigned when match ends, although its good enough
            if has_selfkill and score > 2:
                for event in history:
                    if not self._is_selfkill(event):
                        self.add_score('SUICIDE_BOMBER', event)

            state[event.killer_id] = (event.time, 1, self._is_selfkill(event), [event])
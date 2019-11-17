import pandas as pd


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

    def badge():  # noqa, used as decorator
        def wrapper(func):
            badger_handlers.append(func)
            return func
        return wrapper

    def from_special_score(self, name, aggregate, count, head):
        """
        Group special score (:name) by player_id, :aggregate, sort
        Take :count head or tail
        """
        if count == 0:
            return []
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

    def get_multi_badge_count(self):
        # world is also a player
        total_players = len(self.scores.player_score)
        if total_players <= 2:
            return 0
        elif total_players <= 3:
            return 1
        elif total_players <= 4:
            return 2
        else:
            return 3

    @badge()
    def winners(self):
        players = self.scores.players_sorted_by_score()
        try:
            self.add_badge('WIN_GOLD', players[0], 1)
            self.add_badge('WIN_SILVER', players[1], 1)
            self.add_badge('WIN_BRONZE', players[2], 1)
            self.add_badge('WIN_ALMOST', players[3], 1)
        except IndexError:
            # Don't worry, this code will add proper amount of badges
            # even if less than 4 players are participating.
            # It works because badges are assigned in specific ORDER
            # So IndexError is raise when there is nothing more to assign
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
        badge_count = self.get_multi_badge_count()
        scores = self.from_special_score('DEATH', 'sum', badge_count, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('DEATH', index, count)

    @badge()
    def gauntlet_kill(self):
        scores = self.from_special_score('GAUNTLET_KILL', 'sum', 3, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('GAUNTLET_KILL', index, count)

    @badge()
    def excellent(self):
        badge_count = self.get_multi_badge_count()
        scores = self.from_special_score(
            'KILLING_SPREE', 'count', badge_count, False
        )
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

    @badge()
    def dreadnought(self):
        if not self.special_scores.lifespan:
            return
        sorted_lifespan = sorted(
            self.special_scores.lifespan, reverse=True,
            key=lambda pid: self.special_scores.lifespan[pid])

        self.add_badge('DREADNOUGHT', sorted_lifespan[0], 1)

    @badge()
    def vengeance(self):
        badge_count = self.get_multi_badge_count()
        scores = self.from_special_score(
            'VENGEANCE', 'sum', badge_count, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('VENGEANCE', index, count)

    @badge()
    def mosquito(self):
        scores = self.from_special_score('MOSQUITO', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('MOSQUITO', index, count)

    @badge()
    def headless_knight(self):
        scores = self.from_special_score('HEADLESS_KNIGHT', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('HEADLESS_KNIGHT', index, count)

    @badge()
    def kamikaze(self):
        scores = self.from_special_score('KAMIKAZE', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('KAMIKAZE', index, count)

    @badge()
    def ghost_kill(self):
        scores = self.from_special_score('GHOST_KILL', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('GHOST_KILL', index, count)

    @badge()
    def lumberjack(self):
        scores = self.from_special_score('LUMBERJACK', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('LUMBERJACK', index, count)

    @badge()
    def marauder(self):
        scores = self.from_special_score('MARAUDER', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('MARAUDER', index, count)

    @badge()
    def railman(self):
        scores = self.from_special_score('CONSECUTIVE_RAIL_KILL', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('CONSECUTIVE_RAIL_KILL', index, count)

    @badge()
    def suicide_bomber(self):
        scores = self.from_special_score('SUICIDE_BOMBER', 'sum', 1, False)
        for count, (index, ts, value) in enumerate(scores, start=1):
            self.add_badge('SUICIDE_BOMBER', index, count)
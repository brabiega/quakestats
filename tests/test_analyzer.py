import pytest
import mock
from quakestats.dataprovider import analyze


class TestPlayerScores():
    def test_from_player_kill(self):
        ps = analyze.PlayerScores()
        assert ps.kdr['A'].r == 0

        ps.from_player_kill({
            "TIME": 1, "KILLER": {"STEAM_ID": "A"},
            "VICTIM": {"STEAM_ID": "B"},
            "MOD": "SHOTGUN"})

        assert len(ps.scores) == 1
        assert ps.player_score['A'] == [1, 1]
        assert ps.scores[0] == (1, 'A', 1, 'SHOTGUN')
        assert len(ps.kills) == 1
        assert ps.kills[0] == (1, 'A', 'B', 'SHOTGUN')
        assert ps.kdr['A'].r == 1

        ps.from_player_kill({
            "TIME": 2, "KILLER": {"STEAM_ID": "A"},
            "VICTIM": {"STEAM_ID": "C"},
            "MOD": "MOD3"})

        assert len(ps.scores) == 2
        assert ps.player_score['A'] == [2, 2]
        assert ps.scores[1] == (2, 'A', 2, 'MOD3')
        assert len(ps.kills) == 2
        assert ps.kills[1] == (2, 'A', 'C', 'MOD3')
        assert ps.kdr['A'].r == 2

        ps.from_player_kill({
            "TIME": 2, "KILLER": {"STEAM_ID": "B"},
            "VICTIM": {"STEAM_ID": "A"},
            "MOD": "MOD3"})

        assert len(ps.scores) == 3
        assert ps.player_score['B'] == [1, 2]
        assert ps.scores[2] == (2, 'B', 1, 'MOD3')
        assert len(ps.kills) == 3
        assert ps.kills[2] == (2, 'B', 'A', 'MOD3')

    def test_from_player_kill_selfkill(self):
        ps = analyze.PlayerScores()
        ps.from_player_kill({
            "TIME": 2, "KILLER": {"STEAM_ID": "A"},
            "VICTIM": {"STEAM_ID": "A"},
            "MOD": "SHOTGUN"})

        assert ps.player_score['A'] == [0, 0]
        assert ps.kills == [(2, 'A', 'A', 'SHOTGUN')]
        assert ps.scores == []

    def test_from_player_swtichteam(self):
        ps = analyze.PlayerScores()
        ps.player_score['A'] = [10, 0]
        ps.from_player_switchteam({
            "TIME": 3,
            "KILLER": {"STEAM_ID": 'A'}})

        assert ps.scores[0] == (3, 'A', 0, 'SWITCHTEAM')
        ps.player_score['A'] == [0, 0]

    def test_from_player_disconnect(self):
        ps = analyze.PlayerScores()
        ps.match_duration = 100
        ps.player_score['A'] = [10, 0]
        ps.from_player_disconnect({
            "TIME": 3,
            "STEAM_ID": 'A'})

        assert ps.scores[0] == (3, 'A', 0, 'DISCONNECTED')
        assert ps.player_score['A'] == [0, 0]

        ps.player_score['A'] = [10, 1]
        ps.from_player_disconnect({
            "TIME": 300,
            "STEAM_ID": 'A'})
        assert ps.player_score['A'] == [10, 1]

    def test_from_player_death_world(self):
        ps = analyze.PlayerScores()
        ps.from_player_death({
            'TIME': 3,
            'KILLER': {'STEAM_ID': 'q3-world'},
            'VICTIM': {'STEAM_ID': 'B'},
            'MOD': 'FALLING'})

        assert ps.scores[0] == (3, 'B', -1, 'FALLING')
        assert ps.player_score['B'] == [-1, 0]
        assert ps.deaths[0] == (3, 'q3-world', 'B', 'FALLING')

    def test_from_player_death_selfkill(self):
        ps = analyze.PlayerScores()
        ps.from_player_death({
            'TIME': 3,
            'KILLER': {'STEAM_ID': 'B'},
            'VICTIM': {'STEAM_ID': 'B'},
            'MOD': 'FALLING'})

        assert ps.scores[0] == (3, 'B', -1, 'FALLING')
        assert ps.player_score['B'] == [-1, 0]
        assert ps.deaths[0] == (3, 'B', 'B', 'FALLING')

    def test_from_player_death(self):
        ps = analyze.PlayerScores()
        ps.from_player_death({
            'TIME': 3,
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'B'},
            'MOD': 'MOD_ROCKET'})

        assert ps.scores == []
        assert ps.player_score['B'] == [0, 0]
        assert ps.deaths[0] == (3, 'A', 'B', 'MOD_ROCKET')

    def test_players_sorted_by_score(self):
        ps = analyze.PlayerScores()
        ps.match_duration = 900
        ps.from_player_kill({
            "TIME": 1, "MOD": "SHOTGUN",
            "KILLER": {"STEAM_ID": "A"},
            "VICTIM": {"STEAM_ID": "B"},
        })
        ps.from_player_kill({
            "TIME": 2, "MOD": "SHOTGUN",
            "KILLER": {"STEAM_ID": "A"},
            "VICTIM": {"STEAM_ID": "B"},
        })
        ps.from_player_kill({
            "TIME": 1, "MOD": "SHOTGUN",
            "KILLER": {"STEAM_ID": "B"},
            "VICTIM": {"STEAM_ID": "C"},
        })
        assert ps.players_sorted_by_score() == ['A', 'B']

        ps.from_player_kill({
            "TIME": 3, "MOD": "SHOTGUN",
            "KILLER": {"STEAM_ID": "B"},
            "VICTIM": {"STEAM_ID": "C"},
        })
        assert ps.players_sorted_by_score() == ['B', 'A']

        ps.from_player_kill({
            "TIME": 4, "MOD": "SHOTGUN",
            "KILLER": {"STEAM_ID": "A"},
            "VICTIM": {"STEAM_ID": "B"},
        })
        assert ps.players_sorted_by_score() == ['A', 'B']

        ps.from_player_disconnect({"TIME": 10, "STEAM_ID": 'A'})
        assert ps.players_sorted_by_score() == ['B']

        ps.from_player_switchteam({
            "TIME": 10,
            "KILLER": {"STEAM_ID": 'B'}})
        assert ps.players_sorted_by_score() == []


class TestSpecialScores():

    @pytest.fixture
    def pss(self):
        return analyze.SpecialScores(None)

    def test_add_score(self, pss):
        pss.add_score(
            'TEST', {
                'KILLER': {'STEAM_ID': 'A'},
                'VICTIM': {'STEAM_ID': 'B'},
                'TIME': 12},
            weight=10)

        assert pss.scores['TEST'] == [(12, 'A', 'B', 10)]

        pss.add_score(
            'TEST', {
                'KILLER': {'STEAM_ID': 'A'},
                'VICTIM': {'STEAM_ID': 'B'},
                'TIME': 12},
            swap_kv=True, weight=12)

        assert pss.scores['TEST'][1] == (12, 'B', 'A', 12)

    @pytest.mark.parametrize('event, expected', [
        (
            {'KILLER': {'STEAM_ID': 'A'}, 'VICTIM': {'STEAM_ID': 'A'}},
            (10, 'A', 'A', 1)),
        (
            {'KILLER': {'STEAM_ID': 'q3-world'}, 'VICTIM': {'STEAM_ID': 'A'}},
            (10, 'A', 'q3-world', 1)),
    ])
    def test_score_selfkill(self, pss, event, expected):
        event['TIME'] = 10
        pss.score_selfkill(event)
        assert pss.scores['SELFKILL'] == [expected]

    def test_score_killing_spree(self, pss):
        event = {
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'B'}
        }

        pss.score_killing_spree(event)
        assert pss.player_state['A']['killing_spree']['max'] == [event]
        assert pss.player_state['A']['killing_spree']['current'] == [event]

        pss.score_killing_spree(event)
        assert pss.player_state['A']['killing_spree']['max'] == [event, event]
        assert pss.player_state['A']['killing_spree']['current'] == \
            [event, event]

        pss.score_killing_spree({
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'A'}
        })

        assert pss.player_state['A']['killing_spree']['max'] == [event, event]
        assert pss.player_state['A']['killing_spree']['current'] == []

    def test_postprocess_killing_spree(self, pss):
        event = {
            'TIME': 10,
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'B'}
        }
        pss.score_killing_spree(event)
        pss.score_killing_spree(event)
        pss.postprocess_killing_spree({})
        assert pss.scores['KILLING_SPREE_R'] == [
            (10, 'A', 'B', 1),
            (10, 'A', 'B', 1)
        ]

    def test_score_dying_spree(self, pss):
        event = {
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'B'}
        }

        pss.score_dying_spree(event)
        assert pss.player_state['B']['dying_spree']['max'] == [event]
        assert pss.player_state['B']['dying_spree']['current'] == [event]

        pss.score_dying_spree(event)
        assert pss.player_state['B']['dying_spree']['max'] == [event, event]
        assert pss.player_state['B']['dying_spree']['current'] == \
            [event, event]

        event_selfkill = {
            'KILLER': {'STEAM_ID': 'B'},
            'VICTIM': {'STEAM_ID': 'B'}
        }
        pss.score_dying_spree(event_selfkill)
        assert pss.player_state['B']['dying_spree']['max'] == \
            [event, event, event_selfkill]
        assert pss.player_state['B']['dying_spree']['current'] == \
            [event, event, event_selfkill]

        event_kill = {
            'KILLER': {'STEAM_ID': 'B'},
            'VICTIM': {'STEAM_ID': 'A'}
        }
        pss.score_dying_spree(event_kill)
        assert pss.player_state['B']['dying_spree']['max'] == \
            [event, event, event_selfkill]
        assert pss.player_state['B']['dying_spree']['current'] == []

    def test_postprocess_dying_spree(self, pss):
        event = {
            'TIME': 10,
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'B'}
        }
        pss.score_dying_spree(event)
        pss.score_dying_spree(event)
        pss.postprocess_dying_spree({})
        assert pss.scores['DYING_SPREE'] == [
            (10, 'B', 'A', 1),
            (10, 'B', 'A', 1)
        ]

    def test_score_lavasaurus(self, pss):
        event = {
            'TIME': 10,
            'MOD': 'LAVA',
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'B'}
        }

        pss.score_lavasaurus(event)
        assert pss.scores['LAVASAURUS'] == [
            (10, 'B', 'A', 1)
        ]

        event = {
            'TIME': 10,
            'MOD': 'MACHINEGUN',
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'B'}
        }
        pss.score_lavasaurus(event)
        assert pss.scores['LAVASAURUS'] == [
            (10, 'B', 'A', 1)
        ]

    def test_score_headduckhunter_empty(self, pss):
        pss.player_scores = mock.Mock(name='player_scores')
        pss.player_scores.players_sorted_by_score.return_value = []
        pss.score_headduckhunter({
            'MOD': 'GAUNTLET',
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'B'},
        })
        assert pss.scores['HEADHUNTER'] == []
        assert pss.scores['DUCKHUNTER'] == []

    def test_score_headduckhunter_world(self, pss):
        pss.player_scores = mock.Mock(name='player_scores')
        pss.player_scores.players_sorted_by_score.return_value = [
            'A', 'B']
        pss.score_headduckhunter({
            'MOD': 'GAUNTLET', 'TIME': 1,
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'B'},
        })
        assert pss.scores['HEADHUNTER'] == []
        assert pss.scores['DUCKHUNTER'] == [(1, 'A', 'B', 1)]

        pss.score_headduckhunter({
            'MOD': 'GAUNTLET', 'TIME': 1,
            'KILLER': {'STEAM_ID': 'B'},
            'VICTIM': {'STEAM_ID': 'A'},
        })
        assert pss.scores['HEADHUNTER'] == [(1, 'B', 'A', 1)]
        assert pss.scores['DUCKHUNTER'] == [(1, 'A', 'B', 1)]
        pss.player_scores.players_sorted_by_score.assert_called_with(
            skip_world=True)

    def test_lifespan(self, pss):
        pss.process_lifespan({
            'TIME': 1,
            'VICTIM': {'STEAM_ID': 'A'},
            'KILLER': {'STEAM_ID': 'B'}})
        assert pss.player_state['A']['lifespan']['max'] == 0
        assert pss.player_state['A']['lifespan']['last_death'] == 1

        pss.process_lifespan({
            'TIME': 15,
            'VICTIM': {'STEAM_ID': 'A'},
            'KILLER': {'STEAM_ID': 'B'}})
        assert pss.player_state['A']['lifespan']['max'] == 14
        assert pss.player_state['A']['lifespan']['last_death'] == 15
        assert 'MOSQUITO' not in pss.scores

        pss.process_lifespan({
            'TIME': 17,
            'VICTIM': {'STEAM_ID': 'A'},
            'KILLER': {'STEAM_ID': 'B'}})
        assert pss.player_state['A']['lifespan']['max'] == 14
        assert pss.player_state['A']['lifespan']['last_death'] == 17
        assert pss.scores['MOSQUITO'] == [(17, 'A', 'B', 1)]

    def test_lifespan_postprocess(self, pss):
        pss.player_scores = mock.Mock(name='player_scores')
        pss.player_scores.players_sorted_by_score.return_value = ['A', 'B']
        pss.postprocess_lifespan({})
        assert pss.lifespan == {}

        pss.player_state['A']['lifespan'] = {'max': 1024}
        pss.postprocess_lifespan({})
        assert pss.lifespan == {'A': 1024}

        pss.player_scores.players_sorted_by_score.assert_called_with(
            skip_world=True)

    def test_vengeance_start(self, pss):
        event = {
            'TIME': 10,
            'MOD': 'LAVA',
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'B'}
        }
        pss.vengeance_start(event)
        assert pss.player_state['B']['vengeance_target'] == 'A'

        event = {
            'TIME': 10,
            'MOD': 'LAVA',
            'KILLER': {'STEAM_ID': 'C'},
            'VICTIM': {'STEAM_ID': 'B'}
        }
        pss.vengeance_start(event)
        assert pss.player_state['B']['vengeance_target'] == 'C'

        event = {
            'TIME': 10,
            'MOD': 'LAVA',
            'KILLER': {'STEAM_ID': 'B'},
            'VICTIM': {'STEAM_ID': 'B'}
        }
        pss.vengeance_start(event)
        assert pss.player_state['B']['vengeance_target'] is None

    def test_score_vengeance(self, pss):
        event = {
            'TIME': 10,
            'MOD': 'LAVA',
            'KILLER': {'STEAM_ID': 'A'},
            'VICTIM': {'STEAM_ID': 'B'}
        }
        pss.score_vengeance(event)
        assert pss.scores['VENGEANCE'] == []

        pss.player_state['A']['vengeance_target'] = 'B'
        pss.score_vengeance(event)
        assert pss.scores['VENGEANCE'] == [(10, 'A', 'B', 1)]


class TestBadger():
    @pytest.fixture
    def badger(self):
        scores = mock.Mock()
        scores.name = 'scores'
        special_scores = mock.Mock()
        special_scores.name = 'special_scores'

        return analyze.Badger(scores, special_scores)

    def test_add_badge(self, badger):
        badger.add_badge('test', 'dummy', 5)
        assert badger.badges == [('test', 'dummy', 5)]

        badger.add_badge('test2', 'dummy2', 6)
        assert badger.badges == [
            ('test', 'dummy', 5),
            ('test2', 'dummy2', 6)]

    def test_win(self, badger):
        badger.scores.players_sorted_by_score.return_value = [
            '1st', '2nd', '3rd', '4th']
        badger.winners()
        assert badger.badges == [
            ('WIN_GOLD', '1st', 1),
            ('WIN_SILVER', '2nd', 1),
            ('WIN_BRONZE', '3rd', 1),
            ('WIN_ALMOST', '4th', 1),
        ]

    def test_kdr_stars(self, badger):
        badger.scores.get_final_kdr.return_value = [
            ('p1', 5),
            ('p2', 0.1),
            ('p3', 0.4),
            ('p4', -0.01)]
        badger.kdr_stars()
        assert badger.badges == [
            ('RISING_STAR', 'p2', 1)
        ]

    def test_deaths(self, badger):
        badger.special_scores.scores = {
            'DEATH': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.deaths()
        assert badger.badges == [
            ('DEATH', 'C', 1),
            ('DEATH', 'A', 2),
            ('DEATH', 'B', 3),
        ]

    def test_gauntlet_kill(self, badger):
        badger.special_scores.scores = {
            'GAUNTLET_KILL': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.gauntlet_kill()
        assert badger.badges == [
            ('GAUNTLET_KILL', 'C', 1),
            ('GAUNTLET_KILL', 'A', 2),
            ('GAUNTLET_KILL', 'B', 3),
        ]

    def test_excellent(self, badger):
        badger.special_scores.scores = {
            'KILLING_SPREE': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 2),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 2),
                (10, 'C', 'D', 3),
            ]
        }
        badger.excellent()
        assert badger.badges == [
            ('KILLING_SPREE', 'C', 1),
            ('KILLING_SPREE', 'A', 2),
            ('KILLING_SPREE', 'B', 3),
        ]

    def test_gauntlet_death(self, badger):
        badger.special_scores.scores = {
            'GAUNTLET_DEATH': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.gauntlet_death()
        assert badger.badges == [
            ('GAUNTLET_DEATH', 'B', 1),
        ]

    def test_headhunter(self, badger):
        badger.special_scores.scores = {
            'HEADHUNTER': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.headhunter()
        assert badger.badges == [
            ('HEADHUNTER', 'B', 1),
        ]

    def test_duckhunter(self, badger):
        badger.special_scores.scores = {
            'DUCKHUNTER': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.duckhunter()
        assert badger.badges == [
            ('DUCKHUNTER', 'B', 1),
        ]

    def test_selfkill(self, badger):
        badger.special_scores.scores = {
            'SELFKILL': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.selfkill()
        assert badger.badges == [
            ('SELFKILL', 'B', 1),
        ]

    def test_dyingspree(self, badger):
        badger.special_scores.scores = {
            'DYING_SPREE': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.dying_spree()
        assert badger.badges == [
            ('DYING_SPREE', 'B', 1),
        ]

    def test_lavasaurus(self, badger):
        badger.special_scores.scores = {
            'LAVASAURUS': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.lavasaurus()
        assert badger.badges == [
            ('LAVASAURUS', 'B', 1),
        ]

    def test_vengeance(self, badger):
        badger.special_scores.scores = {
            'VENGEANCE': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.vengeance()
        assert badger.badges == [
            ('VENGEANCE', 'C', 1),
            ('VENGEANCE', 'A', 2),
            ('VENGEANCE', 'B', 3),
        ]

    def test_dreadnought(self, badger):
        badger.special_scores.lifespan = {
            'A': 100, 'B': 500, 'C': 50}
        badger.dreadnought()

        assert badger.badges == [
            ('DREADNOUGHT', 'B', 1)
        ]

    def test_mosquito(self, badger):
        badger.special_scores.scores = {
            'MOSQUITO': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.mosquito()
        assert badger.badges == [
            ('MOSQUITO', 'B', 1),
        ]

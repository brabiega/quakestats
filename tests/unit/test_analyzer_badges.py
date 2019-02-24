import pytest
import mock

from quakestats.dataprovider.analyzer.badges import Badger


class TestBadger():
    @pytest.fixture
    def badger(self):
        scores = mock.Mock()
        scores.name = 'scores'
        special_scores = mock.Mock()
        special_scores.name = 'special_scores'

        return Badger(scores, special_scores)

    @pytest.mark.parametrize('player_score, expected', [
        ({'A': 1, 'B': 3, 'C': 4, 'wrld': 0}, 2),
        ({'A': 1, 'B': 3, 'C': 4, 'D': 5, 'wrld': 0}, 3),
        ({'A': 1, 'B': 3, 'wrld': 0}, 1),
        ({'A': 1, 'B': 3, 'C': 4, 'D': 5, 'E': 6, 'wrld': 0}, 3),
    ])
    def test_get_multi_badge_count(self, badger, player_score, expected):
        badger.scores.player_score = player_score
        assert badger.get_multi_badge_count() == expected

    def test_add_badge(self, badger):
        badger.add_badge('test', 'dummy', 5)
        assert badger.badges == [('test', 'dummy', 5)]

        badger.add_badge('test2', 'dummy2', 6)
        assert badger.badges == [
            ('test', 'dummy', 5),
            ('test2', 'dummy2', 6)]

    @pytest.mark.parametrize('players_sorted, expected', [
        (
            ['A', 'B', 'C', 'D', 'E', 'F'],
            [
                ('WIN_GOLD', 'A', 1),
                ('WIN_SILVER', 'B', 1),
                ('WIN_BRONZE', 'C', 1),
                ('WIN_ALMOST', 'D', 1),
            ],
        ),
        (
            ['A', 'B'],
            [
                ('WIN_GOLD', 'A', 1),
                ('WIN_SILVER', 'B', 1),
            ],
        ),
    ])
    def test_win(self, badger, players_sorted, expected):
        badger.scores.players_sorted_by_score.return_value = players_sorted
        badger.winners()
        assert badger.badges == expected

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
        with mock.patch.object(Badger, 'get_multi_badge_count') as bc:
            bc.return_value = 3
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
        with mock.patch.object(Badger, 'get_multi_badge_count') as bc:
            bc.return_value = 3
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
        with mock.patch.object(Badger, 'get_multi_badge_count') as bc:
            bc.return_value = 3
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

    def test_kamikaze(self, badger):
        badger.special_scores.scores = {
            'KAMIKAZE': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.kamikaze()
        assert badger.badges == [
            ('KAMIKAZE', 'B', 1),
        ]

    def test_ghost_kill(self, badger):
        badger.special_scores.scores = {
            'GHOST_KILL': [
                (10, 'A', 'B', 1),
                (11, 'A', 'B', 1),
                (10, 'B', 'C', 1),
                (12, 'B', 'C', 1),
                (10, 'C', 'D', 1),
            ]
        }
        badger.ghost_kill()
        assert badger.badges == [
            ('GHOST_KILL', 'B', 1),
        ]

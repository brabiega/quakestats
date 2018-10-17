import pytest
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


class TestAnalyzer(object):
    @pytest.fixture
    def an(self):
        return analyze.Analyzer()

    @pytest.fixture
    def started_ffa(self, an):
        an.analyze_event({
            'TYPE': 'MATCH_STARTED',
            'DATA': {
                'GAME_TYPE': 'FFA',
                'PLAYERS': [
                    {'STEAM_ID': 'A', 'NAME': 'AN', 'TEAM': 0},
                    {'STEAM_ID': 'B', 'NAME': 'BN', 'TEAM': 0},
                ]
            }
        })

    def test_headhunter_when_getting_1st_place(self, an, started_ffa):
        # A kills B, 1:0, A is first
        # B kills A, 1:1, B is first
        # A kills B, should earn headhunter badge
        an.analyze_event({
            'TYPE': 'PLAYER_KILL',
            'DATA': {
                'TIME': 1,
                'KILLER': {
                    'STEAM_ID': 'A',
                    'NAME': 'AN',
                },
                'VICTIM': {
                    'STEAM_ID': 'B',
                    'NAME': 'BN',
                },
                'MOD': 'MACHINEGUN',
            }
        })
        an.analyze_event({
            'TYPE': 'PLAYER_KILL',
            'DATA': {
                'TIME': 2,
                'KILLER': {
                    'STEAM_ID': 'B',
                    'NAME': 'BN',
                },
                'VICTIM': {
                    'STEAM_ID': 'A',
                    'NAME': 'AN',
                },
                'MOD': 'GAUNTLET',
            }
        })
        an.analyze_event({
            'TYPE': 'PLAYER_KILL',
            'DATA': {
                'TIME': 3,
                'KILLER': {
                    'STEAM_ID': 'A',
                    'NAME': 'AN',
                },
                'VICTIM': {
                    'STEAM_ID': 'B',
                    'NAME': 'BN',
                },
                'MOD': 'GAUNTLET',
            }
        })

        assert an.special_scores.scores['HEADHUNTER'] == [
            (2, 'B', 'A', 1),
            (3, 'A', 'B', 1),
        ]

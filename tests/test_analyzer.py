import pytest
from quakestats.dataprovider import analyze


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

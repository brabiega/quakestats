import pytest
import mock

from quakestats.dataprovider.analyzer.specials import SpecialScores
from quakestats.dataprovider.analyzer.events import Event


def gen_kill(time, killer_id, victim_id, mod):
    return Event.from_dict({
        'TYPE': 'PLAYER_KILL',
        'DATA': {
            'TIME': time,
            'VICTIM': {
                'STEAM_ID': victim_id,
            },
            'KILLER': {
                'STEAM_ID': killer_id,
            },
            'MOD': mod,
        },
    })


def gen_death(time, killer_id, victim_id, mod):
    return Event.from_dict({
        'TYPE': 'PLAYER_DEATH',
        'DATA': {
            'TIME': time,
            'VICTIM': {
                'STEAM_ID': victim_id,
            },
            'KILLER': {
                'STEAM_ID': killer_id,
            },
            'MOD': mod,
        },
    })


class TestSpecialScores():
    @pytest.fixture
    def pss(self):
        return SpecialScores(None)

    def test_add_score(self, pss):
        pss.add_score(
            'TEST', gen_kill(12, 'A', 'B', 'dummy'), weight=10
        )
        assert pss.scores['TEST'] == [(12, 'A', 'B', 10)]

        pss.add_score(
            'TEST', gen_kill(12, 'A', 'B', 'dummy'),
            swap_kv=True, weight=12
        )
        assert pss.scores['TEST'][1] == (12, 'B', 'A', 12)

    @pytest.mark.parametrize('event, expected', [
        (
            gen_kill(10, 'A', 'A', 'dummy'),
            (10, 'A', 'A', 1)),
        (
            gen_kill(10, 'q3-world', 'A', 'dummy'),
            (10, 'A', 'q3-world', 1)),
    ])
    def test_score_selfkill(self, pss, event, expected):
        pss.score_selfkill(event)
        assert pss.scores['SELFKILL'] == [expected]

    def test_score_killing_spree(self, pss):

        event = gen_kill(1, 'A', 'B', 'dummy')
        pss.score_killing_spree(event)
        assert pss.player_state['A']['killing_spree']['max'] == [event]
        assert pss.player_state['A']['killing_spree']['current'] == [event]

        pss.score_killing_spree(event)
        assert pss.player_state['A']['killing_spree']['max'] == [event, event]
        assert pss.player_state['A']['killing_spree']['current'] == \
            [event, event]

        pss.score_killing_spree(
            gen_kill(2, 'A', 'A', 'dummy')
        )

        assert pss.player_state['A']['killing_spree']['max'] == [event, event]
        assert pss.player_state['A']['killing_spree']['current'] == []

    def test_postprocess_killing_spree(self, pss):
        event = gen_kill(10, 'A', 'B', 'dummy')
        pss.score_killing_spree(event)
        pss.score_killing_spree(event)
        pss.postprocess_killing_spree({})
        assert pss.scores['KILLING_SPREE_R'] == [
            (10, 'A', 'B', 1),
            (10, 'A', 'B', 1)
        ]

    def test_score_dying_spree(self, pss):
        event = gen_kill(1, 'A', 'B', 'dummy')

        pss.score_dying_spree(event)
        assert pss.player_state['B']['dying_spree']['max'] == [event]
        assert pss.player_state['B']['dying_spree']['current'] == [event]

        pss.score_dying_spree(event)
        assert pss.player_state['B']['dying_spree']['max'] == [event, event]
        assert pss.player_state['B']['dying_spree']['current'] == \
            [event, event]

        event_selfkill = gen_kill(2, 'B', 'B', 'dummy')
        pss.score_dying_spree(event_selfkill)
        assert pss.player_state['B']['dying_spree']['max'] == \
            [event, event, event_selfkill]
        assert pss.player_state['B']['dying_spree']['current'] == \
            [event, event, event_selfkill]

        event_kill = gen_kill(3, 'B', 'A', 'dummy')
        pss.score_dying_spree(event_kill)
        assert pss.player_state['B']['dying_spree']['max'] == \
            [event, event, event_selfkill]
        assert pss.player_state['B']['dying_spree']['current'] == []

    def test_postprocess_dying_spree(self, pss):
        event = gen_kill(10, 'A', 'B', 'dummy')
        pss.score_dying_spree(event)
        pss.score_dying_spree(event)
        pss.postprocess_dying_spree({})
        assert pss.scores['DYING_SPREE'] == [
            (10, 'B', 'A', 1),
            (10, 'B', 'A', 1)
        ]

    def test_score_lavasaurus(self, pss):
        event = gen_kill(10, 'A', 'B', 'LAVA')
        pss.score_lavasaurus(event)
        assert pss.scores['LAVASAURUS'] == [
            (10, 'B', 'A', 1)
        ]

        event = gen_kill(10, 'A', 'B', 'MACHINEGUN')
        pss.score_lavasaurus(event)
        assert pss.scores['LAVASAURUS'] == [
            (10, 'B', 'A', 1)
        ]

    def test_score_headduckhunter_empty(self, pss):
        pss.player_scores = mock.Mock(name='player_scores')
        pss.player_scores.players_sorted_by_score.return_value = []
        pss.score_headduckhunter(gen_kill(1, 'A', 'B', 'GAUNTLET'))
        assert pss.scores['HEADHUNTER'] == []
        assert pss.scores['DUCKHUNTER'] == []

    def test_score_headduckhunter_world(self, pss):
        pss.player_scores = mock.Mock(name='player_scores')
        pss.player_state[None]['previous_players_by_score'] = ['A', 'B']
        pss.player_scores.players_sorted_by_score.return_value = [
            'A', 'B']
        pss.score_headduckhunter(gen_kill(1, 'A', 'B', 'GAUNTLET'))
        assert pss.scores['HEADHUNTER'] == []
        assert pss.scores['DUCKHUNTER'] == [(1, 'A', 'B', 1)]

        pss.score_headduckhunter(gen_kill(1, 'B', 'A', 'GAUNTLET'))
        assert pss.scores['HEADHUNTER'] == [(1, 'B', 'A', 1)]
        assert pss.scores['HEADLESS_KNIGHT'] == [(1, 'A', 'B', 1)]
        assert pss.scores['DUCKHUNTER'] == [(1, 'A', 'B', 1)]
        pss.player_scores.players_sorted_by_score.assert_called_with(
            skip_world=True)

    def test_lifespan(self, pss):
        pss.process_lifespan(gen_death(1, 'B', 'A', 'dummy'))
        assert pss.player_state['A']['lifespan']['max'] == 0
        assert pss.player_state['A']['lifespan']['last_death'] == 1

        pss.process_lifespan(gen_death(15, 'B', 'A', 'dummy'))
        assert pss.player_state['A']['lifespan']['max'] == 14
        assert pss.player_state['A']['lifespan']['last_death'] == 15
        assert 'MOSQUITO' not in pss.scores

        pss.process_lifespan(gen_death(17, 'B', 'A', 'dummy'))
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
        event = gen_death(10, 'A', 'B', 'LAVA')
        pss.vengeance_start(event)
        assert pss.player_state['B']['vengeance_target'] == 'A'

        event = gen_death(10, 'C', 'B', 'LAVA')
        pss.vengeance_start(event)
        assert pss.player_state['B']['vengeance_target'] == 'C'

        event = gen_death(10, 'B', 'B', 'LAVA')
        pss.vengeance_start(event)
        assert pss.player_state['B']['vengeance_target'] is None

    def test_score_vengeance(self, pss):
        event = gen_death(10, 'A', 'B', 'LAVA')
        pss.score_vengeance(event)
        assert pss.scores['VENGEANCE'] == []

        pss.player_state['A']['vengeance_target'] = 'B'
        pss.score_vengeance(event)
        assert pss.scores['VENGEANCE'] == [(10, 'A', 'B', 1)]

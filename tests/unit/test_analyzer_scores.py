from quakestats.dataprovider.analyzer.events import Event
from quakestats.dataprovider.analyzer.scores import PlayerScores


def gen_switch_team(time, player_id, old_team, new_team):
    return Event.from_dict({
        'TYPE': 'PLAYER_SWITCHTEAM',
        'DATA': {
            'TIME': time,
            'KILLER': {
                'STEAM_ID': player_id,
                'OLD_TEAM': old_team,
                'TEAM': new_team,
            }
        }
    })


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


class TestPlayerScores():
    def test_from_player_kill(self):
        ps = PlayerScores()
        assert ps.kdr['A'].r == 0

        ps.from_player_kill(gen_kill(1, 'A', 'B', 'SHOTGUN'))

        assert len(ps.scores) == 1
        assert ps.player_score['A'] == [1, 1]
        assert ps.scores[0] == (1, 'A', 1, 'SHOTGUN')
        assert len(ps.kills) == 1
        assert ps.kills[0] == (1, 'A', 'B', 'SHOTGUN')
        assert ps.kdr['A'].r == 1

        ps.from_player_kill(gen_kill(2, 'A', 'C', 'MOD3'))
        assert len(ps.scores) == 2
        assert ps.player_score['A'] == [2, 2]
        assert ps.scores[1] == (2, 'A', 2, 'MOD3')
        assert len(ps.kills) == 2
        assert ps.kills[1] == (2, 'A', 'C', 'MOD3')
        assert ps.kdr['A'].r == 2

        ps.from_player_kill(gen_kill(2, 'B', 'A', 'MOD3'))

        assert len(ps.scores) == 3
        assert ps.player_score['B'] == [1, 2]
        assert ps.scores[2] == (2, 'B', 1, 'MOD3')
        assert len(ps.kills) == 3
        assert ps.kills[2] == (2, 'B', 'A', 'MOD3')

    def test_from_player_kill_selfkill(self):
        ps = PlayerScores()
        ps.from_player_kill(gen_kill(2, 'A', 'A', 'SHOTGUN'))

        assert ps.player_score['A'] == [0, 0]
        assert ps.kills == [(2, 'A', 'A', 'SHOTGUN')]
        assert ps.scores == []

    def test_from_player_swtichteam(self):
        ps = PlayerScores()
        ps.player_score['A'] = [10, 0]
        ps.from_player_switchteam(gen_switch_team(3, 'A', 'Free', 'Spect'))

        assert ps.scores[0] == (3, 'A', 0, 'SWITCHTEAM')
        ps.player_score['A'] == [0, 0]

    def test_from_player_disconnect(self):
        ps = PlayerScores()
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
        ps = PlayerScores()
        ps.from_player_death(gen_death(3, 'q3-world', 'B', 'FALLING'))

        assert ps.scores[0] == (3, 'B', -1, 'FALLING')
        assert ps.player_score['B'] == [-1, 0]
        assert ps.deaths[0] == (3, 'q3-world', 'B', 'FALLING')

    def test_from_player_death_selfkill(self):
        ps = PlayerScores()
        ps.from_player_death(gen_death(3, 'B', 'B', 'FALLING'))

        assert ps.scores[0] == (3, 'B', -1, 'FALLING')
        assert ps.player_score['B'] == [-1, 0]
        assert ps.deaths[0] == (3, 'B', 'B', 'FALLING')

    def test_from_player_death(self):
        ps = PlayerScores()
        ps.from_player_death(gen_death(3, 'A', 'B', 'MOD_ROCKET'))

        assert ps.scores == []
        assert ps.player_score['B'] == [0, 0]
        assert ps.deaths[0] == (3, 'A', 'B', 'MOD_ROCKET')

    def test_players_sorted_by_score(self):
        ps = PlayerScores()
        ps.match_duration = 900
        ps.from_player_kill(gen_kill(1, 'A', 'B', 'SHOTGUN'))
        ps.from_player_kill(gen_kill(2, 'A', 'B', 'SHOTGUN'))
        ps.from_player_kill(gen_kill(1, 'B', 'C', 'SHOTGUN'))
        assert ps.players_sorted_by_score() == ['A', 'B']

        ps.from_player_kill(gen_kill(3, 'B', 'C', 'SHOTGUN'))
        assert ps.players_sorted_by_score() == ['B', 'A']

        ps.from_player_kill(gen_kill(4, 'A', 'B', 'SHOTGUN'))
        assert ps.players_sorted_by_score() == ['A', 'B']

        ps.from_player_disconnect({"TIME": 10, "STEAM_ID": 'A'})
        assert ps.players_sorted_by_score() == ['B']

        ps.from_player_switchteam(gen_switch_team(10, 'B', 'Free', 'Spect'))
        assert ps.players_sorted_by_score() == []

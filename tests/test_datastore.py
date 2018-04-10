import mock
import pytest
import pymongo
from quakestats.datasource import mongo2


class TestDataStoreMongo():

    @pytest.fixture
    def ds(self):
        return mongo2.DataStoreMongo(mock.Mock())

    @pytest.fixture
    def report(self):
        report = mock.Mock()
        md = mock.Mock()
        report.match_metadata = md
        md.match_guid = 'match_guid'
        md.server_domain = 'domain'
        md.capture_limit = 10
        md.duration = 20
        md.exit_message = 'Exit'
        md.finish_date = 0
        md.frag_limit = 200
        md.game_type = 'FFA'
        md.map_name = 'map1'
        md.score_limit = 1000
        md.server_name = 'sv_name'
        md.start_date = 1
        md.time_limit = 100
        report.players = {}
        for i in ['1']:
            p = mock.Mock()
            p.name = 'n{}'.format(i)
            p.model = 'm{}'.format(i)
            report.players[i] = p

        report.team_switches = [
            (4, 'p1', 't1', 't2'),
            (5, 'p1', 't2', 't1'),
            (6, 'p2', 't2', 't1'),
        ]
        report.scores = [
            (27.2, '36c691b681ce0bdf7eace585', 2, 'LIGHTNING'),
            (29.0, '073430507f5ef4dddf99bf8b', 1, 'RAILGUN'),
            (31.8, '87bf60cac665cf641d87ba4f', 3, 'SHOTGUN'),
        ]
        report.kills = [
            (890.4, '88fdc96e8804eaa084d740f8', '7ee3d47a164c6544ea50fee6', 'LIGHTNING'),
            (891.3, 'e0fbefd04b9203526e6f22b8', 'a126a35a25eab0623f504183', 'SHOTGUN'),
            (891.8, '88fdc96e8804eaa084d740f8', '9ac5682eefa9134bbfe3c481', 'LIGHTNING'),
        ]
        report.special_scores = {
            'HEADHUNTER': [(664.4, '87bf60cac665cf641d87ba4f', '073430507f5ef4dddf99bf8b', 1)],
        }
        return report

    @pytest.fixture
    def stored_switches(self):
        return [
            {'match_guid': 'match_guid', 'game_time': 4, 'player_id': 'p1', 'from': 't1', 'to': 't2'},
            {'match_guid': 'match_guid', 'game_time': 5, 'player_id': 'p1', 'from': 't2', 'to': 't1'},
            {'match_guid': 'match_guid', 'game_time': 6, 'player_id': 'p2', 'from': 't2', 'to': 't1'},
        ]

    def test_store_players(self, ds, report):
        ds.store_players(report)

        ds.db.player.bulk_write.assert_called_with([
            pymongo.UpdateOne(
                {'id': '1', 'server_domain': 'domain'},
                {'$set': {
                    'server_domain': 'domain', 'name': 'n1', 'model': 'm1', 'id': '1',
                }},
                upsert=True
            )])

    def test_store_match(self, ds, report):
        ds.store_match(report)
        ds.db.match.insert_one.assert_called_with({
            'server_domain': 'domain',
            'match_guid': 'match_guid',
            'capture_limit': 10,
            'duration': 20,
            'exit_message': 'Exit',
            'finish_date': 0,
            'frag_limit': 200,
            'game_type': 'FFA',
            'map_name': 'map1',
            'server_name': 'sv_name',
            'start_date': 1,
            'time_limit': 100,
            'score_limit': 1000,
        })

    def test_store_team_lifecycle(self, ds, report, stored_switches):
        ds.store_team_lifecycle(report)
        ds.db.team_switch.insert_many.assert_called_with(stored_switches)

    def test_store_scores(self, ds, report):
        ds.store_scores(report)
        ds.db.score.insert_many.assert_called_with([
            {
                'game_time': 27.2, 'match_guid': 'match_guid',
                'player_id': '36c691b681ce0bdf7eace585', 'score': 2, 'by': 'LIGHTNING'},
            {
                'game_time': 29.0, 'match_guid': 'match_guid',
                'player_id': '073430507f5ef4dddf99bf8b', 'score': 1, 'by': 'RAILGUN'},
            {
                'game_time': 31.8, 'match_guid': 'match_guid',
                'player_id': '87bf60cac665cf641d87ba4f', 'score': 3, 'by': 'SHOTGUN'},
        ])

    def test_store_kills(self, ds, report):
        ds.store_kills(report)
        ds.db.kill.insert_many.assert_called_with([
            {
                'game_time': 890.4, 'match_guid': 'match_guid',
                'killer_id': '88fdc96e8804eaa084d740f8', 'victim_id': '7ee3d47a164c6544ea50fee6',
                'by': 'LIGHTNING'},
            {
                'game_time': 891.3, 'match_guid': 'match_guid',
                'killer_id': 'e0fbefd04b9203526e6f22b8', 'victim_id': 'a126a35a25eab0623f504183',
                'by': 'SHOTGUN'},
            {
                'game_time': 891.8, 'match_guid': 'match_guid',
                'killer_id': '88fdc96e8804eaa084d740f8', 'victim_id': '9ac5682eefa9134bbfe3c481',
                'by': 'LIGHTNING'},
        ])

    def test_store_special_kills(self, ds, report):
        ds.store_special_scores(report)
        ds.db.special_score.insert_many.assert_called_with([
            {
                'game_time': 664.4, 'match_guid': 'match_guid', 'score_type': 'HEADHUNTER',
                'killer_id': '87bf60cac665cf641d87ba4f', 'victim_id': '073430507f5ef4dddf99bf8b',
                'value': 1
            }
        ])

    def test_get_matches(self, ds):
        ds.db.match.find.return_value = [
            {'match_guid': 1, '_id': 1},
            {'match_guid': 2, '_id': 2}
        ]
        res = ds.get_matches()
        ds.db.match.find.assert_called()

        assert res == [
            {'match_guid': 1},
            {'match_guid': 2}
        ]

    def test_get_match_players(self, ds, stored_switches):
        ds.db.team_switch.find.return_value = stored_switches
        ds.db.player.find.return_value = []
        res = ds.get_match_players('dummy')
        ds.db.team_switch.find.assert_called_with({'match_guid': 'dummy'})
        call_args = ds.db.player.find.call_args[0][0]
        assert set(call_args['id']['$in']) == set(['p1', 'p2'])
        assert res == []

    def test_get_match_special_scores(self, ds):
        ds.db.special_score.find.return_value = [{'test': 5, '_id': 1}]
        res = ds.get_match_special_scores('dummy')
        ds.db.special_score.find.assert_called_with({'match_guid': 'dummy'})
        assert res == [{'test': 5}]

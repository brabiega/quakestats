from quakestats.dataprovider.quake3 import Q3MatchFeeder, FeedFull
from quakestats.dataprovider.quakelive import QLMatchFeeder
from quakestats.dataprovider.quakelive import collector
from quakestats import dataprovider
from quakestats.dataprovider import quake3
import datetime
import json
import pytest
import mock
from contextlib import ExitStack


# TODO use some better approach for test data
TEST_DATA_PATH = './sampledata/quakelive/ca-full.json'
Q3_MATCH = './sampledata/match.log'


class MatchHelper():
    def __init__(self, data):
        self.data = data

    def get_event(self, _type):
        for entry in self.data['EVENTS']:
            if entry['TYPE'] == _type:
                return entry
        raise Exception("Missing event {}".format(_type))

    def match_report(self):
        return self.get_event('MATCH_REPORT')

    def match_start(self):
        return self.get_event('MATCH_STARTED')


@pytest.fixture
def q3_full_match():
    with open(Q3_MATCH) as fh:
        data = fh.read()
        return data


@pytest.fixture
def ql_ca_full():
    with open(TEST_DATA_PATH) as fh:
        data = fh.read()

    match_info = json.loads(data)
    return MatchHelper(match_info)


class TestQuakeLive():
    def test_ql_match_feeder(self, ql_ca_full):
        feeder = QLMatchFeeder()
        for event in ql_ca_full.data['EVENTS']:
            feeder.feed(event)

    def test_ql_match_feeder_full(self):
        events = [
            {'DATA': {'MATCH_GUID': '123'}},
            {'DATA': {'MATCH_GUID': '125'}},
        ]

        feeder = QLMatchFeeder()
        feeder.feed(events[0])
        feeder.feed(events[0])
        with pytest.raises(FeedFull):
            feeder.feed(events[1])

        result = feeder.consume()
        assert len(result['EVENTS']) == 2
        feeder.feed(events[1])


class TestQuake3():
    data = (
        """13.0 ShutdownGame:
13.0 ------------------------------------------------------------
13.0 ------------------------------------------------------------
""")
    server_time = (
        """0.0 ServerTime: 20170621112912  11:29:12 (21 Jun 2017)""")

    def test_q3_to_ql(self, q3_full_match):
        feeder = Q3MatchFeeder()
        matches = []
        for line in q3_full_match.splitlines():
            try:
                feeder.feed(line)
            except FeedFull:
                match = feeder.consume()
                matches.append(match)

        game = matches[-1]

        transformer = quake3.Q3toQL(game['EVENTS'])
        transformer.process()

    def test_q3_to_ql_extract(self):
        data = "15.6 ServerTime:    20170623124300  12:43:00 (23 Jun 2017)"

        transformer = quake3.Q3toQL([])
        ts, name, args = transformer.extract(data)
        assert ts == 15.6
        assert name == "ServerTime"
        assert args == "20170623124300  12:43:00 (23 Jun 2017)"

        data = "15.7 Game End:"
        ts, name, args = transformer.extract(data)
        assert ts == 15.7
        assert name == "Game End"
        assert args == ""

    def test_q3_to_ql_process_server_time(self):
        data = "15.6 ServerTime:    20170623124301  12:43:01 (23 Jun 2017)"
        transformer = quake3.Q3toQL([])
        si = transformer.result['server_info']
        si['gametype'] = 'FFA'
        si['timelimit'] = 15
        si['fraglimit'] = 200
        si['capturelimit'] = 8
        si['mapname'] = 'q3dm6'
        si['sv_hostname'] = 'MyServ'
        event = transformer.process_raw_event(data)
        result = transformer.result

        assert result['start_date'] == datetime.datetime(2017, 6, 23, 12, 43, 1)

        assert event['TYPE'] == 'MATCH_STARTED'
        evd = event['DATA']
        assert evd['GAME_TYPE'] == 'FFA'
        assert evd['TIME_LIMIT'] == 15
        assert evd['FRAG_LIMIT'] == 200
        assert evd['CAPTURE_LIMIT'] == 8
        assert evd['MAP'] == 'q3dm6'
        assert evd['SERVER_TITLE'] == 'MyServ'

    def test_q3_to_ql_process_warmup(self):
        data = "15.6 Warmup:"
        transformer = quake3.Q3toQL([])
        result = transformer.result
        assert not result['warmup']
        transformer.process_raw_event(data)
        assert result['warmup']

    def test_q3_to_ql_ts2match_time(self):
        transformer = quake3.Q3toQL([])
        with pytest.raises(AssertionError):
            transformer.ts2match_time(10)

        transformer.time_offset = 10
        res = transformer.ts2match_time(15)
        assert res == 5

        with pytest.raises(AssertionError):
            transformer.ts2match_time(5)

    def test_q3_to_ql_process_user_info(self):
        data = (
            r"0.2 ClientUserinfoChanged: 2 "
            r"n\Bartoszer\t\0\model\xaero/default\hmodel\xaero/default"
            r"\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0")
        transformer = quake3.Q3toQL([])
        transformer.time_offset = 0.1
        transformer.server_domain = "mydomain"
        transformer.match_guid = 'dummy'
        result = transformer.process_raw_event(data)

        assert transformer.players
        player_info = list(transformer.players.values())[0]
        assert player_info['name'] == 'Bartoszer'
        assert player_info['model'] == r'xaero/default'

        player_id = transformer.client_player_map['2']
        assert player_id
        assert transformer.players[player_id] is player_info

        ev = result[0]
        assert ev['TYPE'] == 'PLAYER_CONNECT'
        evd = ev['DATA']
        assert evd['MATCH_GUID'] == 'dummy'
        assert evd['NAME'] == 'Bartoszer'
        assert evd['STEAM_ID']
        assert evd['TIME'] == 0.1
        assert evd['WARMUP'] is False

        ev = result[1]
        assert ev['TYPE'] == 'PLAYER_SWITCHTEAM'
        assert ev['DATA']['KILLER']['NAME'] == 'Bartoszer'
        assert ev['DATA']['KILLER']['OLD_TEAM'] == 'SPECTATOR'
        assert ev['DATA']['KILLER']['TEAM'] == 'FREE'

    def test_q3_to_ql_process_user_info_twice_same_team(self):
        data = (
            r"0.2 ClientUserinfoChanged: 2 "
            r"n\Bartoszer\t\0\model\xaero/default\hmodel\xaero/default"
            r"\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0")
        data2 = (
            r"0.2 ClientUserinfoChanged: 2 "
            r"n\Bartoszer\t\0\model\sarge/default\hmodel\xaero/default"
            r"\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0")
        transformer = quake3.Q3toQL([])
        transformer.time_offset = 0.1
        transformer.server_domain = "mydomain"
        transformer.match_guid = 'dummy'
        transformer.process_raw_event(data)

        assert transformer.players
        player_info = list(transformer.players.values())[0]
        assert player_info['name'] == 'Bartoszer'
        assert player_info['model'] == r'xaero/default'

        events = transformer.process_raw_event(data2)
        assert events == []

        assert len(transformer.players) == 1
        player_info = list(transformer.players.values())[0]
        assert player_info['model'] == r'sarge/default'

    def test_q3_to_ql_process_user_info_twice_change_team(self):
        data = (
            r"0.2 ClientUserinfoChanged: 2 "
            r"n\Bartoszer\t\3\model\xaero/default\hmodel\xaero/default"
            r"\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0")
        data2 = (
            r"0.2 ClientUserinfoChanged: 2 "
            r"n\Bartoszer\t\0\model\sarge/default\hmodel\xaero/default"
            r"\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0")
        transformer = quake3.Q3toQL([])
        transformer.time_offset = 0.1
        transformer.server_domain = "mydomain"
        transformer.match_guid = 'dummy'
        transformer.process_raw_event(data)

        assert transformer.players
        player_info = list(transformer.players.values())[0]
        assert player_info['name'] == 'Bartoszer'
        assert player_info['model'] == r'xaero/default'

        events = transformer.process_raw_event(data2)
        assert len(events) == 1
        ev = events[0]
        assert ev['TYPE'] == 'PLAYER_SWITCHTEAM'
        assert ev['DATA']['TIME'] == 0.1
        assert ev['DATA']['WARMUP'] is False
        assert ev['DATA']['MATCH_GUID'] == 'dummy'
        assert ev['DATA']['KILLER']['NAME'] == 'Bartoszer'
        assert ev['DATA']['KILLER']['STEAM_ID']
        assert ev['DATA']['KILLER']['OLD_TEAM'] == 'SPECTATOR'
        assert ev['DATA']['KILLER']['TEAM'] == 'FREE'

    @pytest.mark.xfail
    def test_q3_to_ql_process_client_info_changed_same_nick(self):
        # This test is not incorrect at the moment
        # multiple clients may be present the same,
        # unique id is assigned during connection and
        # changed later
        data = (
            r"0.2 ClientUserinfoChanged: 2 "
            r"n\Bartoszer\t\3\model\xaero/default\hmodel\xaero/default"
            r"\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0")
        data2 = (
            r"0.2 ClientUserinfoChanged: 3 "
            r"n\Bartoszer\t\0\model\sarge/default\hmodel\xaero/default"
            r"\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0")

        transformer = quake3.Q3toQL([])
        transformer.time_offset = 0.1
        transformer.server_domain = "mydomain"
        transformer.match_guid = 'dummy'

        transformer.process_raw_event(data)
        with pytest.raises(AssertionError):
            transformer.process_raw_event(data2)

    def test_q3_to_ql_process_kill(self):
        data = (
            r"0.2 ClientUserinfoChanged: 2 "
            r"n\Bartoszer\t\3\model\xaero/default\hmodel\xaero/default"
            r"\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0")
        data2 = (
            r"0.2 ClientUserinfoChanged: 3 "
            r"n\Bolek\t\0\model\sarge/default\hmodel\xaero/default"
            r"\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0")
        data3 = (
            r"884.3 Kill: 2 3 7: Bartoszer killed Bolek by MOD_ROCKET_SPLASH 5")

        transformer = quake3.Q3toQL([])
        transformer.time_offset = 0.1
        transformer.server_domain = "mydomain"
        transformer.match_guid = 'dummy'

        transformer.process_raw_event(data)
        transformer.process_raw_event(data2)

        events = transformer.process_raw_event(data3)
        ev = events[0]
        assert ev['TYPE'] == 'PLAYER_KILL'
        assert ev['DATA']['MATCH_GUID'] == 'dummy'
        assert ev['DATA']['MOD'] == 'ROCKET_SPLASH'
        assert int(ev['DATA']['TIME']) == 884

        assert ev['DATA']['KILLER']['NAME'] == 'Bartoszer'
        assert ev['DATA']['KILLER']['STEAM_ID']
        assert ev['DATA']['KILLER']['TEAM'] == '3'

        assert ev['DATA']['VICTIM']['NAME'] == 'Bolek'
        assert ev['DATA']['VICTIM']['STEAM_ID']
        assert ev['DATA']['VICTIM']['TEAM'] == '0'

        evd = events[1]
        assert evd['TYPE'] == 'PLAYER_DEATH'
        assert evd['DATA'] == ev['DATA']

    def test_q3_to_ql_process_exit(self):
        transformer = quake3.Q3toQL([])
        transformer.server_domain = "mydomain"
        transformer.match_guid = 'dummy'
        data = (
            r'10.0 InitGame: \dmflags\0\fraglimit\200\timelimit\15'
            r'\sv_hostname\MY Q3\sv_maxclients\32\sv_minRate\0\sv_maxRate\0'
            r'\sv_dlRate\100\sv_minPing\0\sv_maxPing\0\sv_floodProtect\0'
            r'\sv_allowDownload\1\sv_dlURL\http://10.40.3.11:8000/\capturelimit\8'
            r'\version\ioq31.36+u20160616+dfsg1-1/'
            r'Ubuntu linux-x86_64 Jun 27 2016\com_gamename\Quake3Arena'
            r'\com_protocol\71\g_gametype\0\mapname\nodm9\sv_privateClients\0'
            r'\server_ospauth\0\gamename\osp\gameversion\OSP v1.03a'
            r'\Players_Active\1 2 3 4 5 6 7 8 \server_promode\0\g_needpass\0\server_freezetag\0'
        )
        data1 = (
            "15.6 ServerTime:    20170623124301  12:43:01 (23 Jun 2017)")
        data2 = (
            r'915.6 Exit: Timelimit hit.')
        transformer.process_raw_event(data)
        assert transformer.time_offset == 10
        assert transformer.match_report_event is None
        transformer.process_raw_event(data1)
        assert transformer.result['start_date']

        transformer.process_raw_event(data2)
        ev = transformer.match_report_event
        assert ev
        assert ev['TYPE'] == 'MATCH_REPORT'
        assert ev['DATA']['MAP'] == 'nodm9'
        assert ev['DATA']['GAME_LENGTH'] == 905.6
        assert ev['DATA']['GAME_TYPE'] == 'FFA'
        assert ev['DATA']['EXIT_MSG'] == 'Timelimit hit.'
        assert transformer.result['finish_date']

    def test_q3_to_ql_player_disconnected(self):
        data1 = (
            r"0.2 ClientUserinfoChanged: 1 "
            r"n\Bartoszer\t\3\model\xaero/default\hmodel\xaero/default"
            r"\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0")
        data2 = (
            r'712.9 ClientDisconnect: 1')

        transformer = quake3.Q3toQL([])
        transformer.time_offset = 0.1
        transformer.server_domain = "mydomain"
        transformer.match_guid = 'dummy'

        transformer.process_raw_event(data1)
        ev = transformer.process_raw_event(data2)
        assert ev
        assert ev['TYPE'] == 'PLAYER_DISCONNECT'
        assert ev['DATA']['NAME'] == 'Bartoszer'
        assert ev['DATA']['STEAM_ID']
        assert ev['DATA']['TIME'] == 712.8
        assert ev['DATA']['WARMUP'] is False
        assert ev['DATA']['MATCH_GUID'] == 'dummy'


class TestMatchPreprocessor():
    @pytest.mark.parametrize('aborted', [True, False])
    def test_process_events_aborted(self, aborted):
        mp = dataprovider.MatchPreprocessor()
        events = [
            {'TYPE': 'MATCH_STARTED', 'DATA': {'MATCH_GUID': 'dummy'}},
            {'TYPE': 'MATCH_REPORT', 'DATA': {
                'MATCH_GUID': 'dummy', 'ABORTED': aborted, 'GAME_LENGTH': 900}}
        ]
        mp.process_events(events)
        assert aborted == mp.aborted

    def test_process_events_finish_only(self):
        mp = dataprovider.MatchPreprocessor()
        events = [
            {'TYPE': 'MATCH_REPORT', 'DATA': {
                'MATCH_GUID': 'dummy', 'ABORTED': False, 'GAME_LENGTH': 900}}
        ]
        mp.process_events(events)
        assert mp.finished
        assert not mp.started

    def test_process_events_start_only(self):
        mp = dataprovider.MatchPreprocessor()
        events = [
            {'TYPE': 'MATCH_STARTED', 'DATA': {'MATCH_GUID': 'dummy'}},
        ]
        mp.process_events(events)
        assert mp.started
        assert not mp.finished
        assert events[0] in mp.events

    def test_process_events_warmup(self):
        mp = dataprovider.MatchPreprocessor()
        events = [
            {'TYPE': 'MATCH_STARTED', 'DATA': {
                'MATCH_GUID': 'dummy', 'WARMUP': True}},
        ]
        mp.process_events(events)
        assert events[0] not in mp.events

    @pytest.mark.parametrize(
        'started,finished,aborted,result', [
            (True, True, True, False),
            (True, True, False, True),
            (False, True, False, False),
            (True, False, False, False)]
    )
    def test_is_valid(self, started, finished, aborted, result):
        mp = dataprovider.MatchPreprocessor()
        mp.started = started
        mp.finished = finished
        mp.aborted = aborted
        assert mp.is_valid() is result


class TestMatchCollector():
    @pytest.fixture
    def mc(self):
        return collector.MatchCollector('/tmp/ql')

    def test_init(self):
        mc = collector.MatchCollector('/tmp/ql')
        assert mc

    def test_process_event(self, mc):
        dummy_event = {}
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(mc, 'validate_match'))
            stack.enter_context(mock.patch.object(mc, 'save_match'))
            stack.enter_context(mock.patch.object(mc.feeder, 'feed'))
            stack.enter_context(mock.patch.object(mc, 'save_invalid'))

            mc.process_event(dummy_event)
            assert mc.feeder.feed.called
            assert not mc.validate_match.called

            mc.feeder.feed.side_effect = FeedFull('Feed full')
            mc.validate_match.side_effect = lambda self: None
            mc.process_event(dummy_event)

            mc.validate_match.assert_called()
            mc.save_match.assert_not_called()
            mc.save_invalid.assert_called()

            mc.save_match.reset()
            mc.save_invalid.reset()

            mc.validate_match.side_effect = lambda self: {"EVENTS": []}
            mc.process_event(dummy_event)
            assert mc.validate_match.called
            assert mc.save_match.called

    def test_validate_match(self, mc):
        match_info = {"EVENTS": []}
        result = mc.validate_match(match_info)
        assert result is None

        match_info = {"EVENTS": [
            {"TYPE": "MATCH_REPORT", 'DATA': {
                'GAME_LENGTH': 10, 'ABORTED': False, 'MATCH_GUID': 'MEH'}}
        ]}
        with mock.patch(
            'quakestats.dataprovider.quakelive.'
            'collector.MatchPreprocessor.is_valid'
        ):
            res = mc.validate_match(match_info)
            assert res['MATCH_GUID'] == 'MEH'
            assert res['EVENTS']

    def test_save_match(self, mc):
        mock_open = mock.mock_open()
        with ExitStack() as stack:
            stack.enter_context(mock.patch(
                'quakestats.dataprovider.quakelive.'
                'collector.open', mock_open))
            rename = stack.enter_context(mock.patch(
                'quakestats.dataprovider.quakelive.collector.os.rename'))
            match_info = {"MATCH_GUID": 'dummy'}

            mc.save_match(match_info)
            mock_open.assert_called_once_with(
                '/tmp/ql/match-dummy.tmp', 'w')

            rename.assert_called_once_with(
                '/tmp/ql/match-dummy.tmp', '/tmp/ql/match-dummy.json')

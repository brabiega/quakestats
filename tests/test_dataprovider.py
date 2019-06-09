from quakestats.dataprovider.quake3 import Q3MatchFeeder, FeedFull
from quakestats.dataprovider.quakelive import QLMatchFeeder
from quakestats.dataprovider.quakelive import collector
from quakestats import dataprovider
from quakestats.dataprovider import quake3
import json
import pytest
import os
from unittest import mock
from contextlib import ExitStack


FIXTURE_DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'sampledata',
)
TEST_DATA_PATH = os.path.join(FIXTURE_DATA_DIR, 'quakelive/ca-full.json')
Q3_MATCH = os.path.join(FIXTURE_DATA_DIR, 'match.log')


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

import pytest
import json
import mock
from contextlib import ExitStack
from quakestats import dataprovider
from quakestats.dataprovider import quakelive, quake3, analyze
from quakestats.dataprovider.quakelive import collector

QL_DUMP_PATH = 'sampledata/quakelive/qldump.txt'
Q3_DUMP_PATH = 'sampledata/match.log'


@pytest.fixture(scope='session')
def q3_dump():
    with open(Q3_DUMP_PATH) as fh:
        return fh.read()


@pytest.fixture(scope='session')
def quakelive_dump():
    with open(QL_DUMP_PATH) as fh:
        data = fh.read()
    return json.loads(data)


def test_quakelive_feed_preprocess(quakelive_dump):
    feeder = quakelive.QLMatchFeeder()
    matches = []
    for event in quakelive_dump:
        try:
            feeder.feed(event)
        except dataprovider.FeedFull:
            matches.append(feeder.consume())

    for match in matches:
        preprocessor = dataprovider.MatchPreprocessor()
        preprocessor.process_events(match['EVENTS'])

        for ev in preprocessor.events:
            assert not ev['DATA'].get('WARMUP', False)

        assert preprocessor.match_guid
        assert preprocessor.events

        if preprocessor.finished:
            assert preprocessor.duration


def test_qukelive_collector(quakelive_dump):
    mc = collector.MatchCollector('/tmp/qltest')
    mock_open = mock.mock_open()
    with ExitStack() as stack:
        stack.enter_context(mock.patch(
            'quakestats.dataprovider.quakelive.'
            'collector.open', mock_open))
        stack.enter_context(mock.patch(
            'quakestats.dataprovider.quakelive.'
            'collector.os.rename'))

        for event in quakelive_dump:
            mc.process_event(event)

        assert mock_open.call_count == 5


def test_quake3_feed_preprocess(q3_dump):
    feeder = quake3.Q3MatchFeeder()
    matches = []
    for line in q3_dump.splitlines():
        try:
            feeder.feed(line)
        except dataprovider.FeedFull:
            matches.append(feeder.consume())

    for match in matches:
        transformer = quake3.Q3toQL(match['EVENTS'])
        transformer.process()
        result = transformer.result
        preprocessor = dataprovider.MatchPreprocessor()

        preprocessor.process_events(result['events'])

        for ev in preprocessor.events:
            assert not ev['DATA'].get('WARMUP', False)

        assert preprocessor.match_guid
        assert preprocessor.events

        if preprocessor.finished:
            assert preprocessor.duration


def test_quake3_analyze(q3_dump):
    feeder = quake3.Q3MatchFeeder()
    matches = []
    for line in q3_dump.splitlines():
        try:
            feeder.feed(line)
        except dataprovider.FeedFull:
            matches.append(feeder.consume())

    for match in matches[-1:]:
        transformer = quake3.Q3toQL(match['EVENTS'])
        transformer.process()
        result = transformer.result
        preprocessor = dataprovider.MatchPreprocessor()

        preprocessor.process_events(result['events'])

        if not preprocessor.finished:
            continue

        fmi = dataprovider.FullMatchInfo.from_preprocessor(
            preprocessor,
            transformer.result['start_date'],
            transformer.result['finish_date'],
            'serv-domain', 'Q3')

        analyzer = analyze.Analyzer()
        result = analyzer.analyze(fmi)

        assert result.match_metadata.duration == 900
        assert result.match_metadata.frag_limit == 200
        assert result.match_metadata.map_name == 'nodm9'
        assert result.match_metadata.match_guid
        assert result.match_metadata.server_domain == 'serv-domain'
        assert result.match_metadata.server_name == 'MY Q3'
        assert result.match_metadata.time_limit == 15

        assert result.final_scores['291b0ba5fdf78b268369a9d7'][0] == 0
        assert result.final_scores['6a018beb6405ef59ce1471b0'][0] == 27
        assert result.final_scores['7ee3d47a164c6544ea50fee6'][0] == 37
        assert result.final_scores['88fdc96e8804eaa084d740f8'][0] == 33
        assert result.final_scores['9ac5682eefa9134bbfe3c481'][0] == 42
        assert result.final_scores['a126a35a25eab0623f504183'][0] == 41
        assert result.final_scores['d37928942982cc79e7e0fe12'][0] == 85
        assert result.final_scores['e0fbefd04b9203526e6f22b8'][0] == 45
        assert result.final_scores['q3-world'][0] == 16

        assert len(result.team_switches) == 10
        assert result.team_switches[-1] == (697.3, '291b0ba5fdf78b268369a9d7', None, 'DISCONNECTED')

        assert result.players['291b0ba5fdf78b268369a9d7'].name == 'Turbo Wpierdol'
        assert result.players['6a018beb6405ef59ce1471b0'].name == 'MACIEK'
        assert result.players['7ee3d47a164c6544ea50fee6'].name == 'n0npax'
        assert result.players['88fdc96e8804eaa084d740f8'].name == 'darkside'
        assert result.players['9ac5682eefa9134bbfe3c481'].name == 'BOLEK'
        assert result.players['a126a35a25eab0623f504183'].name == 'killer clown'
        assert result.players['d37928942982cc79e7e0fe12'].name == 'Bartoszer'
        assert result.players['e0fbefd04b9203526e6f22b8'].name == 'Stefan'

        assert result.kills[-1] == (897.1, 'd37928942982cc79e7e0fe12', 'd37928942982cc79e7e0fe12', 'ROCKET_SPLASH')

        assert result.server_info.server_name == 'MY Q3'
        assert result.server_info.server_domain == 'serv-domain'
        assert result.server_info.server_type == 'Q3'

        assert result.special_scores['GAUNTLET_KILL'][3] == (
            150.4, 'd37928942982cc79e7e0fe12',
            'e0fbefd04b9203526e6f22b8', 1)

        assert result.special_scores['KILLING_SPREE'][2] == (
            64.9, 'd37928942982cc79e7e0fe12',
            '9ac5682eefa9134bbfe3c481', 1)

import pytest
import json
import os
from unittest import mock
from contextlib import ExitStack
from quakestats import dataprovider
from quakestats.dataprovider import quakelive, quake3, analyze
from quakestats.dataprovider.quakelive import collector


FIXTURE_DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'sampledata',
)
QL_DUMP_PATH = os.path.join(FIXTURE_DATA_DIR, 'quakelive/qldump.txt')
Q3_DUMP_PATH = os.path.join(FIXTURE_DATA_DIR, 'match.log')


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


def test_quake3_analyze_nodm9(q3_dump):
    feeder = quake3.Q3MatchFeeder()
    matches = []
    for line in q3_dump.splitlines():
        try:
            feeder.feed(line)
        except dataprovider.FeedFull:
            matches.append(feeder.consume())

    # nodm9
    match = matches[-1]
    transformer = quake3.Q3toQL(match['EVENTS'])
    transformer.process()
    result = transformer.result
    preprocessor = dataprovider.MatchPreprocessor()

    preprocessor.process_events(result['events'])

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
    assert result.team_switches[-1] == (697.3, '291b0ba5fdf78b268369a9d7', None, 'DISCONNECTED')  # noqa

    assert result.players['291b0ba5fdf78b268369a9d7'].name == 'Turbo Wpierdol' # noqa
    assert result.players['6a018beb6405ef59ce1471b0'].name == 'MACIEK'
    assert result.players['7ee3d47a164c6544ea50fee6'].name == 'n0npax'
    assert result.players['88fdc96e8804eaa084d740f8'].name == 'darkside'
    assert result.players['9ac5682eefa9134bbfe3c481'].name == 'BOLEK'
    assert result.players['a126a35a25eab0623f504183'].name == 'killer clown'  # noqa
    assert result.players['d37928942982cc79e7e0fe12'].name == 'Bartoszer'
    assert result.players['e0fbefd04b9203526e6f22b8'].name == 'Stefan'

    assert result.kills[-1] == (897.1, 'd37928942982cc79e7e0fe12', 'd37928942982cc79e7e0fe12', 'ROCKET_SPLASH')  # noqa

    assert result.server_info.server_name == 'MY Q3'
    assert result.server_info.server_domain == 'serv-domain'
    assert result.server_info.server_type == 'Q3'

    assert result.special_scores['GAUNTLET_KILL'][3] == (
        150.4, 'd37928942982cc79e7e0fe12',
        'e0fbefd04b9203526e6f22b8', 1)

    assert result.special_scores['KILLING_SPREE'][2] == (
        64.9, 'd37928942982cc79e7e0fe12',
        '9ac5682eefa9134bbfe3c481', 1)

    assert result.player_stats == [
        {'player_id': '291b0ba5fdf78b268369a9d7', 'total_armor_pickup': 170, 'total_health_pickup': 330, 'damage_dealt': 3609, 'damage_taken': 4677},  # noqa
        {'player_id': '6a018beb6405ef59ce1471b0', 'total_armor_pickup': 630, 'total_health_pickup': 505, 'damage_dealt': 5161, 'damage_taken': 8688},  # noqa
        {'player_id': 'd37928942982cc79e7e0fe12', 'total_armor_pickup': 680, 'total_health_pickup': 1695, 'damage_dealt': 13193, 'damage_taken': 5924},  # noqa
        {'player_id': 'a126a35a25eab0623f504183', 'total_armor_pickup': 485, 'total_health_pickup': 1300, 'damage_dealt': 7173, 'damage_taken': 9244},  # noqa
        {'player_id': 'e0fbefd04b9203526e6f22b8', 'total_armor_pickup': 430, 'total_health_pickup': 520, 'damage_dealt': 8465, 'damage_taken': 6385},  # noqa
        {'player_id': '7ee3d47a164c6544ea50fee6', 'total_armor_pickup': 395, 'total_health_pickup': 420, 'damage_dealt': 7055, 'damage_taken': 7866},  # noqa
        {'player_id': '9ac5682eefa9134bbfe3c481', 'total_armor_pickup': 405, 'total_health_pickup': 270, 'damage_dealt': 8569, 'damage_taken': 7386},  # noqa
        {'player_id': '88fdc96e8804eaa084d740f8', 'total_armor_pickup': 725, 'total_health_pickup': 575, 'damage_dealt': 6562, 'damage_taken': 9617},  # noqa
    ]


def test_quake3_analyze_ktsdm3(q3_dump):
    feeder = quake3.Q3MatchFeeder()
    matches = []
    for line in q3_dump.splitlines():
        try:
            feeder.feed(line)
        except dataprovider.FeedFull:
            matches.append(feeder.consume())

    # ktsdm3
    match = matches[15]
    transformer = quake3.Q3toQL(match['EVENTS'])
    transformer.process()
    result = transformer.result
    preprocessor = dataprovider.MatchPreprocessor()

    preprocessor.process_events(result['events'])

    fmi = dataprovider.FullMatchInfo.from_preprocessor(
        preprocessor,
        transformer.result['start_date'],
        transformer.result['finish_date'],
        'serv-domain', 'Q3')

    analyzer = analyze.Analyzer()
    result = analyzer.analyze(fmi)

    assert result.match_metadata.duration == 900
    assert result.match_metadata.frag_limit == 200
    assert result.match_metadata.map_name == 'ktsdm3'
    assert result.match_metadata.match_guid
    assert result.match_metadata.server_domain == 'serv-domain'
    assert result.match_metadata.server_name == 'MY Q3'
    assert result.match_metadata.time_limit == 15

    assert result.final_scores['014b02cb82074fed03802651'][0] == 35
    assert result.final_scores['291b0ba5fdf78b268369a9d7'][0] == 77
    assert result.final_scores['6a018beb6405ef59ce1471b0'][0] == 33
    assert result.final_scores['6abd7638a2f6b427533ab1d8'][0] == 59
    assert result.final_scores['7ee3d47a164c6544ea50fee6'][0] == 41
    assert result.final_scores['88fdc96e8804eaa084d740f8'][0] == 44
    assert result.final_scores['a126a35a25eab0623f504183'][0] == 55
    assert result.final_scores['bebb93eb648c03edad5c12a9'][0] == 0
    assert result.final_scores['d37928942982cc79e7e0fe12'][0] == 74
    assert result.final_scores['e0fbefd04b9203526e6f22b8'][0] == 64
    assert result.final_scores['q3-world'][0] == 1

    assert result.players['014b02cb82074fed03802651'].name == 'Slawek' # noqa
    assert result.players['291b0ba5fdf78b268369a9d7'].name == 'Turbo Wpierdol'
    assert result.players['6a018beb6405ef59ce1471b0'].name == 'MACIEK'
    assert result.players['6abd7638a2f6b427533ab1d8'].name == 'sadziu'
    assert result.players['7ee3d47a164c6544ea50fee6'].name == 'n0npax'
    assert result.players['88fdc96e8804eaa084d740f8'].name == 'darkside'  # noqa
    assert result.players['a126a35a25eab0623f504183'].name == 'killer clown'
    assert result.players['d37928942982cc79e7e0fe12'].name == 'Bartoszer'
    assert result.players['e0fbefd04b9203526e6f22b8'].name == 'Stefan'

    assert result.player_stats == [
        {'player_id': 'a126a35a25eab0623f504183', 'total_armor_pickup': 225, 'total_health_pickup': 535, 'damage_dealt': 8838, 'damage_taken': 7659},  # noqa
        {'player_id': '014b02cb82074fed03802651', 'total_armor_pickup': 440, 'total_health_pickup': 245, 'damage_dealt': 6202, 'damage_taken': 10229},  # noqa
        {'player_id': 'd37928942982cc79e7e0fe12', 'total_armor_pickup': 335, 'total_health_pickup': 605, 'damage_dealt': 10992, 'damage_taken': 6602},  # noqa
        {'player_id': '88fdc96e8804eaa084d740f8', 'total_armor_pickup': 260, 'total_health_pickup': 415, 'damage_dealt': 6174, 'damage_taken': 8397},  # noqa
        {'player_id': '6abd7638a2f6b427533ab1d8', 'total_armor_pickup': 325, 'total_health_pickup': 255, 'damage_dealt': 7145, 'damage_taken': 7926},  # noqa
        {'player_id': '6a018beb6405ef59ce1471b0', 'total_armor_pickup': 260, 'total_health_pickup': 120, 'damage_dealt': 5801, 'damage_taken': 9063},  # noqa
        {'player_id': 'e0fbefd04b9203526e6f22b8', 'total_armor_pickup': 470, 'total_health_pickup': 255, 'damage_dealt': 10459, 'damage_taken': 8736},  # noqa
        {'player_id': '291b0ba5fdf78b268369a9d7', 'total_armor_pickup': 435, 'total_health_pickup': 285, 'damage_dealt': 10799, 'damage_taken': 6565},  # noqa
        {'player_id': '7ee3d47a164c6544ea50fee6', 'total_armor_pickup': 205, 'total_health_pickup': 385, 'damage_dealt': 7538, 'damage_taken': 8771},  # noqa
    ]

    assert result.special_scores['CONSECUTIVE_RAIL_KILL'] == (
        [
            (95.6, 'e0fbefd04b9203526e6f22b8', '88fdc96e8804eaa084d740f8', 1),
            (97.8, 'e0fbefd04b9203526e6f22b8', '7ee3d47a164c6544ea50fee6', 1),
            (97.8, 'e0fbefd04b9203526e6f22b8', '014b02cb82074fed03802651', 1),
            (122.5, 'a126a35a25eab0623f504183', '014b02cb82074fed03802651', 1),
            (466.7, 'd37928942982cc79e7e0fe12', '7ee3d47a164c6544ea50fee6', 1),
            (466.7, 'd37928942982cc79e7e0fe12', 'a126a35a25eab0623f504183', 1),
            (523.0, '291b0ba5fdf78b268369a9d7', '6a018beb6405ef59ce1471b0', 1),
            (604.5, 'd37928942982cc79e7e0fe12', 'e0fbefd04b9203526e6f22b8', 1),
            (682.2, 'd37928942982cc79e7e0fe12', '6a018beb6405ef59ce1471b0', 1),
            (721.1, 'e0fbefd04b9203526e6f22b8', 'a126a35a25eab0623f504183', 1),
            (866.1, 'd37928942982cc79e7e0fe12', 'e0fbefd04b9203526e6f22b8', 1)
        ]
    )

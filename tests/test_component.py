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


def _regen_stats_asserts(result):
    """
    Helper function to build asserts for player summary
    """
    for idx, entry in enumerate(result.player_stats):
        accessor = "e[{}]".format(idx)
        for attr in sorted(entry):
            val = entry[attr]
            if isinstance(val, str):
                assert_val = "'{}'".format(val)
            else:
                assert_val = val
            print(
                'assert {}["{}"] == {}  # noqa'
                .format(accessor, attr, assert_val)
                )


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

    e = result.player_stats
    # Use _regen_stats_asserts(result) to regenerate
    assert e[0]["damage_dealt"] == 3609  # noqa
    assert e[0]["damage_taken"] == 4677  # noqa
    assert e[0]["player_id"] == '291b0ba5fdf78b268369a9d7'  # noqa
    assert e[0]["total_armor_pickup"] == 170  # noqa
    assert e[0]["total_health_pickup"] == 330  # noqa
    assert e[0]["weapons"] == {'MACHINEGUN': {'S': 1105, 'H': 254, 'K': None, 'D': None}, 'SHOTGUN': {'S': 154, 'H': 29, 'K': None, 'D': None}, 'GRENADE': {'S': 9, 'H': 2, 'K': None, 'D': None}, 'ROCKET': {'S': 55, 'H': 25, 'K': None, 'D': None}, 'LIGHTNING': {'S': 198, 'H': 26, 'K': None, 'D': None}}  # noqa
    assert e[1]["damage_dealt"] == 5161  # noqa
    assert e[1]["damage_taken"] == 8688  # noqa
    assert e[1]["player_id"] == '6a018beb6405ef59ce1471b0'  # noqa
    assert e[1]["total_armor_pickup"] == 630  # noqa
    assert e[1]["total_health_pickup"] == 505  # noqa
    assert e[1]["weapons"] == {'GAUNTLET': {'S': 0, 'H': 10, 'K': None, 'D': None}, 'MACHINEGUN': {'S': 1221, 'H': 207, 'K': None, 'D': None}, 'SHOTGUN': {'S': 418, 'H': 59, 'K': None, 'D': None}, 'GRENADE': {'S': 14, 'H': 2, 'K': None, 'D': None}, 'ROCKET': {'S': 71, 'H': 26, 'K': None, 'D': None}, 'LIGHTNING': {'S': 474, 'H': 110, 'K': None, 'D': None}}  # noqa
    assert e[2]["damage_dealt"] == 13193  # noqa
    assert e[2]["damage_taken"] == 5924  # noqa
    assert e[2]["player_id"] == 'd37928942982cc79e7e0fe12'  # noqa
    assert e[2]["total_armor_pickup"] == 680  # noqa
    assert e[2]["total_health_pickup"] == 1695  # noqa
    assert e[2]["weapons"] == {'GAUNTLET': {'S': 0, 'H': 26, 'K': None, 'D': None}, 'MACHINEGUN': {'S': 146, 'H': 26, 'K': None, 'D': None}, 'SHOTGUN': {'S': 517, 'H': 137, 'K': None, 'D': None}, 'GRENADE': {'S': 78, 'H': 23, 'K': None, 'D': None}, 'ROCKET': {'S': 190, 'H': 96, 'K': None, 'D': None}, 'LIGHTNING': {'S': 833, 'H': 231, 'K': None, 'D': None}}  # noqa
    assert e[3]["damage_dealt"] == 7173  # noqa
    assert e[3]["damage_taken"] == 9244  # noqa
    assert e[3]["player_id"] == 'a126a35a25eab0623f504183'  # noqa
    assert e[3]["total_armor_pickup"] == 485  # noqa
    assert e[3]["total_health_pickup"] == 1300  # noqa
    assert e[3]["weapons"] == {'MACHINEGUN': {'S': 1230, 'H': 311, 'K': None, 'D': None}, 'SHOTGUN': {'S': 682, 'H': 134, 'K': None, 'D': None}, 'GRENADE': {'S': 0, 'H': 0, 'K': None, 'D': None}, 'ROCKET': {'S': 127, 'H': 48, 'K': None, 'D': None}, 'LIGHTNING': {'S': 444, 'H': 85, 'K': None, 'D': None}}  # noqa
    assert e[4]["damage_dealt"] == 8465  # noqa
    assert e[4]["damage_taken"] == 6385  # noqa
    assert e[4]["player_id"] == 'e0fbefd04b9203526e6f22b8'  # noqa
    assert e[4]["total_armor_pickup"] == 430  # noqa
    assert e[4]["total_health_pickup"] == 520  # noqa
    assert e[4]["weapons"] == {'GAUNTLET': {'S': 0, 'H': 7, 'K': None, 'D': None}, 'MACHINEGUN': {'S': 591, 'H': 160, 'K': None, 'D': None}, 'SHOTGUN': {'S': 473, 'H': 51, 'K': None, 'D': None}, 'GRENADE': {'S': 181, 'H': 41, 'K': None, 'D': None}, 'ROCKET': {'S': 97, 'H': 49, 'K': None, 'D': None}, 'LIGHTNING': {'S': 525, 'H': 115, 'K': None, 'D': None}}  # noqa
    assert e[5]["damage_dealt"] == 7055  # noqa
    assert e[5]["damage_taken"] == 7866  # noqa
    assert e[5]["player_id"] == '7ee3d47a164c6544ea50fee6'  # noqa
    assert e[5]["total_armor_pickup"] == 395  # noqa
    assert e[5]["total_health_pickup"] == 420  # noqa
    assert e[5]["weapons"] == {'MACHINEGUN': {'S': 1314, 'H': 341, 'K': None, 'D': None}, 'SHOTGUN': {'S': 319, 'H': 64, 'K': None, 'D': None}, 'GRENADE': {'S': 38, 'H': 12, 'K': None, 'D': None}, 'ROCKET': {'S': 100, 'H': 43, 'K': None, 'D': None}, 'LIGHTNING': {'S': 398, 'H': 82, 'K': None, 'D': None}}  # noqa
    assert e[6]["damage_dealt"] == 8569  # noqa
    assert e[6]["damage_taken"] == 7386  # noqa
    assert e[6]["player_id"] == '9ac5682eefa9134bbfe3c481'  # noqa
    assert e[6]["total_armor_pickup"] == 405  # noqa
    assert e[6]["total_health_pickup"] == 270  # noqa
    assert e[6]["weapons"] == {'MACHINEGUN': {'S': 1093, 'H': 248, 'K': None, 'D': None}, 'SHOTGUN': {'S': 473, 'H': 83, 'K': None, 'D': None}, 'GRENADE': {'S': 16, 'H': 3, 'K': None, 'D': None}, 'ROCKET': {'S': 179, 'H': 63, 'K': None, 'D': None}, 'LIGHTNING': {'S': 967, 'H': 152, 'K': None, 'D': None}}  # noqa
    assert e[7]["damage_dealt"] == 6562  # noqa
    assert e[7]["damage_taken"] == 9617  # noqa
    assert e[7]["player_id"] == '88fdc96e8804eaa084d740f8'  # noqa
    assert e[7]["total_armor_pickup"] == 725  # noqa
    assert e[7]["total_health_pickup"] == 575  # noqa
    assert e[7]["weapons"] == {'MACHINEGUN': {'S': 1985, 'H': 372, 'K': None, 'D': None}, 'SHOTGUN': {'S': 319, 'H': 70, 'K': None, 'D': None}, 'GRENADE': {'S': 5, 'H': 2, 'K': None, 'D': None}, 'ROCKET': {'S': 55, 'H': 20, 'K': None, 'D': None}, 'LIGHTNING': {'S': 520, 'H': 97, 'K': None, 'D': None}}  # noqa


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
  
    e = result.player_stats
    # Use _regen_stats_asserts(result) to regenerate
    assert e[0]["damage_dealt"] == 8838  # noqa
    assert e[0]["damage_taken"] == 7659  # noqa
    assert e[0]["player_id"] == 'a126a35a25eab0623f504183'  # noqa
    assert e[0]["total_armor_pickup"] == 225  # noqa
    assert e[0]["total_health_pickup"] == 535  # noqa
    assert e[0]["weapons"] == {'GAUNTLET': {'S': 0, 'H': 1, 'K': None, 'D': None}, 'MACHINEGUN': {'S': 1491, 'H': 367, 'K': None, 'D': None}, 'SHOTGUN': {'S': 858, 'H': 202, 'K': None, 'D': None}, 'GRENADE': {'S': 77, 'H': 14, 'K': None, 'D': None}, 'ROCKET': {'S': 42, 'H': 20, 'K': None, 'D': None}, 'LIGHTNING': {'S': 583, 'H': 130, 'K': None, 'D': None}, 'RAILGUN': {'S': 13, 'H': 7, 'K': None, 'D': None}, 'PLASMA': {'S': 85, 'H': 20, 'K': None, 'D': None}}  # noqa
    assert e[1]["damage_dealt"] == 6202  # noqa
    assert e[1]["damage_taken"] == 10229  # noqa
    assert e[1]["player_id"] == '014b02cb82074fed03802651'  # noqa
    assert e[1]["total_armor_pickup"] == 440  # noqa
    assert e[1]["total_health_pickup"] == 245  # noqa
    assert e[1]["weapons"] == {'MACHINEGUN': {'S': 1908, 'H': 418, 'K': None, 'D': None}, 'SHOTGUN': {'S': 473, 'H': 93, 'K': None, 'D': None}, 'GRENADE': {'S': 61, 'H': 12, 'K': None, 'D': None}, 'ROCKET': {'S': 15, 'H': 4, 'K': None, 'D': None}, 'LIGHTNING': {'S': 792, 'H': 154, 'K': None, 'D': None}, 'RAILGUN': {'S': 2, 'H': 0, 'K': None, 'D': None}, 'PLASMA': {'S': 60, 'H': 10, 'K': None, 'D': None}}  # noqa
    assert e[2]["damage_dealt"] == 10992  # noqa
    assert e[2]["damage_taken"] == 6602  # noqa
    assert e[2]["player_id"] == 'd37928942982cc79e7e0fe12'  # noqa
    assert e[2]["total_armor_pickup"] == 335  # noqa
    assert e[2]["total_health_pickup"] == 605  # noqa
    assert e[2]["weapons"] == {'GAUNTLET': {'S': 0, 'H': 14, 'K': None, 'D': None}, 'MACHINEGUN': {'S': 590, 'H': 147, 'K': None, 'D': None}, 'SHOTGUN': {'S': 517, 'H': 142, 'K': None, 'D': None}, 'GRENADE': {'S': 75, 'H': 23, 'K': None, 'D': None}, 'ROCKET': {'S': 39, 'H': 24, 'K': None, 'D': None}, 'LIGHTNING': {'S': 1019, 'H': 304, 'K': None, 'D': None}, 'RAILGUN': {'S': 50, 'H': 22, 'K': None, 'D': None}, 'PLASMA': {'S': 147, 'H': 37, 'K': None, 'D': None}}  # noqa
    assert e[3]["damage_dealt"] == 6174  # noqa
    assert e[3]["damage_taken"] == 8397  # noqa
    assert e[3]["player_id"] == '88fdc96e8804eaa084d740f8'  # noqa
    assert e[3]["total_armor_pickup"] == 260  # noqa
    assert e[3]["total_health_pickup"] == 415  # noqa
    assert e[3]["weapons"] == {'GAUNTLET': {'S': 0, 'H': 1, 'K': None, 'D': None}, 'MACHINEGUN': {'S': 2238, 'H': 424, 'K': None, 'D': None}, 'SHOTGUN': {'S': 572, 'H': 115, 'K': None, 'D': None}, 'GRENADE': {'S': 10, 'H': 5, 'K': None, 'D': None}, 'ROCKET': {'S': 12, 'H': 4, 'K': None, 'D': None}, 'LIGHTNING': {'S': 779, 'H': 131, 'K': None, 'D': None}, 'RAILGUN': {'S': 3, 'H': 0, 'K': None, 'D': None}, 'PLASMA': {'S': 136, 'H': 23, 'K': None, 'D': None}}  # noqa
    assert e[4]["damage_dealt"] == 7145  # noqa
    assert e[4]["damage_taken"] == 7926  # noqa
    assert e[4]["player_id"] == '6abd7638a2f6b427533ab1d8'  # noqa
    assert e[4]["total_armor_pickup"] == 325  # noqa
    assert e[4]["total_health_pickup"] == 255  # noqa
    assert e[4]["weapons"] == {'GAUNTLET': {'S': 0, 'H': 18, 'K': None, 'D': None}, 'MACHINEGUN': {'S': 1113, 'H': 190, 'K': None, 'D': None}, 'SHOTGUN': {'S': 913, 'H': 156, 'K': None, 'D': None}, 'GRENADE': {'S': 61, 'H': 20, 'K': None, 'D': None}, 'ROCKET': {'S': 49, 'H': 15, 'K': None, 'D': None}, 'LIGHTNING': {'S': 401, 'H': 84, 'K': None, 'D': None}, 'RAILGUN': {'S': 8, 'H': 1, 'K': None, 'D': None}, 'PLASMA': {'S': 138, 'H': 21, 'K': None, 'D': None}}  # noqa
    assert e[5]["damage_dealt"] == 5801  # noqa
    assert e[5]["damage_taken"] == 9063  # noqa
    assert e[5]["player_id"] == '6a018beb6405ef59ce1471b0'  # noqa
    assert e[5]["total_armor_pickup"] == 260  # noqa
    assert e[5]["total_health_pickup"] == 120  # noqa
    assert e[5]["weapons"] == {'GAUNTLET': {'S': 0, 'H': 16, 'K': None, 'D': None}, 'MACHINEGUN': {'S': 1803, 'H': 297, 'K': None, 'D': None}, 'SHOTGUN': {'S': 528, 'H': 58, 'K': None, 'D': None}, 'GRENADE': {'S': 77, 'H': 20, 'K': None, 'D': None}, 'ROCKET': {'S': 52, 'H': 17, 'K': None, 'D': None}, 'LIGHTNING': {'S': 188, 'H': 36, 'K': None, 'D': None}, 'RAILGUN': {'S': 21, 'H': 5, 'K': None, 'D': None}}  # noqa
    assert e[6]["damage_dealt"] == 10459  # noqa
    assert e[6]["damage_taken"] == 8736  # noqa
    assert e[6]["player_id"] == 'e0fbefd04b9203526e6f22b8'  # noqa
    assert e[6]["total_armor_pickup"] == 470  # noqa
    assert e[6]["total_health_pickup"] == 255  # noqa
    assert e[6]["weapons"] == {'GAUNTLET': {'S': 0, 'H': 6, 'K': None, 'D': None}, 'MACHINEGUN': {'S': 655, 'H': 190, 'K': None, 'D': None}, 'SHOTGUN': {'S': 528, 'H': 110, 'K': None, 'D': None}, 'GRENADE': {'S': 73, 'H': 32, 'K': None, 'D': None}, 'ROCKET': {'S': 46, 'H': 20, 'K': None, 'D': None}, 'LIGHTNING': {'S': 631, 'H': 160, 'K': None, 'D': None}, 'RAILGUN': {'S': 61, 'H': 30, 'K': None, 'D': None}, 'PLASMA': {'S': 24, 'H': 8, 'K': None, 'D': None}}  # noqa
    assert e[7]["damage_dealt"] == 10799  # noqa
    assert e[7]["damage_taken"] == 6565  # noqa
    assert e[7]["player_id"] == '291b0ba5fdf78b268369a9d7'  # noqa
    assert e[7]["total_armor_pickup"] == 435  # noqa
    assert e[7]["total_health_pickup"] == 285  # noqa
    assert e[7]["weapons"] == {'MACHINEGUN': {'S': 1455, 'H': 369, 'K': None, 'D': None}, 'SHOTGUN': {'S': 440, 'H': 106, 'K': None, 'D': None}, 'GRENADE': {'S': 110, 'H': 35, 'K': None, 'D': None}, 'ROCKET': {'S': 61, 'H': 26, 'K': None, 'D': None}, 'LIGHTNING': {'S': 703, 'H': 148, 'K': None, 'D': None}, 'RAILGUN': {'S': 39, 'H': 14, 'K': None, 'D': None}, 'PLASMA': {'S': 93, 'H': 26, 'K': None, 'D': None}}  # noqa
    assert e[8]["damage_dealt"] == 7538  # noqa
    assert e[8]["damage_taken"] == 8771  # noqa
    assert e[8]["player_id"] == '7ee3d47a164c6544ea50fee6'  # noqa
    assert e[8]["total_armor_pickup"] == 205  # noqa
    assert e[8]["total_health_pickup"] == 385  # noqa
    assert e[8]["weapons"] == {'GAUNTLET': {'S': 0, 'H': 4, 'K': None, 'D': None}, 'MACHINEGUN': {'S': 1746, 'H': 437, 'K': None, 'D': None}, 'SHOTGUN': {'S': 297, 'H': 60, 'K': None, 'D': None}, 'GRENADE': {'S': 123, 'H': 36, 'K': None, 'D': None}, 'ROCKET': {'S': 46, 'H': 12, 'K': None, 'D': None}, 'LIGHTNING': {'S': 242, 'H': 46, 'K': None, 'D': None}, 'RAILGUN': {'S': 21, 'H': 5, 'K': None, 'D': None}, 'PLASMA': {'S': 12, 'H': 0, 'K': None, 'D': None}}  # noqa

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

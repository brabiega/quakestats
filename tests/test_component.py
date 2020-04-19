import json
import os

import pytest

from quakestats import (
    dataprovider,
)
from quakestats.core.q3toql import parse as q3parse
from quakestats.dataprovider import (
    analyze,
    quakelive,
)

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


def test_quake3_analyze_nodm9(q3_dump):
    matches = list(q3parse.read_games(q3_dump, 'osp'))

    # nodm9
    game, game_log = matches[-1]

    fmi = dataprovider.FullMatchInfo(
        events=game.get_events(),
        match_guid=game.game_guid,
        duration=game.metadata.duration,
        start_date=game.metadata.start_date,
        finish_date=game.metadata.finish_date,
        server_domain="serv-domain",
        source=game.source,
    )

    analyzer = analyze.Analyzer()
    result = analyzer.analyze(fmi)

    assert result.match_metadata.duration == 900
    assert result.match_metadata.frag_limit == 200
    assert result.match_metadata.map_name == 'nodm9'
    assert result.match_metadata.match_guid
    assert result.match_metadata.server_domain == 'serv-domain'
    assert result.match_metadata.server_name == 'MY Q3'
    assert result.match_metadata.time_limit == 15

    assert result.final_scores['2f7d40fff23683c6ab15b2ba'][0] == 0
    assert result.final_scores['773fa00f3f3a7e960b561492'][0] == 27
    assert result.final_scores['3086e90f19e4d4d30a6ece78'][0] == 37
    assert result.final_scores['cc6b3555fc360da8aec21f60'][0] == 33
    assert result.final_scores['a8f9128a42e1e6a4168f26fc'][0] == 42
    assert result.final_scores['761d1593e6faf9c12eaba9d4'][0] == 41
    assert result.final_scores['6179638dba55b8f5d2da7838'][0] == 85
    assert result.final_scores['14e3d92ed5055145aab6e920'][0] == 45
    assert result.final_scores['q3-world'][0] == 16

    assert len(result.team_switches) == 10
    assert result.team_switches[-1] == (697.3, '2f7d40fff23683c6ab15b2ba', None, 'DISCONNECTED')  # noqa

    assert result.players['2f7d40fff23683c6ab15b2ba'].name == 'Turbo Wpierdol' # noqa
    assert result.players['773fa00f3f3a7e960b561492'].name == 'MACIEK'
    assert result.players['3086e90f19e4d4d30a6ece78'].name == 'n0npax'
    assert result.players['cc6b3555fc360da8aec21f60'].name == 'darkside'
    assert result.players['a8f9128a42e1e6a4168f26fc'].name == 'BOLEK'
    assert result.players['761d1593e6faf9c12eaba9d4'].name == 'killer clown'  # noqa
    assert result.players['6179638dba55b8f5d2da7838'].name == 'Bartoszer'
    assert result.players['14e3d92ed5055145aab6e920'].name == 'Stefan'

    assert result.kills[-1] == (897.1, '6179638dba55b8f5d2da7838', '6179638dba55b8f5d2da7838', 'ROCKET_SPLASH')  # noqa

    assert result.server_info.server_name == 'MY Q3'
    assert result.server_info.server_domain == 'serv-domain'
    assert result.server_info.server_type == 'Q3'

    assert result.special_scores['GAUNTLET_KILL'][3] == (
        150.4, '6179638dba55b8f5d2da7838',
        '14e3d92ed5055145aab6e920', 1)

    assert result.special_scores['KILLING_SPREE'][2] == (
        64.9, '6179638dba55b8f5d2da7838',
        'a8f9128a42e1e6a4168f26fc', 1)

    e = result.player_stats
    # _regen_stats_asserts(result)  # to regenerate
    assert e[0]["damage_dealt"] == 3609  # noqa
    assert e[0]["damage_taken"] == 4677  # noqa
    assert e[0]["player_id"] == '2f7d40fff23683c6ab15b2ba'  # noqa
    assert e[0]["total_armor_pickup"] == 170  # noqa
    assert e[0]["total_health_pickup"] == 330  # noqa
    assert e[0]["weapons"] == {'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 254, 'D': None, 'DG': None, 'T': None, 'S': 1105}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 29, 'D': None, 'DG': None, 'T': None, 'S': 154}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 2, 'D': None, 'DG': None, 'T': None, 'S': 9}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 25, 'D': None, 'DG': None, 'T': None, 'S': 55}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 26, 'D': None, 'DG': None, 'T': None, 'S': 198}}  # noqa
    assert e[1]["damage_dealt"] == 5161  # noqa
    assert e[1]["damage_taken"] == 8688  # noqa
    assert e[1]["player_id"] == '773fa00f3f3a7e960b561492'  # noqa
    assert e[1]["total_armor_pickup"] == 630  # noqa
    assert e[1]["total_health_pickup"] == 505  # noqa
    assert e[1]["weapons"] == {'GAUNTLET': {'K': None, 'P': None, 'DR': None, 'H': 10, 'D': None, 'DG': None, 'T': None, 'S': 0}, 'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 207, 'D': None, 'DG': None, 'T': None, 'S': 1221}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 59, 'D': None, 'DG': None, 'T': None, 'S': 418}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 2, 'D': None, 'DG': None, 'T': None, 'S': 14}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 26, 'D': None, 'DG': None, 'T': None, 'S': 71}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 110, 'D': None, 'DG': None, 'T': None, 'S': 474}}  # noqa
    assert e[2]["damage_dealt"] == 13193  # noqa
    assert e[2]["damage_taken"] == 5924  # noqa
    assert e[2]["player_id"] == '6179638dba55b8f5d2da7838'  # noqa
    assert e[2]["total_armor_pickup"] == 680  # noqa
    assert e[2]["total_health_pickup"] == 1695  # noqa
    assert e[2]["weapons"] == {'GAUNTLET': {'K': None, 'P': None, 'DR': None, 'H': 26, 'D': None, 'DG': None, 'T': None, 'S': 0}, 'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 26, 'D': None, 'DG': None, 'T': None, 'S': 146}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 137, 'D': None, 'DG': None, 'T': None, 'S': 517}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 23, 'D': None, 'DG': None, 'T': None, 'S': 78}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 96, 'D': None, 'DG': None, 'T': None, 'S': 190}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 231, 'D': None, 'DG': None, 'T': None, 'S': 833}}  # noqa
    assert e[3]["damage_dealt"] == 7173  # noqa
    assert e[3]["damage_taken"] == 9244  # noqa
    assert e[3]["player_id"] == '761d1593e6faf9c12eaba9d4'  # noqa
    assert e[3]["total_armor_pickup"] == 485  # noqa
    assert e[3]["total_health_pickup"] == 1300  # noqa
    assert e[3]["weapons"] == {'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 311, 'D': None, 'DG': None, 'T': None, 'S': 1230}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 134, 'D': None, 'DG': None, 'T': None, 'S': 682}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 0, 'D': None, 'DG': None, 'T': None, 'S': 0}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 48, 'D': None, 'DG': None, 'T': None, 'S': 127}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 85, 'D': None, 'DG': None, 'T': None, 'S': 444}}  # noqa
    assert e[4]["damage_dealt"] == 8465  # noqa
    assert e[4]["damage_taken"] == 6385  # noqa
    assert e[4]["player_id"] == '14e3d92ed5055145aab6e920'  # noqa
    assert e[4]["total_armor_pickup"] == 430  # noqa
    assert e[4]["total_health_pickup"] == 520  # noqa
    assert e[4]["weapons"] == {'GAUNTLET': {'K': None, 'P': None, 'DR': None, 'H': 7, 'D': None, 'DG': None, 'T': None, 'S': 0}, 'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 160, 'D': None, 'DG': None, 'T': None, 'S': 591}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 51, 'D': None, 'DG': None, 'T': None, 'S': 473}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 41, 'D': None, 'DG': None, 'T': None, 'S': 181}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 49, 'D': None, 'DG': None, 'T': None, 'S': 97}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 115, 'D': None, 'DG': None, 'T': None, 'S': 525}}  # noqa
    assert e[5]["damage_dealt"] == 7055  # noqa
    assert e[5]["damage_taken"] == 7866  # noqa
    assert e[5]["player_id"] == '3086e90f19e4d4d30a6ece78'  # noqa
    assert e[5]["total_armor_pickup"] == 395  # noqa
    assert e[5]["total_health_pickup"] == 420  # noqa
    assert e[5]["weapons"] == {'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 341, 'D': None, 'DG': None, 'T': None, 'S': 1314}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 64, 'D': None, 'DG': None, 'T': None, 'S': 319}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 12, 'D': None, 'DG': None, 'T': None, 'S': 38}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 43, 'D': None, 'DG': None, 'T': None, 'S': 100}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 82, 'D': None, 'DG': None, 'T': None, 'S': 398}}  # noqa
    assert e[6]["damage_dealt"] == 8569  # noqa
    assert e[6]["damage_taken"] == 7386  # noqa
    assert e[6]["player_id"] == 'a8f9128a42e1e6a4168f26fc'  # noqa
    assert e[6]["total_armor_pickup"] == 405  # noqa
    assert e[6]["total_health_pickup"] == 270  # noqa
    assert e[6]["weapons"] == {'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 248, 'D': None, 'DG': None, 'T': None, 'S': 1093}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 83, 'D': None, 'DG': None, 'T': None, 'S': 473}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 3, 'D': None, 'DG': None, 'T': None, 'S': 16}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 63, 'D': None, 'DG': None, 'T': None, 'S': 179}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 152, 'D': None, 'DG': None, 'T': None, 'S': 967}}  # noqa
    assert e[7]["damage_dealt"] == 6562  # noqa
    assert e[7]["damage_taken"] == 9617  # noqa
    assert e[7]["player_id"] == 'cc6b3555fc360da8aec21f60'  # noqa
    assert e[7]["total_armor_pickup"] == 725  # noqa
    assert e[7]["total_health_pickup"] == 575  # noqa
    assert e[7]["weapons"] == {'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 372, 'D': None, 'DG': None, 'T': None, 'S': 1985}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 70, 'D': None, 'DG': None, 'T': None, 'S': 319}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 2, 'D': None, 'DG': None, 'T': None, 'S': 5}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 20, 'D': None, 'DG': None, 'T': None, 'S': 55}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 97, 'D': None, 'DG': None, 'T': None, 'S': 520}}  # noqa


def test_quake3_analyze_ktsdm3(q3_dump):
    matches = list(q3parse.read_games(q3_dump, 'osp'))
    # ktsdm3
    game, game_log = matches[15]

    fmi = dataprovider.FullMatchInfo(
        events=game.get_events(),
        match_guid=game.game_guid,
        duration=game.metadata.duration,
        start_date=game.metadata.start_date,
        finish_date=game.metadata.finish_date,
        server_domain="serv-domain",
        source=game.source,
    )

    analyzer = analyze.Analyzer()
    result = analyzer.analyze(fmi)

    assert result.match_metadata.duration == 900
    assert result.match_metadata.frag_limit == 200
    assert result.match_metadata.map_name == 'ktsdm3'
    assert result.match_metadata.match_guid
    assert result.match_metadata.server_domain == 'serv-domain'
    assert result.match_metadata.server_name == 'MY Q3'
    assert result.match_metadata.time_limit == 15

    assert result.final_scores['8fff33431b55a197b4de8bd0'][0] == 35
    assert result.final_scores['2f7d40fff23683c6ab15b2ba'][0] == 77
    assert result.final_scores['773fa00f3f3a7e960b561492'][0] == 33
    assert result.final_scores['e77d225d36c1db87574948f5'][0] == 59
    assert result.final_scores['3086e90f19e4d4d30a6ece78'][0] == 41
    assert result.final_scores['cc6b3555fc360da8aec21f60'][0] == 44
    assert result.final_scores['761d1593e6faf9c12eaba9d4'][0] == 55
    assert result.final_scores['014b02cb82074fed03802651'][0] == 0
    assert result.final_scores['6179638dba55b8f5d2da7838'][0] == 74
    assert result.final_scores['14e3d92ed5055145aab6e920'][0] == 64
    assert result.final_scores['q3-world'][0] == 1

    assert result.players['8fff33431b55a197b4de8bd0'].name == 'Slawek' # noqa
    assert result.players['2f7d40fff23683c6ab15b2ba'].name == 'Turbo Wpierdol'
    assert result.players['773fa00f3f3a7e960b561492'].name == 'MACIEK'
    assert result.players['e77d225d36c1db87574948f5'].name == 'sadziu'
    assert result.players['3086e90f19e4d4d30a6ece78'].name == 'n0npax'
    assert result.players['cc6b3555fc360da8aec21f60'].name == 'darkside'  # noqa
    assert result.players['761d1593e6faf9c12eaba9d4'].name == 'killer clown'
    assert result.players['6179638dba55b8f5d2da7838'].name == 'Bartoszer'
    assert result.players['14e3d92ed5055145aab6e920'].name == 'Stefan'

    e = result.player_stats
    # _regen_stats_asserts(result)  # to regenerate
    assert e[0]["damage_dealt"] == 8838  # noqa
    assert e[0]["damage_taken"] == 7659  # noqa
    assert e[0]["player_id"] == '761d1593e6faf9c12eaba9d4'  # noqa
    assert e[0]["total_armor_pickup"] == 225  # noqa
    assert e[0]["total_health_pickup"] == 535  # noqa
    assert e[0]["weapons"] == {'GAUNTLET': {'K': None, 'P': None, 'DR': None, 'H': 1, 'D': None, 'DG': None, 'T': None, 'S': 0}, 'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 367, 'D': None, 'DG': None, 'T': None, 'S': 1491}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 202, 'D': None, 'DG': None, 'T': None, 'S': 858}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 14, 'D': None, 'DG': None, 'T': None, 'S': 77}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 20, 'D': None, 'DG': None, 'T': None, 'S': 42}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 130, 'D': None, 'DG': None, 'T': None, 'S': 583}, 'RAILGUN': {'K': None, 'P': None, 'DR': None, 'H': 7, 'D': None, 'DG': None, 'T': None, 'S': 13}, 'PLASMA': {'K': None, 'P': None, 'DR': None, 'H': 20, 'D': None, 'DG': None, 'T': None, 'S': 85}}  # noqa
    assert e[1]["damage_dealt"] == 6202  # noqa
    assert e[1]["damage_taken"] == 10229  # noqa
    assert e[1]["player_id"] == '8fff33431b55a197b4de8bd0'  # noqa
    assert e[1]["total_armor_pickup"] == 440  # noqa
    assert e[1]["total_health_pickup"] == 245  # noqa
    assert e[1]["weapons"] == {'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 418, 'D': None, 'DG': None, 'T': None, 'S': 1908}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 93, 'D': None, 'DG': None, 'T': None, 'S': 473}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 12, 'D': None, 'DG': None, 'T': None, 'S': 61}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 4, 'D': None, 'DG': None, 'T': None, 'S': 15}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 154, 'D': None, 'DG': None, 'T': None, 'S': 792}, 'RAILGUN': {'K': None, 'P': None, 'DR': None, 'H': 0, 'D': None, 'DG': None, 'T': None, 'S': 2}, 'PLASMA': {'K': None, 'P': None, 'DR': None, 'H': 10, 'D': None, 'DG': None, 'T': None, 'S': 60}}  # noqa
    assert e[2]["damage_dealt"] == 10992  # noqa
    assert e[2]["damage_taken"] == 6602  # noqa
    assert e[2]["player_id"] == '6179638dba55b8f5d2da7838'  # noqa
    assert e[2]["total_armor_pickup"] == 335  # noqa
    assert e[2]["total_health_pickup"] == 605  # noqa
    assert e[2]["weapons"] == {'GAUNTLET': {'K': None, 'P': None, 'DR': None, 'H': 14, 'D': None, 'DG': None, 'T': None, 'S': 0}, 'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 147, 'D': None, 'DG': None, 'T': None, 'S': 590}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 142, 'D': None, 'DG': None, 'T': None, 'S': 517}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 23, 'D': None, 'DG': None, 'T': None, 'S': 75}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 24, 'D': None, 'DG': None, 'T': None, 'S': 39}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 304, 'D': None, 'DG': None, 'T': None, 'S': 1019}, 'RAILGUN': {'K': None, 'P': None, 'DR': None, 'H': 22, 'D': None, 'DG': None, 'T': None, 'S': 50}, 'PLASMA': {'K': None, 'P': None, 'DR': None, 'H': 37, 'D': None, 'DG': None, 'T': None, 'S': 147}}  # noqa
    assert e[3]["damage_dealt"] == 6174  # noqa
    assert e[3]["damage_taken"] == 8397  # noqa
    assert e[3]["player_id"] == 'cc6b3555fc360da8aec21f60'  # noqa
    assert e[3]["total_armor_pickup"] == 260  # noqa
    assert e[3]["total_health_pickup"] == 415  # noqa
    assert e[3]["weapons"] == {'GAUNTLET': {'K': None, 'P': None, 'DR': None, 'H': 1, 'D': None, 'DG': None, 'T': None, 'S': 0}, 'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 424, 'D': None, 'DG': None, 'T': None, 'S': 2238}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 115, 'D': None, 'DG': None, 'T': None, 'S': 572}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 5, 'D': None, 'DG': None, 'T': None, 'S': 10}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 4, 'D': None, 'DG': None, 'T': None, 'S': 12}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 131, 'D': None, 'DG': None, 'T': None, 'S': 779}, 'RAILGUN': {'K': None, 'P': None, 'DR': None, 'H': 0, 'D': None, 'DG': None, 'T': None, 'S': 3}, 'PLASMA': {'K': None, 'P': None, 'DR': None, 'H': 23, 'D': None, 'DG': None, 'T': None, 'S': 136}}  # noqa
    assert e[4]["damage_dealt"] == 7145  # noqa
    assert e[4]["damage_taken"] == 7926  # noqa
    assert e[4]["player_id"] == 'e77d225d36c1db87574948f5'  # noqa
    assert e[4]["total_armor_pickup"] == 325  # noqa
    assert e[4]["total_health_pickup"] == 255  # noqa
    assert e[4]["weapons"] == {'GAUNTLET': {'K': None, 'P': None, 'DR': None, 'H': 18, 'D': None, 'DG': None, 'T': None, 'S': 0}, 'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 190, 'D': None, 'DG': None, 'T': None, 'S': 1113}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 156, 'D': None, 'DG': None, 'T': None, 'S': 913}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 20, 'D': None, 'DG': None, 'T': None, 'S': 61}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 15, 'D': None, 'DG': None, 'T': None, 'S': 49}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 84, 'D': None, 'DG': None, 'T': None, 'S': 401}, 'RAILGUN': {'K': None, 'P': None, 'DR': None, 'H': 1, 'D': None, 'DG': None, 'T': None, 'S': 8}, 'PLASMA': {'K': None, 'P': None, 'DR': None, 'H': 21, 'D': None, 'DG': None, 'T': None, 'S': 138}}  # noqa
    assert e[5]["damage_dealt"] == 5801  # noqa
    assert e[5]["damage_taken"] == 9063  # noqa
    assert e[5]["player_id"] == '773fa00f3f3a7e960b561492'  # noqa
    assert e[5]["total_armor_pickup"] == 260  # noqa
    assert e[5]["total_health_pickup"] == 120  # noqa
    assert e[5]["weapons"] == {'GAUNTLET': {'K': None, 'P': None, 'DR': None, 'H': 16, 'D': None, 'DG': None, 'T': None, 'S': 0}, 'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 297, 'D': None, 'DG': None, 'T': None, 'S': 1803}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 58, 'D': None, 'DG': None, 'T': None, 'S': 528}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 20, 'D': None, 'DG': None, 'T': None, 'S': 77}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 17, 'D': None, 'DG': None, 'T': None, 'S': 52}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 36, 'D': None, 'DG': None, 'T': None, 'S': 188}, 'RAILGUN': {'K': None, 'P': None, 'DR': None, 'H': 5, 'D': None, 'DG': None, 'T': None, 'S': 21}}  # noqa
    assert e[6]["damage_dealt"] == 10459  # noqa
    assert e[6]["damage_taken"] == 8736  # noqa
    assert e[6]["player_id"] == '14e3d92ed5055145aab6e920'  # noqa
    assert e[6]["total_armor_pickup"] == 470  # noqa
    assert e[6]["total_health_pickup"] == 255  # noqa
    assert e[6]["weapons"] == {'GAUNTLET': {'K': None, 'P': None, 'DR': None, 'H': 6, 'D': None, 'DG': None, 'T': None, 'S': 0}, 'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 190, 'D': None, 'DG': None, 'T': None, 'S': 655}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 110, 'D': None, 'DG': None, 'T': None, 'S': 528}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 32, 'D': None, 'DG': None, 'T': None, 'S': 73}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 20, 'D': None, 'DG': None, 'T': None, 'S': 46}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 160, 'D': None, 'DG': None, 'T': None, 'S': 631}, 'RAILGUN': {'K': None, 'P': None, 'DR': None, 'H': 30, 'D': None, 'DG': None, 'T': None, 'S': 61}, 'PLASMA': {'K': None, 'P': None, 'DR': None, 'H': 8, 'D': None, 'DG': None, 'T': None, 'S': 24}}  # noqa
    assert e[7]["damage_dealt"] == 10799  # noqa
    assert e[7]["damage_taken"] == 6565  # noqa
    assert e[7]["player_id"] == '2f7d40fff23683c6ab15b2ba'  # noqa
    assert e[7]["total_armor_pickup"] == 435  # noqa
    assert e[7]["total_health_pickup"] == 285  # noqa
    assert e[7]["weapons"] == {'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 369, 'D': None, 'DG': None, 'T': None, 'S': 1455}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 106, 'D': None, 'DG': None, 'T': None, 'S': 440}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 35, 'D': None, 'DG': None, 'T': None, 'S': 110}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 26, 'D': None, 'DG': None, 'T': None, 'S': 61}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 148, 'D': None, 'DG': None, 'T': None, 'S': 703}, 'RAILGUN': {'K': None, 'P': None, 'DR': None, 'H': 14, 'D': None, 'DG': None, 'T': None, 'S': 39}, 'PLASMA': {'K': None, 'P': None, 'DR': None, 'H': 26, 'D': None, 'DG': None, 'T': None, 'S': 93}}  # noqa
    assert e[8]["damage_dealt"] == 7538  # noqa
    assert e[8]["damage_taken"] == 8771  # noqa
    assert e[8]["player_id"] == '3086e90f19e4d4d30a6ece78'  # noqa
    assert e[8]["total_armor_pickup"] == 205  # noqa
    assert e[8]["total_health_pickup"] == 385  # noqa
    assert e[8]["weapons"] == {'GAUNTLET': {'K': None, 'P': None, 'DR': None, 'H': 4, 'D': None, 'DG': None, 'T': None, 'S': 0}, 'MACHINEGUN': {'K': None, 'P': None, 'DR': None, 'H': 437, 'D': None, 'DG': None, 'T': None, 'S': 1746}, 'SHOTGUN': {'K': None, 'P': None, 'DR': None, 'H': 60, 'D': None, 'DG': None, 'T': None, 'S': 297}, 'GRENADE': {'K': None, 'P': None, 'DR': None, 'H': 36, 'D': None, 'DG': None, 'T': None, 'S': 123}, 'ROCKET': {'K': None, 'P': None, 'DR': None, 'H': 12, 'D': None, 'DG': None, 'T': None, 'S': 46}, 'LIGHTNING': {'K': None, 'P': None, 'DR': None, 'H': 46, 'D': None, 'DG': None, 'T': None, 'S': 242}, 'RAILGUN': {'K': None, 'P': None, 'DR': None, 'H': 5, 'D': None, 'DG': None, 'T': None, 'S': 21}, 'PLASMA': {'K': None, 'P': None, 'DR': None, 'H': 0, 'D': None, 'DG': None, 'T': None, 'S': 12}}  # noqa

    assert result.special_scores['CONSECUTIVE_RAIL_KILL'] == (
        [
            (95.6, '14e3d92ed5055145aab6e920', 'cc6b3555fc360da8aec21f60', 1),
            (97.8, '14e3d92ed5055145aab6e920', '3086e90f19e4d4d30a6ece78', 1),
            (97.8, '14e3d92ed5055145aab6e920', '8fff33431b55a197b4de8bd0', 1),
            (122.5, '761d1593e6faf9c12eaba9d4', '8fff33431b55a197b4de8bd0', 1),
            (466.7, '6179638dba55b8f5d2da7838', '3086e90f19e4d4d30a6ece78', 1),
            (466.7, '6179638dba55b8f5d2da7838', '761d1593e6faf9c12eaba9d4', 1),
            (523.0, '2f7d40fff23683c6ab15b2ba', '773fa00f3f3a7e960b561492', 1),
            (604.5, '6179638dba55b8f5d2da7838', '14e3d92ed5055145aab6e920', 1),
            (682.2, '6179638dba55b8f5d2da7838', '773fa00f3f3a7e960b561492', 1),
            (721.1, '14e3d92ed5055145aab6e920', '761d1593e6faf9c12eaba9d4', 1),
            (866.1, '6179638dba55b8f5d2da7838', '14e3d92ed5055145aab6e920', 1)
        ]
    )

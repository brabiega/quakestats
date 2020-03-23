import pytest

from quakestats.core.q3toql.parsers.base import (
    Q3LogParserModOsp,
)
from quakestats.core.q3toql.transform import (
    Q3toQL,
)


def _regen_asserts(data, accessor: str = 'e'):
    if isinstance(data, int):
        print(f'assert {accessor} == {data}  # noqa')
    elif isinstance(data, str):
        print(f"assert {accessor} == '{data}'  # noqa")
    elif isinstance(data, bool):
        print(f"assert {accessor} is {data}  # noqa")
    elif data is None:
        print(f"assert {accessor} is None  # noqa")
    elif isinstance(data, dict):
        # go deeper
        for k, v in data.items():
            nested_accessor = f"{accessor}['{k}']"
            _regen_asserts(v, nested_accessor)
    elif isinstance(data, list):
        for idx, v in enumerate(data):
            nested_accessor = f"{accessor}[{idx}]"
            _regen_asserts(v, nested_accessor)
    else:
        raise NotImplementedError(f"{data} of {type(data)}")


class TestQ3toQL():
    @pytest.fixture
    def osp_game_1(self, testdata_loader):
        ld = testdata_loader('osp-ffa-1.log')
        raw_data = ld.read()
        parser = Q3LogParserModOsp(raw_data)
        games = list(parser.games())
        yield games[0]

    def test_process(self, osp_game_1):
        tf = Q3toQL()
        game = tf.transform(osp_game_1)

        ql_events = list(game.get_events())
        e = ql_events
        _regen_asserts(e)
        assert e[0]['DATA']['INSTAGIB'] == 0  # noqa
        assert e[0]['DATA']['FACTORY'] == 'quake3'  # noqa
        assert e[0]['DATA']['FACTORY_TITLE'] == 'quake3'  # noqa
        assert e[0]['DATA']['INFECTED'] == 0  # noqa
        assert e[0]['DATA']['TIME_LIMIT'] == '0'  # noqa
        assert e[0]['DATA']['TRAINING'] == 0  # noqa
        assert e[0]['DATA']['FRAG_LIMIT'] == '20'  # noqa
        assert e[0]['DATA']['CAPTURE_LIMIT'] == '0'  # noqa
        assert e[0]['DATA']['SERVER_TITLE'] == 'noname'  # noqa
        assert e[0]['DATA']['GAME_TYPE'] == 'FFA'  # noqa
        assert e[0]['DATA']['QUADHOG'] == 0  # noqa
        assert e[0]['DATA']['ROUND_LIMIT'] == 0  # noqa
        assert e[0]['DATA']['MERCY_LIMIT'] == 0  # noqa
        assert e[0]['DATA']['SCORE_LIMIT'] == 0  # noqa
        assert e[0]['DATA']['MATCH_GUID'] == '84b6924313d35786dc04603e71e5f6f3'  # noqa
        assert e[0]['DATA']['MAP'] == 'ASYLUM'  # noqa
        assert e[0]['TYPE'] == 'MATCH_STARTED'  # noqa
        assert e[1]['TYPE'] == 'PLAYER_CONNECT'  # noqa
        assert e[1]['DATA']['MATCH_GUID'] == '84b6924313d35786dc04603e71e5f6f3'  # noqa
        assert e[1]['DATA']['TIME'] == 300  # noqa
        assert e[1]['DATA']['WARMUP'] == False  # noqa
        assert e[1]['DATA']['NAME'] == 'Bartoszer'  # noqa
        assert e[1]['DATA']['STEAM_ID'] == '6179638dba55b8f5d2da7838'  # noqa
        assert e[2]['TYPE'] == 'PLAYER_SWITCHTEAM'  # noqa
        assert e[2]['DATA']['MATCH_GUID'] == '84b6924313d35786dc04603e71e5f6f3'  # noqa
        assert e[2]['DATA']['TIME'] == 300  # noqa
        assert e[2]['DATA']['WARMUP'] == False  # noqa
        assert e[2]['DATA']['KILLER']['STEAM_ID'] == '6179638dba55b8f5d2da7838'  # noqa
        assert e[2]['DATA']['KILLER']['OLD_TEAM'] == 'SPECTATOR'  # noqa
        assert e[2]['DATA']['KILLER']['TEAM'] == 'FREE'  # noqa
        assert e[2]['DATA']['KILLER']['NAME'] == 'Bartoszer'  # noqa
        assert e[3]['TYPE'] == 'PLAYER_CONNECT'  # noqa
        assert e[3]['DATA']['MATCH_GUID'] == '84b6924313d35786dc04603e71e5f6f3'  # noqa
        assert e[3]['DATA']['TIME'] == 300  # noqa
        assert e[3]['DATA']['WARMUP'] == False  # noqa
        assert e[3]['DATA']['NAME'] == 'Daemia'  # noqa
        assert e[3]['DATA']['STEAM_ID'] == '254e24151c9e5466251073e6'  # noqa
        assert e[4]['TYPE'] == 'PLAYER_SWITCHTEAM'  # noqa
        assert e[4]['DATA']['MATCH_GUID'] == '84b6924313d35786dc04603e71e5f6f3'  # noqa
        assert e[4]['DATA']['TIME'] == 300  # noqa
        assert e[4]['DATA']['WARMUP'] == False  # noqa
        assert e[4]['DATA']['KILLER']['STEAM_ID'] == '254e24151c9e5466251073e6'  # noqa
        assert e[4]['DATA']['KILLER']['OLD_TEAM'] == 'SPECTATOR'  # noqa
        assert e[4]['DATA']['KILLER']['TEAM'] == 'FREE'  # noqa
        assert e[4]['DATA']['KILLER']['NAME'] == 'Daemia'  # noqa
        assert e[5]['TYPE'] == 'PLAYER_CONNECT'  # noqa
        assert e[5]['DATA']['MATCH_GUID'] == '84b6924313d35786dc04603e71e5f6f3'  # noqa
        assert e[5]['DATA']['TIME'] == 300  # noqa
        assert e[5]['DATA']['WARMUP'] == False  # noqa
        assert e[5]['DATA']['NAME'] == 'Doom'  # noqa
        assert e[5]['DATA']['STEAM_ID'] == '7727c59e2bf61c4a67428d15'  # noqa
        assert e[6]['TYPE'] == 'PLAYER_SWITCHTEAM'  # noqa
        assert e[6]['DATA']['MATCH_GUID'] == '84b6924313d35786dc04603e71e5f6f3'  # noqa
        assert e[6]['DATA']['TIME'] == 300  # noqa
        assert e[6]['DATA']['WARMUP'] == False  # noqa
        assert e[6]['DATA']['KILLER']['STEAM_ID'] == '7727c59e2bf61c4a67428d15'  # noqa
        assert e[6]['DATA']['KILLER']['OLD_TEAM'] == 'SPECTATOR'  # noqa
        assert e[6]['DATA']['KILLER']['TEAM'] == 'FREE'  # noqa
        assert e[6]['DATA']['KILLER']['NAME'] == 'Doom'  # noqa

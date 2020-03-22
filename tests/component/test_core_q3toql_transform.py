import pytest

from quakestats.core.q3toql.parsers.base import (
    Q3LogParserModOsp,
)
from quakestats.core.q3toql.transform import (
    Q3toQL,
)


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

        match_start = game.ql_events[0]
        assert match_start == {
            'DATA': {
                'INSTAGIB': 0,
                'FACTORY': 'quake3',
                'FACTORY_TITLE': 'quake3',
                'INFECTED': 0,
                'TIME_LIMIT': '0',
                'TRAINING': 0,
                'FRAG_LIMIT': '20',
                'CAPTURE_LIMIT': '0',
                'SERVER_TITLE': 'noname',
                'GAME_TYPE': 'FFA',
                'QUADHOG': 0,
                'ROUND_LIMIT': 0,
                'MERCY_LIMIT': 0,
                'SCORE_LIMIT': 0,
                'MATCH_GUID': '84b6924313d35786dc04603e71e5f6f3',
                'MAP': 'ASYLUM',
                'PLAYERS': {},
            },
            'TYPE': 'MATCH_STARTED'
        }

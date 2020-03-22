from unittest import (
    mock,
)

from quakestats.core.q3toql.transform import (
    Q3toQL,
)


class TestQ3toQL():
    def _build_assert(self, ev):
        print(f'assert e["TYPE"] == "{ev["TYPE"]}"')
        for key in sorted(ev['DATA']):
            if key == 'PLAYERS':
                continue

            val = ev['DATA'][key]
            if isinstance(val, str):
                print(f'assert d["{key}"] == "{val}"')
            else:
                print(f'assert d["{key}"] == {val}')

    def test_build_match_start(self):
        tf = Q3toQL()
        gamelog = mock.Mock()
        gamelog.checksum.hexdigest.return_value = 'match id'
        init_game = mock.Mock()
        init_game.name = 'InitGame'
        init_game.payload = r'\dmflags\0\fraglimit\20\g_gametype\0\mapname\ASYLUM\protocol\68\sv_allowDownload\1\sv_dlRate\100\sv_floodProtect\1\sv_hostname\noname\sv_maxRate\0\sv_maxclients\8\sv_minRate\0\sv_privateClients\0\timelimit\0\version\Q3 1.32e linux-x86_64 Mar 19 2020\capturelimit\0\g_needpass\0\gamename\osp\gameversion\OSP v1.03a\server_freezetag\0\server_ospauth\0\server_promode\0'  # noqa
        gamelog.events = [init_game]
        tf.gamelog = gamelog

        time, result = tf.build_match_start()
        # self._build_assert(result)
        e = result
        d = result['DATA']
        assert e["TYPE"] == "MATCH_STARTED"
        assert d["CAPTURE_LIMIT"] == "0"
        assert d["FACTORY"] == "quake3"
        assert d["FACTORY_TITLE"] == "quake3"
        assert d["FRAG_LIMIT"] == "20"
        assert d["GAME_TYPE"] == "FFA"
        assert d["INFECTED"] == 0
        assert d["INSTAGIB"] == 0
        assert d["MAP"] == "ASYLUM"
        assert d["MATCH_GUID"] == "match id"
        assert d["MERCY_LIMIT"] == 0
        assert d["QUADHOG"] == 0
        assert d["ROUND_LIMIT"] == 0
        assert d["SCORE_LIMIT"] == 0
        assert d["SERVER_TITLE"] == "noname"
        assert d["TIME_LIMIT"] == "0"
        assert d["TRAINING"] == 0

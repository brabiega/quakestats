import pytest

from quakestats.core.q3toql.parsers.base import (
    DefaultParserMixin,
    OspParserMixin,
    Q3LogParser,
    Q3LogParserModOsp,
    RawEvent,
)
from quakestats.system.qa import _regen_asserts  # noqa


class TestQ3LogParser():
    def test_read_lines(self, testdata_loader):
        ld = testdata_loader('osp-warmups.log')
        raw_data = ld.read()

        parser = Q3LogParser(raw_data)

        result = list(parser.read_lines())

        assert result[0] == '0.0 ------------------------------------------------------------'  # noqa
        assert result[-1] == '13.0 ------------------------------------------------------------'  # noqa
        assert len(result) == 24


class TestQ3LogParserModOsp():

    def __regen_asserts(self, games):
        games_count = len(games)
        print(f'assert len(e) == {games_count}')
        for idx, game in enumerate(games):
            accessor = 'e[{}]'.format(idx)
            ev_num = len(game.events)
            ev_check = game.checksum.hexdigest()

            print(f'assert len({accessor}.events) == {ev_num}  # noqa')
            print(f"assert {accessor}.checksum.hexdigest() == '{ev_check}'  # noqa")

    def test_games(self, testdata_loader):
        ld = testdata_loader('osp-warmups.log')
        raw_data = ld.read()
        res = Q3LogParserModOsp(raw_data)
        games = list(res.games())

        # self.__regen_asserts(games)  # use to regenerate asserts
        e = games
        assert len(e) == 3
        assert len(e[0].events) == 4  # noqa
        assert e[0].checksum.hexdigest() == 'b8fee375dae59abeb06850fc82d8a1b3'  # noqa
        assert len(e[1].events) == 4  # noqa
        assert e[1].checksum.hexdigest() == '6275aafca888f67ee53936e9c548ab2d'  # noqa
        assert len(e[2].events) == 10  # noqa
        assert e[2].checksum.hexdigest() == '1ea0d0be8f93babc98fd4579a4c1ba20'  # noqa

    @pytest.mark.parametrize('ts, expected', [
        ('0.0', 0),
        ('123.2', 123200),
        ('2.6', 2600),
    ])
    def test_mktime(self, ts, expected):
        res = Q3LogParserModOsp.mktime(ts)

        assert res == expected

    @pytest.mark.parametrize('line, expected', [
        (
            '13.0 ------------------------------------------------------------',  # noqa
            (13000, '___SEPARATOR___')
        ),
        (
            '0.0 ------------------------------------------------------------',  # noqa
            (0, '___SEPARATOR___')
        ),
    ])
    def test_line_to_event_separator(self, line, expected):
        parser = Q3LogParserModOsp('')

        ex_time, ex_name = expected
        result = parser.line_to_raw_event(line)
        assert result.time == ex_time
        assert result.payload is None
        assert result.name == ex_name

    @pytest.mark.parametrize('line, expected', [
        (
            '0.0 ServerTime:	20170621112912	11:29:12 (21 Jun 2017)',  # noqa
            (0, 'ServerTime', '20170621112912	11:29:12 (21 Jun 2017)'),  # noqa
        ),
        (
            '5.2 ClientUserinfoChanged: 0 n\Bartoszer\t\0\model\xaero/default\hmodel\xaero/default\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0',  # noqa
            (5200, 'ClientUserinfoChanged', '0 n\Bartoszer\t\0\model\xaero/default\hmodel\xaero/default\c1\4\c2\5\hc\100\w\0\l\0\rt\0\st\0'),  # noqa
        ),
    ])
    def test_line_to_event(self, line, expected):
        parser = Q3LogParserModOsp('')
        ex_time, ex_name, ex_payload = expected
        result = parser.line_to_raw_event(line)
        assert result.time == ex_time
        assert result.payload == ex_payload
        assert result.name == ex_name


class TestDefaultParser():
    def test_parse_user_info_changed(self):
        parser = DefaultParserMixin()
        raw_data = r'4 n\n0npax\t\0\model\sarge\hmodel\sarge\c1\1\c2\5\hc\100\w\0\l\0\rt\0\st\0'  # noqa
        raw_event = RawEvent(0, '', raw_data)
        event = parser.parse_user_info(raw_event)

        assert event.time == 0
        assert event.client_id == 4
        assert event.name == 'n0npax'
        assert event.team == 'FREE'

    def test_parse_kill(self):
        parser = DefaultParserMixin()
        raw_data = r'Kill: 2 3 1: Bartoszer killed Turbo W by MOD_SHOTGUN 3'
        raw_event = RawEvent(0, '', raw_data)
        event = parser.parse_kill(raw_event)
        assert event.client_id == 2
        assert event.victim_id == 3
        assert event.reason == 'MOD_SHOTGUN'

    def test_parse_disconnect(self):
        raw_data = r'8'
        raw_event = RawEvent(0, '', raw_data)
        parser = DefaultParserMixin()
        ev = parser.parse_client_disconnect(raw_event)
        assert ev.client_id == 8


class TestOspParser():
    def test_parse_weapon_stats(self):
        parser = OspParserMixin()
        raw_data = r'2 MachineGun:1367:267:0:0 Shotgun:473:107:23:8 G.Launcher:8:1:8:3 R.Launcher:30:11:9:5 LightningGun:403:68:15:10 Plasmagun:326:45:13:8 Given:5252 Recvd:7836 Armor:620 Health:545'  # noqa
        raw_event = RawEvent(0, '', raw_data)
        event = parser.parse_weapon_stat(raw_event)

        assert event.client_id == 2
        # _regen_asserts(event.pickups)
        e = event.pickups
        assert e.health == 545  # noqa
        assert e.armor == 620  # noqa

        # _regen_asserts(event.damage)
        e = event.damage
        assert e.given == 5252  # noqa
        assert e.received == 7836  # noqa

        # _regen_asserts(event.weapons)
        e = event.weapons
        assert e['MACHINEGUN'].shots == 1367  # noqa
        assert e['MACHINEGUN'].hits == 267  # noqa
        assert e['SHOTGUN'].shots == 473  # noqa
        assert e['SHOTGUN'].hits == 107  # noqa
        assert e['GRENADE'].shots == 8  # noqa
        assert e['GRENADE'].hits == 1  # noqa
        assert e['ROCKET'].shots == 30  # noqa
        assert e['ROCKET'].hits == 11  # noqa
        assert e['LIGHTNING'].shots == 403  # noqa
        assert e['LIGHTNING'].hits == 68  # noqa
        assert e['PLASMA'].shots == 326  # noqa
        assert e['PLASMA'].hits == 45  # noqa
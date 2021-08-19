import pytest

from quakestats.core.q3parser.events import (
    RawEvent,
)
from quakestats.core.q3parser.parser import (
    BaseQ3ParserMixin,
    GameLogParserOsp,
    OspParserMixin,
)
from quakestats.system.qa import _regen_asserts  # noqa


class TestGameLogParserOsp():
    @pytest.mark.parametrize('ts, expected', [
        ('0.0', 0),
        ('123.2', 123200),
        ('2.6', 2600),
    ])
    def test_mktime(self, ts, expected):
        res = GameLogParserOsp().mktime(ts)

        assert res == expected

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
        parser = GameLogParserOsp()
        ex_time, ex_name, ex_payload = expected
        result = parser.line_to_raw_event(line)
        assert result.time == ex_time
        assert result.payload == ex_payload
        assert result.name == ex_name


class TestDefaultParser():
    def test_parse_user_info_changed(self):
        parser = BaseQ3ParserMixin()
        raw_data = r'4 n\n0npax\t\0\model\sarge\hmodel\sarge\c1\1\c2\5\hc\100\w\0\l\0\rt\0\st\0'  # noqa
        raw_event = RawEvent(0, '', raw_data)
        event = parser.parse_user_info(raw_event)

        assert event.time == 0
        assert event.client_id == 4
        assert event.name == 'n0npax'
        assert event.team == 'FREE'

    def test_parse_kill(self):
        parser = BaseQ3ParserMixin()
        raw_data = r'Kill: 2 3 1: Bartoszer killed Turbo W by MOD_SHOTGUN 3'
        raw_event = RawEvent(0, '', raw_data)
        event = parser.parse_kill(raw_event)
        assert event.client_id == 2
        assert event.victim_id == 3
        assert event.reason == 'MOD_SHOTGUN'

    def test_parse_disconnect(self):
        raw_data = r'8'
        raw_event = RawEvent(0, '', raw_data)
        parser = BaseQ3ParserMixin()
        ev = parser.parse_client_disconnect(raw_event)
        assert ev.client_id == 8

    def test_parse_item(self):
        raw_data = r'3 item_quad'
        raw_event = RawEvent(0, '', raw_data)
        parser = BaseQ3ParserMixin()
        ev = parser.parse_item(raw_event)
        assert ev.client_id == 3
        assert ev.item_name == 'item_quad'


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

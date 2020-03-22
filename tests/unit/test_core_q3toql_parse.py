import pytest
from quakestats.core.q3toql.parsers.base import (
    Q3LogParser, Q3LogParserModOsp
)


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
    def test_read_event(self, testdata_loader):
        ld = testdata_loader('osp-warmups.log')

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
            (13000, '__separator__')
        ),
        (
            '0.0 ------------------------------------------------------------',  # noqa
            (0, '__separator__')
        ),
    ])
    def test_line_to_event_separator(self, line, expected):
        parser = Q3LogParserModOsp('')

        ex_time, ex_name = expected
        result = parser.line_to_event(line)
        assert result.time == ex_time
        assert result.payload is None
        assert result.name == '__separator__'

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
        result = parser.line_to_event(line)
        assert result.time == ex_time
        assert result.payload == ex_payload
        assert result.name == ex_name
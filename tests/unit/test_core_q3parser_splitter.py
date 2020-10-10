import datetime

import pytest

from quakestats.core.q3parser.splitter import (
    GameLogSplitter,
    Q3GameLog,
)


class TestQ3GameLog():

    def test_serialize(self):
        log = Q3GameLog(datetime.datetime(2020, 10, 10, 22, 22), 'osp')
        log.add_line('testing 1')
        log.add_line('testing 2')
        res = log.serialize()

        assert res == (
            "Quake3\n"
            "02cd73ea62677edd360fde3179013acd 1602361320.0 osp\n"
            "testing 1\n"
            "testing 2"
        )


class TestGameLogSplitter():
    @pytest.mark.parametrize('data, expected', [
        (
            (
                "------------------\n"
                "test\n"
                "------------------\n"
            ),
            # number of results, results
            (1, [['test']]),
        ),
        (
            (
                "------------------\n"
                "test\n"
                "test2\n"
                "------------------\n"
                "test3\n"
            ),
            # number of results, results
            (2, [['test', 'test2'], ['test3']]),
        ),
        (
            (
                "------------------\n"
                "------------------\n"
                "test\n"
                "test2\n"
                "------------------\n"
                "------------------\n"
                "test3\n"
                "------------------\n"
            ),
            # number of results, results
            (2, [['test', 'test2'], ['test3']]),
        ),
        (
            (
                "test\n"
                "test2\n"
                "------------------\n"
                "------------------\n"
                "------------------\n"
            ),
            # number of results, results
            (1, [['test', 'test2']]),
        ),
    ])
    def test_split_osp(self, data, expected):
        splitter = GameLogSplitter('osp')
        res = list(splitter.iter_games(data))

        ex_len, ex_data = expected
        assert len(res) == ex_len
        for r, ex in zip(res, ex_data):
            assert r.lines == ex

    def test_split_testdata(self, testdata_loader):
        data = testdata_loader('osp-warmups.log')
        splitter = GameLogSplitter('osp')
        res = list(splitter.iter_games(data.read()))

        assert len(res) == 3
        res[0].identifier == '5acd2bb0453735885f5a9294b5ff67a3'
        res[1].identifier == '671b1bf98bb8e0c91d2137e749cb3d7c'
        res[2].identifier == 'f66ad0e4bdb4216e77d5e5856af6f5c0'

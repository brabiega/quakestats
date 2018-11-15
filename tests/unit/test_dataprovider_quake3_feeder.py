import pytest

from quakestats.dataprovider.quake3.feeder import Q3MatchFeeder, FeedFull


class TestQuake3MatchFeeder():
    @pytest.fixture
    def dummy_match_log(self):
        return (
            "13.0 ShutdownGame:\n"
            "14.0 ------------------------------------------------------------\n"  # noqa
            "15.0 ------------------------------------------------------------\n"  # noqa
        ).splitlines()

    def test_feeder_full(self, dummy_match_log):
        match_log = dummy_match_log
        feeder = Q3MatchFeeder()
        assert feeder.full is False
        assert not feeder.events
        feeder.feed(match_log[0])

        assert feeder.full is False
        assert feeder.events

        with pytest.raises(FeedFull):
            feeder.feed(match_log[1])
            assert feeder.full is True

        with pytest.raises(FeedFull):
            feeder.feed(match_log)

        feed = feeder.consume()
        assert feeder.full is False
        assert not feeder.events
        assert feed

    def test_feeder_empty(self, dummy_match_log):
        log_delimiter = dummy_match_log[-1]
        feeder = Q3MatchFeeder()
        feeder.feed(log_delimiter)
        feeder.feed(log_delimiter)
        assert not feeder.events
        assert not feeder.full

import json
from datetime import (
    datetime,
)

from quakestats.core.qlparser.splitter import (
    QLGameLog,
    QLGameLogSplitter,
)


class TestQLSplitter():
    def test_ql_splitter(self, testdata_loader):
        ld = testdata_loader('ql-dump-1.log')
        raw_data = ld.read()
        data = json.loads(raw_data)

        splitter = QLGameLogSplitter()
        matches = []
        for event in data:
            match = splitter.add_event(event)
            if match:
                matches.append(match)

        assert len(matches) == 5
        assert matches[0].identifier == '83abea54-9ea3-4537-b57b-92d5e17ac571'
        assert matches[1].identifier == '743b0332-8eb0-4f4b-b657-133fe122fcca'
        assert matches[2].identifier == '3a2d494f-ac2d-4c8a-8b33-df17b6dedf05'
        assert matches[3].identifier == '32f116ec-ef8a-424d-a1cc-1c53c183b91c'
        assert matches[4].identifier == '7ae0e362-3c99-442f-9f3c-f2d2eca37c61'


class TestQLGameLog():
    def test_serialize(self):
        log = QLGameLog(datetime(2020, 10, 5, 22, 11), 'identifier123')
        log.add_event({'type': 'kill', 'data': 'killem'})
        log.add_event({'type': 'kill2', 'data': 'killem2'})

        data = log.serialize()
        assert data == (
            "QuakeLive\n"
            "identifier123 1601928660.0\n"
            '[{"type": "kill", "data": "killem"}, {"type": "kill2", "data": "killem2"}]'
        )

    def test_deserialize(self):
        data = (
            "QuakeLive\n"
            "identifier123 1601928660.0\n"
            '[{"type": "kill", "data": "killem"}, {"type": "kill2", "data": "killem2"}]'
        ).splitlines()
        log = QLGameLog.deserialize(data)

        assert log.identifier == 'identifier123'
        assert log.received == datetime(2020, 10, 5, 22, 11)

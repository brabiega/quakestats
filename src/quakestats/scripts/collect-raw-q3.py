#!/usr/bin/env python
"""
DEPRECATED, unusable
Example usage
cat q3log | ./collect-raw-q3.py
Will write proper matches to specific path
"""

import json
import os
import sys

from quakestats import (
    dataprovider,
)
from quakestats.dataprovider import (
    quake3,
)


class QJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, quake3.PlayerId):
            return str(o.steam_id)
        return json.JSONEncoder.default(self, o)


# TODO read from config file or args
SERVER_DOMAIN = "serverdomain"
PATH = "/tmp/q3test"

data = sys.stdin.read()

feeder = quake3.Q3MatchFeeder()

raw_matches = []
for line in data.splitlines():
    try:
        feeder.feed(line)
    except quake3.FeedFull:
        raw_matches.append(feeder.consume())
        feeder.feed(line)

raw_matches.append(feeder.consume())

final_results = []

for match in raw_matches:
    transformer = quake3.Q3toQL(match["EVENTS"])
    transformer.server_domain = SERVER_DOMAIN

    try:
        transformer.process()
    except Exception as e:
        print(e)
        continue

    results = transformer.result

    # PREPROCESS
    preprocessor = dataprovider.MatchPreprocessor()
    preprocessor.process_events(results["events"])

    if not preprocessor.finished:
        continue

    res = dataprovider.FullMatchInfo(
        events=preprocessor.events,
        match_guid=preprocessor.match_guid,
        duration=preprocessor.duration,
        start_date=results["start_date"],
        finish_date=results["finish_date"],
        server_domain=SERVER_DOMAIN,
        source="Q3",
    )

    m = res.as_dict()
    m["START_DATE"] = m["START_DATE"].strftime(dataprovider.DATE_FORMAT)
    m["FINISH_DATE"] = m["FINISH_DATE"].strftime(dataprovider.DATE_FORMAT)

    path = os.path.join(PATH, "{}.json".format(res.match_guid))
    with open(path, "w") as fh:
        print("Writing {}".format(path))
        fh.write(json.dumps(m, cls=QJsonEncoder))

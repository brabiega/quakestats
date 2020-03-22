#!/usr/bin/env python
"""
Example usage
cat quakesamples/qldata/match-f2296f81-ed20-436c-a235-175fc33771e6.json | ./collect-raw-ql.py  # noqa
"""
import json
import sys

from quakestats.dataprovider.quakelive import (
    collector,
)

mc = collector.MatchCollector("/tmp/qltest2")


data = sys.stdin.read()
events = json.loads(data)

# support raw event stream and preprocessed data too
if "EVENTS" in events:
    events = events["EVENTS"]
    events.append({"TYPE": "EOF", "DATA": {"MATCH_GUID": "EOF"}})

for event in events:
    mc.process_event(event)

#!/usr/bin/env python

"""
Match analyzer read from stdin
"""

import json
import sys
from quakestats import dataprovider
from quakestats.dataprovider import analyze
from quakestats.datasource import mongo2
import pymongo


data = sys.stdin.read()

raw_data = json.loads(data)

fmi = dataprovider.FullMatchInfo.from_dict(raw_data)

analyzer = analyze.Analyzer()
report = analyzer.analyze(fmi)

db = pymongo.MongoClient().qlstats2
ds = mongo2.DataStoreMongo(db)

res = ds.store_analysis_report(report)
print(res)

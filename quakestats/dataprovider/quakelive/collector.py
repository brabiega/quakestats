#!/usr/bin/env python

from quakestats.dataprovider import FeedFull, MatchPreprocessor, FullMatchInfo
from quakestats.dataprovider.quakelive import QLMatchFeeder
import logging
import os
import json
import uuid
from datetime import datetime, timedelta


logger = logging.getLogger('quakestats.dataprovider.quakelive')


class MatchCollector():
    def __init__(self, data_store):
        self.data_store = data_store
        self.feeder = QLMatchFeeder()
        logger.info("Match collector initialized -> {}".format(data_store))

    def process_event(self, event):
        try:
            self.feeder.feed(event)
        except FeedFull:
            match_info = self.feeder.consume()
            result = self.validate_match(match_info)
            if result:
                self.save_match(result)
            else:
                self.save_invalid(match_info)

    def validate_match(self, match_info):
        preprocessor = MatchPreprocessor()
        preprocessor.process_events(match_info['EVENTS'])

        if preprocessor.is_valid():
            match_info = FullMatchInfo(
                events=preprocessor.events,
                match_guid=preprocessor.match_guid,
                duration=preprocessor.duration,
                start_date=(datetime.now() - timedelta(seconds=preprocessor.duration)).isoformat(),
                finish_date=datetime.now().isoformat(),
                server_domain='CELLS',
                source="QL")

            result = match_info.get_summary()
            result['EVENTS'] = preprocessor.events
            return result
        else:
            logger.info("Match is invalid, skipping")
            return None

    def save_match(self, match):
        match_guid = match['MATCH_GUID']
        tmp_filename = "match-{}.tmp".format(match_guid)
        filename = "match-{}.json".format(match_guid)

        tmp_path = os.path.join(self.data_store, tmp_filename)
        real_path = os.path.join(self.data_store, filename)

        with open(tmp_path, "w") as fh:
            fh.write(json.dumps(match))

        os.rename(tmp_path, real_path)
        logger.info("Match saved '{}'".format(real_path))

    def save_invalid(self, match):
        match['DATE'] = datetime.utcnow().isoformat()
        match_id = str(uuid.uuid4())
        filename = 'invalid-{}.json'.format(match_id)

        path = os.path.join(self.data_store, filename)
        with open(path, 'w') as fh:
            fh.write(json.dumps(match))

        logger.info("Invalid match saved '{}'".format(path))

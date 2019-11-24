import logging
import time
import io
import requests

from quakestats.dataprovider.quake3 import Q3MatchFeeder, FeedFull


logger = logging.getLogger(__name__)


class Q3LogWatcher():
    def __init__(self, log_file_path, api_token, api_endpoint):
        self.log_file_path = log_file_path
        self.interval = 5  # pool for changes every 5s
        self._cursor_location = 0
        self.match_feeder = Q3MatchFeeder()
        self.api_token = api_token
        self.api_endpoint = api_endpoint

    def has_changed(self, fd):
        """
        Return True, True if file is bigger than last seen
        Return True, False if file is smaller than last seen
        Return False, False if file size has not changed
        """
        fd.seek(0, io.SEEK_END)
        end = fd.tell()
        if end > self._cursor_location:
            return True, True

        elif end < self._cursor_location:
            return True, False

        else:
            return False, False

    def watch(self, ignore_history=False):
        logger.info("Watching file '%s'", self.log_file_path)

        if ignore_history:
            logger.info("Historical entries are ignored")
            with open(self.log_file_path) as fd:
                fd.seek(0, io.SEEK_END)
                self._cursor_location = fd.tell()

        while True:       
            with open(self.log_file_path) as fd:
                changed, forward = self.has_changed(fd)

                if changed:
                    new_loc = fd.tell()
                    logger.debug(
                        "File change detected (%s -> %s, forward %s)",
                        self._cursor_location, new_loc, forward
                    )

                    if not forward:
                        logger.info("File reset detected")
                        self._cursor_location = 0

                        self.match_feeder = Q3MatchFeeder()

                    fd.seek(self._cursor_location)
                    self.consume_change(fd)

                else:
                    pass

            time.sleep(self.interval)

    def consume_change(self, fd):
        for line in fd:
            line = line.strip()
            try:
                self.match_feeder.feed(line)
            except FeedFull:
                match = self.match_feeder.consume()
                match['TOKEN'] = self.api_token

                logger.info("Consumed match with %s events", len(match['EVENTS']))
                response = requests.post(
                    '{}/api/v2/upload/json'.format(self.api_endpoint),
                    json=match
                )
                logger.info("Match sent to endpoint %s, response %s", self.api_endpoint, response)

                self.match_feeder.feed(line)

        self._cursor_location = fd.tell()
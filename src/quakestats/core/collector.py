"""
QL zmq event collector
"""

import asyncio
import logging
import time

import zmq
import zmq.asyncio

logger = logging.getLogger(__name__)
ctx = zmq.asyncio.Context()


class QLStatCollector():

    def __init__(self, host: str, port: str, password: str):
        self.host = host
        self.port = port
        self.password = password
        self.endpoint = f"tcp://{self.host}:{self.port}"
        self.socket = None
        self.reader: asyncio.Task = None
        self.last_event_timestamp = None

    async def refresh_idle(self, on_event_cb: callable):
        """
        There is a bug in QL server side, PUB socket stops sending events after long idle time.
        To overcome this issue the socket has to be reconnected when no data was received for 15mins.
        According to qlstats:
        https://github.com/PredatH0r/XonStat/tree/master/feeder#connecting-to-quake-live-game-zmq
        """
        while True:
            await asyncio.sleep(60)
            if (time.time() - self.last_event_timestamp) > 60 * 15:
                logger.debug("Socked idle, restarting")
                self.reader.cancel()
                self.socket.close()
                self.reader = asyncio.create_task(self.read_loop(on_event_cb))

    async def start(self, on_event_cb: callable):
        self.reader = asyncio.create_task(self.read_loop(on_event_cb))
        return await asyncio.create_task(self.refresh_idle(on_event_cb))

    async def read_loop(self, on_event_cb: callable):
        """
        def on_event_cb(timestamp, event)
        """
        logger.info("Establishing connection to %s", self.endpoint)
        self.socket = ctx.socket(zmq.SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.socket.setsockopt_string(zmq.PLAIN_USERNAME, "stats")
        self.socket.setsockopt_string(zmq.PLAIN_PASSWORD, self.password)
        self.socket.setsockopt(zmq.RECONNECT_IVL, 60000)
        self.socket.connect(self.endpoint)

        timestamp = time.time()
        while True:
            self.last_event_timestamp = timestamp
            data = await self.socket.recv_json()
            timestamp = time.time()
            try:
                on_event_cb(timestamp, data)
            except Exception as e:
                logger.error("Error processing %s", self.endpoint)
                logger.exception(e)

"""
QL zmq event collector
"""

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

    async def read_loop(self, on_event_cb: callable):
        """
        def on_event_cb(timestamp, event)
        """
        logger.info("Establishing connection to %s", self.endpoint)
        self.socket = ctx.socket(zmq.SUB)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
        self.socket.setsockopt_string(zmq.PLAIN_USERNAME, "stats")
        self.socket.setsockopt_string(zmq.PLAIN_PASSWORD, self.password)
        self.socket.setsockopt(zmq.RECONNECT_IVL, 15000)
        self.socket.connect(self.endpoint)

        while True:
            data = await self.socket.recv_json()
            timestamp = time.time()
            try:
                on_event_cb(timestamp, data)
            except Exception as e:
                logger.error("Error processing %s", self.endpoint)
                logger.exception(e)

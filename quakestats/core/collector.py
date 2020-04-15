"""
QL zmq event collector
"""

import logging
import time

import zmq
from zmq.utils.monitor import (
    recv_monitor_message,
)

# see https://github.com/zeromq/pyzmq/wiki/Building-and-Installing-PyZMQ
# QuakeLive requires CZMQ 3.x APIs or newer (libzmq 4.x)


logger = logging.getLogger(__name__)


class QLStatCollector():
    mon_ev_map = {
        zmq.EVENT_ACCEPTED: "EVENT_ACCEPTED",
        zmq.EVENT_ACCEPT_FAILED: "EVENT_ACCEPT_FAILED",
        zmq.EVENT_BIND_FAILED: "EVENT_BIND_FAILED",
        zmq.EVENT_CLOSED: "EVENT_CLOSED",
        zmq.EVENT_CLOSE_FAILED: "EVENT_CLOSE_FAILED",
        zmq.EVENT_CONNECTED: "EVENT_CONNECTED",
        zmq.EVENT_CONNECT_DELAYED: "EVENT_CONNECT_DELAYED",
        zmq.EVENT_CONNECT_RETRIED: "EVENT_CONNECT_RETRIED",
        zmq.EVENT_DISCONNECTED: "EVENT_DISCONNECTED",
        zmq.EVENT_LISTENING: "EVENT_LISTENING",
        zmq.EVENT_MONITOR_STOPPED: "EVENT_MONITOR_STOPPED",
    }

    def __init__(self, host: str, port: str, password: str):
        logger.info(
            "Using zmq python bindings %s, libzmq version %s",
            zmq.__version__, zmq.zmq_version()
        )
        self.host = host
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.mon_socket = self.socket.get_monitor_socket(zmq.EVENT_ALL)
        self.socket.plain_username = b"stats"
        self.socket.plain_password = bytes(password, "utf-8")
        self.socket.zap_domain = b"stats"

    def read_loop(self, on_event_cb: callable):
        """
        def on_event_cb(timestamp, event)
        """
        self.socket.connect(f"tcp://{self.host}:{self.port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

        probe_ts = time.time()
        while True:
            if (time.time() - probe_ts) > 360:
                logger.info("No events received. Waiting...")
                probe_ts = time.time()

            try:
                monitor_data = recv_monitor_message(
                    self.mon_socket, zmq.NOBLOCK
                )
                try:
                    ev_name = self.mon_ev_map[monitor_data['event']]
                except KeyError:
                    ev_name = 'Unknown'
                logger.info("Monitor event '%s': %s", ev_name, monitor_data)
            except zmq.error.Again:
                pass

            try:
                data = self.socket.recv_json(zmq.NOBLOCK)
            except zmq.error.Again:
                time.sleep(0.1)
                continue

            probe_ts = time.time()
            on_event_cb(time.time(), data)

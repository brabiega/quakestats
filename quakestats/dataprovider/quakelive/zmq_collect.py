#!/usr/bin/env python

from quakestats.dataprovider.quakelive.collector import MatchCollector
import click
import struct
import os
import logging
import zmq

logging.basicConfig(level=logging.DEBUG)

# see https://github.com/zeromq/pyzmq/wiki/Building-and-Installing-PyZMQ
# QuakeLive requires CZMQ 3.x APIs or newer (libzmq 4.x)


POLL_TIMEOUT = 1000

logger = logging.getLogger('quakestats.dataprovider.quakelive')


# TODO: why do we need such mapping anyway?
event_names = {
    zmq.EVENT_ACCEPTED: 'EVENT_ACCEPTED',
    zmq.EVENT_ACCEPT_FAILED: 'EVENT_ACCEPT_FAILED',
    zmq.EVENT_BIND_FAILED: 'EVENT_BIND_FAILED',
    zmq.EVENT_CLOSED: 'EVENT_CLOSED',
    zmq.EVENT_CLOSE_FAILED: 'EVENT_CLOSE_FAILED',
    zmq.EVENT_CONNECTED: 'EVENT_CONNECTED',
    zmq.EVENT_CONNECT_DELAYED: 'EVENT_CONNECT_DELAYED',
    zmq.EVENT_CONNECT_RETRIED: 'EVENT_CONNECT_RETRIED',
    zmq.EVENT_DISCONNECTED: 'EVENT_DISCONNECTED',
    zmq.EVENT_LISTENING: 'EVENT_LISTENING',
    zmq.EVENT_MONITOR_STOPPED: 'EVENT_MONITOR_STOPPED'}


def _readSocketEvent(msg):
    # NOTE: little endian - hopefully that's not platform specific?
    event_id = struct.unpack('<H', msg[:2])[0]
    # NOTE: is it possible I would get a bitfield?
    event_name = event_names[event_id] if event_id in event_names else '%d' % event_id
    event_value = struct.unpack('<I', msg[2:])[0]
    return (event_id, event_name, event_value)


def _checkMonitor(monitor):
    try:
        event_monitor = monitor.recv(zmq.NOBLOCK)
    except zmq.Again:
        return

    (event_id, event_name, event_value) = _readSocketEvent(event_monitor)
    event_monitor_endpoint = monitor.recv(zmq.NOBLOCK)
    logger.info(
        'Socket monitor: {} {} endpoint {}'
        .format(event_name, event_value, event_monitor_endpoint))


def subscribe_and_process(endpoint, password):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    monitor = socket.get_monitor_socket(zmq.EVENT_ALL)
    if (password is not None):
        logger.info('setting password for access')
        socket.plain_username = b'stats'
        socket.plain_password = bytes(password, 'utf-8')
        socket.zap_domain = b'stats'
    logger.info('Connecting SUB to {}'.format(endpoint))
    socket.connect(endpoint)
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    logger.info('Connected SUB to {}'.format(endpoint))
    read_loop(monitor, socket)


def read_loop(monitor, socket):
    match_collector = MatchCollector(os.environ['QLS_DATA_STORE'])
    counter = 0
    while (True):
        event = socket.poll(POLL_TIMEOUT)
        # check if there are any events to report on the socket
        _checkMonitor(monitor)

        if (event == 0):
            continue

        while (True):
            try:
                msg = socket.recv_json(zmq.NOBLOCK)
            except zmq.error.Again:
                break
            else:
                match_collector.process_event(msg)
                counter += 1
                if counter % 50 == 0:
                    logger.info("{} processed".format(counter))


@click.command()
@click.argument('host')
@click.argument('port')
@click.argument('password')
def main(host, port, password):
    assert os.environ['QLS_DATA_STORE']
    endpoint = "tcp://{}:{}".format(host, port)

    logger.debug(
        'zmq python bindings {}, libzmq version {}'
        .format(zmq.__version__, zmq.zmq_version()))

    subscribe_and_process(endpoint, password)


if __name__ == "__main__":
    main()

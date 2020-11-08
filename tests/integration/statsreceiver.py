import asyncio
import logging
import time

import zmq
import zmq.asyncio

from quakestats.sdk import (
    QSSdk,
)
from quakestats.system.context import (
    SystemContext,
)

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[logging.StreamHandler()]
)

ctx = zmq.asyncio.Context()


async def recv_and_process():
    # this has to be within async func
    socket = ctx.socket(zmq.SUB)
    socket.setsockopt_string(zmq.SUBSCRIBE, '')
    socket.setsockopt_string(zmq.PLAIN_USERNAME, "stats")
    socket.setsockopt_string(zmq.PLAIN_PASSWORD, "test")
    socket.setsockopt(zmq.RECONNECT_IVL, 1000)
    socket.connect("tcp://127.0.0.1:55055")

    sdk_ctx = SystemContext()
    sdk = QSSdk(sdk_ctx)

    feed = sdk.create_ql_feed()

    while True:
        data = await socket.recv_json()
        data['__recv_timestamp'] = int(time.time())

        print(data)
        continue
        sdk.feed_ql(feed, data)


async def main():
    tasks = [asyncio.create_task(t1(f'a-{t}')) for t in range(5)]
    for t in tasks:
        await t


async def t1(v):
    while True:
        print(v)
        await asyncio.sleep(1)


# asyncio.run(main())

asyncio.run(recv_and_process())

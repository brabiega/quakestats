"""
This simple app simulates QL stat sending capabilities.

Given match stream is sent 5s after script launch.
Once data is sent script ends.
"""

import asyncio
import json
import logging

import click
import zmq
import zmq.asyncio
from zmq.auth.asyncio import (
    AsyncioAuthenticator,
)

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[logging.StreamHandler()]

)


@click.group()
def cli():
    pass


@cli.command(name="serve")
@click.argument("datapath")
def serve(datapath):
    with open(datapath) as fh:
        data = json.load(fh)

    ctx = zmq.asyncio.Context()
    socket = ctx.socket(zmq.PUB)
    authenticator = AsyncioAuthenticator(ctx)
    authenticator.configure_plain(passwords={'stats': 'test'})
    authenticator.allow('127.0.0.1')
    socket.plain_server = True
    socket.bind("tcp://127.0.0.1:55055")

    asyncio.run(recv_and_process(authenticator, socket, data))


async def recv_and_process(authenticator, socket, data):
    authenticator.start()
    await asyncio.sleep(5)
    for p in data:
        await socket.send_json(p)


if __name__ == "__main__":
    cli()

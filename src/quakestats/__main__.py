#!/usr/bin/env python

import asyncio
import logging
import time
from configparser import (
    ConfigParser,
)
from functools import (
    partial,
)

import click

from quakestats import (
    manage,
)
from quakestats.core.collector import (
    QLStatCollector,
)
from quakestats.health import (
    HealthInfo,
)
from quakestats.sdk import (
    QSSdk,
)
from quakestats.system import (
    context,
    log,
)

logger = logging.getLogger(__name__)


# TODO consider moving to separate CLI module
@click.group()
def cli():
    pass


@cli.command(name="set-admin-pwd")
@click.argument("password")
def set_admin_password(password):
    # TODO find a good way to initialize DB access of the webapp
    from quakestats.web import mongo_db

    manage.set_admin_password(mongo_db.db, password)


@cli.command(name="rebuild-db")
def run_rebuild_db():
    ctx = context.SystemContext()
    sdk = QSSdk(ctx)
    sdk.rebuild_db()


@cli.command(name="collect-ql")
@click.argument("configfile")
def collect_ql(configfile):
    """
    Config format

    [serv1]
    port = 1
    ip = 1.2.3.4
    password = 101001

    [serv2]
    ...
    """
    ctx = context.SystemContext()
    sdk = QSSdk(ctx)

    collector_config = ConfigParser()
    collector_config.read(configfile)

    def event_cb(feed, timestamp: int, event: dict):
        event['__recv_timestamp'] = time.time()
        sdk.feed_ql(feed, event)

    async def main():
        tasks = []
        for section in collector_config.sections():
            logger.info("Attaching stats from %s", section)
            feed = sdk.create_ql_feed()
            cb = partial(event_cb, feed)

            ip = collector_config.get(section, 'ip')
            port = collector_config.get(section, 'port')
            pwd = collector_config.get(section, 'password')

            collector = QLStatCollector(ip, port, pwd)
            tasks.append(asyncio.create_task(collector.start(cb)))

        await asyncio.gather(*tasks)

    asyncio.run(main())


@cli.command(name="load-ql-game")
@click.argument('file_path')
def load_ql_game(file_path):
    raise NotImplementedError()


@cli.command()
def status():
    colormap = {
        0: "green",
        1: "blue",
        2: "yellow",
        3: "red",
        4: "red",
    }

    ctx = context.SystemContext()
    health_info = HealthInfo(ctx)
    health = health_info.run()
    for key, val in health.items():
        click.echo(key + ": ", nl=False)
        level, comment = val
        click.secho(comment, fg=colormap[level])


@cli.command(name="process-q3-log")
@click.argument('file_path')
@click.argument('mod')
def process_q3_log(file_path, mod):
    ctx = context.SystemContext()
    sdk = QSSdk(ctx)

    with open(file_path) as fh:
        sdk.process_q3_log(fh.read(), mod)


@cli.command('list-matches')
def list_matches():
    ctx = context.SystemContext()
    sdk = QSSdk(ctx)
    for match in sdk.iter_matches():
        print(match)


@cli.command('warehouse-list')
def warehouse_list():
    ctx = context.SystemContext()
    sdk = QSSdk(ctx)
    for item in sdk.warehouse_iter():
        print(item)


@cli.command(name="match-delete")
@click.argument('match-guid')
def delete_match(match_guid):
    ctx = context.SystemContext()
    sdk = QSSdk(ctx)
    sdk.delete_match(match_guid)


def main(args=None):
    log.configure_logging(logging.DEBUG)
    cli()


if __name__ == "__main__":
    main()

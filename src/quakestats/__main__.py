#!/usr/bin/env python

import logging

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
    conf,
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
@click.argument("host")
@click.argument("port")
@click.argument("password")
def collect_ql(host, port, password):
    from quakestats.core.ql import QLGame, MatchMismatch

    game = QLGame()
    ctx = context.SystemContext()
    sdk = QSSdk(ctx)

    data_dir = conf.get_conf_val("RAW_DATA_DIR")

    def event_cb(timestamp: int, event: dict):
        nonlocal game
        try:
            ev = game.add_event(timestamp, event)
        except MatchMismatch:
            logger.info("Got game %s with %s events", game.game_guid, len(game.ql_events))

            if game.ql_events:
                if data_dir:
                    manage.store_game(game, 'QL', data_dir)

                try:
                    sdk.analyze_and_store(game)
                except Exception as e:
                    logger.error('Failed to process match %s', game.game_guid)
                    logger.exception(e)

            game = QLGame()
            ev = game.add_event(timestamp, event)

        if ev:
            logger.debug("%s -> %s", ev.data['MATCH_GUID'], ev.type)

    collector = QLStatCollector(host, port, password)
    collector.read_loop(event_cb)


@cli.command(name="load-ql-game")
@click.argument('file_path')
def load_ql_game(file_path):
    ctx = context.SystemContext()
    sdk = QSSdk(ctx)
    server_domain, game = manage.load_game(file_path)
    sdk.analyze_and_store(game)


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

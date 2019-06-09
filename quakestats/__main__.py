#!/usr/bin/env python

import click
from quakestats.health import HealthInfo
from quakestats import manage


# TODO consider moving to separate CLI module
@click.group()
def cli():
    pass


@cli.command(name='set-admin-pwd')
@click.argument('password')
def set_admin_password(password):
    # TODO find a good way to initialize DB access of the webapp
    from quakestats.web import mongo_db
    manage.set_admin_password(mongo_db.db, password)


@cli.command(name='rebuild-db')
def run_rebuild_db():
    from quakestats.web import app, data_store
    # TODO at the moment config is too closely bound to flask app
    result = manage.rebuild_db(
        app.config['RAW_DATA_DIR'],
        app.config['SERVER_DOMAIN'],
        data_store,
    )
    print("Processed {} matches".format(result))


@cli.command()
def status():
    colormap = {
        0: 'green',
        1: 'blue',
        2: 'yellow',
        3: 'red',
        4: 'red',
    }

    health_info = HealthInfo()
    health = health_info.run()
    for key, val in health.items():
        click.echo(key + ': ', nl=False)
        level, comment = val
        click.secho(comment, fg=colormap[level])


def main(args=None):
    cli()


if __name__ == '__main__':
    main()

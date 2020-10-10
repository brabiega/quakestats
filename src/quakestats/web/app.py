import logging

from flask import (
    Flask,
)
from flask_pymongo import (
    PyMongo,
)

from quakestats.datasource import (
    mongo2,
)
from quakestats.system.conf import (
    ENV_VAR_NAME,
)
from quakestats.system.context import (
    SystemContext,
)
from quakestats.system.log import (
    configure_logging,
)

app = Flask(__name__)
app.config.from_envvar(ENV_VAR_NAME)

mongo_db = PyMongo(app)


def data_store():
    return mongo2.DataStoreMongo(mongo_db.db)


def load_stuff():
    from quakestats.web import api  # noqa
    from quakestats.web import views  # noqa


def get_sys_ctx():
    return SystemContext()


load_stuff()

configure_logging(logging.DEBUG)

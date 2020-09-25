from flask import (
    Flask,
)
from flask_pymongo import (
    PyMongo,
)

from quakestats.datasource import (
    mongo2,
)

app = Flask(__name__)
app.config.from_envvar("QUAKESTATS_SETTINGS")

mongo_db = PyMongo(app)


def data_store():
    return mongo2.DataStoreMongo(mongo_db.db)


def load_stuff():
    from quakestats.web import api  # noqa
    from quakestats.web import views  # noqa


load_stuff()

from flask import (
    Flask,
)
from flask_pymongo import (
    PyMongo,
)

from quakestats.datasource import (
    mongo2,
)
# load web app handlers for views and api
from quakestats.web import (
    utils,
)

app = Flask(__name__)
app.config.from_envvar("QUAKESTATS_SETTINGS")

mongo_db = PyMongo(app)


def data_store():
    return mongo2.DataStoreMongo(mongo_db.db)


def load_stuff():
    from quakestats.web import api  # noqa
    from quakestats.web import views  # noqa


app.json_encoder = utils.QJsonEncoder
load_stuff()

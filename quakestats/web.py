from flask import Flask
from flask_pymongo import PyMongo

import quakestats.api  # noqa
import quakestats.views  # noqa
from quakestats.datasource import mongo2

app = Flask(__name__)
app.config.from_envvar("QUAKESTATS_SETTINGS")

mongo_db = PyMongo(app)


def data_store():
    return mongo2.DataStoreMongo(mongo_db.db)


app.json_encoder = quakestats.api.QJsonEncoder

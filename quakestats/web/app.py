from flask import Flask
from flask_pymongo import PyMongo


from quakestats.datasource import mongo2

app = Flask(__name__)
app.config.from_envvar("QUAKESTATS_SETTINGS")

mongo_db = PyMongo(app)


def data_store():
    return mongo2.DataStoreMongo(mongo_db.db)


from quakestats.web import (
    views,
    api,
)

app.json_encoder = api.QJsonEncoder
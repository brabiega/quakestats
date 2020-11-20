import logging

import pymongo

from quakestats.datasource.mongo2 import (
    DataStoreMongo,
)
from quakestats.system import (
    conf,
)

logger = logging.getLogger(__name__)


class SystemContext:
    def __init__(self):
        self.config = conf.cnf
        self.ds: DataStoreMongo = None
        self.ds_client: pymongo.MongoClient = None
        self.configure()

    def configure(self):
        uri = conf.get_conf_val('MONGO_URI')
        self.ds_client = pymongo.MongoClient(uri)
        parsed_uri = pymongo.uri_parser.parse_uri(uri)
        database_name = parsed_uri["database"]
        self.ds = DataStoreMongo(self.ds_client.get_database(database_name))

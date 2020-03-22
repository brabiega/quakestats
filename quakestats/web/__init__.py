from quakestats.web import (
    api,
)
from quakestats.web.app import (
    app,
    mongo_db,
    utils,
)

# FIXME mongo shouldn't exposed here
# for now it is due to fact that config file is loaded
# by flask
__all__ = ['app', 'api', 'mongo_db', 'utils']

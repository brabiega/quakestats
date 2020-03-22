"""
temporary 'bag' module to get rid of circular dependencies.
please get rid of it whenever possible
"""

import flask

from quakestats.dataprovider import (
    quake3,
)


class QJsonEncoder(flask.json.JSONEncoder):
    def default(self, o):  # pylint: disable=method-hidden
        # TODO too tightly coupled with internal data structures
        if isinstance(o, quake3.PlayerId):
            return str(o.steam_id)
        return flask.json.JSONEncoder.default(self, o)

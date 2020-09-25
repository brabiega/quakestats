# TODO refactor this relation...
from quakestats.web import (
    app,
)


def get_conf_val(key: str):
    return app.config[key]

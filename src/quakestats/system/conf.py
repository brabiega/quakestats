"""
We will use flask Config class as configuration
"""
import os

from flask import (
    Config,
)

ENV_VAR_NAME = "QUAKESTATS_SETTINGS"

cnf = Config(os.path.dirname(__file__))
cnf.from_envvar(variable_name=ENV_VAR_NAME)


def get_conf_val(key: str):
    return cnf[key]

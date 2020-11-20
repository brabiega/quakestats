"""
Base module for Q3 game parser
"""

import logging

from quakestats.core.q3parser.parser import (
    Q3Game,
)
from quakestats.core.q3toql.transform import (
    Q3toQL,
    QuakeGame,
)

logger = logging.getLogger(__name__)


class Q3toQLAPI():
    def transform(self, q3game: Q3Game) -> QuakeGame:
        tf = Q3toQL()
        return tf.transform(q3game)

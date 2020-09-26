import logging
import typing

from quakestats.datasource.entities import (
    Q3Match,
)
from quakestats.system.context import (
    SystemContext,
)

logger = logging.getLogger(__name__)


class QSSdk:
    def __init__(self, ctx: SystemContext):
        self.ctx = ctx

    def iter_matches(self, latest: typing.Optional[int] = None) -> typing.Iterator[Q3Match]:
        return self.ctx.ds.get_matches_n(latest=latest)

    def get_match(self, matchid: str):
        pass

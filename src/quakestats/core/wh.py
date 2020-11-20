"""
File based warehouse for raw log files/event files from quake matches
"""

import logging
import os
import typing
from datetime import (
    datetime,
)

logger = logging.getLogger(__name__)


class WarehouseItem():
    def __init__(self, identifier: str, path: str, ext: str):
        self.identifier = identifier
        self.ext = ext
        self.create_date: datetime = None
        self.path: str = path
        self.data: str = None  # use read_item to fetch the data

    def __repr__(self) -> str:
        return f"WarehouseItem({self.identifier}) - {self.ext} {self.create_date}"


class Warehouse():
    """
    Warehouse stores raw quake log/event files before conversion/analysis
    Such data can be used to rebuild the DB in case when some analysis logic changes
    """
    def __init__(self, datadir: str):
        self.datadir = datadir

    def _gen_path(self, identifier: str) -> str:
        return os.path.join(self.datadir, f"{identifier}.log")

    def iter_matches(self) -> typing.Iterator[WarehouseItem]:
        files = os.listdir(self.datadir)
        for fname in files:
            fbasename, fext = os.path.splitext(fname)
            path = os.path.join(self.datadir, fname)
            item = WarehouseItem(fbasename, path, fext.lstrip('.'))
            item.create_date = datetime.fromtimestamp(os.path.getctime(path))
            yield item

    def save_match_log(self, identifier: str, match_log: str):
        path = self._gen_path(identifier)
        if os.path.isfile(path):
            raise Exception(f"File already exists {path}")
        with open(path, 'w') as fh:
            fh.write(match_log)

    def read_item(self, item: WarehouseItem) -> WarehouseItem:
        with open(item.path) as fh:
            item.data = fh.read()

        return item

    def has_item(self, identifier: str) -> bool:
        path = self._gen_path(identifier)
        return os.path.exists(path)

    def delete_item(self, identifier: str):
        path = self._gen_path(identifier)
        os.remove(path)

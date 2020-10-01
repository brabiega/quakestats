"""
File based warehouse for log files/event files from quake matches
"""

import logging
import os
import typing

logger = logging.getLogger(__name__)


class WarehouseItem():
    def __init__(self, identifier: str, logtype: str, path: str):
        self.identifier = identifier
        self.logtype = logtype
        self.path: str = path
        self.data: str = None  # use read_item to fetch the data

    def __repr__(self) -> str:
        return f"WarehouseItem({self.identifier}, {self.logtype})"


class Warehouse():
    def __init__(self, datadir: str):
        self.datadir = datadir

    def iter_matches(self) -> typing.Iterator[WarehouseItem]:
        files = os.listdir(self.datadir)
        for fname in files:
            fbasename, fext = os.path.splitext(fname)
            yield WarehouseItem(fbasename, 'Q3-OSP', os.path.join(self.datadir, fname))

    def save_match_log(self, match_id: str, match_log: str):
        path = os.path.join(self.datadir, f"{match_id}.log")
        if os.path.isfile(path):
            raise Exception(f"File already exists {path}")
        with open(path, 'w') as fh:
            fh.write(match_log)

    def read_item(self, item: WarehouseItem) -> WarehouseItem:
        with open(item.path) as fh:
            item.data = fh.read()

        return item

"""
File based warehouse for log files/event files from quake matches
"""

import logging
import os

logger = logging.getLogger(__name__)


class WarehouseItem():
    def __init__(self, identifier: str, logtype: str):
        self.identifier = identifier
        self.logtype = logtype

    def __repr__(self) -> str:
        return f"WarehouseItem({self.identifier}, {self.logtype})"


class Warehouse():
    def __init__(self, datadir: str):
        self.datadir = datadir

    def list_matches(self):
        files = os.listdir(self.datadir)
        for fname in files:
            fbasename, fext = os.path.splitext(fname)
            yield WarehouseItem(fbasename, 'Q3-OSP')

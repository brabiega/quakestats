import os
import pytest

@pytest.fixture(scope='session')
def testdata_loader():
    class Loader():
        def __init__(self, filename, subdir=None):
            self.filename = filename
            self.subdir = subdir

        def _buildpath(self):
            if self.subdir:
                return os.path.join(os.path.dirname(__file__), 'data', self.subdir, self.filename)
            else:
                return os.path.join(os.path.dirname(__file__), 'data', self.filename)

        def read(self):           
            with open(self._buildpath()) as fh:
                return fh.read()
        
    return Loader
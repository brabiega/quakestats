from io import StringIO
from quakestats.dataprovider.quake3.logwatch import Q3LogWatcher


class TestQ3LogWatch():
    def test_read_changes_empty(self):
        watcher = Q3LogWatcher('path', 'token', 'endpoint')      
        fd = StringIO()

        result = watcher.read_changes(fd)
        assert result == []
        assert watcher._cursor_location == 0

        result = watcher.read_changes(fd)
        assert result == []
        assert watcher._cursor_location == 0

    def test_read_changes_sequential(self):
        watcher = Q3LogWatcher('path', 'token', 'endpoint')      
        fd = StringIO()

        result = watcher.read_changes(fd)
        assert result == []
        assert watcher._cursor_location == 0

        fd.write("Testing\nHalf writt\n")

        result = watcher.read_changes(fd)
        assert result == ['Testing']

        fd.seek(0)
        fd.write("Testing\nHalf written\n")

        result = watcher.read_changes(fd)
        assert result == ['Half written']
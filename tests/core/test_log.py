"""The log file of a build can be rotated while an earlier build in the process still writes to it."""

import logging

from kb4it.core.log import release_log_file


def test_release_log_file_closes_only_its_handlers(tmp_path):
    root = logging.getLogger()
    mine = logging.FileHandler(tmp_path / "kb4it.log", encoding="utf-8")
    other = logging.FileHandler(tmp_path / "other.log", encoding="utf-8")
    root.addHandler(mine)
    root.addHandler(other)
    try:
        release_log_file(tmp_path / "kb4it.log")
        assert mine not in root.handlers
        assert mine.stream is None
        assert other in root.handlers
        # Windows refuses to remove a file that a handler keeps open.
        (tmp_path / "kb4it.log").unlink()
    finally:
        for handler in (mine, other):
            handler.close()
            root.removeHandler(handler)

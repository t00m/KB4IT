#!/usr/bin/env python

"""
Polling file watcher used by `kb4it serve`.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

Polling needs no extra dependency and behaves the same on Linux, macOS and
Windows: every interval the watched files are listed with their size and
modification time, and any difference is a change. A burst of changes (an
editor writing several files, a git checkout) is collected until the tree has
been quiet for the debounce time, so it triggers one rebuild.
"""

import os
import time

from kb4it.core.log import get_logger

log = get_logger(__name__)

# Editor scratch files that must not trigger a rebuild.
_IGNORED_SUFFIXES = ("~", ".swp", ".swx", ".swo", ".tmp", ".part")
_IGNORED_PREFIXES = (".#", ".~lock.")
_IGNORED_NAMES = {"4913", ".DS_Store", "Thumbs.db"}
_IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache"}


def ignored(name: str) -> bool:
    """True for editor scratch files and system files that are not content."""
    return (name in _IGNORED_NAMES or name.startswith(_IGNORED_PREFIXES)
            or name.endswith(_IGNORED_SUFFIXES))


def snapshot(paths) -> dict:
    """Map every file under paths (files or folders, recursively) to (mtime_ns, size)."""
    state = {}
    for path in paths:
        path = str(path)
        if os.path.isfile(path):
            _add(state, path)
            continue
        for root, dirs, files in os.walk(path):
            dirs[:] = sorted(d for d in dirs if d not in _IGNORED_DIRS)
            for name in files:
                if not ignored(name):
                    _add(state, os.path.join(root, name))
    return state


def _add(state, path):
    try:
        info = os.stat(path)
    except OSError:
        return  # removed between listing and stat
    state[path] = (info.st_mtime_ns, info.st_size)


def diff(old: dict, new: dict) -> list:
    """Sorted paths added, removed or modified between two snapshots."""
    return sorted(p for p in old.keys() | new.keys() if old.get(p) != new.get(p))


class PollingWatcher:
    """Wait for changes under a set of files and folders."""

    def __init__(self, paths, interval=1.0, debounce=0.5):
        self.paths = [str(p) for p in paths if p]
        self.interval = interval
        self.debounce = debounce
        self.state = snapshot(self.paths)

    def wait(self, stop=None):
        """Block until something changes and stays quiet for the debounce time.

        Returns the changed paths, or None when stop (a threading.Event) is set.
        """
        while stop is None or not stop.is_set():
            time.sleep(self.interval)
            current = snapshot(self.paths)
            changed = set(diff(self.state, current))
            if not changed:
                continue
            # Collect the rest of the burst.
            while True:
                if stop is not None and stop.is_set():
                    return None
                time.sleep(self.debounce)
                later = snapshot(self.paths)
                more = diff(current, later)
                current = later
                if not more:
                    break
                changed.update(more)
            self.state = current
            log.debug(f"[WATCH] CHANGE files={len(changed)}")
            return sorted(changed)
        return None

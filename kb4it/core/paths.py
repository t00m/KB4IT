#!/usr/bin/env python

"""
Repository path helpers: resolve repo.json paths and check that the target folder is safe.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

from __future__ import annotations

import os
import sys
from typing import Union

from kb4it.core.exceptions import ConfigError

StrPath = Union[str, "os.PathLike[str]"]


def resolve_repo_path(raw: str, root: StrPath) -> str:
    """Expand ~ and $VARS and anchor a relative path to the repository root."""
    expanded = os.path.expanduser(os.path.expandvars(raw))
    if not os.path.isabs(expanded):
        expanded = os.path.join(str(root), expanded)
    return os.path.realpath(expanded)


def _key(path: StrPath) -> str:
    """Comparable form of path: real, absolute and, on Windows and macOS, case folded."""
    path = os.path.normcase(os.path.realpath(str(path)))
    if sys.platform == "darwin":
        path = path.lower()
    return path


def _inside(parent: str, child: str) -> bool:
    """Return True if child is parent or lives inside it (both already passed through _key)."""
    try:
        return os.path.commonpath([parent, child]) == parent
    except ValueError:  # different drives on Windows
        return False


def check_target(target: StrPath, root: StrPath, source: StrPath, home: StrPath | None = None) -> None:
    """Raise ConfigError if the target folder overlaps a folder KB4IT must never sweep.

    The deployer deletes pages from the target, so the target may not be, or hold, the
    repository root, the source folder, config/, var/, the home folder or a filesystem
    root; nor may it live inside the source folder.
    """
    home = os.path.expanduser("~") if home is None else home
    tkey = _key(target)
    anchor = os.path.splitdrive(tkey)[0] + os.sep
    if tkey == _key(anchor):
        raise ConfigError(f"Target folder {target} is a filesystem root; choose a folder of its own")
    protected = (
        ("repository root", root),
        ("source folder", source),
        ("config folder", os.path.join(str(root), "config")),
        ("var folder", os.path.join(str(root), "var")),
        ("home folder", home),
    )
    for name, path in protected:
        if _inside(tkey, _key(path)):
            raise ConfigError(f"Target folder {target} holds the {name} {path}; choose a folder of its own")
    if _inside(_key(source), tkey):
        raise ConfigError(f"Target folder {target} is inside the source folder {source}; move it out")

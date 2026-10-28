"""
Last-modified date of each document: the Modified key, else the last git commit, else the file time.

# File: moddates.py
# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

import os
import subprocess
from datetime import datetime
from typing import Any

from kb4it.core import trace
from kb4it.core.files import json_load, json_save
from kb4it.core.structured import iso_date

GIT_CACHE = "gitdates.json"
COMMIT_MARK = "\x00"  # git writes it for %x00; a file name cannot hold it


def _git(folder: str, *args: str) -> str | None:
    """Output of a git command run in folder, or None when git is missing or fails."""
    try:
        done = subprocess.run(["git", "-C", folder, *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=120, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def parse_log(text: str) -> dict[str, str]:
    """{file: date} from 'git log --name-only' output; the newest commit comes first and wins."""
    dates: dict[str, str] = {}
    date = ""
    for line in text.splitlines():
        if line.startswith(COMMIT_MARK):
            date = line[1:].strip()
        elif line and date and "/" not in line:
            dates.setdefault(line, date)
    return dates


def git_dates(source_dir: str, cache_file: str) -> dict[str, str]:
    """{file name in source_dir: ISO date of the last commit that touched it}; {} outside a git work tree.

    One 'git log' at most per build: the result is kept in cache_file for the current HEAD.
    """
    with trace.span("git_dates"):
        head = _git(source_dir, "rev-parse", "HEAD")
        if head is None:
            return {}
        head = head.strip()
        key = os.path.abspath(source_dir)
        cached: dict[str, Any] = {}
        if os.path.isfile(cache_file):
            try:
                cached = json_load(cache_file)
            except (OSError, ValueError):
                cached = {}
        if cached.get("head") == head and cached.get("source") == key and isinstance(cached.get("dates"), dict):
            return dict(cached["dates"])
        out = _git(source_dir, "-c", "core.quotepath=off", "log", "--relative", "--name-only", "--no-renames",
                   "--format=%x00%cI", "--", ".")
        if out is None:
            return {}
        dates = parse_log(out)
        try:
            json_save(cache_file, {"head": head, "source": key, "dates": dates})
        except OSError:
            pass
        return dates


def file_time(path: str) -> str:
    """Modification time of a file as an ISO date with the local offset; empty when it cannot be read."""
    try:
        stamp = os.path.getmtime(path)
    except OSError:
        return ""
    return datetime.fromtimestamp(stamp).astimezone().isoformat(timespec="seconds")


def with_zone(value: str) -> str:
    """An ISO date and time without an offset gets the local one; a plain date stays as it is."""
    if "T" not in value:
        return value
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        moment = moment.astimezone()
    return moment.isoformat(timespec="seconds")


def _moment(value: str) -> datetime:
    moment = datetime.fromisoformat(value)
    return moment if moment.tzinfo is not None else moment.astimezone()


def modified_date(modified: str, published: str, git: str, mtime: str) -> str:
    """dateModified of a document: Modified, else the git date, else the file time; never before Date.

    Every argument is a raw value or empty; the result is an ISO date, with an offset when it has a time.
    """
    value = iso_date(modified) if modified else ""
    value = with_zone(value) if value else (git or mtime)
    first = iso_date(published) if published else ""
    if first and (not value or _moment(value) < _moment(first)):
        value = with_zone(first)
    return value

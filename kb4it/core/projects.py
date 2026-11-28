#!/usr/bin/env python

"""
The list of projects in projects.json, shared by the command line and the TUI.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

Each entry has a display name, the absolute path of its repo.json and, when
the user gave one, a short id. The id works wherever a config path does.
Every change to the file runs under registry_lock().
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable

from kb4it.core.env import ENV
from kb4it.core.exceptions import KB4ITError
from kb4it.core.lock import registry_lock
from kb4it.core.log import get_logger, q
from kb4it.core.util import json_load, json_save, quarantine

PROJECTS_FILE = Path(ENV["LPATH"]["ROOT"]) / "projects.json"
ID_RE = re.compile(r"^[a-z][a-z0-9-]{0,31}$")

log = get_logger("PROJECTS")


class ProjectError(KB4ITError):
    """A project reference or id that cannot be used."""


def _load(on_corrupt: Callable[[str, Exception], None] | None = None, quarantine_bad: bool = True) -> list[dict]:
    path = Path(PROJECTS_FILE)
    if not path.exists():
        return []
    try:
        data = json_load(str(path))
        entries = data["projects"]
        if not isinstance(entries, list):
            raise TypeError("'projects' is not a list")
        return entries
    except (ValueError, KeyError, TypeError) as error:
        if not quarantine_bad:
            return []
        # Keep the unreadable file: the next save would otherwise replace the whole list.
        kept = quarantine(str(path))
        log.warning(f"[PROJECTS] PROJECTS_CORRUPT path={q(path)} kept={q(kept)} reason={q(error)}")
        if on_corrupt is not None:
            on_corrupt(kept, error)
        return []
    except OSError:
        return []


def _save(entries: list[dict]) -> None:
    path = Path(PROJECTS_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    json_save(str(path), {"projects": entries})


def load(on_corrupt: Callable[[str, Exception], None] | None = None, quarantine_bad: bool = True) -> list[dict]:
    """Every entry of projects.json.

    An unreadable file is renamed aside and gives []; on_corrupt(kept_path, error) is told so.
    With quarantine_bad=False it is left alone and nothing is logged, as shell completion needs.
    """
    return _load(on_corrupt, quarantine_bad)


def save(entries: list[dict]) -> None:
    """Write the whole list."""
    with registry_lock():
        _save(entries)


def _real(config: str) -> str:
    return os.path.realpath(os.path.expanduser(str(config)))


def id_problem(pid: str, entries: list[dict], config: str | None = None) -> str | None:
    """Why pid cannot be used as an id, or None when it can.

    An id already held by the entry of config itself is not taken.
    """
    if not ID_RE.match(pid or ""):
        return (f"Invalid id '{pid}': use 1 to 32 lowercase letters, digits and dashes, "
                "starting with a letter.")
    own = _real(config) if config else None
    for entry in entries:
        if entry.get("id") == pid and _real(entry.get("config", "")) != own:
            return f"The id '{pid}' is already used by {entry.get('name') or entry.get('config')}."
    return None


def find(ref: str, entries: list[dict] | None = None) -> dict | None:
    """The entry whose id is ref, else the one whose config is ref."""
    entries = load() if entries is None else entries
    for entry in entries:
        if entry.get("id") and entry.get("id") == ref:
            return entry
    real = _real(ref)
    for entry in entries:
        if _real(entry.get("config", "")) == real:
            return entry
    return None


def resolve(ref: str) -> str:
    """The config path for ref: an existing file as given, else the config of the id ref."""
    if os.path.isfile(ref) or not ID_RE.match(ref):
        # A path, even a missing one, goes on as given so the build reports it as before.
        return ref
    entry = next((e for e in load() if e.get("id") == ref), None)
    if entry is None:
        raise ProjectError(f"No project with id '{ref}' and no file '{ref}'. "
                           "Run 'kb4it projects' to see the ids.")
    config = entry.get("config", "")
    if not os.path.isfile(config):
        raise ProjectError(f"Project '{ref}' points to a missing file: {config}")
    return config


def root_of(config: str) -> Path:
    """Project folder: the parent of the config/ folder holding repo.json."""
    return Path(config).resolve().parent.parent


def _repo_dir(config: str, key: str) -> Path:
    value = json_load(str(config)).get(key) or key
    path = Path(os.path.expanduser(str(value)))
    return path if path.is_absolute() else root_of(config) / path


def source_dir(config: str) -> Path:
    """The source folder of repo.json, resolved against the project folder when relative."""
    return _repo_dir(config, "source")


def target_dir(config: str) -> Path:
    """The target folder of repo.json, resolved against the project folder when relative."""
    return _repo_dir(config, "target")


def _default_name(config: str) -> str:
    try:
        title = json_load(str(config)).get("title")
    except Exception:
        title = None
    return str(title) if title else root_of(config).name


def _abs(config: str) -> str:
    return os.path.abspath(os.path.expanduser(str(config)))


def register(config: str, name: str | None = None, pid: str | None = None) -> tuple[dict, list[str]]:
    """Add config to the list, or update its name and id; return the entry and what changed.

    The path is stored as given (made absolute), so delete sees a symlink; duplicates are found by real path.
    """
    real = _real(config)
    with registry_lock():
        entries = _load()
        if pid:
            problem = id_problem(pid, entries, real)
            if problem:
                raise ProjectError(problem)
        entry = next((e for e in entries if _real(e.get("config", "")) == real), None)
        changes: list[str] = []
        if entry is None:
            entry = {}
            if pid:
                entry["id"] = pid
            entry["name"] = name or _default_name(real)
            entry["config"] = _abs(config)
            entries.append(entry)
            changes = ["added"] + (["id"] if pid else [])
        else:
            if pid and entry.get("id") != pid:
                entry["id"] = pid
                changes.append("id")
            if name and entry.get("name") != name:
                entry["name"] = name
                changes.append("name")
        if changes:
            _save(entries)
    if "added" in changes:
        log.info(f"[PROJECTS] PROJECT_IMPORTED id={q(entry.get('id', ''))} name={q(entry['name'])} config={q(real)}")
    elif "id" in changes:
        log.info(f"[PROJECTS] PROJECT_ID_SET id={q(pid)} config={q(real)}")
    return entry, changes


def set_id(config: str, pid: str | None) -> dict:
    """Give the entry of config the id pid; None or '' removes the id."""
    real = _real(config)
    with registry_lock():
        entries = _load()
        if pid:
            problem = id_problem(pid, entries, real)
            if problem:
                raise ProjectError(problem)
        entry = next((e for e in entries if _real(e.get("config", "")) == real), None)
        if entry is None:
            raise ProjectError(f"Not in the list: {config}")
        if pid:
            entry["id"] = pid
        else:
            entry.pop("id", None)
        _save(entries)
    log.info(f"[PROJECTS] PROJECT_ID_SET id={q(pid or '')} config={q(real)}")
    return entry


def remove(config: str) -> dict | None:
    """Remove the entry of config from the list and return it; None when it is not listed."""
    real = _real(config)
    with registry_lock():
        entries = _load()
        entry = next((e for e in entries if _real(e.get("config", "")) == real), None)
        if entry is None:
            return None
        entries.remove(entry)
        _save(entries)
    log.info(f"[PROJECTS] PROJECT_REMOVED id={q(entry.get('id', ''))} config={q(real)}")
    return entry


def format_projects(entries: list[dict], table: bool) -> list[str]:
    """Lines for kb4it projects: an aligned table for a person, or id, name and config split by tabs."""
    if not table:
        return [f"{e.get('id', '')}\t{e.get('name', '')}\t{e.get('config', '')}" for e in entries]
    rows = [(e.get("id") or "-", e.get("name", ""), e.get("config", "")) for e in entries]
    wid = max([2] + [len(r[0]) for r in rows])
    wname = max([4] + [len(r[1]) for r in rows])
    lines = [f"{'ID':<{wid}}  {'Name':<{wname}}  Config", "-" * (wid + wname + 12)]
    lines += [f"{pid:<{wid}}  {name:<{wname}}  {config}" for pid, name, config in rows]
    return lines

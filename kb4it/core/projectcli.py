#!/usr/bin/env python

"""
Command line actions on the project list: kb4it import and kb4it delete.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

They need no services, so main() runs them directly, as it runs serve and help.
Each returns the exit status.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Callable

from kb4it.core import projects
from kb4it.core.env import ENV
from kb4it.core.exceptions import LockBusyError
from kb4it.core.lock import FileLock, read_holder, repo_lock_path
from kb4it.core.log import q
from kb4it.core.projects import ProjectError
from kb4it.core.util import json_load


def _label(entry: dict) -> str:
    return entry.get("id") or entry.get("name") or entry.get("config", "")


def run_import(params: dict) -> int:
    """Add an existing knowledge base to the list, or set the id and name of a listed one."""
    config = os.path.abspath(os.path.expanduser(params["config"]))
    try:
        repo = json_load(config)
    except (OSError, ValueError) as error:
        print(f"Error: cannot read {config}: {error}", file=sys.stderr)
        return 1
    if not isinstance(repo, dict) or not repo.get("theme"):
        print(f"Error: {config} is not a KB4IT repo.json (no theme)", file=sys.stderr)
        return 1
    try:
        entry, changes = projects.register(config, name=params.get("name"), pid=params.get("id"))
    except ProjectError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    if "added" in changes:
        print(f"Imported {_label(entry)}: {entry['name']} ({entry['config']})")
    elif changes:
        print(f"Updated {_label(entry)}: {', '.join(changes)}")
    else:
        print(f"Already in the list as {_label(entry)}")
    return 0


def _protected() -> list[Path]:
    return [Path(os.path.realpath(p)) for p in (os.sep, str(Path.home()), ENV["LPATH"]["ROOT"])]


def delete_refusal(root: Path, config: str) -> str | None:
    """Why the project folder root must not be deleted, as a reason code, or None."""
    real_config = Path(os.path.realpath(config))
    if real_config.parent.name != "config" or not real_config.is_file():
        return "no_config"
    root = Path(os.path.realpath(root))
    for folder in _protected():
        if root == folder or root in folder.parents:
            return "protected_folder"
    try:
        FileLock(repo_lock_path(real_config)).acquire().release()
    except LockBusyError:
        return "locked"
    return None


REFUSALS = {
    "no_config": "it has no config/ folder holding the repo.json of this project",
    "protected_folder": "it is, or contains, /, your home folder or the KB4IT folder",
    "locked": "KB4IT is working on it",
}


def run_delete(params: dict, ask: Callable[[str], str] = input, interactive: bool | None = None) -> int:
    """Remove a project from the list; with files, delete its folder first."""
    ref = params["project"]
    entries = projects.load()
    # As everywhere else, an existing file wins over an id.
    if os.path.isfile(ref):
        entry = projects.find(os.path.realpath(ref), entries)
    else:
        entry = next((e for e in entries if e.get("id") == ref), None)
    if entry is None:
        if os.path.isfile(ref):
            print(f"Error: Not in the list: {ref}", file=sys.stderr)
        else:
            print(f"Error: No project with id '{ref}' and no file '{ref}'. "
                  "Run 'kb4it projects' to see the ids.", file=sys.stderr)
        return 1
    config = entry["config"]
    root = projects.root_of(config)
    label = _label(entry)
    if not params.get("files"):
        projects.remove(config)
        print(f"Removed {label} from the list; files kept in {root}")
        return 0

    reason = delete_refusal(root, config)
    if reason:
        projects.log.warning(f"[PROJECTS] PROJECT_DELETE_REFUSED id={q(entry.get('id', ''))} "
                             f"path={q(root)} reason={reason}")
        extra = ""
        if reason == "locked":
            pid = read_holder(repo_lock_path(os.path.realpath(config)))
            extra = f" (PID {pid})" if pid else ""
        print(f"Error: will not delete {root}: {REFUSALS[reason]}{extra}", file=sys.stderr)
        return 1

    count = sum(len(files) for _dir, _dirs, files in os.walk(root))
    expected = entry.get("id") or root.name
    if not params.get("yes"):
        if interactive is None:
            interactive = sys.stdin.isatty()
        if not interactive:
            print("Error: deleting files needs a terminal to confirm, or --yes", file=sys.stderr)
            return 1
        print(f"This deletes {root} and its {count} files.")
        try:
            answer = ask(f"Type {expected} to confirm: ")
        except EOFError:
            answer = ""
        if (answer or "").strip() != expected:
            print("Cancelled; nothing was deleted.")
            return 1

    try:
        target = projects.target_dir(config).resolve()
    except Exception:
        target = None
    try:
        shutil.rmtree(root)
    except OSError as error:
        print(f"Error: could not delete {root}: {error}. {label} stays in the list.", file=sys.stderr)
        return 1
    projects.remove(config)
    projects.log.info(f"[PROJECTS] PROJECT_FILES_DELETED id={q(entry.get('id', ''))} path={q(root)} files={count}")
    print(f"Deleted {root} ({count} files) and removed {label} from the list")
    if target is not None and root not in target.parents and target != root and target.exists():
        print(f"The target folder is outside the project and was kept: {target}")
    return 0

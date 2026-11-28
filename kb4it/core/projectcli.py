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


def _lock_problem(lock: FileLock) -> str | None:
    """Take lock; the reason code when that fails, else None."""
    try:
        lock.acquire()
    except LockBusyError:
        return "locked"
    except OSError:
        return "no_access"
    return None


def delete_refusal(root: Path, config: str) -> str | None:
    """Why the project folder root must not be deleted, as a reason code, or None."""
    cfg = Path(os.path.abspath(config))
    if cfg.parent.name != "config" or not cfg.is_file():
        return "no_config"
    # A link would make KB4IT delete the folder it points to, not the one the user sees.
    if any(os.path.islink(path) for path in (cfg, cfg.parent, root)):
        return "symlink"
    real_root = Path(os.path.realpath(root))
    for folder in _protected():
        if real_root == folder or real_root in folder.parents:
            return "protected_folder"
    lock_file = repo_lock_path(cfg)
    if os.path.exists(lock_file):  # no lock file means no build; do not create one just to look
        lock = FileLock(lock_file)
        problem = _lock_problem(lock)
        lock.release()
        if problem:
            return problem
    return None


REFUSALS = {
    "no_config": "it has no config/ folder holding the repo.json of this project",
    "symlink": "its config/repo.json, config/ or the folder itself is a symbolic link",
    "protected_folder": "it is, or contains, /, your home folder or the KB4IT folder",
    "locked": "KB4IT is working on it",
    "no_access": "its lock file cannot be opened",
}


def _refuse(entry: dict, root: Path, config: str, reason: str) -> int:
    projects.log.warning(f"[PROJECTS] PROJECT_DELETE_REFUSED id={q(entry.get('id', ''))} "
                         f"path={q(root)} reason={reason}")
    extra = ""
    if reason == "locked":
        pid = read_holder(repo_lock_path(os.path.abspath(config)))
        extra = f" (PID {pid})" if pid else ""
    print(f"Error: will not delete {root}: {REFUSALS[reason]}{extra}", file=sys.stderr)
    return 1


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
            entry = projects.find(ref, entries)  # a listed project whose files are already gone
    if entry is None:
        if os.path.isfile(ref):
            print(f"Error: Not in the list: {ref}", file=sys.stderr)
        else:
            print(f"Error: No project with id '{ref}' and no file '{ref}'. "
                  "Run 'kb4it projects' to see the ids.", file=sys.stderr)
        return 1
    config = entry["config"]
    root = Path(os.path.abspath(config)).parent.parent
    label = _label(entry)
    if not params.get("files"):
        projects.remove(config)
        print(f"Removed {label} from the list; files kept in {root}")
        return 0

    reason = delete_refusal(root, config)
    if reason:
        return _refuse(entry, root, config, reason)

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
    # Hold the build lock from here on, so no build can start while the folder goes away.
    lock = FileLock(repo_lock_path(os.path.abspath(config)))
    problem = _lock_problem(lock)
    if problem:
        return _refuse(entry, root, config, problem)
    try:
        if sys.platform == "win32":
            lock.release()  # Windows cannot delete a file that is open
        shutil.rmtree(root)
    except OSError as error:
        print(f"Error: could not delete {root}: {error}. {label} stays in the list.", file=sys.stderr)
        return 1
    finally:
        lock.release()
    projects.remove(config)
    projects.log.info(f"[PROJECTS] PROJECT_FILES_DELETED id={q(entry.get('id', ''))} path={q(root)} files={count}")
    print(f"Deleted {root} ({count} files) and removed {label} from the list")
    if target is not None and root not in target.parents and target != root and target.exists():
        print(f"The target folder is outside the project and was kept: {target}")
    return 0

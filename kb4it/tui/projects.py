"""
Project registry and the themes and apps KB4IT ships.
"""

from __future__ import annotations

import logging
from pathlib import Path

from kb4it.core.env import ENV
from kb4it.core.util import json_load, json_save, quarantine

PROJECTS_FILE = Path(ENV["LPATH"]["ROOT"]) / "projects.json"


VERSION = ENV["APP"]["version"]


def load_projects() -> list[dict]:
    if not PROJECTS_FILE.exists():
        return []
    try:
        data = json_load(str(PROJECTS_FILE))
        projects = data["projects"]
        if not isinstance(projects, list):
            raise TypeError("'projects' is not a list")
        return projects
    except (ValueError, KeyError, TypeError) as error:
        # Keep the unreadable file: the next save would otherwise replace the whole list.
        kept = quarantine(str(PROJECTS_FILE))
        logging.getLogger(__name__).warning(f"[TUI] PROJECTS_CORRUPT path={PROJECTS_FILE} kept={kept} reason={error}")
        return []
    except OSError:
        return []


def save_projects(projects: list[dict]) -> None:
    from kb4it.core.lock import registry_lock
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with registry_lock():
        json_save(str(PROJECTS_FILE), {"projects": projects})


def get_themes() -> list[dict]:
    themes: list[dict] = []
    seen_ids: set[str] = set()
    for scope, base in [
        ("global", ENV["GPATH"]["THEMES"]),
        ("local", ENV["LPATH"]["THEMES"]),
    ]:
        base_path = Path(base)
        if not base_path.exists():
            continue
        for entry in sorted(base_path.iterdir()):
            if not entry.is_dir():
                continue
            tfile = entry / "theme.json"
            if not tfile.exists():
                continue
            try:
                data = json_load(str(tfile))
                tid = data.get("id", entry.name)
                if tid in seen_ids:
                    continue
                seen_ids.add(tid)
                data["_scope"] = scope
                data["version"] = VERSION  # every theme listed has KB4IT\'s version
                data["_path"] = str(entry)
                themes.append(data)
            except Exception:
                pass
    return themes


def get_apps(theme_name: str) -> list[str]:
    apps: list[str] = []
    seen: set[str] = set()
    for base in [ENV["GPATH"]["THEMES"], ENV["LPATH"]["THEMES"]]:
        apps_path = Path(base) / theme_name / "apps"
        if not apps_path.exists():
            continue
        for entry in sorted(apps_path.iterdir()):
            if entry.is_dir() and entry.name not in seen:
                seen.add(entry.name)
                apps.append(entry.name)
    return apps


def _project_root(config_path: str) -> Path:
    """Project root is the parent of the config/ directory holding repo.json."""
    return Path(config_path).resolve().parent.parent


def _resolve_repo_path(config_path: str, value: str) -> Path:
    """Resolve a value from repo.json (may be relative) against the project root."""
    p = Path(value)
    return p if p.is_absolute() else _project_root(config_path) / p


def _log_path(config_path: str) -> Path | None:
    try:
        p = _project_root(config_path) / "var" / "log" / "kb4it.log"
        return p if p.exists() else None
    except Exception:
        return None


def _kbdict_path(config_path: str) -> Path | None:
    try:
        p = _project_root(config_path) / "var" / "db" / "kbdict.json"
        return p if p.exists() else None
    except Exception:
        return None

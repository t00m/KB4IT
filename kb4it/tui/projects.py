"""
Project registry and the themes and apps KB4IT ships.
"""

from __future__ import annotations

from pathlib import Path

from kb4it.core.env import ENV
from kb4it.core.projects import PROJECTS_FILE, root_of  # noqa: F401  PROJECTS_FILE is a public name
from kb4it.core.projects import load as load_projects  # noqa: F401  public name
from kb4it.core.projects import save as save_projects  # noqa: F401  public name
from kb4it.core.util import json_load
from kb4it.core.version import theme_fingerprint

VERSION = ENV["APP"]["version"]
BUILD_VERSION = ENV["APP"]["build_version"]  # shown in titles, so a development build is identifiable (BI-08)


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
                data["version"] = data.get("version") or "unversioned"  # the theme's own version (TV-01)
                data["fingerprint"] = _fingerprint(entry, data)
                data["_path"] = str(entry)
                themes.append(data)
            except Exception:
                pass
    return themes


def _fingerprint(theme_dir: Path, data: dict) -> str:
    """The theme fingerprint, as the build computes it (TV-03)."""
    base = data.get("template_base")
    base_dir = Path(ENV["GPATH"]["BASES"]) / base / "templates" if isinstance(base, str) and base else None
    return theme_fingerprint(theme_dir, base_dir if base_dir and base_dir.is_dir() else None,
                             ENV["GPATH"]["TEMPLATES"])


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
    return root_of(config_path)


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

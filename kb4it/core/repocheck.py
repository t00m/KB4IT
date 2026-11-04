"""
Check the text of a repo.json the way a build reads it, without building.

The TUI editor saves a repo.json only when check_repo() finds no problem. Each step calls
the loader the build uses, so the check accepts what the build accepts. The only step it
does not repeat is running the hooks file: it checks that the file exists.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from kb4it.core.exceptions import KB4ITError

REQUIRED_KEYS = ("title", "theme", "source", "target")


def _parse(text: str) -> tuple[dict | None, list[str]]:
    """The settings in the text, or None and the reason it is not a JSON object."""
    try:
        repo = json.loads(text)
    except json.JSONDecodeError as error:
        return None, [f"Not valid JSON: {error.msg} (line {error.lineno}, column {error.colno})"]
    if not isinstance(repo, dict):
        return None, ["repo.json must be a JSON object, between { and }"]
    return repo, []


def _required(repo: dict) -> list[str]:
    return [f"'{key}' is required and must be a non-empty text"
            for key in REQUIRED_KEYS
            if not isinstance(repo.get(key), str) or not repo[key].strip()]


def _theme(repo: dict, root: Path) -> list[str]:
    """The theme must be found where the build looks for it (Frontend.theme_search)."""
    from kb4it.core.env import ENV
    from kb4it.core.paths import resolve_repo_path
    raw = repo.get("theme_path")
    if raw is not None:
        if not isinstance(raw, str) or not raw.strip():
            return ["repo.json 'theme_path' must be a non-empty string"]
        folder = resolve_repo_path(raw, root)
        if not os.path.isfile(os.path.join(folder, "theme.json")):
            return [f"theme_path does not contain theme.json: {folder}"]
        return []
    theme = repo["theme"]
    places = (os.path.join(resolve_repo_path(repo["source"], root), "resources", "themes"),
              ENV["LPATH"]["THEMES"], ENV["GPATH"]["THEMES"])
    if any(os.path.isfile(os.path.join(place, theme, "theme.json")) for place in places):
        return []
    return [f"Theme '{theme}' not found in {', '.join(str(place) for place in places)}"]


def _folders(repo: dict, root: Path) -> list[str]:
    from kb4it.core.paths import check_target, resolve_repo_path
    source = resolve_repo_path(repo["source"], root)
    target = resolve_repo_path(repo["target"], root)
    problems = [] if os.path.isdir(source) else [f"Source folder {source} does not exist"]
    try:
        check_target(target, root, source)
    except KB4ITError as error:
        problems.append(str(error))
    return problems


def _hooks(repo: dict, root: Path) -> list[str]:
    value = repo.get("hooks")
    if value in (None, ""):
        return []
    if not isinstance(value, str):
        return ["repo.json 'hooks' must be the path of a Python file"]
    from kb4it.core.paths import resolve_repo_path
    path = resolve_repo_path(value, root)
    return [] if os.path.isfile(path) else [f"Hooks file not found: {path}"]


def _loaders(repo: dict) -> list[str]:
    """Run the build's own loaders; each raises with the reason when its block is wrong."""
    from kb4it.core.dateclass import date_reserved_names, load_dates
    from kb4it.core.mdconfig import load_settings
    from kb4it.core.profiles import load_profiles
    from kb4it.core.publish import site_url
    from kb4it.core.structured import load_seo
    from kb4it.services.addpage import check_editor_setting

    def overrides(repo: dict) -> None:
        value = repo.get("overrides", "overrides")
        if not isinstance(value, str) or not value.strip():
            raise ValueError("repo.json 'overrides' must be a folder path")

    steps = (
        check_editor_setting,
        load_settings,
        site_url,
        overrides,
        load_seo,
        load_profiles,
        lambda repo: load_dates(repo, reserved_names=date_reserved_names(repo)),
    )
    problems = []
    for step in steps:
        try:
            step(repo)
        except Exception as error:  # noqa: BLE001 - any failure is a problem to show, never a crash
            problems.append(str(error))
    return problems


def check_repo(text: str, config_path: str | os.PathLike) -> list[str]:
    """Problems that would stop a build with this repo.json text; an empty list means it passes.

    config_path is where the file lives (config/repo.json), to resolve the folders against the
    repository root.
    """
    repo, problems = _parse(text)
    if repo is None:
        return problems
    problems = _required(repo)
    if problems:
        return problems
    root = Path(config_path).absolute().parent.parent
    problems += _theme(repo, root)
    problems += _folders(repo, root)
    problems += _hooks(repo, root)
    problems += _loaders(repo)
    return problems


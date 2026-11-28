#!/usr/bin/env python

"""
Shell completion for the kb4it command line.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

argcomplete asks the parser for the words that complete the one under the
cursor. The theme and app arguments come from the installed themes, so the
lists stay correct without a generated script. Without argcomplete installed
`enable()` does nothing and the command line works as before.
"""

from __future__ import annotations

import os
from typing import Any

from kb4it.core.env import ENV


def installed_themes() -> list[str]:
    """Theme ids installed for the user or shipped with KB4IT."""
    names: set[str] = set()
    for root in (ENV["GPATH"]["THEMES"], ENV["LPATH"]["THEMES"]):
        try:
            names.update(
                entry for entry in os.listdir(root)
                if os.path.isdir(os.path.join(root, entry))
            )
        except OSError:
            continue
    return sorted(names)


def apps_of(theme: str) -> list[str]:
    """Sample apps inside an installed theme."""
    for root in (ENV["LPATH"]["THEMES"], ENV["GPATH"]["THEMES"]):
        apps_dir = os.path.join(root, theme, "apps")
        try:
            return sorted(
                entry for entry in os.listdir(apps_dir)
                if os.path.isdir(os.path.join(apps_dir, entry))
            )
        except OSError:
            continue
    return []


def theme_completer(prefix: str, **kwargs: Any) -> list[str]:
    """Complete `create` and `apps` with the installed theme ids."""
    return [name for name in installed_themes() if name.startswith(prefix)]


def local_theme_completer(prefix: str, **kwargs: Any) -> list[str]:
    """Complete `uninstall-theme` with the ids of the user's own themes."""
    from kb4it.core.themeinstall import local_themes
    return [name for name in local_themes() if name.startswith(prefix)]


def app_completer(prefix: str, **kwargs: Any) -> list[str]:
    """Complete `create`'s app from the theme already typed, else from every theme."""
    parsed = kwargs.get("parsed_args")
    # argparse puts the word after the theme in repo_path while the path is still missing,
    # so a repo_path here means the app is already typed and the cursor is on the path.
    if getattr(parsed, "repo_path", None) is not None:
        return []
    theme = getattr(parsed, "theme", None)
    themes = [theme] if theme else installed_themes()
    names = {name for item in themes for name in apps_of(item)}
    return [name for name in sorted(names) if name.startswith(prefix)]


def enable(parser: Any) -> None:
    """Answer a shell completion request; must run before parse_args()."""
    try:
        import argcomplete
    except ImportError:
        return
    argcomplete.autocomplete(parser)


def _ids(prefix: str) -> list[str]:
    from kb4it.core import projects
    return [e["id"] for e in projects.load(quarantine_bad=False) if e.get("id", "").startswith(prefix)]


def id_completer(prefix: str, **kwargs: Any) -> list[str]:
    """Complete `search -p` with the project ids."""
    try:
        return _ids(prefix)
    except Exception:
        return []


def project_completer(prefix: str, **kwargs: Any) -> list[str]:
    """Complete a project reference with the ids and the file paths."""
    try:
        from argcomplete.completers import FilesCompleter
        return _ids(prefix) + list(FilesCompleter()(prefix))
    except Exception:
        return []


def _index_of(refs: list[str]) -> dict:
    """key -> value -> paths for the projects refs, merged."""
    from kb4it.core import projects
    from kb4it.core.explore import index, read_properties
    merged: dict = {}
    for ref in refs:
        try:
            data = index(read_properties(projects.resolve(ref))[0])
        except Exception:
            continue  # one moved or broken project must not stop completion for the others
        for key, by_value in data.items():
            merged.setdefault(key, {}).update(by_value)
    return merged


def key_completer(prefix: str, **kwargs: Any) -> list[str]:
    """Complete `keys`' property name from the project's documents."""
    try:
        data = _index_of([kwargs["parsed_args"].project])
        return sorted(k for k in data if k.startswith(prefix))
    except Exception:
        return []


def value_completer(prefix: str, **kwargs: Any) -> list[str]:
    """Complete `keys`' value from the values of the property already typed."""
    try:
        from kb4it.core.explore import matching
        parsed = kwargs["parsed_args"]
        data = _index_of([parsed.project])
        values = {v for k in matching(data, parsed.key) for v in data[k]}
        return sorted(v for v in values if v.startswith(prefix))
    except Exception:
        return []


def where_completer(prefix: str, **kwargs: Any) -> list[str]:
    """Complete `search --where` as KEY= and then KEY=VALUE, from the -p projects or every project."""
    try:
        from kb4it.core import projects
        from kb4it.core.explore import matching
        refs = (getattr(kwargs.get("parsed_args"), "projects", None)
                or [e["config"] for e in projects.load(quarantine_bad=False)])
        data = _index_of(refs)
        if "=" not in prefix:
            return sorted(f"{k}=" for k in data if k.startswith(prefix))
        key, _sep, start = prefix.partition("=")
        values = {v for k in matching(data, key) for v in data[k]}
        return sorted(f"{key}={v}" for v in values if v.startswith(start))
    except Exception:
        return []

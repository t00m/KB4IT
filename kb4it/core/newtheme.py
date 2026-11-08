#!/usr/bin/env python

"""
kb4it new-theme: copy a starter theme (kb4it/resources/starters/) under a new id.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

from __future__ import annotations

import json
import os
import shutil
import sys

from kb4it.core.env import ENV
from kb4it.core.exceptions import ThemeError
from kb4it.core.themeinstall import THEME_ID_RE, bundled_version

STARTERS = os.path.join(ENV["GPATH"]["RESOURCES"], "starters")


def _rewrite_json(path: str, **values: str) -> None:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    data.update(values)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=4, ensure_ascii=False)
        fh.write("\n")


def create_theme(theme_id: str, plain: bool = False, dest: str | None = None) -> str:
    """Copy starter-plain (plain) or starter-docs into dest/<theme_id>; return that folder.

    dest defaults to the user's themes folder. Nothing is written when theme_id is not a plain
    lower-case id, names a bundled theme, or the folder exists.
    """
    if not isinstance(theme_id, str) or not THEME_ID_RE.fullmatch(theme_id):
        raise ThemeError(f"'{theme_id}' is not a theme id: use lower-case letters, digits, '-' and '_'")
    if bundled_version(theme_id) is not None:
        raise ThemeError(f"'{theme_id}' is a bundled theme; choose another id")
    parent = os.path.abspath(dest or ENV["LPATH"]["THEMES"])
    folder = os.path.join(parent, theme_id)
    if os.path.lexists(folder):
        raise ThemeError(f"{folder} exists; remove it or choose another id")
    starter = os.path.join(STARTERS, "starter-plain" if plain else "starter-docs")
    os.makedirs(parent, exist_ok=True)
    shutil.copytree(starter, folder, ignore=shutil.ignore_patterns("__pycache__", "target", "var"))
    _rewrite_json(os.path.join(folder, "theme.json"), id=theme_id, name=theme_id.capitalize())
    sample = os.path.join(folder, "apps", "default", "config", "repo.json")
    if os.path.isfile(sample):
        _rewrite_json(sample, theme=theme_id)
    return folder


def run_new_theme(params: dict) -> int:
    """CLI: create the theme and say what to do next; 1 with the reason when it is refused."""
    try:
        folder = create_theme(params["id"], plain=params.get("plain", False), dest=params.get("dir"))
    except ThemeError as error:
        print(f"Error: {error}")
        return 1
    print(f"Theme {params['id']} created in {folder}")
    if os.path.dirname(folder) == os.path.abspath(ENV["LPATH"]["THEMES"]):
        print(f"Try it: kb4it create {params['id']} default ~/my-site && kb4it build ~/my-site/config/repo.json")
    else:
        print(f'To build with it, add "theme_path": "{folder}" to the repo.json of a site.')
    sys.stdout.flush()
    return 0

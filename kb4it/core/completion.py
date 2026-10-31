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


def app_completer(prefix: str, **kwargs: Any) -> list[str]:
    """Complete `create`'s app from the theme already typed, else from every theme."""
    parsed = kwargs.get("parsed_args")
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

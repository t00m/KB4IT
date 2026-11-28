#!/usr/bin/env python

"""
kb4it install-theme and kb4it uninstall-theme.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

from __future__ import annotations

import sys
from typing import Callable

from kb4it.core import themeinstall
from kb4it.core.exceptions import LockBusyError
from kb4it.core.themeinstall import ThemeInstallError


def install_lines(result: themeinstall.InstallResult) -> list[str]:
    """What install-theme prints after a successful install."""
    line = f"Installed {result.id} {result.version} in {result.path}"
    if result.replaced:
        line += f", replacing {result.replaced}"
    lines = [line]
    if result.bundled:
        lines.append(f"It takes the place of the bundled {result.id} {result.bundled} in every build.")
    return lines


def project_warning(theme_id: str, users: list[dict]) -> str | None:
    """What uninstalling theme_id means for the listed projects that use it."""
    if not users:
        return None
    names = ", ".join(entry.get("id") or entry.get("name") or entry["config"] for entry in users)
    bundled = themeinstall.bundled_version(theme_id)
    if bundled:
        return f"These projects will use the bundled {theme_id} {bundled} again: {names}"
    return f"These projects use {theme_id}; their builds will fail until it is installed again: {names}"


def run_install_theme(params: dict) -> int:
    try:
        result = themeinstall.install(params["source"])
    except (ThemeInstallError, LockBusyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    for line in install_lines(result):
        print(line)
    return 0


def run_uninstall_theme(params: dict, ask: Callable[[str], str] = input,
                        interactive: bool | None = None) -> int:
    theme_id = params["id"]
    try:
        folder = themeinstall.local_theme(theme_id)
    except ThemeInstallError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    warning = project_warning(theme_id, themeinstall.projects_using(theme_id))
    if warning:
        print(warning)
    if not params.get("yes"):
        if interactive is None:
            interactive = sys.stdin.isatty()
        if not interactive:
            print("Error: uninstalling a theme needs a terminal to confirm, or --yes", file=sys.stderr)
            return 1
        print(f"This deletes {folder}.")
        try:
            answer = ask(f"Type {theme_id} to confirm: ")
        except EOFError:
            answer = ""
        if (answer or "").strip() != theme_id:
            print("Cancelled; nothing was removed.")
            return 1
    try:
        version = themeinstall.uninstall(theme_id)
    except (ThemeInstallError, LockBusyError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Uninstalled {theme_id} {version} from {folder}")
    bundled = themeinstall.bundled_version(theme_id)
    if bundled:
        print(f"Builds now use the bundled {theme_id} {bundled}.")
    return 0

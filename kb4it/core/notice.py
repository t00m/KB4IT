#!/usr/bin/env python

"""
First-run help notice.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

Owns the notice text, the online URL, the offline index lookup and the marker
file that hides the notice once the user dismisses it.
"""

import os
from importlib import resources
from pathlib import Path

from kb4it.core.env import ENV

HELP_ONLINE_URL = "https://t00m.github.io/KB4IT/"
MARKER_NAME = "help-notice-dismissed"


def offline_index() -> Path | None:
    override = os.environ.get("KB4IT_HELP_INDEX")
    if override:
        path = Path(override)
        return path if path.is_file() else None
    try:
        path = Path(str(resources.files("kb4it").joinpath("resources", "help", "index.html")))
    except (ModuleNotFoundError, FileNotFoundError):
        return None
    return path if path.is_file() else None


def help_notice_lines(offline: Path | None, online_url: str) -> list[str]:
    where = f"offline: {offline}, online: {online_url}" if offline else f"online: {online_url}"
    return [
        f"KB4IT has a help center. Run 'kb4it help' to open it ({where}).",
        "Run 'kb4it help --dismiss' to hide this notice.",
    ]


def _marker() -> Path:
    # Read at call time so tests can relocate KB4IT_HOME.
    return Path(ENV["LPATH"]["ROOT"]) / MARKER_NAME


def help_notice_dismissed() -> bool:
    return _marker().exists()


def dismiss_help_notice() -> None:
    marker = _marker()
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()

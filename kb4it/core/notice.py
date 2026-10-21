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
        # Absolute, so as_uri() works; .html only, so the browser gets a web page.
        path = Path(override).expanduser().resolve()
        return path if path.suffix.lower() == ".html" and path.is_file() else None
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


def help_notice_visible() -> bool:
    """True when the notice should be shown: not dismissed and not running under CI."""
    return not os.environ.get("CI") and not help_notice_dismissed()


def run_help(url: bool = False, dismiss: bool = False) -> int:
    """Run 'kb4it help' and return the process exit code."""
    if url:
        print(HELP_ONLINE_URL)
        return 0
    if dismiss:
        try:
            dismiss_help_notice()
        except OSError as error:
            print(f"Cannot dismiss the help notice: {error}")
            return 1
        print("Help notice dismissed.")
        return 0
    index = offline_index()
    if index is None:
        print("No offline help copy found. Build it with scripts/help/build_offline.py "
              f"or read the online help at {HELP_ONLINE_URL}")
        return 1
    import webbrowser
    if not webbrowser.open(index.as_uri()):
        print(f"Could not start a browser. Open this file manually: {index}")
    return 0

#!/usr/bin/env python

"""
Install a theme from a zip file or an https URL, and uninstall it.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

A theme zip holds one top folder named as the id in its theme.json. The theme
goes into the local themes folder (ENV["LPATH"]["THEMES"]). Every check runs
before anything changes there, so a refused zip leaves the folder as it was.
"""

from __future__ import annotations

import json
import re
import stat
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from kb4it.core.env import ENV
from kb4it.core.exceptions import KB4ITError
from kb4it.core.log import get_logger
from kb4it.core.version import requirement_satisfied

log = get_logger("THEMES")

THEME_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
MAX_ENTRIES = 10_000
MAX_UNPACKED = 200 * 1024 * 1024
_DRIVE_RE = re.compile(r"^[A-Za-z]:")


class ThemeInstallError(KB4ITError):
    """A theme could not be installed or uninstalled; reason is a short code."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason


@dataclass
class ThemeZip:
    top: str
    theme: dict
    members: list[zipfile.ZipInfo] = field(default_factory=list)


def _name(info: zipfile.ZipInfo) -> str:
    """Member name with backslashes read as folder separators."""
    return info.filename.replace("\\", "/")


def _is_macosx(name: str) -> bool:
    return name == "__MACOSX" or name.startswith("__MACOSX/")


def _check_entry(info: zipfile.ZipInfo, name: str) -> list[str]:
    """Parts of a safe member name; raises unsafe_entry otherwise."""
    if name.startswith("/") or _DRIVE_RE.match(name):
        raise ThemeInstallError("unsafe_entry", f"The zip has an absolute path: {info.filename}")
    parts = [part for part in name.split("/") if part not in ("", ".")]
    if ".." in parts:
        raise ThemeInstallError("unsafe_entry", f"The zip has a path that leaves its folder: {info.filename}")
    if stat.S_ISLNK(info.external_attr >> 16):
        raise ThemeInstallError("unsafe_entry", f"The zip has a symbolic link: {info.filename}")
    return parts


def _top_folder(entries: list[tuple[zipfile.ZipInfo, list[str]]]) -> str:
    """The single top folder of the zip; raises layout otherwise."""
    tops = sorted({parts[0] for _, parts in entries if parts})
    if len(tops) != 1:
        found = ", ".join(tops) or "nothing"
        raise ThemeInstallError(
            "layout", f"The zip must hold one top folder with the theme in it; found: {found}")
    for info, parts in entries:
        if len(parts) == 1 and not info.is_dir():
            raise ThemeInstallError(
                "layout", f"The zip must hold one top folder; {info.filename} is a file at its root")
    return tops[0]


def _read_theme_json(archive: zipfile.ZipFile, entries, top: str) -> dict:
    wanted = f"{top}/theme.json"
    for info, parts in entries:
        if "/".join(parts) == wanted:
            try:
                data = json.loads(archive.read(info).decode("utf-8"))
            except (ValueError, UnicodeDecodeError, zipfile.BadZipFile) as error:
                raise ThemeInstallError("bad_theme_json", f"{wanted} is not valid JSON: {error}") from None
            if not isinstance(data, dict):
                raise ThemeInstallError("bad_theme_json", f"{wanted} must be a JSON object")
            if not isinstance(data.get("id"), str):
                raise ThemeInstallError("bad_theme_json", f"{wanted} needs an 'id' text")
            return data
    elsewhere = sorted(("/".join(parts) for _, parts in entries if parts and parts[-1] == "theme.json"),
                       key=lambda name: (name.count("/"), name))
    hint = f"; found {elsewhere[0]} instead" if elsewhere else ""
    raise ThemeInstallError("no_theme_json", f"The zip has no {wanted}{hint}")


def _check_theme(theme: dict, top: str) -> None:
    theme_id = theme["id"]
    if theme_id != top:
        raise ThemeInstallError(
            "id_mismatch",
            f"The top folder '{top}' must equal the id in theme.json, which is '{theme_id}'")
    if not THEME_ID_RE.match(theme_id):
        raise ThemeInstallError(
            "bad_id",
            f"Theme id '{theme_id}' is not valid: use lowercase letters, digits, '-' and '_', "
            "starting with a letter or a digit, at most 64 characters")
    spec = theme.get("kb4it")
    if spec is None:
        return
    version = ENV["APP"]["version"]
    try:
        satisfied = requirement_satisfied(spec, version)
    except (ValueError, TypeError, AttributeError):
        raise ThemeInstallError("requirement", f"theme.json has an invalid kb4it requirement: {spec!r}") from None
    if not satisfied:
        raise ThemeInstallError("requirement", f"Theme '{theme_id}' needs KB4IT {spec}; this is {version}")


def inspect_zip(path: str | Path) -> ThemeZip:
    """Check a theme zip without unpacking it; raises ThemeInstallError when it is not installable."""
    path = Path(path)
    if not path.is_file() or not zipfile.is_zipfile(path):
        raise ThemeInstallError("not_a_zip", f"Not a zip file: {path}")
    try:
        archive = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as error:
        raise ThemeInstallError("not_a_zip", f"Cannot read the zip {path}: {error}") from None
    with archive:
        entries = []
        for info in archive.infolist():
            name = _name(info)
            if _is_macosx(name):
                continue
            entries.append((info, _check_entry(info, name)))
        if len(entries) > MAX_ENTRIES:
            raise ThemeInstallError("too_large", f"The zip has {len(entries)} entries; the limit is {MAX_ENTRIES}")
        size = sum(info.file_size for info, _ in entries)
        if size > MAX_UNPACKED:
            raise ThemeInstallError(
                "too_large", f"The zip unpacks to {size} bytes; the limit is {MAX_UNPACKED}")
        top = _top_folder(entries)
        theme = _read_theme_json(archive, entries, top)
    _check_theme(theme, top)
    return ThemeZip(top=top, theme=theme, members=[info for info, _ in entries])

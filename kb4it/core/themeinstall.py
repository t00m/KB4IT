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

import errno
import http.client
import json
import os
import re
import secrets
import shutil
import stat
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from kb4it.core.env import ENV
from kb4it.core.exceptions import KB4ITError
from kb4it.core.lock import _TimedLock
from kb4it.core.log import get_logger, q
from kb4it.core.version import requirement_satisfied

log = get_logger("THEMES")

THEME_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
MAX_ENTRIES = 10_000
MAX_UNPACKED = 200 * 1024 * 1024
LOCK_TIMEOUT = 10.0
MAX_DOWNLOAD = 100 * 1024 * 1024
DOWNLOAD_TIMEOUT = 60
_CHUNK = 64 * 1024
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


@dataclass
class InstallResult:
    id: str
    version: str
    path: Path
    replaced: str | None
    bundled: str | None


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
            except (RuntimeError, NotImplementedError) as error:
                raise ThemeInstallError("not_a_zip", f"Cannot read {wanted}, encrypted or compressed in an unsupported way: {error}") from None
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
    if not THEME_ID_RE.fullmatch(theme_id):
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
    if not path.is_file():
        raise ThemeInstallError("not_a_zip", f"No such file: {path}")
    if not zipfile.is_zipfile(path):
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


def themes_dir() -> Path:
    return Path(ENV["LPATH"]["THEMES"])


def themes_lock() -> _TimedLock:
    """Lock around every change in the local themes folder."""
    return _TimedLock(os.path.join(ENV["LPATH"]["VAR"], "themes.lock"), LOCK_TIMEOUT)


def tmp_dir() -> Path:
    """Folder for downloads and unpacked zips, created when missing."""
    path = Path(ENV["LPATH"]["VAR"]) / "tmp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _version(theme: dict) -> str:
    version = theme.get("version")
    return str(version) if version not in (None, "") else "unversioned"


def _version_in(folder: Path) -> str:
    """Version in folder/theme.json, or 'unversioned' when it has none or cannot be read."""
    try:
        data = json.loads((folder / "theme.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "unversioned"
    return _version(data) if isinstance(data, dict) else "unversioned"


def bundled_version(theme_id: str) -> str | None:
    """Version of the bundled theme with this id, or None when KB4IT bundles none."""
    folder = Path(ENV["GPATH"]["THEMES"]) / theme_id
    if not (folder / "theme.json").is_file():
        return None
    return _version_in(folder)


def _move(src: Path, dst: Path) -> None:
    """Rename src to dst; copy across disks when a rename cannot."""
    try:
        os.replace(src, dst)
    except OSError as error:
        if error.errno != errno.EXDEV:
            raise
        shutil.move(str(src), str(dst))


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _extract(path: Path, info: ThemeZip, work: Path) -> None:
    """Unpack the checked members of the zip into work."""
    try:
        with zipfile.ZipFile(path) as archive:
            for member in info.members:
                parts = _check_entry(member, _name(member))
                target = work.joinpath(*parts)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    except (zipfile.BadZipFile, EOFError, RuntimeError, NotImplementedError) as error:
        raise ThemeInstallError("not_a_zip", f"Cannot unpack {path}: {error}") from None
    except OSError as error:
        raise ThemeInstallError("install", f"Cannot unpack {path}: {error}") from None


def _swap(new: Path, theme_id: str) -> str | None:
    """Put new in place of the local theme theme_id; return the replaced version, if any."""
    themes = themes_dir()
    try:
        themes.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise ThemeInstallError("install", f"Cannot create the themes folder {themes}: {error}") from None
    target = themes / theme_id
    with themes_lock():
        old = None
        replaced = None
        if target.exists() or target.is_symlink():
            replaced = _version_in(target)
            old = tmp_dir() / f"old-{theme_id}-{secrets.token_hex(4)}"
            try:
                _move(target, old)
            except OSError as error:
                raise ThemeInstallError("install", f"Cannot move the old {theme_id} away: {error}") from None
        try:
            _move(new, target)
        except OSError as error:
            if old is not None:
                try:
                    _move(old, target)
                except OSError:
                    raise ThemeInstallError(
                        "install", f"Cannot put {theme_id} in {themes}: {error}. "
                        f"The old copy could not be put back either; it is in {old}") from None
            raise ThemeInstallError("install", f"Cannot put {theme_id} in {themes}: {error}") from None
        if old is not None:
            _remove(old)
    return replaced


def install_zip(path: str | Path, source: str | None = None) -> InstallResult:
    """Install the theme in the zip at path into the local themes folder."""
    path = Path(path)
    source = source or str(path)
    work = None
    try:
        info = inspect_zip(path)
        theme_id = info.top
        work = Path(tempfile.mkdtemp(prefix=f"install-{theme_id}-", dir=tmp_dir()))
        _extract(path, info, work)
        replaced = _swap(work / theme_id, theme_id)
    except ThemeInstallError as error:
        log.info(f"[THEMES] THEME_INSTALL_REFUSED reason={error.reason} source={q(source)}")
        raise
    finally:
        if work is not None:
            shutil.rmtree(work, ignore_errors=True)
    version = _version(info.theme)
    log.info(f"[THEMES] THEME_INSTALLED id={theme_id} version={q(version)} "
             f"replaced={q(replaced or '')} source={q(source)}")
    return InstallResult(id=theme_id, version=version, path=themes_dir() / theme_id,
                         replaced=replaced, bundled=bundled_version(theme_id))


class _HttpsOnlyRedirect(urllib.request.HTTPRedirectHandler):
    """Follow a redirect only when it leads to another https URL."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.lower().startswith("https://"):
            raise ThemeInstallError("insecure_url", f"The download redirects to a URL that is not https: {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open(url: str, timeout: int):
    """Open url for reading, following https redirects only."""
    opener = urllib.request.build_opener(_HttpsOnlyRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": f"KB4IT/{ENV['APP']['version']}"})
    return opener.open(request, timeout=timeout)


def _is_url(source: str) -> bool:
    return source.lower().startswith(("http://", "https://"))


def download(url: str) -> Path:
    """Download the zip at an https URL into the temporary folder and return its path."""
    if not url.lower().startswith("https://"):
        raise ThemeInstallError(
            "insecure_url", f"Only https:// URLs are accepted; a theme runs code at build time: {url}")
    target = tmp_dir() / f"download-{secrets.token_hex(4)}.zip"
    try:
        deadline = time.monotonic() + DOWNLOAD_TIMEOUT
        with _open(url, DOWNLOAD_TIMEOUT) as response, open(target, "wb") as out:
            size = 0
            while True:
                if time.monotonic() > deadline:
                    raise ThemeInstallError("download", f"Cannot download {url}: it took more than {DOWNLOAD_TIMEOUT} seconds")
                chunk = response.read(_CHUNK)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_DOWNLOAD:
                    raise ThemeInstallError(
                        "too_large", f"The download is larger than the limit of {MAX_DOWNLOAD} bytes")
                out.write(chunk)
    except ThemeInstallError:
        target.unlink(missing_ok=True)
        raise
    except (OSError, ValueError, urllib.error.URLError, http.client.HTTPException) as error:
        target.unlink(missing_ok=True)
        raise ThemeInstallError("download", f"Cannot download {url}: {error}") from None
    return target


def install(source: str) -> InstallResult:
    """Install a theme from a zip path or an https URL."""
    if not _is_url(source):
        return install_zip(source)
    try:
        path = download(source)
    except ThemeInstallError as error:
        log.info(f"[THEMES] THEME_INSTALL_REFUSED reason={error.reason} source={q(source)}")
        raise
    try:
        return install_zip(path, source=source)
    finally:
        path.unlink(missing_ok=True)


def local_themes() -> list[str]:
    """Names of the folders in the local themes folder that hold a theme.json."""
    try:
        names = os.listdir(themes_dir())
    except OSError:
        return []
    return sorted(name for name in names if (themes_dir() / name / "theme.json").is_file())


def local_theme(theme_id: str) -> Path:
    """Folder of the local theme theme_id; raises bundled or not_installed when there is none."""
    # Compare with the listing, so an id such as '..' never reaches a path.
    if theme_id in local_themes():
        return themes_dir() / theme_id
    if THEME_ID_RE.fullmatch(theme_id) and bundled_version(theme_id) is not None:
        raise ThemeInstallError("bundled", f"{theme_id} is bundled with KB4IT and cannot be removed")
    raise ThemeInstallError("not_installed", f"Theme {theme_id} is not installed in {themes_dir()}")


def projects_using(theme_id: str) -> list[dict]:
    """Listed projects whose repo.json uses theme_id; unreadable configs are skipped."""
    from kb4it.core import projects
    found = []
    for entry in projects.load(quarantine_bad=False):
        try:
            data = json.loads(Path(entry["config"]).read_text(encoding="utf-8"))
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if isinstance(data, dict) and data.get("theme") == theme_id:
            found.append(entry)
    return found


def uninstall(theme_id: str) -> str:
    """Remove the local theme theme_id and return its version."""
    with themes_lock():
        folder = local_theme(theme_id)
        version = _version_in(folder)
        old = tmp_dir() / f"old-{theme_id}-{secrets.token_hex(4)}"
        try:
            _move(folder, old)
        except OSError as error:
            raise ThemeInstallError("install", f"Cannot remove {folder}: {error}") from None
        _remove(old)
    log.info(f"[THEMES] THEME_UNINSTALLED id={theme_id} version={q(version)}")
    return version

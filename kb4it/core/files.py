"""
File helpers: file names, copy and delete, JSON files, quarantine and hashes.

# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from kb4it.core.log import get_logger

log = get_logger("Util")

# Sources are read with utf-8-sig: identical to utf-8, but drops the byte order mark some Windows
# editors write, which would otherwise hide the opening "---". Text mode turns CRLF into LF.
SOURCE_ENCODING = "utf-8-sig"


def valid_filename(s: object) -> str:
    """Return a clean filename.

    Remove leading and trailing spaces; convert other spaces to
    underscores; remove anything that is not an alphanumeric, dash,
    underscore, or dot; and drop leading dots, so the name is never hidden
    (".note") nor a relative path ("..").
    >>> valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    Borrowed from:
    https://github.com/django/django/blob/master/django/utils/text.py
    """
    s = str(s).strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w.]", "", s).lstrip(".")


def get_source_docs(path: str) -> list[str]:
    """Get source documents (.md, .markdown) from a given path."""
    docs = []
    for ext in ("*.md", "*.markdown"):
        docs.extend(glob.glob(os.path.join(path, ext)))
    return docs


def copy_docs(docs: list[str], target: str) -> None:
    """Copy a list of docs to target directory."""
    for doc in docs:
        try:
            shutil.copy(doc, target)
            log.debug(f"Copied {doc} to {target}")
        except FileNotFoundError:
            log.warning(f"File {doc} not found")
    log.debug(f"{len(docs)} documents copied to '{target}'")


def copydir(source: str, dest: str, keep_existing: bool = False) -> None:
    """Copy a directory structure overwriting existing files.

    With keep_existing, a file already in dest is left as it is.

    https://gist.github.com/dreikanter/5650973#gistcomment-835606
    """
    for root, dirs, files in os.walk(source):
        if not os.path.isdir(root):
            os.makedirs(root, exist_ok=True)

        for file in files:
            rel_path = root.replace(source, "").lstrip(os.sep)
            dest_path = os.path.join(dest, rel_path)

            if keep_existing and os.path.exists(os.path.join(dest_path, file)):
                log.info(f"[FILES] KEEP_EXISTING path={os.path.join(dest_path, file)}")
                continue

            if not os.path.isdir(dest_path):
                os.makedirs(dest_path, exist_ok=True)

            try:
                shutil.copyfile(os.path.join(root, file),
                                os.path.join(dest_path, file))
            except PermissionError:
                log.warning(f"Check permissions for file {file}")


def sync_file(source: str, dest: str) -> bool:
    """Copy source to dest unless dest has the same size and modification time; return True when copied.

    The copy keeps the modification time (shutil.copy2), so the next build sees an unchanged file and skips it.
    Raise FileNotFoundError when source does not exist.
    """
    src = os.stat(source)
    try:
        dst = os.stat(dest)
    except FileNotFoundError:
        pass
    else:
        if src.st_size == dst.st_size and src.st_mtime_ns == dst.st_mtime_ns:
            return False
    shutil.copy2(source, dest)
    return True


def prune_tree(dest: str, keep: Iterable[str]) -> int:
    """Delete every file and folder under dest whose absolute path is not in keep; return the files deleted.

    A folder survives while it holds something kept. Symbolic links are removed, never followed.
    """
    deleted = 0
    dest = os.path.normpath(os.fspath(dest))
    keep = {os.path.normpath(k) for k in keep}
    if not os.path.isdir(dest) or os.path.islink(dest):
        return deleted
    for root, dirs, files in os.walk(dest, topdown=False):
        for name in files:
            path = os.path.join(root, name)
            if path not in keep:
                os.unlink(path)
                deleted += 1
        for name in dirs:
            path = os.path.join(root, name)
            if os.path.islink(path):
                if path not in keep:
                    os.unlink(path)
                    deleted += 1
            elif path not in keep:
                try:
                    os.rmdir(path)
                except OSError:
                    pass  # it still holds a kept file
    return deleted


def sync_tree(source: str, dest: str, mirror: bool = True, keep: Iterable[str] = ()) -> tuple[int, int, set[str]]:
    """Copy the new and changed files of source into dest; with mirror, delete what source does not have.

    keep lists absolute paths another owner fills: they are never deleted nor overwritten. A missing source
    counts as an empty folder. Return (files copied, files deleted, absolute paths of the files source provides).
    """
    source = os.path.normpath(os.fspath(source))
    dest = os.path.normpath(os.fspath(dest))
    wanted = {}
    folders = set()
    if os.path.isdir(source):
        for root, _dirs, files in os.walk(source):
            rel = os.path.relpath(root, source)
            folder = dest if rel == os.curdir else os.path.join(dest, rel)
            folders.add(folder)
            for name in files:
                wanted[os.path.join(folder, name)] = os.path.join(root, name)
    keep = {os.path.normpath(k) for k in keep}
    deleted = 0
    if mirror:
        # Delete first, so a file that became a folder (or the reverse) does not block the copy.
        deleted = prune_tree(dest, set(wanted) | folders | keep)
        for folder in folders:
            if os.path.lexists(folder) and (os.path.islink(folder) or not os.path.isdir(folder)):
                os.unlink(folder)
                deleted += 1
        for path in wanted:
            if os.path.isdir(path) and not os.path.islink(path):
                deleted += prune_tree(path, ())
                os.rmdir(path)
    copied = 0
    for folder in sorted(folders):
        os.makedirs(folder, exist_ok=True)
    for target, origin in wanted.items():
        if target in keep:
            continue
        try:
            copied += sync_file(origin, target)
        except PermissionError:
            log.warning(f"Check permissions for file {target}")
    return copied, deleted, set(wanted)


def delete_target_contents(target_path: str) -> bool:
    """Delete contents from target directory."""
    error = False
    if os.path.exists(target_path):
        if os.path.isdir(target_path):
            for file_object in os.listdir(target_path):
                file_object_path = os.path.join(target_path, file_object)
                if os.path.isfile(file_object_path):
                    os.unlink(file_object_path)
                else:
                    shutil.rmtree(file_object_path)
        elif os.path.isfile(target_path):
            os.unlink(target_path)
    else:
        log.error(f"Target path {target_path} does not exist")
        error = True
    return error


def delete_files(files: Iterable[str]) -> None:
    """Delete a list of given files."""
    for path in files:
        try:
            if os.path.exists(path):
                os.unlink(path)
        except FileNotFoundError as error:
            log.warning("[UTIL] - %s", error)
            log.warning("[UTIL] - %s", path)


def json_load(filepath: str | os.PathLike[str]) -> dict[str, Any]:
    """Load into a dictionary a file in json format (a repo.json saved with a byte order mark loads too)."""
    with open(filepath, "r", encoding=SOURCE_ENCODING) as fin:
        adict: dict[str, Any] = json.load(fin)
    return adict


def json_save(filepath: str, adict: dict[str, Any]) -> None:
    """Save dictionary into a file in json format.

    The data goes to a temporary file in the same folder, which then replaces the
    old file in one step: a crash or a full disk leaves the old file whole.
    """
    folder = os.path.dirname(os.path.abspath(filepath))
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fout:
            json.dump(adict, fout, sort_keys=True, indent=4)
            fout.flush()
            os.fsync(fout.fileno())
        # mkstemp makes the file private; keep the mode a plain open() would give.
        if os.path.exists(filepath):
            mode = os.stat(filepath).st_mode & 0o777
        else:
            umask = os.umask(0)
            os.umask(umask)
            mode = 0o666 & ~umask
        os.chmod(tmp, mode)
        os.replace(tmp, filepath)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def quarantine(filepath: str) -> str:
    """Rename a file that cannot be read to <name>.corrupt-<timestamp>, so it is never overwritten.

    Returns the new path.
    """
    dest = f"{filepath}.corrupt-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    n = 1
    while os.path.exists(dest):
        n += 1
        dest = f"{filepath}.corrupt-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{n}"
    os.replace(filepath, dest)
    return dest


def get_hash_from_content(content: str) -> str:
    """Get the blake2b hash for any string."""
    return hashlib.blake2b(content.encode("utf-8")).hexdigest()


def get_hash_from_file(path: str) -> str | None:
    """Get the blake2b hash for a given filename."""
    if os.path.exists(path):
        with open(path, "rb") as fin:
            fhash = hashlib.file_digest(fin, "blake2b").hexdigest()
    else:
        fhash = None
    return fhash


def tree_hash(path: str | os.PathLike[str] | None) -> str:
    """Hash of every file name and content under path; '' when path is missing."""
    if not path or not os.path.isdir(path):
        return ""
    digest = hashlib.blake2b()
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for name in sorted(files):
            full = os.path.join(root, name)
            digest.update(os.path.relpath(full, path).replace(os.sep, "/").encode("utf-8"))
            with open(full, "rb") as fh:
                digest.update(fh.read())
    return digest.hexdigest()


def get_hash_from_dict(adict: dict[str, Any]) -> str:
    """Get the blake2b hash for a given dictionary."""
    serialized = json.dumps(adict, sort_keys=True, ensure_ascii=False)
    return hashlib.blake2b(serialized.encode("utf-8")).hexdigest()


def get_hash_from_list(alist: list[Any]) -> str:
    """Get the blake2b hash for a given list."""
    serialized = json.dumps(alist, ensure_ascii=False)
    return hashlib.blake2b(serialized.encode("utf-8")).hexdigest()

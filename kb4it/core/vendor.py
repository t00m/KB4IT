"""Shared vendor libraries (P6).

Each library lives once in kb4it/resources/vendor/<name>/. A theme lists the names it
uses in the 'assets' key of its theme.json; the deployer copies those folders into
<target>/resources/vendor/ and templates link them from there.
"""

import os

from kb4it.core.env import ENV
from kb4it.core.exceptions import ThemeError
from kb4it.core.files import prune_tree, sync_tree

VENDOR_DIR = os.path.join(ENV["GPATH"]["RESOURCES"], "vendor")


def vendor_names() -> list[str]:
    """Sorted names of the bundled libraries; [] when the folder is missing."""
    if not os.path.isdir(VENDOR_DIR):
        return []
    return sorted(name for name in os.listdir(VENDOR_DIR) if os.path.isdir(os.path.join(VENDOR_DIR, name)))


def theme_assets(theme: dict) -> list[str]:
    """The validated 'assets' list of a theme.json dict; [] when the key is missing.

    "search": true adds the search library: the shared search box links it, and themes written
    before 'assets' existed must keep a working search.
    """
    assets = theme.get("assets")
    if assets is None:
        return ["search"] if theme.get("search") is True and "search" in vendor_names() else []
    if not isinstance(assets, list) or not all(isinstance(name, str) for name in assets):
        raise ThemeError("theme.json 'assets' must be a list of names")
    known = set(vendor_names())
    for name in assets:
        if name not in known:
            raise ThemeError(f"theme.json 'assets': unknown vendor library: {name}")
    if theme.get("search") is True and "search" not in assets:
        return [*assets, "search"]
    return list(assets)


def vendor_paths(names) -> list[str]:
    """Folder of each named library, in the given order."""
    return [os.path.join(VENDOR_DIR, name) for name in names]


def sync_vendor(dest: str, names, keep=()) -> tuple[int, int, set[str]]:
    """Mirror the named libraries into dest (target/resources/vendor) and delete any other entry there.

    keep lists repository files that are never deleted. Return (files copied, files deleted, files provided).
    """
    keep = {os.path.normpath(k) for k in keep}
    copied = deleted = 0
    provided = set()
    for name in names:
        n_copied, n_deleted, files = sync_tree(os.path.join(VENDOR_DIR, name), os.path.join(dest, name), keep=keep)
        copied += n_copied
        deleted += n_deleted
        provided |= files
    if os.path.isdir(dest):
        for entry in os.listdir(dest):
            path = os.path.join(dest, entry)
            if entry in names or path in keep:
                continue
            if os.path.isdir(path) and not os.path.islink(path):
                deleted += prune_tree(path, keep)
                if not os.listdir(path):
                    os.rmdir(path)
            else:
                os.unlink(path)
                deleted += 1
        if not os.listdir(dest):
            os.rmdir(dest)
    return copied, deleted, provided

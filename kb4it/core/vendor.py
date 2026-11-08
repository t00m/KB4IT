"""Shared vendor libraries (P6).

Each library lives once in kb4it/resources/vendor/<name>/. A theme lists the names it
uses in the 'assets' key of its theme.json; the deployer copies those folders into
<target>/resources/vendor/ and templates link them from there.
"""

import os

from kb4it.core.env import ENV
from kb4it.core.exceptions import ThemeError

VENDOR_DIR = os.path.join(ENV["GPATH"]["RESOURCES"], "vendor")


def vendor_names() -> list[str]:
    """Sorted names of the bundled libraries; [] when the folder is missing."""
    if not os.path.isdir(VENDOR_DIR):
        return []
    return sorted(name for name in os.listdir(VENDOR_DIR) if os.path.isdir(os.path.join(VENDOR_DIR, name)))


def theme_assets(theme: dict) -> list[str]:
    """The validated 'assets' list of a theme.json dict; [] when the key is missing."""
    assets = theme.get("assets")
    if assets is None:
        return []
    if not isinstance(assets, list) or not all(isinstance(name, str) for name in assets):
        raise ThemeError("theme.json 'assets' must be a list of names")
    known = set(vendor_names())
    for name in assets:
        if name not in known:
            raise ThemeError(f"theme.json 'assets': unknown vendor library: {name}")
    return list(assets)


def vendor_paths(names) -> list[str]:
    """Folder of each named library, in the given order."""
    return [os.path.join(VENDOR_DIR, name) for name in names]

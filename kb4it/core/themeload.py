#!/usr/bin/env python

"""
Load the logic/ folder of a theme as a Python package.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

Every theme names its main module ``theme.py``, and many name their helpers the same
way (``config.py``, ``nav.py``). Putting logic/ on ``sys.path`` made the first theme
loaded own those names for the whole process. Here logic/ becomes a package with a
name of its own, ``kb4it_theme_<id>_<8 hex of the path>``, so:

- ``from .admin import AdminFeature`` works inside a theme;
- two themes, or two copies of one theme, never share a module;
- loading a theme again (terminal interface, ``kb4it serve``) runs its files again.

Bare imports of a sibling module (``from techdoc_admin import AdminMixin``) keep
working through a meta path finder limited to the files of the loaded logic/ folders.
The module is loaded once, as ``<package>.<name>``, and the bare name points to it.
"""

from __future__ import annotations

import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import os
import re
import sys
import threading
from importlib.machinery import ModuleSpec
from types import ModuleType
from typing import Any, Callable, Sequence

PREFIX = "kb4it_theme_"


def package_name(theme_id: str, logic: str) -> str:
    """The package name of a logic/ folder: theme id plus 8 hex digits of its absolute path."""
    safe = re.sub(r"\W", "_", theme_id or "theme")
    digest = hashlib.sha1(os.path.abspath(logic).encode("utf-8")).hexdigest()[:8]
    return f"{PREFIX}{safe}_{digest}"


def _sibling(logic: str, name: str) -> bool:
    """True when logic/ holds a module or a package called name."""
    return (os.path.isfile(os.path.join(logic, f"{name}.py"))
            or os.path.isfile(os.path.join(logic, name, "__init__.py")))


def _siblings(logic: str) -> list[str]:
    """The modules of logic/ a bare import may name; never one of the standard library."""
    names = set()
    for entry in os.listdir(logic):
        name = entry[:-3] if entry.endswith(".py") else entry
        if (name.isidentifier() and name != "__init__" and name not in sys.stdlib_module_names
                and _sibling(logic, name)):
            names.add(name)
    return sorted(names)


def _from_theme(module: Any) -> bool:
    """True when module was loaded from a theme logic/ folder (by this module or from sys.path)."""
    if getattr(module, "__name__", "").startswith(PREFIX):
        return True
    folder = os.path.dirname(getattr(module, "__file__", None) or "")
    return os.path.basename(folder) == "logic" and os.path.isfile(os.path.join(folder, "theme.py"))


class _BareLoader(importlib.abc.Loader):
    """Give the module already loaded as <package>.<name> to a bare import of <name>."""

    def __init__(self, qualified: str) -> None:
        self.qualified = qualified
        self.real_spec: ModuleSpec | None = None

    def create_module(self, spec: ModuleSpec) -> ModuleType:
        module = importlib.import_module(self.qualified)
        self.real_spec = module.__spec__
        return module

    def exec_module(self, module: ModuleType) -> None:
        # module_from_spec() replaced __spec__ with the bare one; relative imports need the real one.
        module.__spec__ = self.real_spec


class _BareFinder(importlib.abc.MetaPathFinder):
    """Resolve a top-level import to the sibling module of a loaded theme package."""

    def __init__(self) -> None:
        self.names: dict[str, str] = {}          # bare name -> package
        self.notify: dict[str, Callable[[str], None]] = {}   # package -> callback
        self.seen: set[tuple[str, str]] = set()
        self.lock = threading.Lock()

    def find_spec(self, fullname: str, path: Sequence[str] | None = None,
                  target: ModuleType | None = None) -> ModuleSpec | None:
        if path is not None or "." in fullname:
            return None
        package = self.names.get(fullname)
        if package is None:
            return None
        with self.lock:
            first = (package, fullname) not in self.seen
            self.seen.add((package, fullname))
        callback = self.notify.get(package)
        if first and callback is not None:
            callback(fullname)
        return importlib.machinery.ModuleSpec(fullname, _BareLoader(f"{package}.{fullname}"))


_FINDER = _BareFinder()


def _install_finder() -> None:
    if _FINDER not in sys.meta_path:
        sys.meta_path.insert(0, _FINDER)


def _purge(package: str, logic: str) -> None:
    """Forget every module of package, and any bare-named module a sibling of logic/ would shadow."""
    for name in [n for n in sys.modules if n == package or n.startswith(package + ".")]:
        del sys.modules[name]
    for name in [n for n, owner in _FINDER.names.items() if owner == package]:
        del _FINDER.names[name]
    _FINDER.seen = {pair for pair in _FINDER.seen if pair[0] != package}
    for name in _siblings(logic):
        if name in sys.modules and _from_theme(sys.modules[name]):
            del sys.modules[name]


def _new_package(package: str, logic: str) -> ModuleType:
    init = os.path.join(logic, "__init__.py")
    spec: ModuleSpec | None
    if os.path.isfile(init):
        spec = importlib.util.spec_from_file_location(package, init, submodule_search_locations=[logic])
        if spec is None:
            raise ImportError(f"cannot load {init}")
    else:
        spec = importlib.machinery.ModuleSpec(package, None, is_package=True)
        spec.submodule_search_locations = [logic]
    module = importlib.util.module_from_spec(spec)
    sys.modules[package] = module
    try:
        if spec.loader is not None:
            spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[package]
        raise
    return module


def load_package(logic: str, theme_id: str, on_bare_import: Callable[[str], None] | None = None) -> str:
    """Load logic/ afresh as its own package and return the package name.

    Modules an earlier load of the same folder left in sys.modules are dropped first, so
    the theme's files run again. on_bare_import(name) is called the first time a module of
    this package is imported by its bare name.
    """
    logic = os.path.abspath(logic)
    if not os.path.isdir(logic):
        raise ImportError(f"theme logic folder not found: {logic}")
    package = package_name(theme_id, logic)
    importlib.invalidate_caches()  # files added to logic/ since the last load must be found
    _install_finder()
    _purge(package, logic)
    _new_package(package, logic)
    for name in _siblings(logic):
        _FINDER.names[name] = package
    if on_bare_import is None:
        _FINDER.notify.pop(package, None)
    else:
        _FINDER.notify[package] = on_bare_import
    return package


def load_module(logic: str, theme_id: str, name: str = "theme",
                on_bare_import: Callable[[str], None] | None = None) -> ModuleType:
    """Load logic/ afresh as a package and import its module name (theme.py by default)."""
    package = load_package(logic, theme_id, on_bare_import)
    return importlib.import_module(f"{package}.{name}")


def is_theme_module(module_name: str) -> bool:
    """True for a module loaded from a theme's logic/ folder by this module."""
    return module_name.startswith(PREFIX)

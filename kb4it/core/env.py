#!/usr/bin/python
"""
Environment module.

# File: mod_env.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: Environment variables module
"""

import multiprocessing
import os
import platform
import sys
from os.path import abspath
from pathlib import Path

from kb4it.core.version import build_info


class FrozenDict(dict):
    """A dict subclass that can be frozen to block further mutation.

    All existing dict read operations (ENV["KEY"], ENV.get(), iteration)
    work without modification. After freeze() is called, any attempt to
    set or delete a top-level key raises TypeError. Unknown key access
    raises KeyError with the list of valid keys so typos are caught early.
    """

    def __init__(self, *args, **kwargs):
        self._frozen = False
        super().__init__(*args, **kwargs)

    def freeze(self):
        self._frozen = True

    def __setitem__(self, key, value):
        if self._frozen:
            raise TypeError(f"ENV is frozen; cannot set key '{key}'")
        super().__setitem__(key, value)

    def __delitem__(self, key):
        if self._frozen:
            raise TypeError(f"ENV is frozen; cannot delete key '{key}'")
        super().__delitem__(key)

    def __missing__(self, key):
        raise KeyError(f"ENV has no key '{key}'. Valid keys: {sorted(self.keys())}")


def platform_family(name=None) -> str:
    """Return 'linux', 'darwin', 'windows' or 'other' for sys.platform (or name)."""
    name = sys.platform if name is None else name
    if name.startswith("linux"):
        return "linux"
    if name == "darwin":
        return "darwin"
    if name in ("win32", "cygwin"):
        return "windows"
    return "other"


def platform_description() -> str:
    """Describe the operating system: os-release PRETTY_NAME where it exists, platform.platform() elsewhere."""
    try:
        return platform.freedesktop_os_release()["PRETTY_NAME"]
    except (OSError, KeyError, AttributeError):
        return platform.platform()


def process_name() -> str:
    """Name of the running program, read the same way on every platform."""
    return Path(sys.argv[0]).name if sys.argv and sys.argv[0] else Path(sys.executable).name


ENV = FrozenDict()

# System info
ENV["SYS"] = {}

# Python
ENV["SYS"]["PYTHON"] = {}
ENV["SYS"]["PYTHON"]["VERSION"] = sys.version
ENV["SYS"]["PYTHON"]["PATH"] = sys.path

MAJOR = sys.version_info.major
MINOR = sys.version_info.minor

supported = MAJOR == 3 and MINOR >= 11
if not supported:
    print("KB4IT only runs in with Python version >= 3.11")
    sys.exit(-1)

try:
    import mako
    ENV["SYS"]["MAKO"] = {}
    ENV["SYS"]["MAKO"]["VERSION"] = mako.__version__
except ModuleNotFoundError as error:
    print("Mako template system not found")
    sys.exit(-1)

ENV["SYS"]["PLATFORM"] = {}
ENV["SYS"]["PLATFORM"]["NODE"] = platform.node()
ENV["SYS"]["PLATFORM"]["OS"] = platform_description()
ENV["SYS"]["PLATFORM"]["FAMILY"] = platform_family()

# KB4IT current process
ENV["SYS"]["PS"] = {}
ENV["SYS"]["PS"]["PID"] = os.getpid()
ENV["SYS"]["PS"]["NAME"] = process_name()

# Configuration
ENV["CONF"] = {}
ENV["CONF"]["ROOT"] = abspath(sys.modules[__name__].__file__ + "/../../")

ENV["CONF"]["USER_DIR"] = str(Path.home())
ENV["CONF"]["MAX_WORKERS"] = multiprocessing.cpu_count()  # Avoid MemoryError

# App Info
ENV["APP"] = {}
ENV["APP"]["name"] = "Knowledge Base For IT"
ENV["APP"]["shortname"] = "KB4IT"
ENV["APP"]["description"] = "KB4IT is a static website generator based on \
                      Markdown sources mainly for technical \
                      documentation purposes."
ENV["APP"]["license"] = "GPL v3"
ENV["APP"]["license_long"] = "The code is licensed under the terms of the  GPL v3\n\
                  so you're free to grab, extend, improve and fork the \
                  code\nas you want"
ENV["APP"]["copyright"] = "Copyright \xa9 2019 Tomás Vírseda"
ENV["APP"]["desc"] = ""
FILE_VERSION = os.path.join(ENV["CONF"]["ROOT"], "VERSION")
ENV["APP"]["version"] = Path(FILE_VERSION).read_text(encoding="utf-8").strip()
# The release version names what is built; the build version also says which commit (BI-06).
ENV["APP"]["build"] = build_info(ENV["CONF"]["ROOT"], ENV["APP"]["version"])
ENV["APP"]["build_version"] = ENV["APP"]["build"]["build_version"]
ENV["APP"]["author"] = "Tomás Vírseda"
ENV["APP"]["author_email"] = "tomasvirseda@gmail.com"
ENV["APP"]["documenters"] = ["Tomás Vírseda <tomasvirseda@gmail.com>"]
ENV["APP"]["website"] = "https://github.com/t00m/KB4IT"

# Local paths
ENV["LPATH"] = {}
# KB4IT_HOME relocates every per-user file (tests, portable installs); the default is ~/.kb4it on all systems.
ENV["LPATH"]["ROOT"] = os.environ.get("KB4IT_HOME") or os.path.join(
    ENV["CONF"]["USER_DIR"], f".{ENV['APP']['shortname'].lower()}"
)
ENV["LPATH"]["VAR"] = os.path.join(ENV["LPATH"]["ROOT"], "var")
ENV["LPATH"]["LOG"] = os.path.join(ENV["LPATH"]["VAR"], "log")
ENV["LPATH"]["OPT"] = os.path.join(ENV["LPATH"]["ROOT"], "opt")
ENV["LPATH"]["RESOURCES"] = os.path.join(ENV["LPATH"]["OPT"], "resources")
ENV["LPATH"]["THEMES"] = os.path.join(ENV["LPATH"]["RESOURCES"], "themes")

# Global paths
ENV["GPATH"] = {}
ENV["GPATH"]["ROOT"] = ENV["CONF"]["ROOT"]
ENV["GPATH"]["DATA"] = os.path.join(ENV["GPATH"]["ROOT"], "kb4it")
ENV["GPATH"]["RESOURCES"] = os.path.join(ENV["GPATH"]["ROOT"], "resources")
ENV["GPATH"]["ONLINE"] = os.path.join(ENV["GPATH"]["RESOURCES"], "online")
ENV["GPATH"]["IMAGES"] = os.path.join(ENV["GPATH"]["ONLINE"], "images")
ENV["GPATH"]["COMMON"] = os.path.join(ENV["GPATH"]["RESOURCES"], "common")
ENV["GPATH"]["COMMON_IMG"] = os.path.join(ENV["GPATH"]["COMMON"], "images")
ENV["GPATH"]["TEMPLATES"] = os.path.join(ENV["GPATH"]["COMMON"], "templates")
ENV["GPATH"]["THEMES"] = os.path.join(ENV["GPATH"]["RESOURCES"], "themes")
# Template bases: folders of templates that several themes share ("template_base" in theme.json).
ENV["GPATH"]["BASES"] = os.path.join(ENV["GPATH"]["RESOURCES"], "bases")
ENV["GPATH"]["APPDATA"] = os.path.join(ENV["GPATH"]["COMMON"], "appdata")
ENV["GPATH"]["RES"] = os.path.join(ENV["GPATH"]["DATA"], "res")

# Files
ENV["FILE"] = {}
ENV["FILE"]["LOG"] = os.path.join(
    ENV["LPATH"]["LOG"], f"{ENV['APP']['shortname'].lower()}.log"
)

ENV.freeze()

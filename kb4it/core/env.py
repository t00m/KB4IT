#!/usr/bin/python
"""
Environment module.

# File: mod_env.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: Environment variables module
"""

import locale
import multiprocessing
import os
import platform
import sys
from os.path import abspath
from pathlib import Path

locale.getpreferredencoding()

ENV = {}

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
try:
    ENV["SYS"]["PLATFORM"]["OS"] = platform.freedesktop_os_release()["PRETTY_NAME"]
except FileNotFoundError:
    print("KB4IT only runs in GNU/Linux systems")
    sys.exit(-1)
except AttributeError:
    print("KB4IT couldn't start. Check traceback")
    sys.exit(-1)

# KB4IT current process
pid = os.getpid()
ENV["SYS"]["PS"] = {}
ENV["SYS"]["PS"]["PID"] = os.getpid()
ENV["SYS"]["PS"]["NAME"] = Path(
    f"/proc/{pid}/comm").read_text(encoding="utf-8").strip()

# Configuration
ENV["CONF"] = {}
ENV["CONF"]["ROOT"] = abspath(sys.modules[__name__].__file__ + "/../../")

ENV["CONF"]["USER_DIR"] = os.path.expanduser("~")
ENV["CONF"]["MAX_WORKERS"] = multiprocessing.cpu_count()  # Avoid MemoryError
ENV["CONF"]["EOHMARK"] = "// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE"
ENV["CONF"]["ADOCPROPS"] = {
    "toc": "left",
    "toclevels": "2",
    "icons": "font",
    "linkcss": None,
    "experimental": None,
    "source-highlighter": "highlight.js",
}

# App Info
ENV["APP"] = {}
ENV["APP"]["name"] = "Knowledge Base For IT"
ENV["APP"]["shortname"] = "KB4IT"
ENV["APP"]["description"] = "KB4IT is a static website generator based on \
                      Asciidoctor sources mainly for technical \
                      documentation purposes."
ENV["APP"]["license"] = "GPL v3"
ENV["APP"]["license_long"] = "The code is licensed under the terms of the  GPL v3\n\
                  so you're free to grab, extend, improve and fork the \
                  code\nas you want"
ENV["APP"]["copyright"] = "Copyright \xa9 2019 Tomás Vírseda"
ENV["APP"]["desc"] = ""
FILE_VERSION = os.path.join(ENV["CONF"]["ROOT"], "VERSION")
ENV["APP"]["version"] = Path(FILE_VERSION).read_text(encoding="utf-8").strip()
ENV["APP"]["author"] = "Tomás Vírseda"
ENV["APP"]["author_email"] = "tomasvirseda@gmail.com"
ENV["APP"]["documenters"] = ["Tomás Vírseda <tomasvirseda@gmail.com>"]
ENV["APP"]["website"] = "https://github.com/t00m/KB4IT"

# Local paths
ENV["LPATH"] = {}
ENV["LPATH"]["ROOT"] = os.path.join(
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
ENV["GPATH"]["APPDATA"] = os.path.join(ENV["GPATH"]["COMMON"], "appdata")
ENV["GPATH"]["RES"] = os.path.join(ENV["GPATH"]["DATA"], "res")

# Files
ENV["FILE"] = {}
ENV["FILE"]["LOG"] = os.path.join(
    ENV["LPATH"]["LOG"], f"{ENV['APP']['shortname'].lower()}.log"
)

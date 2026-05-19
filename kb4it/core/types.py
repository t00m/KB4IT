#!/usr/bin/env python

"""
Type definitions for KB4IT core data structures.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

All definitions use TypedDict so existing dict-access patterns are
unchanged. These types are pure static hints: no runtime cost and no
behaviour change. Annotate variable assignments progressively; run
mypy or pyright to surface type errors incrementally.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TypedDict


class DirPaths(TypedDict):
    source: str
    target: str
    tmp:    str
    www:    str
    cache:  str
    log:    str
    db:     str


class DocsInfo(TypedDict):
    count:     int
    bag:       list
    targets:   set
    format:    str
    filenames: list


class Runtime(TypedDict, total=False):
    theme:   dict
    dir:     DirPaths
    docs:    DocsInfo
    logfile: Path
    ncd:     int
    nck:     int
    K_PATH:  list
    KV_PATH: list


class DocumentMeta(TypedDict, total=False):
    """Per-document entry inside kbdict["document"]."""
    content:       str
    keys:          dict
    body_hash:     str
    metadata_hash: str
    compile:       bool


class KBDict(TypedDict, total=False):
    """Top-level structure of the kbdict JSON cache."""
    document:      dict   # dict[str, DocumentMeta]
    metadata:      dict   # dict[str, dict[str, list[str]]]
    kb4it_version: str


class DBRecord(TypedDict, total=False):
    """Per-document row in the in-memory Database."""
    Title:      list   # list[str]
    Date:       list   # list[str]
    SystemPage: list   # [True] when present

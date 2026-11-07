#!/usr/bin/env python

"""
Find text in the Markdown sources of the projects: kb4it search.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

Prints path:line: text, as grep -n does, so vim (vim -q) and other tools can
read it. The exit status follows grep: 0 found, 1 not found, 2 error.
"""

from __future__ import annotations

import os
import re
import sys
from typing import TextIO

from kb4it.core import projects
from kb4it.core.explore import matching, read_properties
from kb4it.core.files import SOURCE_ENCODING, get_source_docs
from kb4it.core.projects import ProjectError

PATH_COLOR = "\x1b[35m"
LINE_COLOR = "\x1b[32m"
MATCH_COLOR = "\x1b[1;31m"
RESET = "\x1b[0m"


def parse_where(text: str) -> tuple[str, str]:
    """'Key=Value' as (key, value); raises ValueError without '=' or without a key."""
    key, sep, value = text.partition("=")
    if not sep or not key.strip():
        raise ValueError(f"--where needs KEY=VALUE, got '{text}'")
    return key.strip(), value.strip()


def where_matches(props: dict[str, list[str]], where: list[tuple[str, str]]) -> bool:
    """True when every key of where has one of its values in props (AND across keys, OR within one)."""
    wanted: dict[str, list[str]] = {}
    for key, value in where:
        wanted.setdefault(key.casefold(), []).append(value)
    for key, values in wanted.items():
        have = [v for name in matching(props, key) for v in props[name]]
        if not any(matching(have, value) for value in values):
            return False
    return True


def compile_pattern(pattern: str, regex: bool, case_sensitive: bool) -> re.Pattern:
    """The pattern to look for: plain text unless regex, case-insensitive unless case_sensitive."""
    return re.compile(pattern if regex else re.escape(pattern), 0 if case_sensitive else re.IGNORECASE)


def _paint(line: str, rx: re.Pattern) -> str:
    return rx.sub(lambda m: f"{MATCH_COLOR}{m.group(0)}{RESET}", line)


def _configs(refs: list[str] | None, err: TextIO) -> list[tuple[str, str]] | None:
    """(label, config) of the projects to search, or None after an error."""
    if refs:
        result = []
        for ref in refs:
            try:
                config = projects.resolve(ref)
            except ProjectError as error:
                print(f"Error: {error}", file=err)
                return None
            if not os.path.isfile(config):
                print(f"Error: no file {config}", file=err)
                return None
            result.append((ref, config))
        return result
    entries = projects.load()
    if not entries:
        print("Error: no projects in the list; add one with kb4it import or give -p", file=err)
        return None
    return [(e.get("id") or e.get("name") or e.get("config", ""), e.get("config", "")) for e in entries]


def run_search(params: dict, out: TextIO = sys.stdout, err: TextIO = sys.stderr) -> int:
    """kb4it search PATTERN [-p PROJECT]... [--where KEY=VALUE]... [-r] [-s] [-l]."""
    try:
        rx = compile_pattern(params["pattern"], params.get("regex"), params.get("case_sensitive"))
        where = [parse_where(text) for text in params.get("where") or []]
    except (re.error, ValueError) as error:
        print(f"Error: {error}", file=err)
        return 2
    targets = _configs(params.get("projects"), err)
    if targets is None:
        return 2
    color = out.isatty() and not os.environ.get("NO_COLOR")
    files_only = params.get("files_with_matches")
    found = False
    for label, config in targets:
        try:
            source = projects.source_dir(config)
            props = read_properties(config)[0] if where else {}
        except (OSError, ValueError) as error:
            print(f"Warning: skipped {label}: {error}", file=err)
            continue
        for path in sorted(get_source_docs(str(source))):
            path = os.path.abspath(path)
            if where and not where_matches(props.get(path, {}), where):
                continue
            try:
                with open(path, encoding=SOURCE_ENCODING, errors="replace") as fh:
                    lines = fh.read().splitlines()
            except OSError as error:
                print(f"Warning: cannot read {path}: {error}", file=err)
                continue
            shown = f"{PATH_COLOR}{path}{RESET}" if color else path
            for number, line in enumerate(lines, 1):
                if not rx.search(line):
                    continue
                found = True
                if files_only:
                    print(shown, file=out)
                    break
                num = f"{LINE_COLOR}{number}{RESET}" if color else str(number)
                print(f"{shown}:{num}: {_paint(line, rx) if color else line}", file=out)
    return 0 if found else 1

#!/usr/bin/env python

"""
Read the properties of a project's documents straight from its sources: kb4it keys.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

No build is needed. Values are split on commas as the build splits them.
kb4it search uses the same reader for its --where filters.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable

from kb4it.core import projects
from kb4it.core.documents import parse_markdown_attributes
from kb4it.core.files import SOURCE_ENCODING, get_source_docs
from kb4it.core.log import get_logger
from kb4it.core.projects import ProjectError


def read_properties(config: str) -> tuple[dict[str, dict[str, list[str]]], int]:
    """Properties of each source document, by absolute path, and how many documents could not be read."""
    props: dict[str, dict[str, list[str]]] = {}
    invalid = 0
    source = projects.source_dir(config)
    if not source.is_dir():
        raise FileNotFoundError(f"the source folder is missing: {source}")
    parser_log = get_logger("Util")  # parse_markdown_attributes reports through it
    was_disabled = parser_log.disabled
    parser_log.disabled = True
    try:
        for path in sorted(get_source_docs(str(source))):
            try:
                with open(path, encoding=SOURCE_ENCODING) as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError):
                invalid += 1
                continue
            keys, valid, _reason, _warned = parse_markdown_attributes(text, os.path.basename(path))
            if not valid:
                invalid += 1
                continue
            props[os.path.abspath(path)] = keys
    finally:
        parser_log.disabled = was_disabled
    return props, invalid


def index(props: dict[str, dict[str, list[str]]]) -> dict[str, dict[str, list[str]]]:
    """Property name, then value, then the sorted paths of the documents that have it."""
    result: dict[str, dict[str, list[str]]] = {}
    for path, keys in props.items():
        for key, values in keys.items():
            by_value = result.setdefault(key, {})
            for value in values:
                by_value.setdefault(value, []).append(path)
    for by_value in result.values():
        for paths in by_value.values():
            paths.sort()
    return result


def matching(names: Iterable[str], wanted: str) -> list[str]:
    """The names equal to wanted, ignoring case."""
    wanted = wanted.casefold()
    return [name for name in names if name.casefold() == wanted]


def _order(name: str) -> tuple[str, str]:
    return name.casefold(), name


def run_keys(params: dict) -> int:
    """kb4it keys PROJECT [KEY [VALUE]]: properties, values of one, or the documents with one value."""
    ref = params["project"]
    try:
        config = projects.resolve(ref)
        props, invalid = read_properties(config)
    except ProjectError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"Error: cannot read the project {ref}: {error}", file=sys.stderr)
        return 1
    if invalid:
        print(f"{invalid} documents could not be read and are left out; "
              f"run 'kb4it verify {ref}' to see why", file=sys.stderr)
    data = index(props)
    key, value = params.get("key"), params.get("value")
    if not key:
        for name in sorted((k for k in data if k != "Title"), key=_order):
            count = len({p for paths in data[name].values() for p in paths})
            print(f"{count:>5}  {name}")
        return 0
    keys = matching(data, key)
    if not keys:
        print(f"Error: no document has the property '{key}'", file=sys.stderr)
        return 1
    by_value: dict[str, set[str]] = {}
    for name in keys:
        for val, paths in data[name].items():
            by_value.setdefault(val, set()).update(paths)
    if value is None:
        for val in sorted(by_value, key=_order):
            print(f"{len(by_value[val]):>5}  {val}")
        return 0
    values = matching(by_value, value)
    if not values:
        print(f"Error: no document has {key}: {value}", file=sys.stderr)
        return 1
    for path in sorted({p for val in values for p in by_value[val]}):
        print(path)
    return 0

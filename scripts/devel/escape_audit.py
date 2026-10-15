#!/usr/bin/env python3
"""List every ${...} expression of a theme's templates, to review what is escaped.

Usage: escape_audit.py THEME_OR_FOLDER [--raw]

THEME_OR_FOLDER is the name of a bundled theme (techdoc, blog, ...), "common" for
KB4IT's common templates, or a folder holding .tpl files. Each line shows
file:line, whether the output is escaped or raw ("| n"), and the expression.
--raw lists only the raw ones, which must print HTML built by KB4IT or the theme,
never a value taken from a document or repo.json as it is.
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESOURCES = os.path.join(ROOT, "kb4it", "resources")


def _bodies(line):
    """Text inside each ${...} of line, with nested braces and quoted strings skipped over."""
    start = line.find("${")
    while start >= 0:
        depth, quote, i = 1, None, start + 2
        while i < len(line) and depth:
            char = line[i]
            if quote:
                if char == quote:
                    quote = None
            elif char in "'\"":
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            i += 1
        if depth:
            return  # an expression that goes on to the next line: rare, and not one of ours
        yield line[start + 2:i - 1]
        start = line.find("${", i)


def _has_filter(body):
    """True if body ends with a Mako filter list (| h, | n, | u, ...) outside quotes."""
    head, sep, tail = body.rpartition("|")
    return bool(sep) and head.count("'") % 2 == 0 and head.count('"') % 2 == 0 and \
        all(f.strip().isidentifier() for f in tail.split(","))


def templates_dir(name):
    if os.path.isdir(name):
        return name
    if name == "common":
        return os.path.join(RESOURCES, "common", "templates")
    return os.path.join(RESOURCES, "themes", name, "templates")


def expressions(folder):
    """Yield (file, line number, expression, filters) for every ${...} in folder's templates."""
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".tpl"):
            continue
        path = os.path.join(folder, name)
        with open(path, encoding="utf-8") as fh:
            for number, line in enumerate(fh, start=1):
                for body in _bodies(line):
                    expr, _, filters = body.rpartition("|") if _has_filter(body) else (body, "", "")
                    yield name, number, expr.strip(), [f.strip() for f in filters.split(",") if f.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("theme", help="bundled theme name, 'common', or a templates folder")
    parser.add_argument("--raw", action="store_true", help="only expressions marked | n")
    args = parser.parse_args()
    folder = templates_dir(args.theme)
    if not os.path.isdir(folder):
        print(f"No templates folder: {folder}", file=sys.stderr)
        return 1
    total = raw = 0
    for name, number, expr, filters in expressions(folder):
        total += 1
        is_raw = "n" in filters
        raw += is_raw
        if args.raw and not is_raw:
            continue
        print(f"{name}:{number}\t{'raw' if is_raw else 'escaped'}\t{expr}")
    print(f"# {total} expressions, {raw} raw, {total - raw} escaped", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

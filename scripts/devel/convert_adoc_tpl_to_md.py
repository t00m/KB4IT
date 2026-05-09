#!/usr/bin/env python
"""One-shot converter: strip AsciiDoc wrapper from theme templates.

Removes `= title`, `:Key: value`, `// END-OF-HEADER` and standalone `++++`
delimiter lines so the templates render as Markdown system pages (raw HTML
is allowed inline).  Mako interpolations (${...}) and embedded HTML are
preserved untouched.
"""
from __future__ import annotations

import sys
from pathlib import Path


def convert(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out = []
    in_header = True
    for raw in lines:
        s = raw.strip()
        if in_header:
            # `= ...` (page title) → drop; theme.py sets the page title via Mako
            if s.startswith("= "):
                continue
            # `:Key: value` (page property) → drop; system-page metadata
            # is set programmatically via add_document_key, not parsed here.
            if s.startswith(":") and s.count(":") >= 2 and not s.startswith("::"):
                continue
            # AsciiDoc inline comments / EOH marker
            if s.startswith("//"):
                continue
            # Header ends at the first non-empty, non-header line
            if s and not s.startswith("<%"):
                in_header = False
        # Strip ++++ passthrough delimiters anywhere in the file
        if s == "++++":
            continue
        out.append(raw)
    # Collapse leading blank lines that the strip may have left behind
    while out and out[0].strip() == "":
        out.pop(0)
    return "".join(out)


def main(paths: list[str]) -> int:
    for p in paths:
        path = Path(p)
        original = path.read_text(encoding="utf-8")
        converted = convert(original)
        if converted != original:
            path.write_text(converted, encoding="utf-8")
            print(f"converted {path}")
        else:
            print(f"unchanged {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

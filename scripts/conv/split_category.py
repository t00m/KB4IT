#!/usr/bin/env python3
"""Move the type of work from Category to WorkType in KB4IT documents.

Usage: split_category.py SOURCE [--csv FILE] [--dry-run]

Reads every *.md file at the top of SOURCE. When the frontmatter Category holds
Change, Incident or Task, the document becomes Category: Record with
WorkType: <type>; Meeting becomes Category: Minutes with WorkType: Meeting.
Other values in a list (Report, Incident) stay in Category. Only the Category
line changes: the body, the key order and the line endings are kept. Documents
that already have a WorkType are left alone, so running it twice is safe.
With --csv, writes one row per changed document. With --dry-run, writes no
document.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

RECORD_TYPES = ("Change", "Incident", "Task", "Meeting")
CATEGORY = re.compile(r"^Category:\s*(.*?)\s*$")
WORKTYPE = re.compile(r"^WorkType:")
FIELDS = ["file", "category_before", "category_after", "worktype"]


def _ending(line):
    # The line ending of one line, empty for a last line without one.
    return line[len(line.rstrip("\r\n")):]


def split_text(text):
    """Return the new text and a change record, or (text, None) when nothing changes."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return text, None
    end = next((i for i in range(1, len(lines)) if lines[i].rstrip("\r\n") == "---"), None)
    if end is None:
        return text, None
    header = [line.rstrip("\r\n") for line in lines[1:end]]
    if any(WORKTYPE.match(line) for line in header):
        return text, None
    for i, line in enumerate(header, start=1):
        match = CATEGORY.match(line)
        if match:
            break
    else:
        return text, None
    before = match.group(1)
    values = [v.strip() for v in before.split(",") if v.strip()]
    kinds = [v for v in values if v in RECORD_TYPES]
    if not kinds:
        return text, None
    worktype = kinds[0]
    forms = [v for v in values if v not in RECORD_TYPES]
    after = ", ".join(forms) or ("Minutes" if worktype == "Meeting" else "Record")
    # The closing --- follows, so the Category line always has an ending.
    eol = _ending(lines[i])
    lines[i] = f"Category: {after}{eol}WorkType: {worktype}{eol}"
    return "".join(lines), {"category_before": before, "category_after": after, "worktype": worktype}


def split_dir(source, csv_path=None, dry_run=False):
    """Apply split_text to every *.md at the top of source and return the change records."""
    changes = []
    for path in sorted(Path(source).glob("*.md")):
        text = path.read_bytes().decode("utf-8")
        new, change = split_text(text)
        if change is None:
            continue
        changes.append({"file": path.name, **change})
        if not dry_run:
            path.write_bytes(new.encode("utf-8"))
    if csv_path:
        with open(csv_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(changes)
    return changes


def main(argv=None):
    parser = argparse.ArgumentParser(description="Move record types from Category to WorkType.")
    parser.add_argument("source", type=Path, help="folder with the Markdown documents")
    parser.add_argument("--csv", type=Path, help="write the changes to this CSV file")
    parser.add_argument("--dry-run", action="store_true", help="report the changes without writing documents")
    args = parser.parse_args(argv)
    if not args.source.is_dir():
        print(f"not a folder: {args.source}", file=sys.stderr)
        return 2
    changes = split_dir(args.source, args.csv, args.dry_run)
    total = len(list(args.source.glob("*.md")))
    print(f"changed={len(changes)} unchanged={total - len(changes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

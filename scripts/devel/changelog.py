#!/usr/bin/env python3
"""CHANGELOG.md helpers for scripts/release.sh (Keep a Changelog format).

  changelog.py has-unreleased          exit 0 when [Unreleased] holds entries
  changelog.py release X.Y.Z DATE      turn [Unreleased] into [X.Y.Z] - DATE, open a new empty [Unreleased]
  changelog.py notes X.Y.Z             print a release notes draft built from the [X.Y.Z] section
"""

import re
import sys
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[2] / "CHANGELOG.md"
SECTION_RE = re.compile(r"(?m)^## \[(?P<name>[^\]]+)\](?P<rest>.*)$")


def sections(text):
    """Return [(name, start, end)] for every '## [...]' section."""
    found = list(SECTION_RE.finditer(text))
    return [(m.group("name"), m.start(), found[i + 1].start() if i + 1 < len(found) else len(text))
            for i, m in enumerate(found)]


def body(text, name):
    for found, start, end in sections(text):
        if found == name:
            lines = text[start:end].splitlines()[1:]
            return "\n".join(line for line in lines if line.strip() != "---").strip()
    return None


def has_unreleased(text):
    content = body(text, "Unreleased")
    return bool(content and re.search(r"(?m)^- ", content))


def release(text, version, date):
    if re.search(rf"(?m)^## \[{re.escape(version)}\]", text):
        return text
    if not has_unreleased(text):
        raise SystemExit("CHANGELOG.md: [Unreleased] is empty")
    return text.replace("## [Unreleased]", f"## [Unreleased]\n\n---\n\n## [{version}] - {date}", 1)


def notes(text, version):
    content = body(text, version)
    if content is None:
        raise SystemExit(f"CHANGELOG.md has no [{version}] section")
    bullets = []
    for line in content.splitlines():
        if line.startswith("- "):
            # First sentence only; a colon is not an end, it is often part of "apphelp: ...".
            first = re.split(r"(?<=\.)\s+(?=[A-Z`])", line[2:], maxsplit=1)[0].rstrip(".")
            bullets.append(f"- {first}")
    return (f"# KB4IT {version}\n\n"
            "TODO: replace this line with one sentence a user can read to decide whether to update, "
            "then cut the list below to the changes a user would notice.\n\n"
            + "\n".join(bullets) + "\n\nFull list of changes: CHANGELOG.md\n")


def main(argv):
    text = CHANGELOG.read_text(encoding="utf-8")
    if argv[:1] == ["has-unreleased"]:
        return 0 if has_unreleased(text) else 1
    if argv[:1] == ["release"] and len(argv) == 3:
        CHANGELOG.write_text(release(text, argv[1], argv[2]), encoding="utf-8")
        return 0
    if argv[:1] == ["notes"] and len(argv) == 2:
        sys.stdout.write(notes(text, argv[1]))
        return 0
    sys.stderr.write(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

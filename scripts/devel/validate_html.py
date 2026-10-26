#!/usr/bin/env python3
"""Check the HTML of KB4IT sites with the Nu HTML Checker (vnu, through html5validator).

Usage: validate_html.py [TARGET_DIR ...]

With folders, checks the pages (*.html) at the top of each. Without, builds the
sample site of every bundled theme, with the documents of tests/fixtures/audit
and two documents with code blocks, and checks those. Fails on any error or
warning. UIkit attributes must be written data-uk-* (uk-* is not HTML); the
only message ignored is the notice that <dialog> may need a polyfill, which
every current browser supports. Needs Java, and html5validator
(pip install html5validator).
Run it with the dependencies of KB4IT, for example:

    uv run --no-project --with-requirements requirements.txt --with html5validator \\
        python scripts/devel/validate_html.py
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
THEMES = ROOT / "kb4it" / "resources" / "themes"
FIXTURES = ROOT / "tests" / "fixtures" / "audit"
IGNORED = re.compile(r"^The .dialog. element is not supported in all browsers")

# A code comment before the title (COR-07) and a fence inside an admonition (MD-01).
EXTRA_DOCS = {
    "cor07.md": "---\nTag: code\n---\n\n```bash\n# install the tool\napt install x\n```\n\n# Real title\n\nText.\n",
    "md01.md": "---\nTag: code\n---\n\n# Note with code\n\n!!! note\n    ```python\n    y = 2\n    ```\n",
}


def kb4it(args, cwd, home):
    env = {"HOME": str(home), "USERPROFILE": str(home), "KB4IT_HOME": str(home / ".kb4it"),
           "PYTHONPATH": str(ROOT), "PATH": os.environ.get("PATH", "")}
    return subprocess.run([sys.executable, "-m", "kb4it.core.main", *map(str, args)], cwd=cwd, env=env, check=False,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")


def build_samples(work):
    """Build the sample apps of every bundled theme under work; return their target folders."""
    home = work / "home"
    home.mkdir()
    targets = []
    for theme_dir in sorted(p for p in THEMES.iterdir() if (p / "apps").is_dir()):
        for app in sorted(p.name for p in (theme_dir / "apps").iterdir() if p.is_dir()):
            repo = work / f"{theme_dir.name}-{app}"
            if kb4it(["create", theme_dir.name, app, repo], work, home).returncode != 0:
                sys.exit(f"Cannot create the {theme_dir.name} {app} sample")
            if theme_dir.name != "apphelp":
                for doc in FIXTURES.glob("*.md"):
                    shutil.copy(doc, repo / "source" / doc.name)
                for name, text in EXTRA_DOCS.items():
                    (repo / "source" / name).write_text(text, encoding="utf-8")
            result = kb4it(["build", repo / "config" / "repo.json"], work, home)
            if result.returncode != 0:
                sys.exit(f"Cannot build the {theme_dir.name} {app} sample:\n{result.stdout}")
            targets.append(repo / "target")
    return targets


def _messages(text):
    """The messages of every JSON report in text (vnu may write one per batch of pages), or None."""
    decoder = json.JSONDecoder()
    messages, found, i = [], False, text.find("{")
    while i >= 0:
        try:
            report, end = decoder.raw_decode(text, i)
        except json.JSONDecodeError:
            i = text.find("{", i + 1)
            continue
        if isinstance(report, dict) and "messages" in report:
            found = True
            messages.extend(report["messages"])
        i = text.find("{", end)
    return messages if found else (None if text.strip() else [])


def validate(pages):
    """Errors and warnings reported by vnu for pages, without the ignored one: [(page, line, message)]."""
    result = subprocess.run(["html5validator", "--show-warnings", "--format", "json", *map(str, pages)],
                            capture_output=True, check=False, text=True, encoding="utf-8")
    messages = _messages(result.stdout)
    if messages is None:
        sys.exit(f"html5validator gave no JSON:\n{result.stdout[:2000]}\n{result.stderr[:2000]}")
    errors = []
    for msg in messages:
        if msg.get("type") not in ("error", "non-document-error", "info") or IGNORED.match(msg.get("message", "")):
            continue
        page = msg.get("url", "").removeprefix("file:")
        errors.append((page, msg.get("lastLine", 0), msg.get("message", "")))
    if not messages and result.returncode not in (0, 1, 2):
        sys.exit(f"html5validator failed:\n{result.stderr}")
    return errors


def main(argv):
    if shutil.which("html5validator") is None:
        sys.exit("html5validator not found: pip install html5validator (it needs Java)")
    with tempfile.TemporaryDirectory(prefix="kb4it-html-") as tmp:
        targets = [Path(a) for a in argv] or build_samples(Path(tmp))
        pages = sorted(p for target in targets for p in target.glob("*.html"))
        if not pages:
            sys.exit("No pages to check")
        errors = validate(pages)
        for page, line, message in errors:
            print(f"{page}:{line}: {message}")
        print(f"{len(pages)} pages in {len(targets)} sites, {len(errors)} errors and warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

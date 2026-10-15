#!/usr/bin/env python3
"""Build every theme's default app and record the produced files and log problems.

Usage:
    theme_snapshot.py OUT                 file lists and log problems per theme
    theme_snapshot.py --content OUT       also every page, normalised, so two runs can be
                                          compared with `diff -r` (theme and template work)

With --content the techdoc, blog and bookshelf sites also get the documents in
tests/fixtures/audit/ (a rich document and one with hostile values), and apphelp is
included. Build dates, times and the KB4IT version are replaced by placeholders.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THEMES = ROOT / "kb4it" / "resources" / "themes"
FIXTURES = ROOT / "tests" / "fixtures" / "audit"

# Values that change from one build to the next.
_VOLATILE = [
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?(\.\d+)?([+-]\d{2}:?\d{2}|Z)?"), "<DATETIME>"),
    (re.compile(r"\b\d{2}:\d{2}:\d{2}\b"), "<TIME>"),
    (re.compile(r"\bat \d{1,2}:\d{2}\b"), "at <TIME>"),
    (re.compile(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,? \d{1,2} [A-Z][a-z]+ \d{4}\b"), "<DATE>"),
    (re.compile(r"\b[A-Z][a-z]+ \d{1,2},? \d{4}( \d{1,2}:\d{2})?\b"), "<DATE>"),
]
RUNNER = "import sys; from kb4it.core.main import main; sys.argv[0] = 'kb4it'; main()"


def kb4it(args, cwd, home):
    env = dict(os.environ, HOME=str(home), PYTHONPATH=str(ROOT), COLUMNS="1000", NO_COLOR="1")
    return subprocess.run([sys.executable, "-c", RUNNER, *args], cwd=cwd, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def listing(folder, skip_resources=False):
    files = []
    for path in folder.rglob("*"):
        rel = path.relative_to(folder)
        if path.is_file() and not (skip_resources and rel.parts[0] == "resources"):
            files.append(str(rel))
    return sorted(files)


def normalise(text):
    version = (ROOT / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()
    text = text.replace(version, "<VERSION>")
    for pattern, repl in _VOLATILE:
        text = pattern.sub(repl, text)
    return text


def save_pages(target, dest):
    """Copy every page of a built site, normalised, under dest."""
    for path in sorted(target.rglob("*.html")):
        rel = path.relative_to(target)
        if rel.parts[0] == "resources":
            continue
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(normalise(path.read_text(encoding="utf-8")), encoding="utf-8")


def main(out, content=False):
    out.mkdir(parents=True, exist_ok=True)
    for theme_dir in sorted(THEMES.iterdir()):
        theme = theme_dir.name
        if not (theme_dir / "apps" / "default").is_dir():
            continue
        if theme == "apphelp" and not content:
            continue
        work = Path(tempfile.mkdtemp(prefix=f"snap-{theme}-"))
        home = work / "home"
        home.mkdir()
        repo = work / "repo"
        kb4it(["create", theme, str(repo)], work, home)
        if content and theme != "apphelp":
            for doc in sorted(FIXTURES.glob("*.md")):
                shutil.copy(doc, repo / "source" / doc.name)
        result = kb4it(["build", str(repo / "config" / "repo.json")], work, home)
        (out / f"{theme}.target").write_text("\n".join(listing(repo / "target", True)) + "\n")
        (out / f"{theme}.source").write_text("\n".join(listing(repo / "source")) + "\n")
        problems = []
        for line in result.stdout.splitlines():
            if " ERROR " in line or " WARNING " in line:
                fields = [f.strip() for f in line.split("|")]
                problems.append(f"{fields[0]} {fields[-1]}")
        (out / f"{theme}.log").write_text(f"exit={result.returncode}\n" + "\n".join(problems) + "\n")
        if content:
            save_pages(repo / "target", out / theme)
        shutil.rmtree(work, ignore_errors=True)
        print(f"{theme}: exit={result.returncode} problems={len(problems)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out", type=Path)
    parser.add_argument("--content", action="store_true", help="also save every page, normalised")
    args = parser.parse_args()
    main(args.out, content=args.content)

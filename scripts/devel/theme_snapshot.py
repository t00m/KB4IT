#!/usr/bin/env python3
"""Build every theme's sample apps and record the produced files and log problems.

Usage:
    theme_snapshot.py OUT                 file lists and log problems per theme and app
    theme_snapshot.py --content OUT       also every page, normalised, so two runs can be
                                          compared with `diff -r` (theme and template work)

With --content every app of every theme is built (apphelp included), the techdoc,
blog and bookshelf sites also get the documents in tests/fixtures/audit/ (a rich
document and one with hostile values), and techdoc and blog are built a second time
after one dated document changed, so the incremental path is recorded too
(OUT/<theme>-<app>.incremental). Build dates, times and the KB4IT version are
replaced by placeholders.
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
    # The commit of the build and the theme fingerprint change with every run of different code.
    (re.compile(r"<VERSION>-dev\+[\w.]+|<VERSION>\+unknown"), "<VERSION>"),
    (re.compile(r"(<meta name=\"generator\" content=\"[^;\"]*); [^\"]*\""), r'\1; <THEME>"'),
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


# Themes whose incremental build is recorded too (they have event pages built from cache).
INCREMENTAL = ("techdoc", "blog")


def apps(content):
    """(theme, app) pairs to build: the default app only, or with --content every app."""
    for theme_dir in sorted(THEMES.iterdir()):
        apps_dir = theme_dir / "apps"
        if not (apps_dir / "default").is_dir():
            continue
        if theme_dir.name == "apphelp" and not content:
            continue
        names = sorted(p.name for p in apps_dir.iterdir() if p.is_dir()) if content else ["default"]
        for app in names:
            yield theme_dir.name, app


def problems_of(result):
    problems = []
    for line in result.stdout.splitlines():
        if " ERROR " in line or " WARNING " in line:
            fields = [f.strip() for f in line.split("|")]
            problems.append(f"{fields[0]} {fields[-1]}")
    return problems


def main(out, content=False):
    out.mkdir(parents=True, exist_ok=True)
    for theme, app in apps(content):
        name = theme if not content else f"{theme}-{app}"
        work = Path(tempfile.mkdtemp(prefix=f"snap-{name}-"))
        home = work / "home"
        home.mkdir()
        repo = work / "repo"
        kb4it(["create", theme, app, str(repo)], work, home)
        if content and theme != "apphelp":
            for doc in sorted(FIXTURES.glob("*.md")):
                shutil.copy(doc, repo / "source" / doc.name)
        config = str(repo / "config" / "repo.json")
        result = kb4it(["build", config], work, home)
        (out / f"{name}.target").write_text("\n".join(listing(repo / "target", True)) + "\n")
        (out / f"{name}.source").write_text("\n".join(listing(repo / "source")) + "\n")
        problems = problems_of(result)
        (out / f"{name}.log").write_text(f"exit={result.returncode}\n" + "\n".join(problems) + "\n")
        if content:
            save_pages(repo / "target", out / name)
            if theme in INCREMENTAL:
                # One dated document changes; the second build takes the incremental path.
                rich = repo / "source" / "rich.md"
                rich.write_text(rich.read_text(encoding="utf-8") + "\nOne more line.\n", encoding="utf-8")
                again = kb4it(["build", config], work, home)
                (out / f"{name}.incremental.log").write_text(
                    f"exit={again.returncode}\n" + "\n".join(problems_of(again)) + "\n")
                save_pages(repo / "target", out / f"{name}.incremental")
        shutil.rmtree(work, ignore_errors=True)
        print(f"{name}: exit={result.returncode} problems={len(problems)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out", type=Path)
    parser.add_argument("--content", action="store_true", help="also save every page, normalised")
    args = parser.parse_args()
    main(args.out, content=args.content)

#!/usr/bin/env python3
"""Check that every theme tracked in git is releasable.

For each tracked theme: theme.json is complete, its id matches its folder, its
kb4it requirement is met by kb4it/VERSION, the required templates and deploy
folders exist, and every sample app under apps/ builds with no error and no
warning. Builds run from an export of what git tracks (HEAD by default), so a
file that only exists in this working tree cannot make a theme look fine.

Usage: check_themes.py [--ref REF | --worktree]
"""

import argparse
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THEMES = "kb4it/resources/themes"
COMMON_TEMPLATES = "kb4it/resources/common/templates"
REQUIRED_KEYS = ("id", "name", "version", "kb4it")
RUNNER = "import sys; from kb4it.core.main import main; sys.argv[0] = 'kb4it'; main()"


def export(ref, dest):
    """Write the tracked files of ref (or of the working tree) into dest."""
    if ref is None:
        files = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True,
                               check=True).stdout.decode().split("\0")
        for rel in filter(None, files):
            src = ROOT / rel
            if src.is_file():
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(src.read_bytes())
        return
    data = subprocess.run(["git", "archive", ref], cwd=ROOT, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=BytesIO(data)) as tar:
        tar.extractall(dest, filter="data")


def kb4it(code_root, args, cwd, home):
    env = dict(os.environ, HOME=str(home), PYTHONPATH=str(code_root), COLUMNS="1000", NO_COLOR="1")
    return subprocess.run([sys.executable, "-c", RUNNER, *map(str, args)], cwd=cwd, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)


def problems_in(log):
    return [line.split("|")[-1].strip() for line in log.splitlines() if " ERROR " in line or " WARNING " in line]


def check_static(code_root, theme_dir, version):
    sys.path.insert(0, str(code_root))
    from kb4it.core.version import requirement_satisfied

    problems = []
    try:
        conf = json.loads((theme_dir / "theme.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"theme.json unreadable: {error}"]
    for key in REQUIRED_KEYS:
        if not conf.get(key):
            problems.append(f"theme.json has no '{key}'")
    if conf.get("id") and conf["id"] != theme_dir.name:
        problems.append(f"theme.json id '{conf['id']}' does not match folder '{theme_dir.name}'")
    if conf.get("kb4it"):
        try:
            if not requirement_satisfied(conf["kb4it"], version):
                problems.append(f"requires KB4IT {conf['kb4it']}, this release is {version}")
        except ValueError as error:
            problems.append(f"invalid kb4it requirement: {error}")
    if not (theme_dir / "logic" / "theme.py").is_file():
        problems.append("logic/theme.py is missing")
    required = ["HTML_BODY", "PAGE_INDEX"]
    if conf.get("metadata_pages", True) is not False:
        required += ["PAGE_KEY", "PAGE_KEY_VALUE"]
    for name in required:
        if not any((d / f"{name}.tpl").is_file() for d in (theme_dir / "templates", code_root / COMMON_TEMPLATES)):
            problems.append(f"required template {name} is missing")
    for name in conf.get("deploy_dirs") or []:
        if not (theme_dir / name).is_dir():
            problems.append(f"deploy_dirs folder '{name}' is missing")
    if not (theme_dir / "apps").is_dir() or not any((theme_dir / "apps").iterdir()):
        problems.append("no sample app under apps/")
    return problems


def check_app(code_root, theme, app, work):
    home = work / f"home-{theme}-{app}"
    home.mkdir()
    repo = work / f"repo-{theme}-{app}"
    created = kb4it(code_root, ["create", theme, app, repo], work, home)
    if created.returncode != 0:
        return [f"kb4it create failed: {problems_in(created.stdout)[-1:] or created.stdout[-200:]}"]
    built = kb4it(code_root, ["build", repo / "config" / "repo.json"], work, home)
    problems = problems_in(built.stdout)
    if built.returncode != 0 and not problems:
        problems = [f"build exited {built.returncode}"]
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ref", default="HEAD", help="git ref to check (default HEAD)")
    group.add_argument("--worktree", action="store_true", help="check the tracked files as they are on disk")
    args = parser.parse_args()

    failures = 0
    with tempfile.TemporaryDirectory(prefix="kb4it-themes-") as tmp:
        work = Path(tmp)
        code_root = work / "src"
        export(None if args.worktree else args.ref, code_root)
        version = (code_root / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()
        source = "working tree" if args.worktree else args.ref
        print(f"Checking themes of {source} for KB4IT {version}")
        for theme_dir in sorted(p for p in (code_root / THEMES).iterdir() if (p / "theme.json").is_file()):
            theme = theme_dir.name
            problems = [f"{theme}: {p}" for p in check_static(code_root, theme_dir, version)]
            apps = sorted(p.name for p in (theme_dir / "apps").iterdir() if p.is_dir()) if (theme_dir / "apps").is_dir() else []
            if not problems:
                for app in apps:
                    problems += [f"{theme}/{app}: {p}" for p in check_app(code_root, theme, app, work)]
            status = "ok" if not problems else "FAIL"
            print(f"  {status:4} {theme} (apps: {', '.join(apps) or 'none'})")
            for problem in problems:
                print(f"       - {problem}")
            failures += len(problems)
    print(f"{'All themes are compliant.' if not failures else f'{failures} problem(s) found.'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

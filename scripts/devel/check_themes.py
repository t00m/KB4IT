#!/usr/bin/env python3
"""Check that every theme tracked in git is releasable.

For each tracked theme: theme.json is complete, its id matches its folder, its
kb4it requirement is met by kb4it/VERSION, the required templates and deploy
folders exist, every sample app under apps/ builds with no error and no
warning, and a theme whose files changed since the previous release tag has a
new version (TV-07). Builds run from an export of what git tracks (HEAD by default), so a
file that only exists in this working tree cannot make a theme look fine.

A forgotten theme version is a warning by default (CI, RA-07) and a failure with
--release (release.sh --commit, publish.yml, RA-06), which also fails when no
release tag can be found although CHANGELOG.md lists an earlier release.
--changed only lists the themes whose version must be raised, without building (RA-05).

Usage: check_themes.py [--ref REF | --worktree] [--release | --changed]
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THEMES = "kb4it/resources/themes"
COMMON_TEMPLATES = "kb4it/resources/common/templates"
BASES = "kb4it/resources/bases"
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


def git(*args):
    """stdout of a git command in the repository, or None when it fails."""
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return out.stdout.strip() if out.returncode == 0 else None


def previous_release(ref, version):
    """The newest vX.Y.Z tag reachable from ref, other than the tag of the version being released."""
    return git("describe", "--tags", "--abbrev=0", "--match", "v[0-9]*", "--exclude", f"v{version}", ref or "HEAD")


def check_version_bump(theme, version_now, ref, previous):
    """A theme whose files changed since the previous release must carry a new version (TV-07)."""
    folder = f"{THEMES}/{theme}"
    old_json = git("show", f"{previous}:{folder}/theme.json")
    if old_json is None:
        return []  # new theme
    old_version = json.loads(old_json).get("version")
    if old_version is None or old_version != version_now:
        return []  # first versioned release, or raised already
    span = [previous, ref] if ref else [previous]
    changed = git("diff", "--name-only", *span, "--", folder, f":(exclude){folder}/apps") or ""
    changed = [line for line in changed.splitlines() if line]
    if not changed:
        return []
    shown = ", ".join(c[len(folder) + 1:] for c in changed[:8]) + (", ..." if len(changed) > 8 else "")
    return [f"files changed since {previous} but version is still {version_now}: {shown}"]


def earlier_release_in_changelog(code_root, version):
    """True when CHANGELOG.md has a dated section for a release other than the one being built."""
    changelog = code_root / "CHANGELOG.md"
    if not changelog.is_file():
        return False
    found = re.findall(r"^## \[(\d+\.\d+\.\d+)\] - \d{4}-\d{2}-\d{2}", changelog.read_text(encoding="utf-8"), re.M)
    return any(v != version for v in found)


def version_bumps(code_root, ref, previous):
    """{theme: problem} for the themes whose files changed since previous while their version did not."""
    bumps = {}
    for theme_dir in sorted(p for p in (code_root / THEMES).iterdir() if (p / "theme.json").is_file()):
        try:
            version_now = json.loads((theme_dir / "theme.json").read_text(encoding="utf-8")).get("version")
        except ValueError:
            continue  # check_static reports the unreadable file
        for problem in check_version_bump(theme_dir.name, version_now, ref, previous):
            bumps[theme_dir.name] = problem
    return bumps


def warn(message):
    """A warning line; GitHub Actions also shows it as an annotation on the run."""
    print(f"  WARN {message}")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning title=Theme version::{message}")


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
    template_dirs = [theme_dir / "templates", code_root / COMMON_TEMPLATES]
    if conf.get("template_base"):
        base_dir = code_root / BASES / str(conf["template_base"]) / "templates"
        if not base_dir.is_dir():
            problems.append(f"template_base '{conf['template_base']}' is not a template base")
        template_dirs.insert(1, base_dir)
    for name in required:
        if not any((d / f"{name}.tpl").is_file() for d in template_dirs):
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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--release", action="store_true",
                      help="a theme changed since the previous release without a new version fails; so do missing tags")
    mode.add_argument("--changed", action="store_true",
                      help="only list the themes whose version must be raised, without building")
    args = parser.parse_args()
    ref = None if args.worktree else args.ref

    failures = 0
    with tempfile.TemporaryDirectory(prefix="kb4it-themes-") as tmp:
        work = Path(tmp)
        code_root = work / "src"
        export(None if args.worktree else args.ref, code_root)
        version = (code_root / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()
        source = "working tree" if args.worktree else args.ref
        previous = previous_release(ref, version)
        print(f"Checking themes of {source} for KB4IT {version} (previous release: {previous or 'none'})")
        strict = args.release or args.changed
        if previous is None and strict and earlier_release_in_changelog(code_root, version):
            print("  FAIL no release tag found although CHANGELOG.md lists earlier releases: run git fetch --tags")
            return 1
        bumps = version_bumps(code_root, ref, previous) if previous else {}
        if args.changed:
            for theme, problem in bumps.items():
                print(f"  RAISE {theme}: {problem}")
            print("No theme version to raise." if not bumps else f"{len(bumps)} theme version(s) to raise.")
            return 1 if bumps else 0
        for theme_dir in sorted(p for p in (code_root / THEMES).iterdir() if (p / "theme.json").is_file()):
            theme = theme_dir.name
            problems = [f"{theme}: {p}" for p in check_static(code_root, theme_dir, version)]
            if theme in bumps:
                if args.release:
                    problems.append(f"{theme}: {bumps[theme]}")
                else:
                    warn(f"{theme}: {bumps[theme]}; raise it before the release")
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

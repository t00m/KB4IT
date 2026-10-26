#!/usr/bin/env python3
"""Create and build the default app of every bundled theme; exit 1 if any fails.

Runs the same on Linux, macOS and Windows. Uses the `kb4it` command on PATH, or
`python -m kb4it.core.main` from this checkout with --from-source.

After an installation, --doctor --all-apps proves it is complete: `kb4it doctor`
must pass, and every sample app of every theme is created and built from the
installed package.
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
THEMES = ("apphelp", "blog", "bookshelf", "techdoc")


def kb4it_command(from_source):
    if from_source or not shutil.which("kb4it"):
        return [sys.executable, "-m", "kb4it.core.main"]
    return [shutil.which("kb4it")]


def run(cmd, env, cwd):
    result = subprocess.run(cmd, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", check=False)
    return result.returncode, result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-source", action="store_true", help="run this checkout instead of the installed kb4it")
    parser.add_argument("--all-apps", action="store_true", help="build every sample app of each theme, not only default")
    parser.add_argument("--doctor", action="store_true", help="run kb4it doctor first; it must pass")
    parser.add_argument("themes", nargs="*", default=THEMES)
    args = parser.parse_args()

    base = Path(tempfile.mkdtemp(prefix="kb4it-smoke-"))
    env = dict(os.environ, KB4IT_HOME=str(base / "home"), COLUMNS="1000", NO_COLOR="1")
    if args.from_source:
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    kb4it = kb4it_command(args.from_source)
    failed = []
    if args.doctor:
        code, out = run([*kb4it, "doctor"], env, str(base))
        print(out)
        print(f"[SMOKE] doctor result={'ok' if code == 0 else 'failed'}")
        if code != 0:
            failed.append(f"doctor exited {code}")
    for theme in args.themes:
        apps = ["default"]
        if args.all_apps:
            code, out = run([*kb4it, "apps", theme], env, str(base))
            apps = re.findall(r"APP name=(\S+)", out) or apps
        for app in apps:
            repo = base / f"{theme}-{app}"
            problem = None
            for name, cmd in (("create", [*kb4it, "create", theme, app, str(repo)]),
                              ("build", [*kb4it, "build", str(repo / "config" / "repo.json")])):
                code, out = run(cmd, env, str(base))
                if code != 0:
                    problem = f"{name} exited {code}"
                    print(out)
                    break
            if problem is None and not (repo / "target" / "index.html").is_file():
                problem = "target/index.html missing"
            if problem:
                failed.append(f"{theme}/{app}: {problem}")
            print(f"[SMOKE] theme={theme} app={app} result={'failed' if problem else 'ok'}")
    shutil.rmtree(base, ignore_errors=True)
    for line in failed:
        print(f"[SMOKE] FAIL {line}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

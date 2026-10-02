#!/usr/bin/env python3
"""Build every theme's default app and record the produced files and log problems."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THEMES = ROOT / "kb4it" / "resources" / "themes"
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


def main(out):
    out.mkdir(parents=True, exist_ok=True)
    for theme_dir in sorted(THEMES.iterdir()):
        theme = theme_dir.name
        if theme == "apphelp" or not (theme_dir / "apps" / "default").is_dir():
            continue
        work = Path(tempfile.mkdtemp(prefix=f"snap-{theme}-"))
        home = work / "home"
        home.mkdir()
        repo = work / "repo"
        kb4it(["create", theme, str(repo)], work, home)
        result = kb4it(["build", str(repo / "config" / "repo.json")], work, home)
        (out / f"{theme}.target").write_text("\n".join(listing(repo / "target", True)) + "\n")
        (out / f"{theme}.source").write_text("\n".join(listing(repo / "source")) + "\n")
        problems = []
        for line in result.stdout.splitlines():
            if " ERROR " in line or " WARNING " in line:
                fields = [f.strip() for f in line.split("|")]
                problems.append(f"{fields[0]} {fields[-1]}")
        (out / f"{theme}.log").write_text(f"exit={result.returncode}\n" + "\n".join(problems) + "\n")
        print(f"{theme}: exit={result.returncode} problems={len(problems)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))

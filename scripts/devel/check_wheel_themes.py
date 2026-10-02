#!/usr/bin/env python3
"""Fail when a theme tracked in git is missing from the built wheel."""

import glob
import subprocess
import sys
import zipfile

PREFIX = "kb4it/resources/themes/"


def themes(paths):
    return {p[len(PREFIX):].split("/")[0] for p in paths if p.startswith(PREFIX) and p.count("/") >= 4}


def main():
    wheels = sorted(glob.glob("dist/*.whl"))
    if not wheels:
        sys.exit("No wheel in dist/. Run: uv build --wheel")
    tracked = themes(subprocess.run(["git", "ls-files", PREFIX], capture_output=True, text=True,
                                    check=True).stdout.split())
    packaged = themes(zipfile.ZipFile(wheels[-1]).namelist())
    missing = sorted(tracked - packaged)
    if missing or "apphelp" not in packaged:
        sys.exit(f"Themes missing from {wheels[-1]}: {', '.join(missing or ['apphelp'])}")
    untracked = sorted(packaged - tracked)
    if untracked:
        print(f"WARNING: themes in the wheel but not tracked in git: {', '.join(untracked)}")
    print(f"OK: {', '.join(sorted(packaged))}")


if __name__ == "__main__":
    main()

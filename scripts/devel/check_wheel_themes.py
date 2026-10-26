#!/usr/bin/env python3
"""Fail when a theme tracked in git, or the offline help, is missing from the built wheel."""

import glob
import os
import subprocess
import sys
import zipfile

PREFIX = "kb4it/resources/themes/"
HELP_INDEX = "kb4it/resources/help/index.html"
EDITOR_BUNDLE = "kb4it/resources/editor/codemirror.min.js"


def themes(paths):
    return {p[len(PREFIX):].split("/")[0] for p in paths if p.startswith(PREFIX) and p.count("/") >= 4}


def has_offline_help(paths):
    return HELP_INDEX in paths


def has_editor_bundle(paths):
    return EDITOR_BUNDLE in paths


def main():
    # A wheel named on the command line (the source installer builds into a temporary folder), else dist/.
    wheels = sys.argv[1:] or sorted(glob.glob("dist/*.whl"))
    if not wheels:
        sys.exit("No wheel in dist/. Run: uv build --wheel")
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tracked = themes(subprocess.run(["git", "ls-files", PREFIX], cwd=root, capture_output=True, text=True,
                                    check=True).stdout.split())
    names = zipfile.ZipFile(wheels[-1]).namelist()
    if not has_offline_help(names):
        sys.exit(f"Offline help missing from {wheels[-1]}: no {HELP_INDEX}. Run scripts/help/build_offline.py first")
    if not has_editor_bundle(names):
        sys.exit(f"Editor bundle missing from {wheels[-1]}: no {EDITOR_BUNDLE}")
    packaged = themes(names)
    missing = sorted(tracked - packaged)
    if missing or "apphelp" not in packaged:
        sys.exit(f"Themes missing from {wheels[-1]}: {', '.join(missing or ['apphelp'])}")
    untracked = sorted(packaged - tracked)
    if untracked:
        print(f"WARNING: themes in the wheel but not tracked in git: {', '.join(untracked)}")
    print(f"OK: {', '.join(sorted(packaged))}")


if __name__ == "__main__":
    main()

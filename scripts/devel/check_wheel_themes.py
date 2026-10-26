#!/usr/bin/env python3
"""Fail when a theme tracked in git, or the offline help, is missing from the built wheel.

--stamp X.Y.Z also wants the build stamp kb4it/BUILD.json of that version;
--release X.Y.Z wants the stamp of the clean release commit (RA-08).

Usage: check_wheel_themes.py [--stamp X.Y.Z | --release X.Y.Z] [WHEEL]
"""

import argparse
import glob
import json
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


def stamp_problem(names, wheel, version, release):
    """Why the wheel's build stamp does not fit, or '' when it does."""
    if "kb4it/BUILD.json" not in names:
        return f"no kb4it/BUILD.json in {wheel}: run scripts/devel/stamp_build.py before building"
    stamp = json.loads(zipfile.ZipFile(wheel).read("kb4it/BUILD.json"))
    build = str(stamp.get("build_version", ""))
    if stamp.get("version") != version or not build.startswith(version):
        return f"the stamp of {wheel} is for {build or stamp.get('version')}, not {version}"
    if release and (stamp.get("source") != "release" or stamp.get("dirty") or build != version):
        return (f"the stamp of {wheel} is {build} (source={stamp.get('source')}, dirty={stamp.get('dirty')}), "
                f"not the release {version}: build from the clean commit of tag v{version}")
    return ""


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--stamp", metavar="X.Y.Z", help="require a build stamp of this version")
    group.add_argument("--release", metavar="X.Y.Z", help="require the release stamp of this version")
    parser.add_argument("wheels", nargs="*", help="the wheel to check (default: the last one in dist/)")
    args = parser.parse_args()
    # A wheel named on the command line (the source installer builds into a temporary folder), else dist/.
    wheels = args.wheels or sorted(glob.glob("dist/*.whl"))
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
    if args.stamp or args.release:
        problem = stamp_problem(names, wheels[-1], args.stamp or args.release, bool(args.release))
        if problem:
            sys.exit(f"Build stamp: {problem}")
    untracked = sorted(packaged - tracked)
    if untracked:
        print(f"WARNING: themes in the wheel but not tracked in git: {', '.join(untracked)}")
    print(f"OK: {', '.join(sorted(packaged))}")


if __name__ == "__main__":
    main()

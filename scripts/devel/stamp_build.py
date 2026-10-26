#!/usr/bin/env python3
"""Write kb4it/BUILD.json: the commit, branch and date of the package being built (BI-01).

The file is git-ignored and shipped in the wheel and sdist, so an installed KB4IT
knows which commit it came from. Run it before every package build;
scripts/distribution/build/build_python.sh and the publish workflow do.

Usage: stamp_build.py [--require-release]
  --require-release   fail unless HEAD is the clean commit of tag v<kb4it/VERSION>
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from kb4it.core.version import BUILD_FILE, build_version, git_info  # noqa: E402

PACKAGE = ROOT / "kb4it"


def stamp(root=ROOT) -> dict:
    """The facts written into BUILD.json for the checkout at root."""
    package = Path(root) / "kb4it"
    version = (package / "VERSION").read_text(encoding="utf-8").strip()
    info = git_info(root, version) or {"version": version, "commit": None, "describe": "", "count": None,
                                       "branch": "", "dirty": False, "diff_hash": "", "source": "unknown"}
    info["build_version"] = build_version(info)
    info["date"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return info


def write(info: dict, package=PACKAGE) -> Path:
    """Write BUILD.json atomically, so a build never packs half a file."""
    target = Path(package) / BUILD_FILE
    fd, tmp = tempfile.mkstemp(dir=package, prefix=".BUILD.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(info, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp, target)
    return target


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--require-release", action="store_true",
                        help="fail unless HEAD is the clean commit of tag v<kb4it/VERSION>")
    args = parser.parse_args(argv)
    info = stamp()
    if args.require_release and (info["source"] != "release" or info["dirty"]):
        print(f"ERROR: not a release build: {info['build_version']} (source={info['source']}, dirty={info['dirty']}); "
              f"HEAD must be the clean commit of tag v{info['version']}", file=sys.stderr)
        return 1
    path = write(info)
    print(f"Stamped {path.relative_to(ROOT)}: KB4IT {info['build_version']} commit={info['commit'] or 'unknown'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

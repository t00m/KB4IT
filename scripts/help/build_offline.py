#!/usr/bin/env python3
"""Build the help site from help/ into kb4it/resources/help/ with this working tree's KB4IT.

The offline copy is generated, never committed. It ships inside the package so
`kb4it help` can open it without network access.
"""

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELP = ROOT / "help"
DEFAULT_OUT = ROOT / "kb4it" / "resources" / "help"
RUNNER = "import sys; from kb4it.core.main import main; sys.argv[0] = 'kb4it'; main()"


# Import names of the optional packages the build needs. Keep in sync with the
# "extras" definition in pyproject.toml (pymdown-extensions, nh3) plus pygments.
REQUIRED = ("pymdownx", "nh3", "pygments")


def missing_packages():
    return [name for name in REQUIRED if importlib.util.find_spec(name) is None]


def build(out):
    """Build the help into out and return 0 only when out/index.html exists."""
    missing = missing_packages()
    if missing:
        print("missing package(s): %s; run: pip install KB4IT[extras]" % ", ".join(missing), file=sys.stderr)
        return 1
    conf = json.loads((HELP / "config" / "repo.json").read_text(encoding="utf-8"))
    out = Path(out).resolve()
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)
    conf["source"] = str(HELP / "source")
    conf["target"] = str(out)
    with tempfile.TemporaryDirectory(prefix="kb4it-help-") as tmp:
        config = Path(tmp) / "config" / "repo.json"
        config.parent.mkdir()
        config.write_text(json.dumps(conf, indent=4), encoding="utf-8")
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(filter(None, [str(ROOT), os.environ.get("PYTHONPATH")])))
        cmd = [sys.executable, "-c", RUNNER, "build", str(config), "--force"]
        code = subprocess.run(cmd, cwd=str(ROOT), env=env).returncode
    if code != 0:
        return code
    if not (out / "index.html").is_file():
        print("build finished but %s is missing" % (out / "index.html"), file=sys.stderr)
        return 1
    print("offline help written to %s" % out)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="output folder (default: %(default)s)")
    args = parser.parse_args(argv)
    return build(args.out)


if __name__ == "__main__":
    sys.exit(main())

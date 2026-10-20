#!/usr/bin/env python3
"""Build the help site from help/ into kb4it/resources/help/ with this working tree's KB4IT.

The offline copy is generated, never committed. It ships inside the package so
`kb4it help` can open it without network access.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HELP = ROOT / "help"
DEFAULT_OUT = ROOT / "kb4it" / "resources" / "help"
RUNNER = "import sys; from kb4it.core.main import main; sys.argv[0] = 'kb4it'; main()"


def build(out):
    """Build the help into out and return the exit code of the KB4IT build."""
    conf = json.loads((HELP / "config" / "repo.json").read_text(encoding="utf-8"))
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    conf["source"] = str(HELP / "source")
    conf["target"] = str(out)
    with tempfile.TemporaryDirectory(prefix="kb4it-help-") as tmp:
        config = Path(tmp) / "config" / "repo.json"
        config.parent.mkdir()
        config.write_text(json.dumps(conf, indent=4), encoding="utf-8")
        env = dict(os.environ, PYTHONPATH=os.pathsep.join(filter(None, [str(ROOT), os.environ.get("PYTHONPATH")])))
        cmd = [sys.executable, "-c", RUNNER, "build", str(config), "--force"]
        return subprocess.run(cmd, cwd=str(ROOT), env=env).returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="output folder (default: %(default)s)")
    args = parser.parse_args()
    return build(args.out)


if __name__ == "__main__":
    sys.exit(main())

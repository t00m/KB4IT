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


def out_problem(out):
    """Return why out is not safe to clear, or None.

    The build deletes out first, so it must sit inside kb4it/resources or the temp
    folder, and hold either nothing or an earlier help build (an index.html).
    """
    roots = [(ROOT / "kb4it" / "resources").resolve(), Path(tempfile.gettempdir()).resolve()]
    if not any(out != root and out.is_relative_to(root) for root in roots):
        return "it must be inside %s" % " or ".join(str(root) for root in roots)
    if out.exists() and not out.is_dir():
        return "it is not a folder"
    if out.is_dir() and any(out.iterdir()) and not (out / "index.html").is_file():
        return "it is not empty and holds no earlier help build (index.html)"
    return None


def build(out):
    """Build the help into out and return 0 only when out/index.html exists."""
    missing = missing_packages()
    if missing:
        print("missing package(s): %s; run: pip install KB4IT[extras]" % ", ".join(missing), file=sys.stderr)
        return 1
    out = Path(out).expanduser().resolve()
    problem = out_problem(out)
    if problem:
        print("refusing --out %s: %s" % (out, problem), file=sys.stderr)
        return 1
    conf = json.loads((HELP / "config" / "repo.json").read_text(encoding="utf-8"))
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
    parser.add_argument("--out", default=str(DEFAULT_OUT),
                        help="output folder, inside kb4it/resources or the temp folder (default: %(default)s)")
    args = parser.parse_args(argv)
    return build(args.out)


if __name__ == "__main__":
    sys.exit(main())

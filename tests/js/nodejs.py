"""Run functions of kb4it-frontmatter.js with node, in one process per call."""

import json
import shutil
import subprocess
from pathlib import Path

NODE = shutil.which("node")
SOURCE = Path(__file__).resolve().parents[2] / "kb4it" / "resources" / "editor" / "kb4it-frontmatter.js"

_RUNNER = """
const fs = require("fs");
const vm = require("vm");
const ctx = {};
vm.runInNewContext(fs.readFileSync(process.argv[1], "utf8"), ctx);
const calls = JSON.parse(fs.readFileSync(0, "utf8"));
const out = calls.map(([name, args]) => ctx.KB4ITFrontmatter[name](...args));
process.stdout.write(JSON.stringify(out));
"""


def run_node(calls):
    """Apply KB4ITFrontmatter[name](*args) to each (name, args) and return the results."""
    proc = subprocess.run(
        [NODE, "-e", _RUNNER, str(SOURCE)],
        input=json.dumps(calls),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    return json.loads(proc.stdout)

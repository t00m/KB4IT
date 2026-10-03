"""Two builds in one process, as the TUI does, each use their own theme logic."""

import json
import os
import subprocess
import sys

from tests.helpers import ROOT, mini_theme, page, write_repo

_TWO_BUILDS = """
import argparse, sys
from kb4it.core.main import KB4IT
for config in sys.argv[1:]:
    params = argparse.Namespace(action="build", config=config, force=False, log_level="INFO")
    assert KB4IT(params).run(), config
"""


def test_second_build_loads_its_own_theme(tmp_path, home):
    first = mini_theme(tmp_path / "first")
    second = mini_theme(tmp_path / "second", id="second", name="Second")
    logic = second / "logic" / "theme.py"
    logic.write_text(logic.read_text(encoding="utf-8").replace("documents.json", "second.json"), encoding="utf-8")
    cfg_a = write_repo(tmp_path / "a", "first", {"a.md": page("A", Tag="x")}, theme_path=str(first))
    cfg_b = write_repo(tmp_path / "b", "second", {"b.md": page("B", Tag="y")}, theme_path=str(second))
    env = dict(os.environ, HOME=str(home), PYTHONPATH=str(ROOT), COLUMNS="1000")
    result = subprocess.run([sys.executable, "-c", _TWO_BUILDS, str(cfg_a), str(cfg_b)], cwd=str(tmp_path),
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600,
                            check=False)
    assert result.returncode == 0, result.stdout
    assert (tmp_path / "a" / "target" / "documents.json").exists()
    assert json.loads((tmp_path / "b" / "target" / "second.json").read_text()) == ["b.md"]
    assert not (tmp_path / "b" / "target" / "documents.json").exists()

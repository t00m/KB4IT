"""Builds in one process, as the TUI and kb4it serve do, never reuse another build's templates."""

import os
import subprocess
import sys

from tests.helpers import ROOT, mini_theme, page, write_repo

_BUILDS = """
import argparse, sys
from pathlib import Path
from kb4it.core.main import KB4IT
args = sys.argv[1:]
edit = None
if args[0] == "--edit":
    edit, args = Path(args[1]), args[2:]
for n, config in enumerate(args):
    if edit is not None and n == 1:
        edit.write_text(edit.read_text(encoding="utf-8").replace("<body>", "<body>EDITED"), encoding="utf-8")
    params = argparse.Namespace(action="build", config=config, force=False, log_level="INFO")
    assert KB4IT(params).run(), config
"""


def _run(tmp_path, home, *args):
    env = dict(os.environ, HOME=str(home), PYTHONPATH=str(ROOT), COLUMNS="1000")
    return subprocess.run([sys.executable, "-c", _BUILDS, *map(str, args)], cwd=str(tmp_path), env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600, check=False)


def test_template_edited_between_builds_is_used(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    cfg = write_repo(tmp_path / "repo", "mini", {"a.md": page("A", Tag="x")}, theme_path=str(theme))
    result = _run(tmp_path, home, "--edit", theme / "templates" / "HTML_BODY.tpl", cfg, cfg)
    assert result.returncode == 0, result.stdout
    # The second build is incremental; a.html is only rebuilt when forced, so check a page built every time.
    rebuilt = (tmp_path / "repo" / "target" / "about_kb4it.html").read_text(encoding="utf-8")
    assert "<body>EDITED" in rebuilt


def test_two_themes_sharing_a_template_name_use_their_own(tmp_path, home):
    first = mini_theme(tmp_path / "first")
    second = mini_theme(tmp_path / "second", id="second", name="Second")
    body = second / "templates" / "HTML_BODY.tpl"
    body.write_text(body.read_text(encoding="utf-8").replace("<body>", "<body>SECOND"), encoding="utf-8")
    cfg_a = write_repo(tmp_path / "a", "first", {"a.md": page("A", Tag="x")}, theme_path=str(first))
    cfg_b = write_repo(tmp_path / "b", "second", {"b.md": page("B", Tag="y")}, theme_path=str(second))
    result = _run(tmp_path, home, cfg_a, cfg_b)
    assert result.returncode == 0, result.stdout
    assert "<body>SECOND" not in (tmp_path / "a" / "target" / "a.html").read_text(encoding="utf-8")
    assert "<body>SECOND" in (tmp_path / "b" / "target" / "b.html").read_text(encoding="utf-8")

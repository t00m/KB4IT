"""The offline help copy is built from the working tree into a throwaway folder."""

import json
import subprocess
import sys

import pytest

from tests.helpers import ROOT, isolated_env

SCRIPT = ROOT / "scripts" / "help" / "build_offline.py"
HELP_SOURCE = ROOT / "help" / "source"
VERSION = (ROOT / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    base = tmp_path_factory.mktemp("offline")
    out = base / "help"
    env = isolated_env(base / "home", NO_COLOR="1")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--out", str(out)], cwd=str(ROOT), env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          encoding="utf-8", timeout=900)
    return proc, out


def test_offline_build_writes_index_and_search(built):
    proc, out = built
    assert proc.returncode == 0, proc.stdout
    assert (out / "index.html").is_file()
    assert any(out.rglob("*search*"))


def test_offline_build_shows_the_package_version(built):
    _, out = built
    html = (out / "index.html").read_text(encoding="utf-8")
    assert VERSION in html
    assert '"0.8"' not in html


def test_offline_build_has_no_absolute_paths(built):
    # The help text shows example paths such as /home/ann, so look for the real build paths instead.
    _, out = built
    leaks = [str(ROOT), str(out), str(out.parent), str(HELP_SOURCE)]
    for path in out.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        for leak in leaks:
            assert leak not in text, (path, leak)


def test_help_config_version_is_not_hardcoded():
    conf = json.loads((ROOT / "help" / "config" / "repo.json").read_text(encoding="utf-8"))
    assert conf.get("version", "kb4it") in ("kb4it", VERSION)

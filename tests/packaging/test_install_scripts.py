"""The source installer and the uninstaller pick the right tool, checked with fake uv, pipx and pip."""

import os
import shutil
import subprocess
import sys

import pytest

from tests.helpers import ROOT

pytestmark = pytest.mark.skipif(sys.platform == "win32" or shutil.which("bash") is None,
                                reason="POSIX shell scripts")

INSTALL = ROOT / "scripts" / "install" / "local" / "install_kb4it_from_source.sh"


def fake_tools(bindir, log, *names):
    """Put scripts named like the tools on PATH that append their arguments to log."""
    bindir.mkdir(exist_ok=True)
    for name in names:
        tool = bindir / name
        tool.write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\n', encoding="utf-8")
        tool.chmod(0o755)


def run(script, bindir, home, *args, stdin=""):
    env = dict(os.environ, HOME=str(home), PATH=f"{bindir}{os.pathsep}/usr/bin{os.pathsep}/bin")
    return subprocess.run(["bash", str(script), *args], env=env, input=stdin, capture_output=True, text=True,
                          encoding="utf-8")


def test_install_with_uv_needs_no_python(tmp_path):
    log = tmp_path / "log"
    fake_tools(tmp_path / "bin", log, "uv", "kb4it")
    result = run(INSTALL, tmp_path / "bin", tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "uv tool install . --force" in log.read_text(encoding="utf-8")
    assert "Python:" not in result.stdout


@pytest.mark.skipif(any(os.path.exists(p) for p in ("/usr/bin/uv", "/bin/uv")), reason="a system uv wins over pipx")
def test_install_with_pipx_passes_a_recent_python(tmp_path):
    log = tmp_path / "log"
    fake_tools(tmp_path / "bin", log, "pipx", "kb4it")
    os.symlink(sys.executable, tmp_path / "bin" / "python3")
    result = run(INSTALL, tmp_path / "bin", tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = log.read_text(encoding="utf-8")
    assert "pipx install --python " in calls and " . --force" in calls

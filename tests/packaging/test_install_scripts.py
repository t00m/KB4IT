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
    env.pop("KB4IT_HOME", None)  # set by conftest; the scripts must use HOME here
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


UNINSTALL = ROOT / "scripts" / "uninstall" / "local" / "uninstall.sh"


def lister(bindir, log, name, listing):
    """A fake tool that prints listing for its list command and logs every call."""
    bindir.mkdir(exist_ok=True)
    tool = bindir / name
    tool.write_text(f'#!/bin/sh\necho "{name} $*" >> "{log}"\ncase "$*" in *list*) echo "{listing}" ;; esac\n',
                    encoding="utf-8")
    tool.chmod(0o755)


def test_uninstall_removes_the_uv_install_and_keeps_user_data(tmp_path):
    log = tmp_path / "log"
    lister(tmp_path / "bin", log, "uv", "kb4it v0.9.0")
    lister(tmp_path / "bin", log, "pipx", "other 1.0")
    (tmp_path / ".kb4it").mkdir()
    result = run(UNINSTALL, tmp_path / "bin", tmp_path)
    assert result.returncode == 0, result.stderr
    calls = log.read_text(encoding="utf-8")
    assert "uv tool uninstall kb4it" in calls and "pipx uninstall" not in calls
    assert (tmp_path / ".kb4it").is_dir()


def test_uninstall_removes_the_pipx_install(tmp_path):
    log = tmp_path / "log"
    lister(tmp_path / "bin", log, "pipx", "kb4it 0.9.0")
    result = run(UNINSTALL, tmp_path / "bin", tmp_path)
    assert result.returncode == 0, result.stderr
    assert "pipx uninstall kb4it" in log.read_text(encoding="utf-8")


def test_uninstall_purge_asks_first(tmp_path):
    (tmp_path / "bin").mkdir()
    data = tmp_path / ".kb4it"
    data.mkdir()
    assert run(UNINSTALL, tmp_path / "bin", tmp_path, "--purge", stdin="n\n").returncode == 0
    assert data.is_dir()
    assert run(UNINSTALL, tmp_path / "bin", tmp_path, "--purge", stdin="y\n").returncode == 0
    assert not data.exists()


def test_uninstall_has_no_unsafe_pip_options():
    text = UNINSTALL.read_text(encoding="utf-8")
    assert "--trusted-host" not in text
    assert "pip install" not in text

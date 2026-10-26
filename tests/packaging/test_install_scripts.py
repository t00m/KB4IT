"""The source installer and the uninstaller pick the right tool, checked with fake uv, pipx and pip."""

import json
import os
import shutil
import subprocess
import sys
import zipfile

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


def make_wheel(folder, build_version="1.2.3-dev+4.gabcdef0"):
    """A wheel file holding only the build stamp, which is all the installer reads from it."""
    folder.mkdir(parents=True, exist_ok=True)
    wheel = folder / "kb4it-1.2.3-py3-none-any.whl"
    with zipfile.ZipFile(wheel, "w") as zf:
        zf.writestr("kb4it/BUILD.json", json.dumps({"version": "1.2.3", "build_version": build_version}))
    return wheel


def installed_kb4it(folder, reports="1.2.3-dev+4.gabcdef0"):
    """A fake installed kb4it: prints its build for --version and passes doctor."""
    folder.mkdir(parents=True, exist_ok=True)
    tool = folder / "kb4it"
    tool.write_text(f'#!/bin/sh\ncase "$1" in --version) echo "KB4IT {reports}"; echo "commit x" ;; esac\nexit 0\n',
                    encoding="utf-8")
    tool.chmod(0o755)
    return tool


def fake_uv(bindir, log, tools_bin):
    """A uv that logs its calls, answers 'uv tool dir --bin' and runs 'uv run ... python' with this Python."""
    bindir.mkdir(exist_ok=True)
    tool = bindir / "uv"
    tool.write_text(f'#!/bin/sh\necho "uv $*" >> "{log}"\n'
                    f'case "$*" in "tool dir --bin") echo "{tools_bin}" ;; esac\n'
                    f'if [ "$1" = run ]; then\n'
                    f'    while [ "$#" -gt 0 ] && [ "$1" != python ]; do shift; done\n'
                    f'    shift\n'
                    f'    exec "{sys.executable}" "$@"\n'
                    f'fi\n', encoding="utf-8")
    tool.chmod(0o755)


def test_install_with_uv_installs_the_wheel_and_checks_it(tmp_path):
    log = tmp_path / "log"
    fake_uv(tmp_path / "bin", log, tmp_path / "bin")
    installed_kb4it(tmp_path / "bin")
    wheel = make_wheel(tmp_path / "dist")
    result = run(INSTALL, tmp_path / "bin", tmp_path, "--wheel", wheel)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"uv tool install {wheel} --force --reinstall" in log.read_text(encoding="utf-8")
    assert "Installed: KB4IT 1.2.3-dev+4.gabcdef0" in result.stdout
    assert "kb4it on PATH is the new installation" in result.stdout


@pytest.mark.skipif(any(os.path.exists(p) for p in ("/usr/bin/uv", "/bin/uv")), reason="a system uv wins over pipx")
def test_install_with_pipx_passes_a_recent_python(tmp_path):
    log = tmp_path / "log"
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (bindir / "pipx").write_text(f'#!/bin/sh\necho "pipx $*" >> "{log}"\n'
                                 f'case "$*" in *PIPX_BIN_DIR*) echo "{bindir}" ;; esac\n', encoding="utf-8")
    (bindir / "pipx").chmod(0o755)
    installed_kb4it(bindir)
    os.symlink(sys.executable, bindir / "python3")
    result = run(INSTALL, bindir, tmp_path, "--method", "pipx", "--wheel", make_wheel(tmp_path / "dist"))
    assert result.returncode == 0, result.stdout + result.stderr
    install = log.read_text(encoding="utf-8").splitlines()[0]
    assert install.startswith("pipx install --python ") and install.endswith(" --force " + str(tmp_path / "dist" / "kb4it-1.2.3-py3-none-any.whl"))


def test_an_old_python_is_refused(tmp_path):
    old = tmp_path / "python3.6"
    old.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    old.chmod(0o755)
    result = run(INSTALL, tmp_path / "bin", tmp_path, "--method", "venv", "--python", old,
                 "--wheel", make_wheel(tmp_path / "dist"))
    assert result.returncode == 1
    assert "needs Python 3.11 or newer" in result.stderr


def test_the_installed_command_must_report_the_wheel_build(tmp_path):
    fake_uv(tmp_path / "bin", tmp_path / "log", tmp_path / "bin")
    installed_kb4it(tmp_path / "bin", reports="1.2.3")
    result = run(INSTALL, tmp_path / "bin", tmp_path, "--wheel", make_wheel(tmp_path / "dist"))
    assert result.returncode == 1
    assert "the wheel is 'KB4IT 1.2.3-dev+4.gabcdef0'" in result.stderr


def test_another_kb4it_first_on_path_exits_2(tmp_path):
    fake_uv(tmp_path / "bin", tmp_path / "log", tmp_path / "tools")
    installed_kb4it(tmp_path / "tools")
    installed_kb4it(tmp_path / "bin", reports="0.0.1")  # an old install that comes first
    result = run(INSTALL, tmp_path / "bin", tmp_path, "--wheel", make_wheel(tmp_path / "dist"))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "another kb4it comes first on PATH" in result.stdout
    assert str(tmp_path / "bin" / "kb4it") in result.stdout


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_a_dirty_tree_is_refused_before_building(tmp_path):
    clone = tmp_path / "clone"
    script = clone / "scripts" / "install" / "local" / "install_kb4it_from_source.sh"
    script.parent.mkdir(parents=True)
    shutil.copy(INSTALL, script)
    (clone / "kb4it").mkdir()
    (clone / "kb4it" / "VERSION").write_text("1.2.3", encoding="utf-8")
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", HOME=str(tmp_path))
    for args in (["init", "-q"], ["add", "."], ["commit", "-q", "-m", "one"]):
        subprocess.run(["git", *args], cwd=clone, env=env, check=True, capture_output=True)
    (clone / "kb4it" / "VERSION").write_text("1.2.4", encoding="utf-8")
    (clone / "kb4it" / "new.py").write_text("", encoding="utf-8")
    log = tmp_path / "log"
    fake_uv(tmp_path / "bin", log, tmp_path / "bin")
    result = run(script, tmp_path / "bin", tmp_path)
    assert result.returncode == 1
    assert "kb4it/VERSION" in result.stdout and "kb4it/new.py" in result.stdout
    assert "--allow-dirty" in result.stderr
    assert "tool install" not in (log.read_text(encoding="utf-8") if log.exists() else "")


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


def test_uninstall_removes_the_source_installer_venv(tmp_path):
    venv = tmp_path / ".local" / "share" / "kb4it" / "venv"
    (venv / "bin").mkdir(parents=True)
    (venv / "bin" / "kb4it").write_text("", encoding="utf-8")
    link = tmp_path / ".local" / "bin" / "kb4it"
    link.parent.mkdir(parents=True)
    link.symlink_to(venv / "bin" / "kb4it")
    (tmp_path / "bin").mkdir()
    result = run(UNINSTALL, tmp_path / "bin", tmp_path)
    assert result.returncode == 0, result.stderr
    assert not venv.exists() and not link.is_symlink()


def test_uninstall_keeps_a_link_that_is_not_the_venv(tmp_path):
    venv = tmp_path / ".local" / "share" / "kb4it" / "venv"
    venv.mkdir(parents=True)
    link = tmp_path / ".local" / "bin" / "kb4it"
    link.parent.mkdir(parents=True)
    link.symlink_to(tmp_path / "elsewhere")
    (tmp_path / "bin").mkdir()
    assert run(UNINSTALL, tmp_path / "bin", tmp_path).returncode == 0
    assert not venv.exists() and link.is_symlink()


def test_uninstall_has_no_unsafe_pip_options():
    text = UNINSTALL.read_text(encoding="utf-8")
    assert "--trusted-host" not in text
    assert "pip install" not in text

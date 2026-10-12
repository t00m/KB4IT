"""The distribution, install and uninstall shell scripts parse, and every script they call exists."""

import os
import re
import shutil
import subprocess
import sys
import zipfile

import pytest

from tests.helpers import ROOT

SCRIPT_DIRS = [ROOT / "scripts" / "distribution", ROOT / "scripts" / "install", ROOT / "scripts" / "uninstall"]
DIST = ROOT / "scripts" / "distribution"
BASH = shutil.which("bash")

# "${SCRIPT_DIR}/x.sh", "${DIST_DIR}/x.sh" and "$(dirname "${BASH_SOURCE[0]}")/x.sh"
_CALLS = re.compile(r'\$\{(SCRIPT_DIR|DIST_DIR)\}/([\w./-]+\.sh)|\$\(dirname "\$\{BASH_SOURCE\[0\]\}"\)/([\w./-]+\.sh)')


def _scripts():
    return sorted(p for d in SCRIPT_DIRS for p in d.rglob("*.sh"))


def _calls(path):
    for match in _CALLS.finditer(path.read_text(encoding="utf-8")):
        if match.group(1) == "DIST_DIR":
            yield DIST / match.group(2)
        else:
            yield path.parent / (match.group(2) or match.group(3))


def test_scripts_found():
    names = {p.name for p in _scripts()}
    assert {"build_python.sh", "common.sh", "build_deb.sh", "build_rpm.sh", "build.sh", "uninstall.sh"} <= names


@pytest.mark.parametrize("path", _scripts(), ids=lambda p: str(p.relative_to(ROOT)))
def test_called_scripts_exist(path):
    for called in _calls(path):
        assert called.resolve().is_file(), f"{path.relative_to(ROOT)} calls missing {called}"


@pytest.mark.skipif(shutil.which("git") is None or not (ROOT / ".git").exists(), reason="not a git checkout")
def test_scripts_tracked_by_git():
    """A .gitignore pattern such as build/ once kept build_python.sh out of the repository."""
    for path in _scripts():
        rel = path.relative_to(ROOT).as_posix()
        ignored = subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT)
        assert ignored.returncode == 1, f"{rel} is ignored by .gitignore"


@pytest.mark.skipif(BASH is None, reason="bash not installed")
@pytest.mark.parametrize("path", _scripts(), ids=lambda p: str(p.relative_to(ROOT)))
def test_script_parses(path):
    result = subprocess.run([BASH, "-n", str(path)], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr


@pytest.mark.skipif(sys.platform == "win32" or shutil.which("uv") is None, reason="needs uv and a POSIX shell")
def test_build_python_makes_wheel_and_sdist(tmp_path):
    out = tmp_path / "dist"
    out.mkdir()
    (out / "kb4it-0.0.1-py3-none-any.whl").write_bytes(b"stale")
    env = dict(os.environ, KB4IT_DIST_OUT=str(out))
    subprocess.run([BASH, str(DIST / "build" / "build_python.sh")], check=True, env=env, capture_output=True)
    version = (ROOT / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()
    built = sorted(p.name for p in out.iterdir() if not p.name.startswith("."))  # uv adds a .gitignore
    assert built == [f"kb4it-{version}-py3-none-any.whl", f"kb4it-{version}.tar.gz"]
    names = zipfile.ZipFile(out / f"kb4it-{version}-py3-none-any.whl").namelist()
    for theme in ("techdoc", "blog", "bookshelf", "apphelp"):
        assert any(n.startswith(f"kb4it/resources/themes/{theme}/") for n in names), theme


def _dist_files():
    return [p for p in DIST.rglob("*") if p.is_file() and p.suffix in ("", ".sh", ".spec", ".md")
            and "__pycache__" not in p.parts]


def test_no_script_names_the_old_changelog():
    for path in _dist_files():
        assert not re.search(r"\bChangelog\b", path.read_text(encoding="utf-8")), path.relative_to(ROOT)


def test_packages_share_one_description():
    common = (DIST / "lib" / "common.sh").read_text(encoding="utf-8")
    assert re.search(r'^KB4IT_DESCRIPTION=".*Themes: techdoc, blog, bookshelf, apphelp\."$', common, re.M)
    assert "${KB4IT_DESCRIPTION}" in (DIST / "deb" / "build_deb.sh").read_text(encoding="utf-8")
    assert "%{kb4it_description}" in (DIST / "rpm" / "kb4it.spec").read_text(encoding="utf-8")
    assert "${KB4IT_DESCRIPTION}" in (DIST / "docker" / "Dockerfile").read_text(encoding="utf-8")
    for path in _dist_files():
        assert "book, blog" not in path.read_text(encoding="utf-8"), path.relative_to(ROOT)


@pytest.mark.skipif(BASH is None, reason="bash not installed")
def test_download_wheels_needs_a_known_architecture():
    result = subprocess.run([BASH, str(DIST / "wheels" / "download_wheels.sh"), "sparc"], capture_output=True,
                            text=True, encoding="utf-8")
    assert result.returncode == 1 and "Usage" in result.stderr


def test_package_pythons_cover_the_supported_range():
    common = (DIST / "lib" / "common.sh").read_text(encoding="utf-8")
    assert "KB4IT_PYTHONS=(3.11 3.12 3.13)" in common

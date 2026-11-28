"""kb4it install-theme and kb4it uninstall-theme."""

import json
from pathlib import Path

import pytest

from kb4it.core import projects, themeinstall
from kb4it.core.env import ENV
from kb4it.core.themecli import run_uninstall_theme
from tests.core.test_themeinstall import mini_zip
from tests.helpers import run_kb4it, write_repo


@pytest.fixture
def kb4it_home(tmp_path, monkeypatch):
    """In-process KB4IT_HOME with its own project list."""
    root = tmp_path / "kbhome"
    monkeypatch.setitem(ENV["LPATH"], "ROOT", str(root))
    monkeypatch.setitem(ENV["LPATH"], "VAR", str(root / "var"))
    monkeypatch.setitem(ENV["LPATH"], "THEMES", str(root / "opt" / "resources" / "themes"))
    monkeypatch.setattr(projects, "PROJECTS_FILE", root / "projects.json")
    return root


def local(root, theme_id):
    return root / "opt" / "resources" / "themes" / theme_id


# install-theme, as a command

def test_install_theme_command_prints_version_and_replacement(tmp_path, home):
    zip_path = mini_zip(tmp_path)
    first = run_kb4it("install-theme", zip_path, cwd=tmp_path, home=home, split_streams=True)
    assert first.returncode == 0, first.stderr
    assert "Installed mini 0.1.0 in " in first.stdout
    assert (home / ".kb4it" / "opt" / "resources" / "themes" / "mini" / "theme.json").is_file()
    second = run_kb4it("install-theme", zip_path, cwd=tmp_path, home=home, split_streams=True)
    assert second.returncode == 0, second.stderr
    assert "replacing 0.1.0" in second.stdout


def test_install_theme_command_over_bundled_says_so(tmp_path, home):
    zip_path = mini_zip(tmp_path, top="techdoc", id="techdoc")
    result = run_kb4it("install-theme", zip_path, cwd=tmp_path, home=home, split_streams=True)
    assert result.returncode == 0, result.stderr
    assert "takes the place of the bundled techdoc" in result.stdout


def test_install_theme_refused_exits_1(tmp_path, home):
    zip_path = mini_zip(tmp_path, id="other")
    result = run_kb4it("install-theme", zip_path, cwd=tmp_path, home=home, split_streams=True)
    assert result.returncode == 1
    assert "must equal the id in theme.json" in result.stderr
    assert "THEME_INSTALL_REFUSED" not in result.stderr
    assert not (home / ".kb4it" / "opt" / "resources" / "themes" / "mini").exists()


# uninstall-theme

def install_mini(tmp_path, top="mini"):
    return themeinstall.install_zip(mini_zip(tmp_path, top=top, id=top))


def test_uninstall_local_theme(tmp_path, kb4it_home, capsys):
    install_mini(tmp_path)
    assert run_uninstall_theme({"id": "mini", "yes": True}) == 0
    assert not local(kb4it_home, "mini").exists()
    assert "Uninstalled mini 0.1.0" in capsys.readouterr().out


def test_uninstall_bundled_refused(kb4it_home, capsys):
    assert run_uninstall_theme({"id": "techdoc", "yes": True}) == 1
    assert "bundled with KB4IT" in capsys.readouterr().err


@pytest.mark.parametrize("theme_id", ["nosuch", "../themes", ".."])
def test_uninstall_unknown_refused(kb4it_home, capsys, theme_id):
    assert run_uninstall_theme({"id": theme_id, "yes": True}) == 1
    assert "not installed" in capsys.readouterr().err


def test_uninstall_warns_about_projects(tmp_path, kb4it_home, capsys):
    install_mini(tmp_path)
    install_mini(tmp_path, top="techdoc")
    mini_repo = write_repo(tmp_path / "a", "mini", {})
    techdoc_repo = write_repo(tmp_path / "b", "techdoc", {})
    projects.register(str(mini_repo), pid="alpha")
    projects.register(str(techdoc_repo), pid="beta")
    assert [p["id"] for p in themeinstall.projects_using("mini")] == ["alpha"]

    assert run_uninstall_theme({"id": "mini", "yes": True}) == 0
    out = capsys.readouterr().out
    assert "alpha" in out and "fail" in out

    assert run_uninstall_theme({"id": "techdoc", "yes": True}) == 0
    out = capsys.readouterr().out
    assert "beta" in out and "bundled techdoc" in out
    assert local(kb4it_home, "techdoc").exists() is False


def test_uninstall_confirmation(tmp_path, kb4it_home, capsys):
    install_mini(tmp_path)
    assert run_uninstall_theme({"id": "mini"}, ask=lambda _: "no", interactive=True) == 1
    assert local(kb4it_home, "mini").exists()
    assert run_uninstall_theme({"id": "mini"}, interactive=False) == 1
    assert "--yes" in capsys.readouterr().err
    assert local(kb4it_home, "mini").exists()
    assert run_uninstall_theme({"id": "mini"}, ask=lambda _: "mini", interactive=True) == 0
    assert not local(kb4it_home, "mini").exists()

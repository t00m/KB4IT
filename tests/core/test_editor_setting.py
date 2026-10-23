"""ET-04: the repo.json 'editor' setting turns the Add page on or off."""

import json

import pytest

from tests.core.test_highlight import _app_conf
from tests.helpers import page, run_kb4it, write_repo

DOCS = {"note.md": page("Note", Category="Note", Date="2026-10-01")}


@pytest.fixture()
def home(tmp_path):
    path = tmp_path / "home"
    path.mkdir()
    return path


def build(base, home, theme, **conf):
    cfg = write_repo(base, theme, DOCS, **{**_app_conf(theme), **conf})
    return cfg, run_kb4it("build", cfg, cwd=base, home=home)


def all_html(target):
    return [p.read_text(encoding="utf-8") for p in target.rglob("*.html")]


def test_editor_must_be_bool(tmp_path, home):
    cfg, result = build(tmp_path, home, "techdoc", editor="yes")
    assert result.returncode != 0
    assert "repo.json 'editor' must be true or false" in result.stdout
    verify = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert "repo.json 'editor' must be true or false" in verify.stdout


def test_default_comes_from_theme(tmp_path, home):
    _, result = build(tmp_path / "a", home, "techdoc")
    assert result.returncode == 0, result.stdout
    assert (tmp_path / "a" / "target" / "add.html").exists()
    _, result = build(tmp_path / "b", home, "blog")
    assert result.returncode == 0, result.stdout
    assert not (tmp_path / "b" / "target" / "add.html").exists()


def test_repo_overrides_theme(tmp_path, home):
    _, result = build(tmp_path, home, "techdoc", editor=False)
    assert result.returncode == 0, result.stdout
    target = tmp_path / "target"
    assert not (target / "add.html").exists()
    assert 'href="add.html"' not in (target / "index.html").read_text(encoding="utf-8")


def test_editor_off_removes_page_and_link(tmp_path, home):
    cfg, result = build(tmp_path, home, "techdoc")
    assert result.returncode == 0, result.stdout
    target = tmp_path / "target"
    assert (target / "add.html").exists()
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["editor"] = False
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert not (target / "add.html").exists()
    assert not (target / "resources" / "editor").exists()
    assert not [h for h in all_html(target) if "add.html" in h]


def test_add_page_log(tmp_path, home):
    _, result = build(tmp_path, home, "techdoc", editor=False)
    assert result.returncode == 0, result.stdout
    log = (tmp_path / "var" / "log" / "kb4it.log").read_text(encoding="utf-8")
    assert "[BUILDER] ADD_PAGE enabled=False" in log

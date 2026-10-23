"""Review fixes of the editor in every theme: add_page flag, theme.json check, sitemap, skeleton ids."""

import os

import pytest

from kb4it.services.addpage import editor_on
from tests.core.test_highlight import _app_conf
from tests.helpers import mini_theme, page, run_kb4it, write_repo

DOCS = {"note.md": page("Note", Category="Note", Date="2026-10-01"), "add.md": page("Mine", Category="Note")}


def log_of(base):
    return (base / "var" / "log" / "kb4it.log").read_text(encoding="utf-8")


@pytest.mark.parametrize("repo,theme,expected", [
    ({}, {}, False),
    ({}, {"editor": True}, True),
    ({"editor": False}, {"editor": True}, False),
    ({"editor": True}, {}, True),
    ({"editor": "yes"}, {"editor": True}, False),
])
def test_editor_on(repo, theme, expected):
    assert editor_on(repo, theme) is expected


def test_theme_without_add_page_keeps_add_md(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", editor=True)
    cfg = write_repo(tmp_path / "repo", "mini", DOCS, theme_path=str(theme), editor=True)
    result = run_kb4it("build", cfg, cwd=tmp_path / "repo", home=home)
    assert result.returncode == 0, result.stdout
    assert "DOC_NAME_RESERVED" not in log_of(tmp_path / "repo")
    assert (tmp_path / "repo" / "target" / "add.html").exists()
    verify = run_kb4it("verify", cfg, cwd=tmp_path / "repo", home=home)
    assert "add.md" not in verify.stdout


def test_theme_editor_must_be_bool(tmp_path, home):
    theme = mini_theme(tmp_path / "mini", editor="yes")
    cfg = write_repo(tmp_path / "repo", "mini", DOCS, theme_path=str(theme))
    for command in ("build", "verify"):
        result = run_kb4it(command, cfg, cwd=tmp_path / "repo", home=home)
        assert "theme.json 'editor' must be true or false" in log_of(tmp_path / "repo")
        assert "mini" in log_of(tmp_path / "repo")
        if command == "build":
            assert result.returncode != 0


def test_add_page_not_in_sitemap(tmp_path, home):
    cfg = write_repo(tmp_path, "techdoc", {"note.md": DOCS["note.md"]}, **_app_conf("techdoc"),
                     site_url="https://ex.org/kb")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert (tmp_path / "target" / "add.html").exists()
    assert "add.html" not in (tmp_path / "target" / "sitemap.xml").read_text(encoding="utf-8")


def _case_sensitive(path):
    probe = path / "Probe"
    probe.write_text("x", encoding="utf-8")
    try:
        return not os.path.exists(path / "probe")
    finally:
        probe.unlink()


def test_same_skeleton_id_twice(tmp_path, home):
    cfg = write_repo(tmp_path, "techdoc", {"note.md": DOCS["note.md"]})
    skel = tmp_path / "overrides" / "templates" / "skeletons"
    skel.mkdir(parents=True)
    if not _case_sensitive(skel):
        pytest.skip("case-insensitive file system")
    for name in ("FOO-SKELETON.md", "Foo-SKELETON.md"):
        (skel / name).write_text("---\nDate: YYYY-MM-DD\n---\n\n# T\n", encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode != 0
    assert "give the same id 'foo'" in log_of(tmp_path)
    assert str(skel) in log_of(tmp_path)

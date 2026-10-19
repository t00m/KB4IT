"""File names that would break a site on another operating system are reported the same way everywhere."""

import pytest

from kb4it.core import util
from tests.helpers import page, run_kb4it, write_repo


@pytest.mark.parametrize("name, reserved", [
    ("con.md", True), ("CON.md", True), ("nul.markdown", True), ("com1.md", True), ("lpt9.md", True),
    ("Aux.notes.md", True), ("console.md", False), ("com10.md", False), ("notes.md", False),
])
def test_windows_reserved_names(name, reserved):
    assert util.is_windows_reserved(name) is reserved


def test_page_name_clashes():
    docs = ["Foo.md", "foo.md", "bar.md", "bar.markdown", "baz.md"]
    assert sorted(util.page_name_clashes(docs)) == [("Foo.md", "foo.md"), ("bar.markdown", "bar.md")]


def test_reserved_name_is_left_out(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"con.md": page("Con", Tag="x"), "ok.md": page("Ok", Tag="y")})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "DOC_NAME_RESERVED doc=con.md" in result.stdout
    assert (tmp_path / "repo" / "target" / "ok.html").exists()
    assert not (tmp_path / "repo" / "target" / "con.html").exists()


def test_clash_warns_and_fails_with_fail_on_invalid(tmp_path, home):
    # .md and .markdown with the same stem clash on every file system, so this runs on all of them.
    pages = {"note.md": page("One", Tag="x"), "note.markdown": page("Two", Tag="y")}
    cfg = write_repo(tmp_path / "warn", "techdoc", pages)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "DOC_NAME_CLASH a=note.markdown b=note.md" in result.stdout
    cfg = write_repo(tmp_path / "fail", "techdoc", pages, fail_on_invalid=True)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "name_clash_with=note.markdown" in result.stdout


def test_verify_reports_reserved_names_and_clashes(tmp_path, home):
    pages = {"nul.md": page("Nul", Tag="x"), "note.md": page("One", Tag="x"), "note.markdown": page("Two", Tag="y")}
    cfg = write_repo(tmp_path / "repo", "techdoc", pages)
    result = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "nul.md (Reason: reserved_name)" in result.stdout
    assert "note.md (Reason: name_clash_with=note.markdown)" in result.stdout

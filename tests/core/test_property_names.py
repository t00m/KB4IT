"""Property names and values always make a usable page name (SC-03)."""

import pytest

from kb4it.core.util import get_markdown_attributes, valid_filename
from tests.helpers import run_kb4it, write_repo


@pytest.mark.parametrize("raw, clean", [
    (".note", "note"), ("..escaped", "escaped"), ("../../escaped", "escaped"), ("a.b", "a.b"),
    ("john's portrait in 2004.jpg", "johns_portrait_in_2004.jpg"), ("...", ""), ("???", ""),
])
def test_valid_filename_never_starts_with_a_dot(raw, clean):
    assert valid_filename(raw) == clean


def _doc(tmp_path, frontmatter):
    path = tmp_path / "doc.md"
    path.write_text(f"---\n{frontmatter}\n---\n# Doc\n\nText.\n", encoding="utf-8")
    return get_markdown_attributes(str(path))


def test_name_that_cleans_to_nothing_is_invalid(tmp_path):
    assert _doc(tmp_path, '"...": a') == ({}, False, "bad_property_name key=...")
    assert _doc(tmp_path, 'Tag: "???"') == ({}, False, "bad_property_value key=Tag")
    assert _doc(tmp_path, "Tag: a, , b")[1] is True  # an empty item is not a bad value


def test_dot_property_builds_the_site(tmp_path, home):
    """The audit reproduction of SEC-03: ".note: a" left the site without index.html."""
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {"a.md": "---\n.note: a\n---\n# A\n\nText.\n"})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert (repo / "target" / "index.html").is_file()
    assert (repo / "target" / "note.html").is_file()
    assert not list((repo / "target").glob(".*.html"))


def test_unusable_property_is_reported_and_the_rest_built(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {"bad.md": '---\n"...": a\n---\n# Bad\n\nText.\n',
                                        "good.md": "---\nTag: x\n---\n# Good\n\nText.\n"})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "DOC_INVALID doc=bad.md reason=bad_property_name key=..." in result.stdout
    assert "invalid=1" in result.stdout
    assert (repo / "target" / "good.html").is_file() and (repo / "target" / "index.html").is_file()
    verify = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert verify.returncode == 1 and "bad_property_name key=..." in verify.stdout

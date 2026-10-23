"""Yes, No, On, Off, True and False in a header stay as written; YAML would read them as booleans."""

import pytest

from kb4it.core.documents import get_markdown_attributes, is_yes, load_frontmatter
from tests.helpers import page, run_kb4it, write_repo


@pytest.mark.parametrize("raw,expected", [
    ("Yes", ["Yes"]), ("no", ["no"]), ("ON", ["ON"]), ("off", ["off"]), ("True", ["True"]), ("false", ["false"]),
    ("[yes, No, x]", ["yes", "No", "x"]), ("Yes, No", ["Yes", "No"]),
    # Other types are read as before.
    ("12", ["12"]), ("2026-10-22", ["2026-10-22"]), ("~", []), ("", []),
])
def test_yes_no_values_stay_as_written(tmp_path, raw, expected):
    path = tmp_path / "doc.md"
    path.write_text(f"---\nK: {raw}\n---\n\n# Heading\n", encoding="utf-8")
    keys, ok, _reason = get_markdown_attributes(str(path))
    assert ok
    assert keys["K"] == expected


def test_load_frontmatter_keeps_booleans_as_text():
    assert load_frontmatter("Bookmark: Yes\nPublic: no") == {"Bookmark": "Yes", "Public": "no"}
    assert load_frontmatter("Order: 10\nEmpty:") == {"Order": 10, "Empty": None}


@pytest.mark.parametrize("value,expected", [
    ("Yes", True), ("yes", True), ("YES", True), ("True", True), ("true", True), ("on", True), (" Yes ", True),
    ("No", False), ("False", False), ("off", False), ("", False), ("maybe", False),
])
def test_is_yes(value, expected):
    assert is_yes(value) is expected


def test_bookmarks_page_lists_every_spelling_of_yes(tmp_path, home):
    repo = tmp_path / "repo"
    pages = {
        "a.md": page("Alpha", Date="2026-01-01", Bookmark="Yes"),
        "b.md": page("Beta", Date="2026-01-02", Bookmark="yes"),
        "c.md": page("Gamma", Date="2026-01-03", Bookmark="true"),
        "d.md": page("Delta", Date="2026-01-04", Bookmark="No"),
    }
    cfg = write_repo(repo, "techdoc", pages)
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    bookmarks = (repo / "target" / "bookmarks.html").read_text(encoding="utf-8")
    assert all(f'href="{name}.html"' in bookmarks for name in ("a", "b", "c"))
    assert 'href="d.html"' not in bookmarks
    # Property pages are named after the value as written, not True or False.
    assert (repo / "target" / "Bookmark_Yes.html").exists()
    assert (repo / "target" / "Bookmark_No.html").exists()
    assert not (repo / "target" / "Bookmark_True.html").exists()

"""Author profiles in the build: kept apart from documents, rebuilds, links."""

import json
from unittest.mock import ANY

from tests.helpers import page, run_kb4it, write_repo

PROFILE = page("Jane Doe", "Bio.", Person="Jane Doe", Alias="J. Doe", Email="j@x.org")


def doc(title, body="Text.", **keys):
    keys.setdefault("Category", "Note")
    keys.setdefault("DocType", "Reference")
    keys.setdefault("Tag", "x")
    return page(title, body, **keys)


def kbdict(repo):
    return json.loads((repo / "var" / "db" / "kbdict.json").read_text(encoding="utf-8"))


def build(tmp_path, home, pages, *flags, **config):
    cfg = write_repo(tmp_path / "repo", "techdoc", pages, **config)
    return cfg, run_kb4it(*flags, "build", cfg, cwd=tmp_path, home=home)


def test_profile_is_not_a_document(tmp_path, home):
    _cfg, result = build(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": PROFILE})
    assert result.returncode == 0, result.stdout
    assert "[PEOPLE] LOADED profiles=1 aliases=1" in result.stdout
    repo = tmp_path / "repo"
    assert not (repo / "target" / "PERSON-JANE-DOE.html").exists()
    data = kbdict(repo)
    assert "PERSON-JANE-DOE.md" not in data["document"]
    assert data["profiles"]["PERSON-JANE-DOE.md"] == {"person": "Jane Doe", "aliases": ["J. Doe"], "hash": ANY,
                                                      "status": "ok"}
    assert "Bio." not in (repo / "target" / "search-index.js").read_text(encoding="utf-8")


def test_invalid_profile_is_left_out(tmp_path, home):
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": page("Jane", Person="Doe, Jane")}
    _cfg, result = build(tmp_path, home, pages)
    assert result.returncode == 0, result.stdout
    assert "[PEOPLE] PROFILE_INVALID doc=PERSON-JANE-DOE.md" in result.stdout
    assert kbdict(tmp_path / "repo")["profiles"] == {}


def test_invalid_profile_fails_with_fail_on_invalid(tmp_path, home):
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": page("Jane", Person="Doe, Jane")}
    _cfg, result = build(tmp_path, home, pages, fail_on_invalid=True)
    assert result.returncode != 0, result.stdout


def test_invalid_frontmatter_stays_doc_invalid(tmp_path, home):
    broken = "---\nPerson: [Jane\n---\n\n# Jane\n\nBio.\n"
    _cfg, result = build(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": broken})
    assert result.returncode == 0, result.stdout
    assert "DOC_INVALID doc=PERSON-JANE-DOE.md" in result.stdout
    assert "[PEOPLE] PROFILE_" not in result.stdout

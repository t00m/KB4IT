"""Author profiles in the build: kept apart from documents, rebuilds, links."""

import json
from unittest.mock import ANY

from tests.helpers import page, run_kb4it, write_repo

PROFILE = page("Jane Doe", "Bio.", Alias="J. Doe", Email="j@x.org")


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
                                                      "status": "ok", "tip": ""}
    assert "Bio." not in (repo / "target" / "search-index.js").read_text(encoding="utf-8")


def test_invalid_profile_is_left_out(tmp_path, home):
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": page("Doe, Jane")}
    _cfg, result = build(tmp_path, home, pages)
    assert result.returncode == 0, result.stdout
    assert "[PEOPLE] PROFILE_INVALID doc=PERSON-JANE-DOE.md" in result.stdout
    assert kbdict(tmp_path / "repo")["profiles"] == {}


def test_invalid_profile_fails_with_fail_on_invalid(tmp_path, home):
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": page("Doe, Jane")}
    _cfg, result = build(tmp_path, home, pages, fail_on_invalid=True)
    assert result.returncode != 0, result.stdout


def test_invalid_frontmatter_stays_doc_invalid(tmp_path, home):
    broken = "---\nAlias: [Jane\n---\n\n# Jane\n\nBio.\n"
    _cfg, result = build(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": broken})
    assert result.returncode == 0, result.stdout
    assert "DOC_INVALID doc=PERSON-JANE-DOE.md" in result.stdout
    assert "[PEOPLE] PROFILE_" not in result.stdout


def rebuild(tmp_path, home, cfg, changes):
    """Write or delete (None) source files, then build again with debug lines."""
    source = tmp_path / "repo" / "source"
    for name, text in changes.items():
        if text is None:
            (source / name).unlink()
        else:
            (source / name).write_text(text, encoding="utf-8")
    result = run_kb4it("-L", "DEBUG", "build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return result.stdout


def kv(key, value):
    return f"[PROCESSOR] KV key={key} value={value} compile=True"


def test_unchanged_profile_rebuilds_nothing(tmp_path, home):
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": PROFILE}
    cfg, _ = build(tmp_path, home, pages)
    out = rebuild(tmp_path, home, cfg, {})
    assert kv("Author", "Jane Doe") not in out
    assert "COMPILED doc=a.md" not in out


def test_profile_edit_forces_author_and_alias_pages(tmp_path, home):
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "b.md": doc("Beta", Author="J. Doe"),
             "PERSON-JANE-DOE.md": PROFILE}
    cfg, _ = build(tmp_path, home, pages)
    out = rebuild(tmp_path, home, cfg, {"PERSON-JANE-DOE.md": PROFILE.replace("Bio.", "New bio.")})
    assert kv("Author", "Jane Doe") in out and kv("Author", "J. Doe") in out
    assert "COMPILED doc=a.md" not in out and "COMPILED doc=b.md" not in out


def test_profile_change_forces_every_people_key(tmp_path, home):
    pages = {"a.md": doc("Alpha", Owner="Jane Doe"), "PERSON-JANE-DOE.md": PROFILE}
    cfg, _ = build(tmp_path, home, pages, people={"keys": ["Author", "Owner"]})
    out = rebuild(tmp_path, home, cfg, {"PERSON-JANE-DOE.md": PROFILE.replace("Bio.", "New bio.")})
    assert kv("Owner", "Jane Doe") in out


def test_status_change_rebuilds_named_docs(tmp_path, home):
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "b.md": doc("Beta"), "PERSON-JANE-DOE.md": PROFILE}
    cfg, _ = build(tmp_path, home, pages)
    out = rebuild(tmp_path, home, cfg, {"PERSON-JANE-DOE.md": PROFILE.replace("Email: j@x.org\n", "")})
    assert "COMPILED doc=a.md" in out
    assert "COMPILED doc=b.md" not in out


def test_first_profile_rebuilds_named_docs(tmp_path, home):
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "c.md": doc("Gamma", Author="Bob"), "d.md": doc("Delta")}
    cfg, _ = build(tmp_path, home, pages)
    out = rebuild(tmp_path, home, cfg, {"PERSON-JANE-DOE.md": PROFILE})
    assert "COMPILED doc=c.md" in out and "COMPILED doc=a.md" in out
    assert "COMPILED doc=d.md" not in out


def test_last_profile_removed_rebuilds_named_docs(tmp_path, home):
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "c.md": doc("Gamma", Author="Bob"), "d.md": doc("Delta"),
             "PERSON-JANE-DOE.md": PROFILE}
    cfg, _ = build(tmp_path, home, pages)
    out = rebuild(tmp_path, home, cfg, {"PERSON-JANE-DOE.md": None})
    assert "COMPILED doc=c.md" in out and "COMPILED doc=a.md" in out
    assert "COMPILED doc=d.md" not in out


def test_link_to_profile_points_to_author_page(tmp_path, home):
    pages = {"a.md": doc("Alpha", "Ask [Jane](PERSON-JANE-DOE.md).", Author="Jane Doe"),
             "PERSON-JANE-DOE.md": PROFILE}
    _cfg, result = build(tmp_path, home, pages)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "repo" / "target" / "a.html").read_text(encoding="utf-8")
    # The Author chip links there too, so check the body link itself.
    assert '<a href="Author_Jane_Doe.html">Jane</a>' in html
    assert "PERSON-JANE-DOE.html" not in html
    assert "broken link to PERSON-JANE-DOE.md" not in html  # techdoc Quality tab
    assert "LINK_BROKEN" not in result.stdout


# A second profile that stays, so the "profiles in use" switch never flips in these tests.
ANN = page("Ann", Email="ann@x.org")


def _y(tmp_path):
    return (tmp_path / "repo" / "target" / "y.html").read_text(encoding="utf-8")


def test_new_profile_rebuilds_linking_pages(tmp_path, home):
    pages = {"y.md": doc("Why", "Ask [Jane](PERSON-X.md)."), "PERSON-ANN.md": ANN}
    cfg, _ = build(tmp_path, home, pages)
    out = rebuild(tmp_path, home, cfg, {"PERSON-X.md": PROFILE})
    assert "COMPILED doc=y.md" in out
    assert '<a href="Author_Jane_Doe.html">Jane</a>' in _y(tmp_path)


def test_renamed_person_rebuilds_linking_pages(tmp_path, home):
    pages = {"y.md": doc("Why", "Ask [Jane](PERSON-X.md)."), "PERSON-ANN.md": ANN, "PERSON-X.md": PROFILE}
    cfg, _ = build(tmp_path, home, pages)
    out = rebuild(tmp_path, home, cfg, {"PERSON-X.md": PROFILE.replace("# Jane Doe", "# Jane Smith")})
    assert "COMPILED doc=y.md" in out
    assert '<a href="Author_Jane_Smith.html">Jane</a>' in _y(tmp_path)


def test_person_key_does_not_make_a_profile(tmp_path, home):
    # Only the PERSON- prefix makes a profile; Person is an ordinary key in a document.
    pages = {"CHANGE-1.md": doc("Change one", Person="Ann, Bob, Carl"), "PERSON-ANN.md": ANN}
    _cfg, result = build(tmp_path, home, pages)
    assert result.returncode == 0, result.stdout
    assert (tmp_path / "repo" / "target" / "CHANGE-1.html").exists()
    assert "PROFILE_INVALID" not in result.stdout


def test_role_change_rebuilds_named_docs(tmp_path, home):
    # The role and team are the tooltip of the name on document pages.
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "b.md": doc("Beta"), "PERSON-JANE-DOE.md": PROFILE}
    cfg, _ = build(tmp_path, home, pages)
    out = rebuild(tmp_path, home, cfg, {"PERSON-JANE-DOE.md": PROFILE.replace("Email: j@x.org\n", "Email: j@x.org\nRole: DBA\n")})
    assert "COMPILED doc=a.md" in out
    assert "COMPILED doc=b.md" not in out

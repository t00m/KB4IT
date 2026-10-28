"""Author profiles on the pages: the profile card, alias pages, pages for profiles nobody names, buttons."""

import pytest

from tests.helpers import page, run_kb4it, write_repo

JANE = page("Jane Doe", "Bio with **bold**.", Person="Jane Doe", Role="Basis admin", Team="SAP Basis",
            Email="j@x.org", Phone="+34 600 000 000", Url="https://x.org/jane", Chat="jane.doe", Badge="42")


def doc(title, body="Text.", **keys):
    keys.setdefault("Category", "Note")
    keys.setdefault("DocType", "Reference")
    keys.setdefault("Tag", "x")
    return page(title, body, **keys)


def site(tmp_path, home, pages, theme="techdoc", **config):
    cfg = write_repo(tmp_path / "repo", theme, pages, **config)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return tmp_path / "repo" / "target"


def html(target, name):
    return (target / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf"])
def test_card_on_person_page(tmp_path, home, theme):
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": JANE}, theme)
    text = html(target, "Author_Jane_Doe.html")
    for piece in ('class="kb-profile', "Jane Doe", "Basis admin", 'href="mailto:j@x.org"', 'href="tel:+34600000000"',
                  'href="https://x.org/jane"', "jane.doe", "<strong>bold</strong>"):
        assert piece in text, piece
    assert text.index("https://x.org/jane") < text.index("Badge")
    assert "a.html" in text  # the documents table is still there


def test_no_card_without_profile(tmp_path, home):
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="Bob"), "PERSON-JANE-DOE.md": JANE}, editor=False)
    assert "kb-profile" not in html(target, "Author_Bob.html")
    assert "kb-profile" not in html(target, "Tag_x.html")


def test_no_card_on_other_keys_with_editor_on(tmp_path, home):
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": JANE}, editor=True)
    assert "kb-profile" not in html(target, "Tag_x.html")


def test_private_keys_left_out(tmp_path, home):
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": JANE},
                  people={"private": ["Phone"]})
    text = html(target, "Author_Jane_Doe.html")
    assert "tel:" not in text and "+34 600" not in text


def test_card_escapes_values(tmp_path, home):
    profile = page("Jane Doe", "Bio.", Person="Jane Doe", Role="R&D <lead>")
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": profile})
    assert "R&amp;D &lt;lead&gt;" in html(target, "Author_Jane_Doe.html")


def test_card_body_links_are_redirected(tmp_path, home):
    profile = page("Jane Doe", "Works with [Ann](PERSON-ANN.md).", Person="Jane Doe")
    pages = {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": profile,
             "PERSON-ANN.md": page("Ann", Person="Ann")}
    target = site(tmp_path, home, pages)
    assert '<a href="Author_Ann.html">Ann</a>' in html(target, "Author_Jane_Doe.html")


def test_url_without_scheme_is_text(tmp_path, home):
    profile = page("Jane Doe", "Bio.", Person="Jane Doe", Url="x.org/jane")
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="Jane Doe"), "PERSON-JANE-DOE.md": profile})
    text = html(target, "Author_Jane_Doe.html")
    assert "x.org/jane" in text and 'href="x.org/jane"' not in text

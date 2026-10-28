"""The Add page offers a Person profile skeleton, except in apphelp."""

import json
import re
from pathlib import Path

import pytest

from kb4it.core.env import ENV
from tests.helpers import page, run_kb4it, write_repo

SKELETON = (
    "---\nEmail: name@example.org\nPerson: Full name\nRole: Role in the team\nTeam: Team name\n---\n\n"
    "# Full name\n\nWhat this person works on, and when to ask them.\n"
)


def doc(title):
    return page(title, Category="Note", DocType="Reference", Tag="x", Author="Bob")


def skeletons(tmp_path, home, theme, **config):
    cfg = write_repo(tmp_path / "repo", theme, {"a.md": doc("Alpha")}, editor=True, **config)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "repo" / "target" / "add.html").read_text(encoding="utf-8")
    found = re.search(r'id="kb-add-skeletons" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(found.group(1)), html


@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf"])
def test_add_page_offers_person_profile(tmp_path, home, theme):
    data, html = skeletons(tmp_path, home, theme)
    assert data["person"] == {"name": "Person profile", "text": SKELETON}
    assert "A person named in the documents: role, team and how to reach them." in html


def test_apphelp_has_no_person_profile(tmp_path, home):
    data, _html = skeletons(tmp_path, home, "apphelp", apphelp={"strict": False})
    assert "person" not in data


def test_own_person_skeleton_wins(tmp_path, home):
    own = tmp_path / "repo" / "overrides" / "templates" / "skeletons"
    own.mkdir(parents=True)
    (own / "PERSON-SKELETON.md").write_text("---\nPerson: Mine\n---\n\n# Mine\n", encoding="utf-8")
    (own / "NOTE-SKELETON.md").write_text("---\nTag: x\n---\n\n# Note\n", encoding="utf-8")
    data, _html = skeletons(tmp_path, home, "techdoc")
    assert data["person"]["text"] == "---\nPerson: Mine\n---\n\n# Mine\n"
    assert list(data).count("person") == 1


def test_person_skeleton_is_a_valid_profile(tmp_path, home):
    text = (Path(ENV["GPATH"]["TEMPLATES"]) / "profile" / "PERSON-SKELETON.md").read_text(encoding="utf-8")
    assert text == SKELETON
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": doc("Alpha"), "PERSON-X.md": text})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "[PEOPLE] LOADED profiles=1" in result.stdout

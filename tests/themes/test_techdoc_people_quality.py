"""techdoc quality: the profile checks in a build, and when they apply."""

import importlib.util
import logging
import sys
from types import SimpleNamespace

from tests.core.test_profile_card import JANE, doc, html, site
from tests.helpers import ROOT, page

LOGIC = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic"


def test_checks_are_off_without_any_profile(tmp_path, home):
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="Bob")})
    assert "Create a profile for Bob" not in html(target, "a.html")


def test_checks_apply_once_there_is_a_profile(tmp_path, home):
    quiet = page("Joe", "Bio.", ProfileOf="Author", Role="DBA")
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="Bob, Joe, Jane Doe"), "PROFILE-JANE-DOE.md": JANE,
                                   "PROFILE-JOE.md": quiet})
    text = html(target, "a.html")
    assert 'href="add.html#new=person&amp;title=Bob">Create a profile for Bob</a>' in text
    assert 'Add contact details to the profile of Joe</a>' in text and 'href="add.html#edit=PROFILE-JOE.md' in text
    assert "profile of Jane Doe" not in text and "profile for Jane Doe" not in text


def test_without_the_editor_the_check_links_to_the_guide(tmp_path, home):
    target = site(tmp_path, home, {"a.md": doc("Alpha", Author="Bob"), "PROFILE-JANE-DOE.md": JANE}, editor=False)
    assert 'href="quality-guide.html#check-author-profile">Create a profile for Bob</a>' in html(target, "a.html")


def test_author_profiles_setting():
    from tests.helpers import techdoc_module
    on = techdoc_module("qualityfeature").Quality.author_profiles_on

    def theme(profiles):
        return SimpleNamespace(db=SimpleNamespace(people=[None] * profiles), log=logging.getLogger("test"))

    assert on(theme(0), {"author_profiles": "auto"}) is False and on(theme(1), {"author_profiles": "auto"}) is True
    assert on(theme(0), {"author_profiles": True}) is True and on(theme(1), {"author_profiles": False}) is False
    assert on(theme(1), {"author_profiles": "maybe"}) is True

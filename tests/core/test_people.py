"""Author profiles: the repo.json "people" block, the profile registry and its rules."""

import json
import re

import pytest

from kb4it.core.exceptions import ConfigError
from kb4it.core.people import (PeopleSettings, build_people, load_people, named_people, notices, person_page,
                               person_status)
from tests.helpers import page, run_kb4it, write_repo


def test_defaults():
    assert load_people({}) == PeopleSettings()
    assert PeopleSettings().keys == ("Author",)
    assert PeopleSettings().contact_keys == ("Email", "Phone", "Chat", "Url")
    assert PeopleSettings().private == ()


def test_values_are_read():
    settings = load_people({"people": {"keys": ["Author", "Owner"], "private": ["Phone"]}})
    assert settings.keys == ("Author", "Owner") and settings.private == ("Phone",)


@pytest.mark.parametrize("block, words", [
    ([], "must be an object"),
    ({"map": {}}, "unknown key 'map'"),
    ({"keys": "Author"}, "'people.keys' must be a list"),
    ({"keys": []}, "'people.keys' must name at least one key"),
    ({"keys": ["Title"]}, "Title is a KB4IT key"),
    ({"keys": ["Person"]}, "Person is reserved"),
    ({"contact_keys": [""]}, "'people.contact_keys' must be a list of key names"),
    ({"private": ["Person"]}, "Person is reserved"),
])
def test_bad_values(block, words):
    with pytest.raises(ConfigError, match=re.escape(words)):
        load_people({"people": block})


def test_people_setting_rebuilds_every_page(tmp_path, home):
    pages = {"a.md": page("Alpha", Author="Jane Doe", Category="Note", DocType="Reference", Tag="x")}
    cfg = write_repo(tmp_path / "repo", "techdoc", pages)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["people"] = {"keys": ["Author", "Owner"]}
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "CORE_SIGNATURE_CHANGED" in result.stdout

S = PeopleSettings()


def entry(doc_id, **keys):
    """(doc_id, keys, text) as the processor hands a source to build_people."""
    parsed = {key: [v.strip() for v in value.split(",") if v.strip()] for key, value in keys.items()}
    front = "".join(f"{key}: {value}\n" for key, value in keys.items())
    return doc_id, parsed, f"---\n{front}---\n\n# Title\n\nBio.\n"


def test_profile_and_alias_lookup():
    people, problems = build_people([entry("PERSON-JANE.md", Person="Jane Doe", Alias="J. Doe, jdoe",
                                           Email="j@x.org")], S)
    assert not problems and len(people) == 1 and people.alias_count() == 2
    assert people.lookup("jdoe").person == "Jane Doe"
    assert people.lookup("Jane Doe").values == {"Email": ["j@x.org"]}
    assert people.lookup("Jane Doe").body.strip() == "Bio."
    assert people.names(people.lookup("J. Doe")) == ["Jane Doe", "J. Doe", "jdoe"]


def test_lookup_is_exact():
    people, _ = build_people([entry("P.md", Person="Jane Doe")], S)
    assert people.lookup("jane doe") is None


@pytest.mark.parametrize("entries, code, left_out", [
    ([entry("P.md", Person="Doe, Jane")], "PROFILE_INVALID", "P.md"),
    ([entry("P.md", Person="")], "PROFILE_INVALID", "P.md"),
    ([entry("A.md", Person="Jane"), entry("B.md", Person="Jane")], "PROFILE_DUPLICATE", "B.md"),
    ([entry("A.md", Person="Jane", Alias="JD"), entry("B.md", Person="John", Alias="JD")], "PROFILE_DUPLICATE", "B.md"),
    ([entry("A.md", Person="Jane", Alias="John"), entry("B.md", Person="John")], "PROFILE_ALIAS_IS_PERSON", "A.md"),
])
def test_problems(entries, code, left_out):
    people, problems = build_people(entries, S)
    assert [p.code for p in problems] == [code]
    assert problems[0].doc_id == left_out
    assert all(profile.doc_id != left_out for profile in people.profiles.values())


def test_status():
    people, _ = build_people([entry("A.md", Person="A"), entry("B.md", Person="B", Email="b@x.org"),
                              entry("C.md", Person="C", Teams="c")], S)
    assert person_status(None, S) == "missing"
    assert person_status(people.lookup("A"), S) == "no_contact"
    assert person_status(people.lookup("B"), S) == "ok"
    assert person_status(people.lookup("B"), PeopleSettings(private=("Email",))) == "no_contact"
    assert person_status(people.lookup("C"), PeopleSettings(contact_keys=("Teams",))) == "ok"


def test_person_page():
    assert person_page("Jane Doe", S) == "Author_Jane_Doe.html"
    assert person_page("Jane Doe", PeopleSettings(keys=("Owner", "Author"))) == "Owner_Jane_Doe.html"


def test_named_people():
    people, _ = build_people([entry("P.md", Person="Jane Doe", Alias="J. Doe")], S)
    values = {"Author": ["J. Doe", "Bob"], "Owner": ["Jane Doe"], "Tag": ["x"]}
    assert named_people(values, people, PeopleSettings(keys=("Author", "Owner"))) == ["Jane Doe", "Bob"]


def test_notices():
    people, _ = build_people([entry("P.md", Person="Jane Doe"), entry("Q.md", Person="Ann", Email="ann@x.org"),
                              entry("R.md", Person="Max", Phone="+34 600 000 000")], S)
    found = notices(people, {"Bob": 3, "Ann": 1, "Max": 1}, S, indexed=False)
    assert found["warning"] == ["PROFILE_NO_CONTACT person=Jane Doe doc=P.md"]
    assert found["information"] == ["AUTHOR_NO_PROFILE person=Bob docs=3", "PROFILE_UNUSED person=Jane Doe doc=P.md"]
    indexed = notices(people, {"Ann": 1, "Max": 1}, S, indexed=True)["information"]
    assert "PROFILE_CONTACT_PUBLIC person=Ann key=Email" in indexed
    assert "PROFILE_CONTACT_PUBLIC person=Max key=Phone" in indexed
    private = notices(people, {"Ann": 1}, PeopleSettings(private=("Email",)), indexed=True)["information"]
    assert not any("person=Ann key=Email" in line for line in private)


def test_no_profiles_no_author_notice():
    empty, _ = build_people([], S)
    assert notices(empty, {"Bob": 3}, S, indexed=False) == {"warning": [], "information": []}

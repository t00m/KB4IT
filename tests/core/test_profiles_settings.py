"""The repo.json profiles block, and the people block read in its place."""

import re

import pytest

from kb4it.core.exceptions import ConfigError
from kb4it.core.profiles import KeyProfile, load_profiles, people_settings


def test_default_is_author_as_person():
    s, notices = load_profiles({})
    assert s.people_keys() == ("Author",) and notices == []
    a = s.entry("Author")
    assert (a.type, a.missing, a.tip) == ("Person", "penalty", ("Role", "Team"))
    assert a.contact_keys == ("Email", "Phone", "Chat", "Url")
    assert s.entry("Team") == KeyProfile()


def test_profiles_block_is_read():
    s, _ = load_profiles({"profiles": {"Author": {"type": "Person", "missing": "penalty"},
                                       "Team": {"type": "Organization", "missing": "notice"}},
                          "profiles_private": ["Phone"]})
    assert s.entry("Team").type == "Organization" and s.entry("Team").missing == "notice"
    assert s.private == ("Phone",)
    assert people_settings(s).keys == ("Author",) and people_settings(s).private == ("Phone",)


def test_people_block_is_read_as_people_entries_and_reported():
    s, notices = load_profiles({"people": {"keys": ["Author", "Owner"], "private": ["Phone"]}})
    assert s.people_keys() == ("Author", "Owner") and s.private == ("Phone",)
    assert notices == ["PEOPLE_BLOCK_DEPRECATED"]


def test_profiles_wins_over_people():
    s, notices = load_profiles({"people": {"keys": ["Owner"]}, "profiles": {"Author": {"type": "Person"}}})
    assert s.people_keys() == ("Author",) and notices == ["PEOPLE_BLOCK_DEPRECATED"]


@pytest.mark.parametrize("block, fragment", [
    ({"Team": {"missing": "maybe"}}, "profiles.Team.missing"),
    ({"Team": {"colour": "red"}}, "profiles.Team"),
    ({"DueDate": {}}, "date key"),
    ({"Title": {}}, "KB4IT key"),
    ({"Team": {"contact_keys": "Email"}}, "profiles.Team.contact_keys"),
    (["Team"], "profiles"),
])
def test_bad_blocks_stop_the_build(block, fragment):
    with pytest.raises(ConfigError, match=re.escape(fragment)):
        load_profiles({"profiles": block})


def test_people_settings_without_person_keys_falls_back_to_author():
    s, _ = load_profiles({"profiles": {"Team": {"type": "Organization"}}})
    assert people_settings(s).keys == ("Author",)


def test_people_settings_carries_contact_keys_and_map_of_the_first_person_key():
    s, _ = load_profiles({"profiles": {"Author": {"type": "Person", "contact_keys": ["Email"],
                                                  "map": {"Badge": "identifier"}}}})
    ps = people_settings(s)
    assert ps.contact_keys == ("Email",) and ps.map == {"Badge": "identifier"}

"""The generic profile registry: PROFILE- files, ProfileOf, profiles found by key and name."""

import pytest

from kb4it.core.people import PeopleSettings, build_people, is_legacy_profile, is_profile

S = PeopleSettings()


def entry(doc_id, title, **keys):
    return (doc_id, {"Title": [title], **{k: [v] if isinstance(v, str) else v for k, v in keys.items()}},
            f"# {title}\n")


def test_profile_prefix_and_legacy_prefix():
    assert is_profile("PROFILE-SAP-BASIS.md") and is_profile("profile-x.md") and is_profile("PERSON-JANE.md")
    assert is_legacy_profile("person-jane.md") and not is_legacy_profile("PROFILE-JANE.md")


def test_profile_without_profileof_is_invalid():
    people, problems = build_people([entry("PROFILE-SAP-BASIS.md", "SAP Basis")], S)
    assert len(people.all_profiles()) == 0
    assert [(p.code, p.detail) for p in problems] == [("PROFILE_INVALID", "ProfileOf is missing")]


def test_legacy_profile_defaults_to_the_first_people_key():
    people, problems = build_people([entry("PERSON-JANE.md", "Jane Doe")], S)
    assert problems == [] and people.lookup("Jane Doe").keys == ("Author",)


@pytest.mark.parametrize("target", ["DueDate", "Title", "Alias"])
def test_refused_targets_are_invalid(target):
    _, problems = build_people([entry("PROFILE-X.md", "X", ProfileOf=target)], S,
                               refused=frozenset({"DueDate", "Title", "Alias", "ProfileOf"}))
    assert [p.code for p in problems] == ["PROFILE_INVALID"] and target in problems[0].detail


def test_same_title_under_two_keys_is_two_profiles():
    people, problems = build_people([entry("PROFILE-SAP-TEAM.md", "SAP", ProfileOf="Team"),
                                     entry("PROFILE-SAP-PRODUCT.md", "SAP", ProfileOf="Product")], S)
    assert problems == []
    assert people.lookup("SAP", "Team").doc_id == "PROFILE-SAP-TEAM.md"
    assert people.lookup("SAP", "Product").doc_id == "PROFILE-SAP-PRODUCT.md"
    assert people.lookup("SAP") is None and len(people) == 0


def test_people_keys_share_a_profile():
    settings = PeopleSettings(keys=("Author", "Owner"))
    people, _ = build_people([entry("PROFILE-JANE.md", "Jane Doe", ProfileOf="Author")], settings)
    assert people.lookup("Jane Doe", "Owner") is people.lookup("Jane Doe", "Author") is people.lookup("Jane Doe")
    assert len(people) == 1 and list(people.profiles) == ["Jane Doe"]


def test_duplicate_is_per_key():
    _, problems = build_people([entry("PROFILE-A.md", "SAP", ProfileOf="Team"),
                                entry("PROFILE-B.md", "SAP", ProfileOf="Team")], S)
    assert [p.code for p in problems] == ["PROFILE_DUPLICATE"]


def test_alias_that_is_another_name_under_the_same_key():
    _, problems = build_people([entry("PROFILE-A.md", "SAP Basis", ProfileOf="Team", Alias="Basis"),
                                entry("PROFILE-B.md", "Basis", ProfileOf="Team")], S)
    assert [p.code for p in problems] == ["PROFILE_ALIAS_IS_NAME"]


def test_profileof_and_alias_are_not_profile_values():
    people, _ = build_people([entry("PROFILE-T.md", "SAP Basis", ProfileOf="Team", Lead="Jane Doe")], S)
    assert people.lookup("SAP Basis", "Team").values == {"Lead": ["Jane Doe"]}


def test_alias_count_covers_every_key():
    people, _ = build_people([entry("PROFILE-T.md", "SAP Basis", ProfileOf="Team", Alias="Basis"),
                              entry("PROFILE-J.md", "Jane Doe", ProfileOf="Author", Alias="JD")], S)
    assert people.alias_count() == 2 and len(people.all_profiles()) == 2

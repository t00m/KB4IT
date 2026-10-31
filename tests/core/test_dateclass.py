"""Date class: the reserved and declared date keys, the time zone, and how values are parsed."""

from zoneinfo import ZoneInfo

import pytest

from kb4it.core.dateclass import load_dates


def test_defaults_without_settings():
    settings, notices = load_dates({})
    assert settings.timezone is None
    assert settings.keys["ScheduledEnd"].closes == "ScheduledStart"
    assert settings.keys["DueDate"].closes == "Date"
    assert settings.keys["Modified"].group is None
    assert notices == ["TIMEZONE_UNSET"]


def test_timezone_is_read():
    settings, notices = load_dates({"timezone": "Europe/Madrid"})
    assert settings.timezone == ZoneInfo("Europe/Madrid")
    assert notices == []


def test_invalid_timezone_falls_back_with_warning():
    settings, notices = load_dates({"timezone": "Mars/Base"})
    assert settings.timezone is None
    assert notices == ["TIMEZONE_INVALID value=Mars/Base"]


def test_declared_keys_join_the_class():
    repo = {"timezone": "UTC", "dates": {
        "WarrantyStart": {"group": "start"},
        "WarrantyEnd": {"group": "end", "closes": "WarrantyStart"},
        "RenewalDate": {"group": "end"},
        "MaintenanceStart": {"group": "start", "supersedes": True}}}
    settings, notices = load_dates(repo)
    assert settings.keys["WarrantyEnd"].closes == "WarrantyStart"
    assert settings.keys["RenewalDate"].closes == "Date"
    assert settings.keys["MaintenanceStart"].supersedes is True
    assert notices == []


@pytest.mark.parametrize("entry, reason", [
    ({"Date": {"group": "start"}}, "reserved"),
    ({"FooDate": {"group": "middle"}}, "group"),
    ({"FooEnd": {"group": "end", "closes": "Nowhere"}}, "closes"),
    ({"FooStart": "start"}, "entry"),
])
def test_bad_entries_are_ignored(entry, reason):
    settings, notices = load_dates({"timezone": "UTC", "dates": entry})
    name = next(iter(entry))
    assert name not in settings.keys or name == "Date"
    assert notices == [f"DATES_BLOCK_INVALID key={name} reason={reason}"]


def test_a_dates_block_that_is_not_an_object_is_ignored():
    settings, notices = load_dates({"timezone": "UTC", "dates": ["WarrantyEnd"]})
    assert set(settings.keys) == set(load_dates({})[0].keys)
    assert notices == ["DATES_BLOCK_INVALID key=dates reason=entry"]


def test_naming_rule_is_a_warning():
    settings, notices = load_dates({"timezone": "UTC", "dates": {"Warranty": {"group": "end"}}})
    assert settings.is_date("Warranty")
    assert notices == ["DATE_KEY_NAME key=Warranty"]


def test_reserved_names_from_other_features_are_refused():
    settings, notices = load_dates({"timezone": "UTC", "dates": {"AuthorDate": {"group": "end"}}},
                                   reserved_names=["AuthorDate"])
    assert not settings.is_date("AuthorDate")
    assert notices == ["DATES_BLOCK_INVALID key=AuthorDate reason=reserved"]

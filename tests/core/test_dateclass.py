"""Date class: the reserved and declared date keys, the time zone, and how values are parsed."""

import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from kb4it.core.dateclass import date_key_names, end_moment, load_dates, parse_date, stored


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


UTC = load_dates({"timezone": "UTC"})[0]
MADRID = load_dates({"timezone": "Europe/Madrid"})[0]


@pytest.mark.parametrize("value, whole_day", [
    ("2026-11-02", True), ("2026-11-02 22:00", False), ("2026-11-02 22:00:30", False)])
def test_standard_forms(value, whole_day):
    parsed = parse_date(value, MADRID)
    assert parsed.standard is True and parsed.whole_day is whole_day


def test_explicit_offset_is_converted_to_the_kb_zone():
    parsed = parse_date("2026-11-02T22:00:00+00:00", MADRID)
    assert stored(parsed) == "2026-11-02 23:00:00"
    assert parsed.standard is True


def test_other_forms_parse_but_are_not_standard():
    parsed = parse_date("02/11/2026", MADRID)
    assert stored(parsed) == "2026-11-02 00:00:00" and parsed.standard is False


@pytest.mark.parametrize("value", ["YYYY-MM-DD", "Thu, 26 Jan 2023 09:26:54 GMT", "next week", ""])
def test_unparsable_values(value):
    assert parse_date(value, UTC) is None


def test_whole_day_end_covers_the_day():
    assert end_moment(parse_date("2026-11-02", UTC)) == datetime(2026, 11, 2, 23, 59, 59)


@pytest.mark.skipif(sys.platform == "win32", reason="time.tzset does not exist on Windows")
def test_same_result_whatever_the_machine_zone(monkeypatch):
    for tz in ("UTC", "Europe/Madrid", "America/New_York"):
        monkeypatch.setenv("TZ", tz)
        time.tzset()
        assert stored(parse_date("2026-11-02T22:00:00+00:00", MADRID)) == "2026-11-02 23:00:00"
    monkeypatch.undo()
    time.tzset()


def test_date_key_names_include_declared_keys():
    names = date_key_names({"dates": {"WarrantyEnd": {"group": "end"}}})
    assert {"Date", "Modified", "DueDate", "WarrantyEnd"} <= names
    assert date_key_names({"dates": ["bad"]}) == frozenset(load_dates({})[0].keys)

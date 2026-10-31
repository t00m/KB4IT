"""Date rules: Date follows the start, specific keys supersede Start and End, missing ends, downtime."""

import pytest

from kb4it.core.dateclass import load_dates
from kb4it.core.daterules import resolve_dates

S = load_dates({"timezone": "UTC", "dates": {
    "MaintenanceStart": {"group": "start", "supersedes": True},
    "MaintenanceEnd": {"group": "end", "closes": "MaintenanceStart", "supersedes": True}}})[0]


def codes(notices):
    return [line.split()[0] for _level, line in notices]


def test_date_filled_from_start():
    keys, notices = resolve_dates({"Start": ["2026-07-01"], "End": ["2026-09-30"]}, S)
    assert keys["Date"] == ["2026-07-01 00:00:00"] and notices == []


def test_scheduled_start_supersedes_start_and_sets_date():
    keys, notices = resolve_dates({"Start": ["2026-11-01 10:00"], "ScheduledStart": ["2026-11-02 22:00"],
                                   "ScheduledEnd": ["2026-11-03 02:00"]}, S)
    assert "Start" not in keys and keys["Date"] == ["2026-11-02 22:00:00"]
    assert codes(notices) == ["DATE_SUPERSEDED"]


def test_downtime_start_never_sets_date():
    keys, _ = resolve_dates({"Date": ["2026-11-02 22:00"], "ScheduledStart": ["2026-11-02 22:00"],
                             "ScheduledEnd": ["2026-11-03 02:00"], "Downtime": ["Yes"],
                             "DowntimeStart": ["2026-11-02 23:00"], "DowntimeEnd": ["2026-11-03 00:00"]}, S)
    assert keys["Date"] == ["2026-11-02 22:00:00"]


def test_date_differing_from_start_is_replaced():
    keys, notices = resolve_dates({"Date": ["2026-10-15"], "Start": ["2026-07-01"]}, S)
    assert keys["Date"] == ["2026-07-01 00:00:00"] and codes(notices) == ["DATE_NOT_START", "DATE_END_MISSING"]


def test_missing_end_equals_start():
    keys, notices = resolve_dates({"Start": ["2026-11-02 10:00"]}, S)
    assert keys["End"] == ["2026-11-02 10:00:00"] and codes(notices) == ["DATE_END_MISSING"]


def test_ends_closing_date_are_never_filled():
    keys, notices = resolve_dates({"Date": ["2026-11-02"]}, S)
    assert "DueDate" not in keys and notices == []


def test_whole_day_end_on_start_day_is_valid():
    _, notices = resolve_dates({"Start": ["2026-11-02 10:00"], "End": ["2026-11-02"]}, S)
    assert notices == []


def test_end_before_start_is_kept_with_warning():
    keys, notices = resolve_dates({"Start": ["2026-11-02"], "End": ["2026-11-01"]}, S)
    assert keys["End"] == ["2026-11-01 00:00:00"] and codes(notices) == ["DATE_END_BEFORE_START"]


def test_invalid_value_is_dropped_and_document_kept():
    keys, notices = resolve_dates({"Date": ["YYYY-MM-DD"], "Tag": ["x"]}, S)
    assert "Date" not in keys and keys["Tag"] == ["x"] and codes(notices) == ["DATE_INVALID"]


def test_extra_values_of_a_date_key_are_dropped():
    keys, notices = resolve_dates({"Date": ["2026-11-02", "2026-11-03"]}, S)
    assert keys["Date"] == ["2026-11-02 00:00:00"]
    assert notices == [("warning", "DATE_INVALID key=Date value=2026-11-03 reason=multiple")]


def test_non_standard_form_is_information():
    keys, notices = resolve_dates({"Date": ["02/11/2026"]}, S)
    assert keys["Date"] == ["2026-11-02 00:00:00"]
    assert notices == [("information", "DATE_NOT_STANDARD key=Date value=02/11/2026")]


def test_empty_values_are_not_dates():
    keys, notices = resolve_dates({"Start": [], "Date": ["2026-11-02"]}, S)
    assert "End" not in keys and notices == []


def test_two_superseding_pairs_conflict():
    keys, notices = resolve_dates({"ScheduledStart": ["2026-11-02"], "MaintenanceStart": ["2026-11-05"]}, S)
    assert keys["Date"] == ["2026-11-02 00:00:00"]
    assert "DATE_SUPERSEDE_CONFLICT" in codes(notices)


@pytest.mark.parametrize("keys, code", [
    ({"Downtime": ["none announced"]}, "DATE_DOWNTIME_VALUE"),
    ({"Downtime": ["Yes"]}, "DATE_DOWNTIME_MISSING"),
    ({"DowntimeStart": ["2026-11-02 23:00"]}, "DATE_DOWNTIME_UNEXPECTED"),
    ({"ScheduledStart": ["2026-11-02 22:00"], "ScheduledEnd": ["2026-11-03 02:00"], "Downtime": ["Yes"],
      "DowntimeStart": ["2026-11-03 01:00"], "DowntimeEnd": ["2026-11-03 04:00"]}, "DATE_DOWNTIME_OUTSIDE"),
])
def test_downtime_checks(keys, code):
    _, notices = resolve_dates(keys, S)
    assert code in codes(notices)


def test_missing_downtime_end_equals_start():
    keys, notices = resolve_dates({"Downtime": ["Yes"], "DowntimeStart": ["2026-11-02 23:00"]}, S)
    assert keys["DowntimeEnd"] == ["2026-11-02 23:00:00"] and codes(notices) == ["DATE_END_MISSING"]


def test_every_notice_is_warning_or_information():
    _, notices = resolve_dates({"Date": ["bad"], "Start": ["2026-11-02"], "End": ["2026-11-01"],
                                "Downtime": ["maybe"]}, S)
    assert {level for level, _ in notices} <= {"warning", "information"}


def test_other_keys_pass_through_unchanged():
    keys, _ = resolve_dates({"Tag": ["a", "b"], "Title": ["T"]}, S)
    assert keys == {"Tag": ["a", "b"], "Title": ["T"]}

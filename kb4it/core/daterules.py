"""
Date rules: the date keys of one document, checked and completed (spec D9 to D12, D17).

Every problem is a notice, never an error: a bad value is dropped, a missing end
takes its start, and Date follows the start of the document's window.

# File: daterules.py
# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

from kb4it.core.dateclass import (DOWNTIME_KEY, DOWNTIME_VALUES, DateSettings, ParsedDate, end_moment,
                                  parse_date, stored)

Notice = tuple[str, str]  # (level, line); level is "warning" or "information"


def _parse_all(keys: dict[str, list[str]], settings: DateSettings,
               notices: list[Notice]) -> tuple[dict[str, list[str]], dict[str, ParsedDate]]:
    """Non-date keys as they are, and the first valid value of every date key."""
    others: dict[str, list[str]] = {}
    parsed: dict[str, ParsedDate] = {}
    for key, values in keys.items():
        if not settings.is_date(key):
            others[key] = values
            continue
        present = [str(value) for value in values if str(value).strip()]
        if not present:
            continue
        first, *extra = present
        for value in extra:
            notices.append(("warning", f"DATE_INVALID key={key} value={value} reason=multiple"))
        value = parse_date(first, settings)
        if value is None:
            notices.append(("warning", f"DATE_INVALID key={key} value={first}"))
            continue
        if not value.standard:
            notices.append(("information", f"DATE_NOT_STANDARD key={key} value={first}"))
        parsed[key] = value
    return others, parsed


def _start(parsed: dict[str, ParsedDate], settings: DateSettings, notices: list[Notice]) -> str | None:
    """The key that opens the document's window, after superseding Start and End (D11)."""
    winners = [name for name, key in settings.keys.items()
               if key.group == "start" and key.supersedes and name in parsed]
    if len(winners) > 1:
        notices.append(("warning", f"DATE_SUPERSEDE_CONFLICT keys={','.join(winners)}"))
    if not winners:
        return "Start" if "Start" in parsed else None
    winner = winners[0]
    winner_end = next((name for name, key in settings.keys.items() if key.closes == winner), winner)
    for generic, by in (("Start", winner), ("End", winner_end)):
        if generic in parsed:
            del parsed[generic]
            notices.append(("information", f"DATE_SUPERSEDED key={generic} by={by}"))
    return winner


def _downtime(keys: dict[str, list[str]], parsed: dict[str, ParsedDate], had: set[str],
              notices: list[Notice]) -> None:
    value = next((str(v) for v in keys.get(DOWNTIME_KEY) or [] if str(v).strip()), "")
    if value and value not in DOWNTIME_VALUES:
        notices.append(("warning", f"DATE_DOWNTIME_VALUE value={value}"))
    if value == "Yes" and "DowntimeStart" not in had:
        notices.append(("warning", "DATE_DOWNTIME_MISSING"))
    if value != "Yes" and had & {"DowntimeStart", "DowntimeEnd"}:
        notices.append(("warning", "DATE_DOWNTIME_UNEXPECTED"))
    window = ("ScheduledStart", "ScheduledEnd", "DowntimeStart", "DowntimeEnd")
    if value == "Yes" and all(key in parsed for key in window):
        if parsed["DowntimeStart"].moment < parsed["ScheduledStart"].moment \
                or end_moment(parsed["DowntimeEnd"]) > end_moment(parsed["ScheduledEnd"]):
            notices.append(("warning", "DATE_DOWNTIME_OUTSIDE"))


def resolve_dates(keys: dict[str, list[str]], settings: DateSettings) -> tuple[dict[str, list[str]], list[Notice]]:
    """The keys with every date value in stored form (bad ones dropped, missing ones filled) and the notices."""
    notices: list[Notice] = []
    others, parsed = _parse_all(keys, settings, notices)
    had = set(parsed)
    start = _start(parsed, settings, notices)
    if start is not None:
        if "Date" in parsed and stored(parsed["Date"]) != stored(parsed[start]):
            notices.append(("warning", f"DATE_NOT_START date={stored(parsed['Date'])} start={stored(parsed[start])}"))
        parsed["Date"] = parsed[start]
    ends = [(name, key.closes) for name, key in settings.keys.items() if key.group == "end" and key.closes]
    for end, closes in ends:
        if closes != "Date" and closes in parsed and end not in parsed:
            parsed[end] = parsed[closes]
            notices.append(("warning", f"DATE_END_MISSING key={end} start={closes}"))
    for end, closes in ends:
        if end in parsed and closes in parsed and end_moment(parsed[end]) < parsed[closes].moment:
            notices.append(("warning", f"DATE_END_BEFORE_START key={end} start={closes}"))
    _downtime(keys, parsed, had, notices)
    return {**others, **{key: [stored(value)] for key, value in parsed.items()}}, notices


def resolve_and_log(keys: dict[str, list[str]], settings: DateSettings | None, log, doc_id: str) -> dict[str, list[str]]:
    """resolve_dates for one document of a build; its notices go to the log with the document name."""
    if settings is None:
        from kb4it.core.dateclass import load_dates
        settings = load_dates({})[0]
    keys, notices = resolve_dates(keys, settings)
    for level, line in notices:
        (log.warning if level == "warning" else log.info)(f"[DATES] {line} doc={doc_id}")
    return keys

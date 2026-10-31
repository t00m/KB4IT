"""
Date class: the date keys of a knowledge base, its time zone, and how a date value is read.

# File: dateclass.py
# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from kb4it.core.dates import guess_datetime

GROUPS = ("start", "end")
NAME_SUFFIXES = ("Date", "Start", "End")
DOWNTIME_KEY = "Downtime"
DOWNTIME_VALUES = ("Yes", "No")
# YYYY-MM-DD, optionally followed by HH:MM or HH:MM:SS (D14).
STANDARD_RE = re.compile(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}(:\d{2})?)?$")


@dataclass(frozen=True)
class DateKey:
    """One date key: its group (start, end, or None for Modified), the start it closes, and if it supersedes Start/End."""

    name: str
    group: str | None
    closes: str | None = None
    supersedes: bool = False


def _reserved() -> dict[str, DateKey]:
    keys = [DateKey("Date", "start"), DateKey("Start", "start"), DateKey("ScheduledStart", "start", supersedes=True),
            DateKey("DowntimeStart", "start"), DateKey("DetectedDate", "start"),
            DateKey("End", "end", "Start"), DateKey("ScheduledEnd", "end", "ScheduledStart", supersedes=True),
            DateKey("DowntimeEnd", "end", "DowntimeStart"),
            DateKey("ResolvedDate", "end", "Date"), DateKey("DueDate", "end", "Date"),
            DateKey("ExpiryDate", "end", "Date"), DateKey("ReviewDate", "end", "Date"),
            DateKey("Modified", None)]
    return {key.name: key for key in keys}


RESERVED_DATES: dict[str, DateKey] = _reserved()


@dataclass(frozen=True)
class DateSettings:
    """The time zone (None: the build machine's) and every date key, reserved and declared."""

    timezone: ZoneInfo | None
    keys: dict[str, DateKey]

    def is_date(self, key: str) -> bool:
        return key in self.keys


def _timezone(repo: Mapping[str, Any], notices: list[str]) -> ZoneInfo | None:
    name = repo.get("timezone")
    if name is None:
        notices.append("TIMEZONE_UNSET")
        return None
    try:
        return ZoneInfo(str(name))
    except (ZoneInfoNotFoundError, ValueError):
        notices.append(f"TIMEZONE_INVALID value={name}")
        return None


def _declared(block: Any, reserved: set[str], notices: list[str]) -> dict[str, DateKey]:
    """The keys of the repo.json "dates" block; a bad entry is left out with a notice."""
    if block is None:
        return {}
    if not isinstance(block, dict):
        notices.append("DATES_BLOCK_INVALID key=dates reason=entry")
        return {}
    starts = {name for name, key in RESERVED_DATES.items() if key.group == "start"}
    starts |= {name for name, spec in block.items() if isinstance(spec, dict) and spec.get("group") == "start"}
    declared: dict[str, DateKey] = {}
    for name, spec in block.items():
        if name in reserved:
            reason = "reserved"
        elif not isinstance(spec, dict):
            reason = "entry"
        elif spec.get("group") not in GROUPS:
            reason = "group"
        elif spec.get("closes") is not None and (spec["group"] != "end" or spec["closes"] not in starts):
            reason = "closes"
        else:
            closes = spec.get("closes") or ("Date" if spec["group"] == "end" else None)
            declared[name] = DateKey(name, spec["group"], closes, bool(spec.get("supersedes", False)))
            if not name.endswith(NAME_SUFFIXES):
                notices.append(f"DATE_KEY_NAME key={name}")
            continue
        notices.append(f"DATES_BLOCK_INVALID key={name} reason={reason}")
    return declared


def load_dates(repo: Mapping[str, Any], reserved_names: Iterable[str] = ()) -> tuple[DateSettings, list[str]]:
    """The date settings of repo.json and the notice lines about them; never raises."""
    notices: list[str] = []
    timezone = _timezone(repo, notices)
    reserved = set(RESERVED_DATES) | {DOWNTIME_KEY} | set(reserved_names)
    keys = {**RESERVED_DATES, **_declared(repo.get("dates"), reserved, notices)}
    return DateSettings(timezone, keys), notices


def date_key_names(repo: Mapping[str, Any]) -> frozenset[str]:
    """Every name of the date class: the reserved keys and the ones repo.json declares."""
    block = repo.get("dates")
    return frozenset(RESERVED_DATES) | frozenset(block if isinstance(block, dict) else ())


@dataclass(frozen=True)
class ParsedDate:
    """A date value read in the knowledge base zone: a naive moment, whether it is a whole day, and its form."""

    moment: datetime
    whole_day: bool
    standard: bool


def _iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_date(value: str, settings: DateSettings) -> ParsedDate | None:
    """The ParsedDate of a value, or None when it is not a date."""
    value = str(value).strip()
    moment = _iso(value) if value else None
    offset = moment is not None and moment.tzinfo is not None
    if moment is None:
        moment = guess_datetime(value) if value else None
        if moment is None:
            return None
    if offset:
        moment = moment.astimezone(settings.timezone).replace(tzinfo=None)
    whole_day = not offset and len(value) <= 10 and moment.time() == time(0)
    return ParsedDate(moment, whole_day, bool(STANDARD_RE.match(value)) or offset)


def stored(parsed: ParsedDate) -> str:
    """The form the database keeps: YYYY-MM-DD HH:MM:SS, naive, in the knowledge base zone."""
    return parsed.moment.strftime("%Y-%m-%d %H:%M:%S")


def end_moment(parsed: ParsedDate) -> datetime:
    """The last moment an end covers: the value itself, or the end of the day for a whole day."""
    if parsed.whole_day:
        return parsed.moment + timedelta(days=1, seconds=-1)
    return parsed.moment

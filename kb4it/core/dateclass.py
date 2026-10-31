"""
Date class: the date keys of a knowledge base, its time zone, and how a date value is read.

# File: dateclass.py
# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

GROUPS = ("start", "end")
NAME_SUFFIXES = ("Date", "Start", "End")
DOWNTIME_KEY = "Downtime"
DOWNTIME_VALUES = ("Yes", "No")


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

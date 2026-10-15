"""
Date helpers: parse date strings, format dates for people and timestamps.

# Author: Tomás Vírseda
# License: GPL v3
"""

from datetime import datetime


class DateCache:
    """Isolated cache for date-string parsing and formatting results.

    Using a class instead of module-level dicts allows test code to inject
    a fresh instance (no cross-test contamination) while production callers
    rely on the module-level singleton without any change.
    """

    def __init__(self):
        self._dt = {}
        self._ymd = {}

    def has_dt(self, key):
        return key in self._dt

    def get_dt(self, key):
        return self._dt[key]

    def set_dt(self, key, value):
        self._dt[key] = value

    def get_ymd(self, key):
        return self._ymd.get(key)

    def set_ymd(self, key, value):
        self._ymd[key] = value

    def clear(self):
        self._dt.clear()
        self._ymd.clear()


_default_date_cache = DateCache()


def now():
    """Return datetime.now in isoformat."""
    return datetime.now().isoformat()


def get_year(timestamp: str) -> int:
    """Return year from timestamp."""
    return int(timestamp[:4])


def get_month(timestamp: str):
    """Return month from timestamp."""
    return int(timestamp[4:6])


def get_day(timestamp: str):
    """Return day from timestamp."""
    return int(timestamp[6:8])


def log_timestamp():
    """Return timestamp for logging purposes."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def kb4it_timestamp():
    """Return timestamp in KB4IT format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def guess_datetime(sdate, _cache=None):
    """Guess a datetime object for a given string."""
    cache = _cache if _cache is not None else _default_date_cache
    if cache.has_dt(sdate):
        return cache.get_dt(sdate)

    patterns = [
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%d-%m-%Y",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%Y/%m/%d",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y.%m.%d",
        "%Y.%m.%d %H:%M",
        "%Y.%m.%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d %H:%M:%S.%f",
        "%Y.%m.%d",
        "%Y.%m.%d %H:%M",
        "%Y.%m.%d %H:%M:%S.%f",
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y%m%d",
        "%Y%m%d%H%M%S",
    ]
    timestamp = None
    for pattern in patterns:
        try:
            td = datetime.strptime(sdate, pattern)
            ts = td.strftime("%Y-%m-%d %H:%M:%S")
            timestamp = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            break
        except ValueError:
            continue
    cache.set_dt(sdate, timestamp)
    return timestamp


def string_timestamp(string):
    """Return datetime object from a given timestamp."""
    dt = guess_datetime(string)
    sdate = dt.strftime("%Y-%m-%d %H:%M:%S")
    return sdate


def get_human_datetime(dt):
    """Return datetime for humans."""
    return dt.strftime("%A, %B %d, %Y at %H:%M")


def get_human_datetime_day(dt):
    """Return day datetime for humans."""
    return dt.strftime("%A, %B %d, %Y")


def get_human_datetime_month(dt):
    """Return month datetime for humans."""
    return dt.strftime("%B, %Y")


def get_human_datetime_year(dt):
    """Return year datetime for humans."""
    return dt.strftime("%Y")


def get_timestamp_yyyymmdd(dt, _cache=None):
    """Return timestamp in yyyymmdd format."""
    cache = _cache if _cache is not None else _default_date_cache
    result = cache.get_ymd(dt)
    if result is None:
        result = dt.strftime("%Y%m%d")
        cache.set_ymd(dt, result)
    return result

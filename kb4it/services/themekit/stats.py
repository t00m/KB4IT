"""The stats page: totals, activity over time, property coverage, metadata health and links.

`collect_stats()` computes everything from the database and the link graph of the
build; `StatsMixin.build_page_stats()` renders it with the theme's `PAGE_STATS`.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from kb4it.core.dates import guess_datetime
from kb4it.core.documents import is_yes
from kb4it.core.util import html_id_for, valid_filename
from kb4it.services.themekit.host import ThemeHost

#: Lists of the health and links sections show at most this many entries.
LIST_LIMIT = 10
#: Values listed per property in the coverage table.
TOP_VALUES = 3
#: Most linked documents listed.
TOP_LINKED = 5
#: Months in the activity section, ending at the month of the newest document.
MONTHS = 12
#: A document with this many properties or fewer (Title aside) has little metadata.
FEW_PROPERTIES = 2
#: Keys that are not metadata a reader chose.
NOT_METADATA = frozenset({'Title', 'SystemPage'})


@dataclass
class DocRef:
    """A document, linked; `count` is what the list ranks it by."""

    title: str
    url: str
    count: int = 0


@dataclass
class ValueRef:
    """A property value, linked to its page."""

    value: str
    url: str
    count: int = 0


@dataclass
class Capped:
    """A list cut to `LIST_LIMIT` entries; `more` is how many were left out."""

    items: list[Any]
    more: int = 0


@dataclass
class Bar:
    """One bar of a time chart: label, count, width in percent and an optional page."""

    label: str
    count: int
    pct: int
    url: str = ''


@dataclass
class CoverageRow:
    """One property: how many documents set it and its most used values."""

    key: str
    url: str
    docs: int
    pct: int
    values: int
    top: list[ValueRef]


@dataclass
class ValueGroup:
    """Values of one property that differ only by case or spacing."""

    key: str
    values: list[ValueRef]


@dataclass
class RareKey:
    """A property used by one document only."""

    key: str
    url: str
    doc: DocRef


@dataclass
class StatsData:
    """Everything the stats page shows."""

    documents: int = 0
    properties: int = 0
    values: int = 0
    dated_pct: int = 0
    bookmarks: int = 0
    links: int = 0
    oldest: str = ''
    newest: str = ''
    undated: int = 0
    years: list[Bar] = field(default_factory=list)
    months: list[Bar] = field(default_factory=list)
    coverage: list[CoverageRow] = field(default_factory=list)
    duplicates: Capped = field(default_factory=lambda: Capped([]))
    rare_keys: Capped = field(default_factory=lambda: Capped([]))
    sparse_docs: Capped = field(default_factory=lambda: Capped([]))
    most_linked: list[DocRef] = field(default_factory=list)
    orphans: Capped = field(default_factory=lambda: Capped([]))
    no_outgoing: int = 0


def _cap(items: list[Any]) -> Capped:
    return Capped(items[:LIST_LIMIT], max(0, len(items) - LIST_LIMIT))


def _pct(part: int, whole: int) -> int:
    return round(part * 100 / whole) if whole else 0


def _bars(counts: list[tuple[str, int, str]]) -> list[Bar]:
    """Bars sized against the highest count; a non-zero count is never thinner than 2%."""
    top = max((count for _, count, _ in counts), default=0)
    return [Bar(label, count, max(2, _pct(count, top)) if count else 0, url) for label, count, url in counts]


def _value_url(key: str, value: str) -> str:
    return f"{valid_filename(key)}_{valid_filename(value)}.html"


def _norm(value: str) -> str:
    return re.sub(r'\s+', ' ', value).strip().casefold()


def collect_stats(db: Any, keys: list[str], backlinks: dict[str, list[list[str]]],
                  events: dict[int, dict[int, Any]] | None = None) -> StatsData:
    """Return the stats of the content documents in `db` (the Database service).

    `keys` are the properties to report, `backlinks` is `BuildPlan.backlinks`
    (`{target: [[source title, source], ...]}`) and `events` the theme's
    `events_docs`: a year or month links to its event page when it is there.
    """
    events = events or {}
    docs = [doc for doc in db.get_documents() if not db.is_system(doc)]
    content = set(docs)
    stats = StatsData(documents=len(docs), properties=len(keys))

    def ref(doc: str, count: int = 0) -> DocRef:
        return DocRef(db.get_values(doc, 'Title')[0] or doc, html_id_for(doc), count)

    def doc_values(doc: str, key: str) -> list[str]:
        return [value for value in db.get_values(doc, key) if value]

    # Totals and dates
    dates: dict[str, Any] = {}
    for doc in docs:
        if is_yes(db.get_values(doc, 'Bookmark')[0]):
            stats.bookmarks += 1
        timestamp = db.get_doc_timestamp(doc)
        parsed = guess_datetime(timestamp) if timestamp else None
        if parsed is None:
            stats.undated += 1
        else:
            dates[doc] = parsed
    stats.dated_pct = _pct(len(dates), len(docs))

    # Activity over time
    if dates:
        oldest, newest = min(dates.values()), max(dates.values())
        stats.oldest, stats.newest = oldest.strftime('%Y-%m-%d'), newest.strftime('%Y-%m-%d')
        per_year = Counter(dt.year for dt in dates.values())
        stats.years = _bars([(str(year), per_year[year], f"events_{year:4d}.html" if year in events else '')
                             for year in sorted(per_year, reverse=True)])
        per_month = Counter((dt.year, dt.month) for dt in dates.values())
        months = []
        year, month = newest.year, newest.month
        for _ in range(MONTHS):
            months.append((year, month))
            year, month = (year, month - 1) if month > 1 else (year - 1, 12)
        stats.months = _bars([(f"{y:4d}-{m:02d}", per_month[(y, m)],
                               f"events_{y:4d}{m:02d}.html" if m in events.get(y, {}) else '')
                              for y, m in reversed(months)])

    # Property coverage and metadata health
    groups: list[ValueGroup] = []
    rare: list[RareKey] = []
    for key in keys:
        users = [doc for doc in docs if doc_values(doc, key)]
        if not users:
            continue
        counts = Counter(value for doc in users for value in set(doc_values(doc, key)))
        stats.values += len(counts)
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0].lower(), item[0]))
        stats.coverage.append(CoverageRow(
            key=key, url=f"{valid_filename(key)}.html", docs=len(users), pct=_pct(len(users), len(docs)),
            values=len(counts), top=[ValueRef(value, _value_url(key, value), count)
                                     for value, count in ranked[:TOP_VALUES]]))
        if len(users) == 1:
            rare.append(RareKey(key, f"{valid_filename(key)}.html", ref(users[0])))
        alike: dict[str, list[str]] = {}
        for value in counts:
            alike.setdefault(_norm(value), []).append(value)
        for values in alike.values():
            if len(values) > 1:
                groups.append(ValueGroup(key, [ValueRef(value, _value_url(key, value), counts[value])
                                               for value in sorted(values)]))
    stats.coverage.sort(key=lambda row: (-row.docs, row.key.lower()))
    stats.duplicates = _cap(groups)
    stats.rare_keys = _cap(rare)
    sparse = [ref(doc, n) for doc in docs
              if (n := sum(1 for key in db.get_doc_keys(doc)
                           if key not in NOT_METADATA and doc_values(doc, key))) <= FEW_PROPERTIES]
    stats.sparse_docs = _cap(sorted(sparse, key=lambda d: (d.count, d.title.lower())))

    # Links between documents
    incoming: dict[str, int] = {}
    sources: set[str] = set()
    for target, items in backlinks.items():
        linked = {source for _title, source in items if source in content}
        if target in content and linked:
            incoming[target] = len(linked)
            sources |= linked
    stats.links = sum(incoming.values())
    if stats.links:
        ranked_docs = sorted((ref(doc, n) for doc, n in incoming.items()), key=lambda d: (-d.count, d.title.lower()))
        stats.most_linked = ranked_docs[:TOP_LINKED]
        stats.orphans = _cap(sorted((ref(doc) for doc in docs if doc not in incoming), key=lambda d: d.title.lower()))
        stats.no_outgoing = sum(1 for doc in docs if doc not in sources)
    return stats


class StatsMixin(ThemeHost):
    """`build_page_stats`; needs `Builder`, `stats_keys` and the reuse helpers of `KeyPagesMixin`."""

    #: Properties left out of the stats page: free text says nothing as a count.
    stats_skip_keys: tuple[str, ...] = ('Summary',)

    if TYPE_CHECKING:
        def stats_keys(self) -> list[str]: ...

        def _reuse_cached_page(self, name: str, counter: str, reason: str, func: str) -> bool: ...

        def _add_system_page(self, name: str, title: str) -> None: ...

    def build_page_stats(self) -> None:
        """Create the stats page of the repository."""
        # The page shows dates and links too, so a document change makes it stale.
        if self.srvbes.get_value('runtime', 'ncd') == 0 and \
                self._reuse_cached_page('stats', 'nck', 'no_changes', 'build_page_stats'):
            return
        keys = [key for key in self.stats_keys() if key not in self.stats_skip_keys]
        plan = self.srvbes.get_plan()
        backlinks = (plan.backlinks if plan else None) or {}
        var = self.get_theme_var()
        var['stats'] = collect_stats(self.srvdtb, keys, backlinks, getattr(self, 'events_docs', None))
        self.distribute_md('stats', self.template('PAGE_STATS').render(var=var))
        self._add_system_page('stats', 'Stats')

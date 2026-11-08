"""Feature events: one page per day, month and year that has event documents.

Also the data of an events page: the event day of each document and the counts a calendar panel draws.
"""

from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime
from typing import TYPE_CHECKING, Any

from kb4it.core.log import q
from kb4it.core.util import get_human_datetime_day, get_human_datetime_month, guess_datetime
from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Doc, Site

EVENTS_TABLE = 'kb4it-events-table'
Index = dict[int, dict[int, dict[int, list[str]]]]


def parse_date(text: str) -> datetime:
    parsed = guess_datetime(text)
    if parsed is None:
        raise ValueError(f"not a date: {text}")
    return parsed


def event_days(events_docs: Index) -> dict[str, str]:
    """Return {document: 'YYYY-MM-DD'} from events_docs, which maps year, month and day to documents."""
    days = {}
    for year, months in events_docs.items():
        for month, month_days in months.items():
            for day, docs in month_days.items():
                for doc in docs:
                    days[doc] = f'{year:04d}-{month:02d}-{day:02d}'
    return days


def calendar_json(days: dict[str, str]) -> str:
    """Return the JSON the calendar panel reads: {"days": {"YYYY-MM-DD": number of events}}, safe inside <script>."""
    counts = dict(sorted(Counter(days.values()).items()))
    return json.dumps({'days': counts}, separators=(',', ':')).replace('</', '<\\/')


class Events(Feature):
    """events_YYYYMMDD.html, events_YYYYMM.html and events_YYYY.html of the event documents.

    index maps year, month and day to the documents of that date; dey maps a year to its
    (month, day) pairs. Both are computed in prepare(), before any page is built.
    """

    name = "events"
    requires = ("table",)
    hooks = ("event_documents",)
    templates = ("EVENTCAL_PAGE_EVENTS_DAYS", "EVENTCAL_PAGE_EVENTS_MONTHS", "EVENTCAL_PAGE_EVENTS_YEARS")

    def __init__(self, theme: Any, engine: Any) -> None:
        super().__init__(theme, engine)
        self._index: Index = {}
        self._dey: dict[int, list[tuple[int, int]]] = {}
        self._docs: set[str] = set()
        self.built_years: set[str] = set()

    # Legacy themes keep the state on the theme: their own code reads self.events_docs and self.dey.
    @property
    def index(self) -> Index:
        index: Index = self.theme.events_docs if self.legacy else self._index
        return index

    @property
    def dey(self) -> dict[int, list[tuple[int, int]]]:
        dey: dict[int, list[tuple[int, int]]] = self.theme.dey if self.legacy else self._dey
        return dey

    # ---------------------------------------------------------------- hook
    def event_documents(self) -> list[Any]:
        """Default: every dated document. A theme returns the ones that are events (Docs or ids)."""
        return [doc for doc in self.site.documents if doc.date]

    # --------------------------------------------------------------- queries
    def has_day_page(self, doc: Doc) -> bool:
        """True when the document is on a day page of this build, so its date may link there."""
        return doc.id in self._docs

    def day_url(self, doc: Doc) -> str | None:
        """events_YYYYMMDD.html of the document, or None when it is not on a day page."""
        date = doc.date
        if not date or not self.has_day_page(doc):
            return None
        return f"events_{date[:10].replace('-', '')}.html"

    def days(self) -> dict[str, str]:
        """{doc id: 'YYYY-MM-DD'} of every event."""
        return event_days(self.index)

    def years(self) -> list[int]:
        return sorted(self.dey, reverse=True)

    def calendar(self, days: dict[str, str] | None = None) -> str:
        """The JSON a calendar panel reads, {"days": {"YYYY-MM-DD": count}}, safe inside <script>."""
        return calendar_json(self.days() if days is None else days)

    # ---------------------------------------------------------------- stages
    def prepare(self, site: Site) -> None:
        self._index, self._dey = {}, {}
        ids = [d if isinstance(d, str) else d.id for d in self.hook("event_documents")()]
        self._docs = set(ids)
        self.collect(ids)

    def pages(self, site: Site) -> None:
        self.built_years = self.build_pages(self._ordered(), collect=False)

    def _ordered(self) -> list[str]:
        """The event documents in the order of the site's documents (newest first)."""
        return [doc for doc in self.engine.srvdtb.get_documents() if doc in self._docs]

    # ------------------------------------------------------------ the pages
    def collect(self, doclist: list[str]) -> None:
        """Add the dated documents of doclist to index and dey."""
        db, index, dey = self.engine.srvdtb, self.index, self.dey
        for doc_id in doclist:
            timestamp = db.get_doc_timestamp(doc_id)
            if timestamp is None:
                continue
            try:
                parsed = parse_date(timestamp)
                y, m, d = parsed.year, parsed.month, parsed.day
                dey.setdefault(y, []).append((m, d))
                index.setdefault(y, {}).setdefault(m, {}).setdefault(d, []).append(doc_id)
            except Exception as error:
                self.engine.log.error(f"[THEME] DATE_INVALID doc={q(os.path.basename(doc_id))} "
                                      f"timestamp={q(timestamp)}", exc_info=True)
                self.engine.log.error(f"[THEME] ERROR {error}")
                raise

    def cached_page(self, name: str) -> str:
        return os.path.join(self.engine.srvbes.get_path('cache'), f"{name}.html")

    def build_pages(self, doclist: list[str], *, collect: bool = True) -> set[str]:
        """Create the day, month and year pages of the dated documents in doclist.

        A page is rebuilt when one of its documents changed, when its documents are
        not the ones it had after the last successful build (a document was added,
        removed or moved to another date), when that build did not record them, or
        when its cached copy is missing; a month and its year are also rebuilt when
        one of their days is. Otherwise the cached page is reused. Returns the years
        whose page was rebuilt, as strings.
        """
        engine = self.engine
        srvbes = engine.srvbes
        tpl_days = engine.template('EVENTCAL_PAGE_EVENTS_DAYS')
        tpl_months = engine.template('EVENTCAL_PAGE_EVENTS_MONTHS')
        tpl_years = engine.template('EVENTCAL_PAGE_EVENTS_YEARS')
        if collect:
            self.collect(doclist)
        index, dey = self.index, self.dey

        kbdict = srvbes.get_kb_dict()
        before = srvbes.get_events_before()
        pages: dict[str, list[str]] = {}
        counts = {'built': 0, 'reused': 0}

        def must_build(name: str, docs: list[str], cascade: bool = False) -> bool:
            pages[name] = sorted(docs)
            build = (cascade or before is None or before.get(name) != pages[name]
                     or not os.path.exists(self.cached_page(name))
                     or any(kbdict['document'][doc_id]['compile'] for doc_id in docs))
            counts['built' if build else 'reused'] += 1
            return build

        var = engine.get_theme_var()
        must_compile_month = set()
        must_compile_year = set()
        built_years: set[str] = set()
        for year in index:
            for month in index[year]:
                for day in index[year][month]:
                    name = f"events_{year:4d}{month:02d}{day:02d}"
                    day_docs = index[year][month][day]
                    if must_build(name, day_docs):
                        must_compile_month.add(f"{year:4d}{month:02d}")
                        must_compile_year.add(f"{year:4d}")
                        edt = parse_date(f"{year:4d}.{month:02d}.{day:02d}")
                        var['page'] = {'datatable': self.table_html(day_docs, filterable=True)}
                        var['page']['title'] = edt.strftime("Events on %A, %B %d %Y")
                        engine.distribute_md(name, tpl_days.render(var=var), listing=True)
                        engine.add_system_page(name, f"Events on {get_human_datetime_day(edt)}")
                    else:
                        engine.distribute_html(name, self.cached_page(name))
                    srvbes.add_target(f"{name}.md", f"{name}.html")

        for year in index:
            for month in index[year]:
                name = f"events_{year:4d}{month:02d}"
                month_docs = [doc_id for day in index[year][month] for doc_id in index[year][month][day]]
                if must_build(name, month_docs, f"{year:4d}{month:02d}" in must_compile_month):
                    edt = parse_date(f"{year:4d}.{month:02d}.01")
                    var['page'] = {'datatable': self.table_html(month_docs, filterable=True)}
                    var['page']['title'] = edt.strftime("Events on %B, %Y")
                    engine.distribute_md(name, tpl_months.render(var=var), listing=True)
                    engine.add_system_page(name, f"Events on {get_human_datetime_month(edt)}")
                else:
                    engine.distribute_html(name, self.cached_page(name))
                srvbes.add_target(f"{name}.md", f"{name}.html")

        for year in sorted(dey.keys(), reverse=True):
            name = f"events_{year:4d}"
            year_docs = [doc_id for month in index[year] for day in index[year][month]
                         for doc_id in index[year][month][day]]
            if must_build(name, year_docs, str(year) in must_compile_year):
                built_years.add(f"{year:4d}")
                var['page'] = {'title': f"Archive / {year}"}
                var['page']['datatable'] = self.table_html(year_docs, filterable=True)
                engine.distribute_md(name, tpl_years.render(var=var), listing=True)
                engine.add_system_page(name, f"Archive / {year}")
            else:
                engine.distribute_html(name, self.cached_page(name))
            srvbes.add_target(f"{name}.md", f"{name}.html")

        srvbes.set_events(pages)
        engine.log.debug(f"[THEME] EVENT_PAGES built={q(counts['built'])} reused={q(counts['reused'])}")
        return built_years

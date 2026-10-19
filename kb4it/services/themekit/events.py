"""Event pages: one page per day, month and year that has dated documents."""

from __future__ import annotations

import os
from datetime import datetime

from kb4it.core.util import (
    get_human_datetime_day,
    get_human_datetime_month,
    guess_datetime,
)
from kb4it.services.themekit.host import ThemeHost


def _parse_date(text: str) -> datetime:
    parsed = guess_datetime(text)
    if parsed is None:
        raise ValueError(f"not a date: {text}")
    return parsed


class EventsMixin(ThemeHost):
    """`build_events`; needs `Builder` and `build_datatable`.

    `dey` maps a year to its (month, day) pairs and `events_docs` maps year, month
    and day to the documents of that date. Both belong to one build.
    """

    def _initialize(self) -> None:
        super()._initialize()
        self.dey: dict[int, list[tuple[int, int]]] = {}
        self.events_docs: dict[int, dict[int, dict[int, list[str]]]] = {}

    def _collect_events(self, doclist: list[str]) -> None:
        for docId in doclist:
            timestamp = self.srvdtb.get_doc_timestamp(docId)
            if timestamp is None:
                continue
            try:
                parsed = _parse_date(timestamp)
                y, m, d = parsed.year, parsed.month, parsed.day
                self.dey.setdefault(y, []).append((m, d))
                self.events_docs.setdefault(y, {}).setdefault(m, {}).setdefault(d, []).append(docId)
            except Exception as error:
                self.log.error(f"[THEME] DATE_INVALID doc={os.path.basename(docId)} timestamp={timestamp}")
                self.log.error(f"[THEME] ERROR {error}")
                raise

    def _cached_page(self, name: str) -> str:
        return os.path.join(self.srvbes.get_path('cache'), f"{name}.html")

    def _add_event_page(self, name: str, title: str) -> None:
        self.srvdtb.add_document(f"{name}.md")
        self.srvdtb.add_document_key(f"{name}.md", 'Title', title)
        self.srvdtb.add_document_key(f"{name}.md", 'SystemPage', 'Yes')

    def build_events(self, doclist: list[str]) -> set[str]:
        """Create the day, month and year pages of the dated documents in `doclist`.

        A page is rebuilt when one of its documents changed, when its documents are
        not the ones it had after the last successful build (a document was added,
        removed or moved to another date), when that build did not record them, or
        when its cached copy is missing; a month and its year are also rebuilt when
        one of their days is. Otherwise the cached page is reused. Returns the years
        whose page was rebuilt, as strings.
        """
        tpl_days = self.template('EVENTCAL_PAGE_EVENTS_DAYS')
        tpl_months = self.template('EVENTCAL_PAGE_EVENTS_MONTHS')
        tpl_years = self.template('EVENTCAL_PAGE_EVENTS_YEARS')
        self._collect_events(doclist)

        kbdict = self.srvbes.get_kb_dict()
        before = self.srvbes.get_events_before()
        pages: dict[str, list[str]] = {}
        counts = {'built': 0, 'reused': 0}

        def must_build(name: str, docs: list[str], cascade: bool = False) -> bool:
            pages[name] = sorted(docs)
            build = (cascade or before is None or before.get(name) != pages[name]
                     or not os.path.exists(self._cached_page(name))
                     or any(kbdict['document'][docId]['compile'] for docId in docs))
            counts['built' if build else 'reused'] += 1
            return build

        var = self.get_theme_var()
        must_compile_month = set()
        must_compile_year = set()
        built_years: set[str] = set()
        for year in self.events_docs:
            for month in self.events_docs[year]:
                for day in self.events_docs[year][month]:
                    name = f"events_{year:4d}{month:02d}{day:02d}"
                    day_docs = self.events_docs[year][month][day]
                    if must_build(name, day_docs):
                        must_compile_month.add(f"{year:4d}{month:02d}")
                        must_compile_year.add(f"{year:4d}")
                        edt = _parse_date(f"{year:4d}.{month:02d}.{day:02d}")
                        var['page'] = {'datatable': self.build_datatable([], day_docs)}
                        var['page']['title'] = edt.strftime("Events on %A, %B %d %Y")
                        self.distribute_md(name, tpl_days.render(var=var))
                        self._add_event_page(name, f"Events on {get_human_datetime_day(edt)}")
                    else:
                        self.distribute_html(name, self._cached_page(name))
                    self.srvbes.add_target(f"{name}.md", f"{name}.html")

        for year in self.events_docs:
            for month in self.events_docs[year]:
                name = f"events_{year:4d}{month:02d}"
                month_docs = [docId for day in self.events_docs[year][month]
                              for docId in self.events_docs[year][month][day]]
                if must_build(name, month_docs, f"{year:4d}{month:02d}" in must_compile_month):
                    edt = _parse_date(f"{year:4d}.{month:02d}.01")
                    var['page'] = {'datatable': self.build_datatable([], month_docs)}
                    var['page']['title'] = edt.strftime("Events on %B, %Y")
                    self.distribute_md(name, tpl_months.render(var=var))
                    self._add_event_page(name, f"Events on {get_human_datetime_month(edt)}")
                else:
                    self.distribute_html(name, self._cached_page(name))
                self.srvbes.add_target(f"{name}.md", f"{name}.html")

        for year in sorted(self.dey.keys(), reverse=True):
            name = f"events_{year:4d}"
            year_docs = [docId for month in self.events_docs[year] for day in self.events_docs[year][month]
                         for docId in self.events_docs[year][month][day]]
            if must_build(name, year_docs, str(year) in must_compile_year):
                built_years.add(f"{year:4d}")
                var['page'] = {'title': f"Archive / {year}"}
                var['page']['datatable'] = self.build_datatable([], year_docs)
                self.distribute_md(name, tpl_years.render(var=var))
                self._add_event_page(name, f"Archive / {year}")
            else:
                self.distribute_html(name, self._cached_page(name))
            self.srvbes.add_target(f"{name}.md", f"{name}.html")

        self.srvbes.set_events(pages)
        self.log.debug(f"[THEME] EVENT_PAGES built={counts['built']} reused={counts['reused']}")
        return built_years

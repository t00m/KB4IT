"""Event pages: one page per day, month and year that has dated documents."""

import os

from kb4it.core.util import (
    get_human_datetime_day,
    get_human_datetime_month,
    guess_datetime,
)


class EventsMixin:
    """`build_events`; needs `Builder` and `build_datatable`.

    `dey` maps a year to its (month, day) pairs and `events_docs` maps year, month
    and day to the documents of that date. Both belong to one build.
    """

    #: Rebuild every event page on each build instead of reusing the cached pages of
    #: dates whose documents did not change.
    events_rebuild_all = False

    def _initialize(self):
        super()._initialize()
        self.dey = {}
        self.events_docs = {}

    def _collect_events(self, doclist):
        for docId in doclist:
            timestamp = self.srvdtb.get_doc_timestamp(docId)
            if timestamp is None:
                continue
            try:
                timestamp = guess_datetime(timestamp)
                y, m, d = timestamp.year, timestamp.month, timestamp.day
                self.dey.setdefault(y, []).append((m, d))
                self.events_docs.setdefault(y, {}).setdefault(m, {}).setdefault(d, []).append(docId)
            except Exception as error:
                self.log.error(f"[THEME] DATE_INVALID doc={os.path.basename(docId)} timestamp={timestamp}")
                self.log.error(f"[THEME] ERROR {error}")
                raise

    def _cached_page(self, name):
        return os.path.join(self.srvbes.get_path('cache'), f"{name}.html")

    def _add_event_page(self, name, title):
        self.srvdtb.add_document(f"{name}.md")
        self.srvdtb.add_document_key(f"{name}.md", 'Title', title)
        self.srvdtb.add_document_key(f"{name}.md", 'SystemPage', 'Yes')

    def build_events(self, doclist):
        """Create the day, month and year pages of the dated documents in `doclist`.

        A page is rebuilt when one of its documents changed or its cached copy is
        missing (always, with `events_rebuild_all`); otherwise the cached page is
        reused. Returns the years whose page was rebuilt, as strings.
        """
        tpl_days = self.template('EVENTCAL_PAGE_EVENTS_DAYS')
        tpl_months = self.template('EVENTCAL_PAGE_EVENTS_MONTHS')
        tpl_years = self.template('EVENTCAL_PAGE_EVENTS_YEARS')
        self._collect_events(doclist)

        kbdict = self.srvbes.get_kb_dict()
        var = self.get_theme_var()
        must_compile_month = set()
        must_compile_year = set()
        for year in self.events_docs:
            for month in self.events_docs[year]:
                for day in self.events_docs[year][month]:
                    name = f"events_{year:4d}{month:02d}{day:02d}"
                    cached = self._cached_page(name)
                    day_docs = self.events_docs[year][month][day]
                    must_compile_day = self.events_rebuild_all or not os.path.exists(cached) or any(
                        kbdict['document'][docId]['compile'] for docId in day_docs)
                    if must_compile_day:
                        must_compile_month.add(f"{year:4d}{month:02d}")
                        must_compile_year.add(f"{year:4d}")
                        edt = guess_datetime(f"{year:4d}.{month:02d}.{day:02d}")
                        var['page'] = {'datatable': self.build_datatable([], day_docs)}
                        var['page']['title'] = edt.strftime("Events on %A, %B %d %Y")
                        self.distribute_md(name, tpl_days.render(var=var))
                        self._add_event_page(name, f"Events on {get_human_datetime_day(edt)}")
                    else:
                        self.distribute_html(name, cached)
                    self.srvbes.add_target(f"{name}.md", f"{name}.html")

        for year in self.events_docs:
            for month in self.events_docs[year]:
                name = f"events_{year:4d}{month:02d}"
                cached = self._cached_page(name)
                if f"{year:4d}{month:02d}" in must_compile_month or not os.path.exists(cached):
                    edt = guess_datetime(f"{year:4d}.{month:02d}.01")
                    month_docs = [docId for day in self.events_docs[year][month]
                                  for docId in self.events_docs[year][month][day]]
                    var['page'] = {'datatable': self.build_datatable([], month_docs)}
                    var['page']['title'] = edt.strftime("Events on %B, %Y")
                    self.distribute_md(name, tpl_months.render(var=var))
                    self._add_event_page(name, f"Events on {get_human_datetime_month(edt)}")
                else:
                    self.distribute_html(name, cached)
                self.srvbes.add_target(f"{name}.md", f"{name}.html")

        for year in sorted(self.dey.keys(), reverse=True):
            name = f"events_{year:4d}"
            cached = self._cached_page(name)
            if str(year) in must_compile_year or not os.path.exists(cached):
                year_docs = [docId for month in self.events_docs[year] for day in self.events_docs[year][month]
                             for docId in self.events_docs[year][month][day]]
                var['page'] = {'title': f"Archive / {year}"}
                var['page']['datatable'] = self.build_datatable([], year_docs)
                self.distribute_md(name, tpl_years.render(var=var))
                self._add_event_page(name, f"Archive / {year}")
            else:
                self.distribute_html(name, cached)
            self.srvbes.add_target(f"{name}.md", f"{name}.html")

        return must_compile_year

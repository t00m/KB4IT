"""Event pages: one page per day, month and year that has dated documents.

Legacy API: the code lives in the events feature (kb4it/theme/features/events.py); the
state stays on the theme (self.dey, self.events_docs), which theme code reads.
"""

from __future__ import annotations

from kb4it.services.themekit.host import ThemeHost, feature_of
from kb4it.theme.features.events import EVENTS_TABLE, Events, calendar_json, event_days, parse_date

__all__ = ["EVENTS_TABLE", "EventsMixin", "calendar_json", "event_days"]
_parse_date = parse_date


class EventsMixin(ThemeHost):
    """`build_events`; needs `Builder` and `build_datatable`.

    `dey` maps a year to its (month, day) pairs and `events_docs` maps year, month
    and day to the documents of that date. Both belong to one build.
    """

    def _initialize(self) -> None:
        super()._initialize()
        self.dey: dict[int, list[tuple[int, int]]] = {}
        self.events_docs: dict[int, dict[int, dict[int, list[str]]]] = {}
        self.__dict__.pop('_event_doc_set', None)

    def event_documents(self) -> list[str]:
        """Documents that get day, month and year pages; default none.

        A theme that builds event pages returns here the list it passes to build_events(), so a date
        links to a day page only for a document that is on it.
        """
        return []

    def has_event_page(self, doc_id: str) -> bool:
        """True when doc_id is on an events day page of this build, so its date may link there.

        Per document, not per date: the pages that show a document are rebuilt when its own
        properties change, so this answer never goes stale in the cache. Key-value pages are
        built before build(), so the list is read here, once per build, not from events_docs.
        """
        found = self.__dict__.get('_event_doc_set')
        if found is None:
            found = self.__dict__['_event_doc_set'] = set(self.event_documents())
        return doc_id in found

    def _collect_events(self, doclist: list[str]) -> None:
        feature_of(self, Events).collect(doclist)

    def _cached_page(self, name: str) -> str:
        return feature_of(self, Events).cached_page(name)

    def _add_event_page(self, name: str, title: str) -> None:
        self.add_system_page(name, title)

    def build_events(self, doclist: list[str]) -> set[str]:
        """Create the day, month and year pages of the dated documents in `doclist`.

        A page is rebuilt when one of its documents changed, when its documents are
        not the ones it had after the last successful build (a document was added,
        removed or moved to another date), when that build did not record them, or
        when its cached copy is missing; a month and its year are also rebuilt when
        one of their days is. Otherwise the cached page is reused. Returns the years
        whose page was rebuilt, as strings.
        """
        return feature_of(self, Events).build_pages(doclist)

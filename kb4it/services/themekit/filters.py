"""Table filter kit (Layer 1). Filter bar of the document tables: pills per property value, behind a Filter button next to the search box.

Legacy API: the code lives in the table_filter feature (kb4it/theme/features/tablefilter.py).
Here a theme on DocumentTheme turns the bar on per page: the page builders set a flag while
they build their table, and build_datatable() reads it.
"""

from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from typing import Any

from kb4it.services.themekit.host import ThemeHost, feature_of
from kb4it.theme.features.tablefilter import (FILTER_KEYS, FILTER_MIN_ROWS, TableFilter, ValuesOf, facet_attrs,
                                              facet_groups, filter_groups, row_attrs)

__all__ = ["FILTER_KEYS", "FILTER_MIN_ROWS", "FilterMixin", "ValuesOf", "facet_attrs", "facet_groups"]


class FilterMixin(ThemeHost):
    """Adds the filter bar to the document tables of the listing pages.

    Needs `build_datatable` and `srvdtb`, the theme's `DATATABLE_FILTER` template and the vendor
    library `tablefilter` in its theme.json `assets`.
    """

    datatable_filter_keys = FILTER_KEYS
    datatable_filter_min_rows = FILTER_MIN_ROWS
    _filter_tables = False  # on while a page that offers the filter builds its table
    _filter_rows = False  # on while the rows of a table that gets the bar are drawn
    _filter_dates = None  # events.html: document -> event day (YYYY-MM-DD)

    @contextmanager
    def _filtered_tables(self, dates: dict[str, str] | None = None) -> Iterator[None]:
        """Turn the filter bar on for the tables built inside; dates also gives every row its event day."""
        self._filter_tables = True
        self._filter_dates = dates
        try:
            yield
        finally:
            self._filter_tables = False
            self._filter_dates = None

    def build_page_index_all(self) -> Any:
        """all.html: its table gets the filter bar."""
        with self._filtered_tables():
            return super().build_page_index_all()

    def build_page_bookmarks(self) -> Any:
        """bookmarks.html: its table gets the filter bar."""
        with self._filtered_tables():
            return super().build_page_bookmarks()

    def build_page_key_value(self, kvpath: Any) -> Any:
        """Property value pages: their table gets the filter bar."""
        with self._filtered_tables():
            return super().build_page_key_value(kvpath)

    def build_events(self, doclist: Any) -> Any:
        """Archive pages of a year, month or day (events_YYYY*.html): their tables get the filter bar."""
        with self._filtered_tables():
            return super().build_events(doclist)

    def list_filter(self, docs: Iterable[str], list_id: str) -> tuple[str, Callable[[Any], str]]:
        """The filter bar of plain document lists (Quality page), and the attributes of each document.

        Returns (bar HTML or '', attrs(doc or [docs]) -> str); without a property that splits docs, no bar.
        """
        return feature_of(self, TableFilter).list_filter(docs, list_id)

    def _values_of(self, doc: str, key: str) -> list[str]:
        return self.srvdtb.get_values(doc, key) or []

    def datatable_title_cell(self, docId: str, properties: Any) -> str:
        """The Title cell of a table with the filter bar carries the values the bar matches on."""
        cell = super().datatable_title_cell(docId, properties)
        if not self._filter_rows:
            return cell
        attrs = row_attrs(self._values_of, docId, self.datatable_filter_keys, self._filter_dates)
        end = cell.find('>', cell.find('<td'))
        return f'{cell[:end]} {attrs}{cell[end:]}' if attrs and end != -1 else cell

    def build_datatable(self, headers: list[str] | None = None, doclist: list[str] | None = None,
                        table_id: str = 'kb4it-datatable') -> str:
        """Put the filter bar, hidden, before the table; datatable-filter.js moves it below the search box."""
        groups = self._filter_groups(headers, doclist)
        if groups is None:
            return super().build_datatable(headers, doclist, table_id)
        self._filter_rows = True
        try:
            html = super().build_datatable(headers, doclist, table_id)
        finally:
            self._filter_rows = False
        bar = feature_of(self, TableFilter).bar(groups, table_id=table_id)
        marker = '<!-- DOCUMENT LIST :: START -->'
        return html.replace(marker, f'{marker}\n{bar}', 1)

    def _filter_groups(self, headers: list[str] | None, doclist: list[str] | None) -> list[dict[str, Any]] | None:
        """The filter groups of a table, or None when it gets no bar: wrong page, no Title column or few rows.

        A table with event days always gets the bar, maybe with no groups: the calendar filters it.
        """
        if not self._filter_tables or 'Title' not in (headers or []):
            return None
        docs = [doc for doc in dict.fromkeys(doclist or []) if not self.srvdtb.is_system(doc)]
        return filter_groups(docs, self._values_of, self.datatable_filter_keys, self.datatable_filter_min_rows,
                             self._filter_dates)

"""Filter bar of the document tables: pills per property value, behind a Filter button next to the search box.

Only the tables of all.html, bookmarks.html, the property value pages, events.html and the archive
pages of a year, month or day (events_YYYY*.html) get it. Each row
carries its values as slugs in data-kb-f-<key> attributes of the Title cell; datatable-filter.js reads
them and filters through DataTables, so the row count and the search box stay right. On events.html
the cell also carries the event day (data-kb-date), which the calendar panel filters on.
"""

from collections import Counter
from contextlib import contextmanager
from html import escape

from kb4it.core.util import slugify

FILTER_KEYS = ('WorkType', 'DocType', 'Category', 'Topic', 'Status', 'Priority')
FILTER_MIN_ROWS = 10  # smaller tables are short enough to scan by eye


def facet_groups(docs, values_of, keys=FILTER_KEYS):
    """Return [{'key', 'slug', 'values': [{'name', 'slug', 'count'}]}] for the keys that split the documents.

    values_of(doc, key) gives the values of a document. A key is left out when no document has a value,
    or when every document has the same single value: filtering by it would change nothing.
    Values are sorted by count, most used first, then by name.
    """
    groups = []
    for key in keys:
        counts = Counter()
        for doc in docs:
            counts.update({value for value in values_of(doc, key) if value and slugify(value)})
        if not counts or (len(counts) == 1 and next(iter(counts.values())) == len(docs)):
            continue
        values = [{'name': name, 'slug': slugify(name), 'count': count}
                  for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))]
        groups.append({'key': key, 'slug': key.lower(), 'values': values})
    return groups


def facet_attrs(values_of, doc, keys=FILTER_KEYS):
    """Return the data-kb-f-<key> attributes of a row: its values as space separated slugs."""
    attrs = []
    for key in keys:
        slugs = sorted({slugify(value) for value in values_of(doc, key) if value} - {''})
        if slugs:
            attrs.append(f'data-kb-f-{key.lower()}="{escape(" ".join(slugs))}"')
    return ' '.join(attrs)


class FilterMixin:
    """Adds the filter bar to the document tables of the listing pages; needs build_datatable and srvdtb."""

    datatable_filter_keys = FILTER_KEYS
    datatable_filter_min_rows = FILTER_MIN_ROWS
    _filter_tables = False  # on while a page that offers the filter builds its table
    _filter_rows = False  # on while the rows of a table that gets the bar are drawn
    _filter_dates = None  # events.html: document -> event day (YYYY-MM-DD)

    @contextmanager
    def _filtered_tables(self, dates=None):
        """Turn the filter bar on for the tables built inside; dates also gives every row its event day."""
        self._filter_tables = True
        self._filter_dates = dates
        try:
            yield
        finally:
            self._filter_tables = False
            self._filter_dates = None

    def build_page_index_all(self):
        """all.html: its table gets the filter bar."""
        with self._filtered_tables():
            return super().build_page_index_all()

    def build_page_bookmarks(self):
        """bookmarks.html: its table gets the filter bar."""
        with self._filtered_tables():
            return super().build_page_bookmarks()

    def build_page_key_value(self, kvpath):
        """Property value pages: their table gets the filter bar."""
        with self._filtered_tables():
            return super().build_page_key_value(kvpath)

    def build_events(self, doclist):
        """Archive pages of a year, month or day (events_YYYY*.html): their tables get the filter bar."""
        with self._filtered_tables():
            return super().build_events(doclist)

    def _values_of(self, doc, key):
        return self.srvdtb.get_values(doc, key) or []

    def datatable_title_cell(self, docId, properties):
        """The Title cell of a table with the filter bar carries the values the bar matches on."""
        cell = super().datatable_title_cell(docId, properties)
        if not self._filter_rows:
            return cell
        attrs = facet_attrs(self._values_of, docId, self.datatable_filter_keys)
        day = (self._filter_dates or {}).get(docId)
        if day:
            attrs = f'{attrs} data-kb-date="{escape(day)}"'.strip()
        end = cell.find('>', cell.find('<td'))
        return f'{cell[:end]} {attrs}{cell[end:]}' if attrs and end != -1 else cell

    def build_datatable(self, headers=None, doclist=None, table_id='kb4it-datatable'):
        """Put the filter bar, hidden, before the table; datatable-filter.js moves it below the search box."""
        groups = self._filter_groups(headers, doclist)
        if groups is None:
            return super().build_datatable(headers, doclist, table_id)
        self._filter_rows = True
        try:
            html = super().build_datatable(headers, doclist, table_id)
        finally:
            self._filter_rows = False
        bar = self.template('DATATABLE_FILTER').render(var={'table_id': table_id, 'groups': groups})
        marker = '<!-- DOCUMENT LIST :: START -->'
        return html.replace(marker, f'{marker}\n{bar}', 1)

    def _filter_groups(self, headers, doclist):
        """The filter groups of a table, or None when it gets no bar: wrong page, no Title column or few rows.

        A table with event days always gets the bar, maybe with no groups: the calendar filters it.
        """
        if not self._filter_tables or 'Title' not in (headers or []):
            return None
        docs = [doc for doc in dict.fromkeys(doclist or []) if not self.srvdtb.is_system(doc)]
        if self._filter_dates is not None:
            return facet_groups(docs, self._values_of, self.datatable_filter_keys) if docs else None
        if len(docs) < self.datatable_filter_min_rows:
            return None
        return facet_groups(docs, self._values_of, self.datatable_filter_keys) or None

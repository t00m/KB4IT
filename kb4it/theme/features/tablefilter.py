"""Feature table_filter: a filter bar over the document tables, behind a Filter button next to the search box.

The bar has pills per property value. Each row carries its values as slugs in data-kb-f-<key>
attributes of the Title cell; datatable-filter.js reads them and filters through DataTables, so the
row count and the search box stay right. A table with event days (Table.dates) also gets data-kb-date
on each row, which a calendar panel filters on.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from html import escape
from typing import TYPE_CHECKING, Any

from kb4it.core.util import slugify
from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Table

FILTER_KEYS = ('WorkType', 'DocType', 'Category', 'Topic', 'Status', 'Priority')
ValuesOf = Callable[[str, str], list[str]]  # values_of(doc, key)
FILTER_MIN_ROWS = 10  # smaller tables are short enough to scan by eye


def facet_groups(docs: list[str], values_of: ValuesOf, keys: Sequence[str] = FILTER_KEYS) -> list[dict[str, Any]]:
    """Return [{'key', 'slug', 'values': [{'name', 'slug', 'count'}]}] for the keys that split the documents.

    values_of(doc, key) gives the values of a document. A key is left out when no document has a value,
    or when every document has the same single value: filtering by it would change nothing.
    Values are sorted by count, most used first, then by name.
    """
    groups = []
    for key in keys:
        counts: Counter[str] = Counter()
        for doc in docs:
            counts.update({value for value in values_of(doc, key) if value and slugify(value)})
        if not counts or (len(counts) == 1 and next(iter(counts.values())) == len(docs)):
            continue
        values = [{'name': name, 'slug': slugify(name), 'count': count}
                  for name, count in sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))]
        groups.append({'key': key, 'slug': key.lower(), 'values': values})
    return groups


def facet_attrs(values_of: ValuesOf, doc: str | list[str] | tuple[str, ...], keys: Sequence[str] = FILTER_KEYS) -> str:
    """Return the data-kb-f-<key> attributes of a row: its values as space separated slugs.

    doc may be a list of documents (a pair of duplicates): the row then has the values of all of them.
    """
    docs = doc if isinstance(doc, (list, tuple)) else [doc]
    attrs = []
    for key in keys:
        slugs = sorted({slugify(value) for d in docs for value in values_of(d, key) if value} - {''})
        if slugs:
            attrs.append(f'data-kb-f-{key.lower()}="{escape(" ".join(slugs))}"')
    return ' '.join(attrs)


def row_attrs(values_of: ValuesOf, doc_id: str, keys: Sequence[str], dates: dict[str, str] | None) -> str:
    """The attributes of the Title cell of a row: its facet slugs and, on an events table, its day."""
    attrs = facet_attrs(values_of, doc_id, keys)
    day = (dates or {}).get(doc_id)
    if day:
        attrs = f'{attrs} data-kb-date="{escape(day)}"'.strip()
    return attrs


def filter_groups(docs: list[str], values_of: ValuesOf, keys: Sequence[str], min_rows: int,
                  dates: dict[str, str] | None) -> list[dict[str, Any]] | None:
    """The groups of the bar of a table, or None when it gets no bar.

    A table with event days always gets the bar, maybe with no groups: the calendar filters it.
    """
    if dates is not None:
        return facet_groups(docs, values_of, keys) if docs else None
    if len(docs) < min_rows:
        return None
    return facet_groups(docs, values_of, keys) or None


class TableFilter(Feature):
    """The filter bar of the tables of all.html, bookmarks.html, the value pages and the events pages."""

    name = "table_filter"
    requires = ("table",)
    options = {"datatable_filter_keys": FILTER_KEYS, "datatable_filter_min_rows": FILTER_MIN_ROWS}
    templates = ("DATATABLE_FILTER",)
    assets = ("tablefilter",)

    def values_of(self, doc: str, key: str) -> list[str]:
        return list(self.engine.srvdtb.get_values(doc, key) or [])

    def bar(self, groups: list[dict[str, Any]], **where: str) -> str:
        """The DATATABLE_FILTER bar: where is table_id=... for a table, list=... for a plain list."""
        html: str = self.engine.template('DATATABLE_FILTER').render(var={**where, 'groups': groups})
        return html

    def table_extension(self, table: Table, columns: list[str],
                        doc_ids: list[str]) -> tuple[str, Callable[[str], str]] | None:
        """The bar and row attributes of a filterable table with a Title column."""
        if not table.filterable or 'Title' not in columns:
            return None
        keys = self.option("datatable_filter_keys")
        dates = dict(table.dates) if table.dates is not None else None
        groups = filter_groups(doc_ids, self.values_of, keys, self.option("datatable_filter_min_rows"), dates)
        if groups is None:
            return None
        return self.bar(groups, table_id=table.id), lambda doc_id: row_attrs(self.values_of, doc_id, keys, dates)

    def list_filter(self, docs: Iterable[str], list_id: str) -> tuple[str, Callable[[Any], str]]:
        """The filter bar of a plain document list, and the attributes of each document.

        Returns (bar HTML or '', attrs(doc or [docs]) -> str); without a property that splits docs, no bar.
        """
        keys = self.option("datatable_filter_keys")

        def attrs(doc: Any) -> str:
            return facet_attrs(self.values_of, doc, keys)
        groups = facet_groups(list(docs), self.values_of, keys)
        if not groups:
            return '', attrs
        return self.bar(groups, list=list_id), attrs

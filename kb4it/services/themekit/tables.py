"""The document table (datatable) of the list pages: all, bookmarks, events, values.

Legacy API: the code lives in the table feature (kb4it/theme/features/table.py);
these methods keep the names and arguments themes on DocumentTheme use.
"""

from __future__ import annotations

from typing import Any

from kb4it.services.themekit.host import ThemeHost, feature_of
from kb4it.theme.features.table import Table


class TableMixin(ThemeHost):
    """`build_datatable` and its hooks; needs `Builder.template`, `srvbes` and `srvdtb`."""

    #: Template of a value link in a cell.
    datatable_link_template = 'LINK_DATATABLE'
    #: Columns when neither the caller nor repo.json "datatable" names them.
    datatable_default_headers: tuple[str, ...] = ('Date', 'Title')

    def _table(self) -> Table:
        return feature_of(self, Table)

    def datatable_date_cell(self, timestamp: str | None, doc_id: str | None = None) -> str:
        """Return the cell of the date column; `timestamp` is None when the document has none.

        The date links to its events day page only when `doc_id` is on one (`has_event_page`).
        """
        return self._table().date_cell_html(timestamp, doc_id)

    def date_cell(self, timestamp: str | None, doc_id: str) -> str:
        """datatable_date_cell() of one row; a theme's override written before `doc_id` existed gets the date only."""
        return self._table().legacy_date_cell(timestamp, doc_id)

    def datatable_title_cell(self, docId: str, properties: dict[str, Any]) -> str:
        """Return the cell of the Title column: the title, shortened, with a tooltip."""
        return self._table().title_cell_html(docId, properties)

    def datatable_custom_cell(self, doc_id: str, key: str) -> str | None:
        """Return the whole <td> of a column the theme draws itself, or None for a plain property cell."""
        return None

    def datatable_value_link(self, properties: dict[str, Any], key: str, value: str) -> dict[str, str]:
        """Return the variables of the link to the page of a value; KeyError leaves the cell empty."""
        return Table.value_link_vars(properties, key, value)

    def build_datatable(self, headers: list[str] | None = None, doclist: list[str] | None = None,
                        table_id: str = 'kb4it-datatable') -> str:
        """Given a list of columns, it builds a datatable; the first column is the date when headers has 'Date'."""
        return self._table().render(headers, doclist, table_id)

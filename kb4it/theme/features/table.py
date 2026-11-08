"""Feature table: the document table (datatable) of the list pages."""

from __future__ import annotations

import inspect
from html import escape
from typing import TYPE_CHECKING, Any

from kb4it.core.log import q
from kb4it.core.util import ellipsize_text
from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Doc


class Table(Feature):
    """Tables of documents: a date, a title and one column per property."""

    name = "table"
    options = {
        "datatable_link_template": "LINK_DATATABLE",       # template of a value link in a cell
        "datatable_default_headers": ("Date", "Title"),     # columns when neither the caller nor repo.json names them
    }
    hooks = ("datatable_date_cell", "datatable_title_cell", "datatable_custom_cell", "datatable_value_link")
    templates = ("DATATABLE", "DATATABLE_HEADER_ITEM", "DATATABLE_BODY_ITEM")

    def properties(self, doc_id: str) -> dict[str, Any]:
        props: dict[str, Any] = self.engine.srvdtb.get_doc_properties(doc_id)
        return props

    def has_day_page(self, doc_id: str) -> bool:
        """True when the document is on an events day page (feature events)."""
        if self.legacy:
            return bool(getattr(self.theme, "has_event_page", lambda _doc: False)(doc_id))
        events = self.feature("events")
        return bool(events is not None and events.has_day_page(self.doc(doc_id)))

    # ------------------------------------------------------- cell builders
    def date_cell_html(self, timestamp: str | None, doc_id: str | None) -> str:
        """The date cell; the date links to its events day page when the document is on one."""
        if timestamp is None:
            return '<td class="uk-text-left"></td>'
        ts_title = escape(timestamp[:16])
        if doc_id is None or not self.has_day_page(doc_id):
            return f'<td class="uk-text-left"><span class="uk-text-left">{ts_title}</span></td>'
        ts_link = escape(f"events_{timestamp[:10].replace('-', '')}.html")
        return (f'<td class="uk-text-left"><a class="uk-link-heading" href="{ts_link}">'
                f'<span class="uk-text-left">{ts_title}</span></a></td>')

    def title_cell_html(self, doc_id: str, properties: dict[str, Any]) -> str:
        """The title cell: the title, shortened, with a tooltip."""
        item = {}
        try:
            title = properties['Title']
            # Built as HTML here, printed raw by the template: escape the document title.
            item['title'] = f"<span data-uk-tooltip=\"{escape(str(title))}\">{escape(ellipsize_text(title, 80))}</span>"
            item['url'] = properties['Title_Url']
            html: str = self.engine.template('DATATABLE_BODY_ITEM').render(var=item)
            return html
        except (KeyError, AttributeError) as e:
            self.engine.log.error(f"[THEME] DATATABLE_FAIL doc={q(doc_id)} item={q(item)} reason={q(e)}")
            raise

    @staticmethod
    def value_link_vars(properties: dict[str, Any], key: str, value: str) -> dict[str, str]:
        """The variables of the link to the page of a value; KeyError leaves the cell empty."""
        return {'class': 'uk-link-heading', 'title': value, 'url': properties[f'{key}_{value}_Url']}

    # ------------------------------------------------- hook defaults (Doc)
    def datatable_date_cell(self, doc: Doc) -> str:
        """The <td> of the date column."""
        return self.date_cell_html(doc.date, doc.id)

    def datatable_title_cell(self, doc: Doc) -> str:
        """The <td> of the Title column."""
        return self.title_cell_html(doc.id, self.properties(doc.id))

    def datatable_custom_cell(self, doc: Doc, key: str) -> str | None:
        """The whole <td> of a column the theme draws itself, or None for a plain property cell."""
        return None

    def datatable_value_link(self, doc: Doc, key: str, value: str) -> dict[str, str]:
        """The variables of LINK_DATATABLE for one value of a cell."""
        return self.value_link_vars(self.properties(doc.id), key, value)

    # ------------------------------------- hook calls, legacy or public API
    def _date(self, doc_id: str) -> str:
        if self.legacy:
            return self.legacy_date_cell(self.engine.srvdtb.get_doc_timestamp(doc_id), doc_id)
        cell: str = self.hook("datatable_date_cell")(self.doc(doc_id))
        return cell

    def legacy_date_cell(self, timestamp: str | None, doc_id: str) -> str:
        """A legacy theme's datatable_date_cell(); an override written before doc_id existed gets the date only."""
        method = self.theme.datatable_date_cell
        takes_doc = self.theme.__dict__.get('_date_cell_takes_doc')
        if takes_doc is None:
            params = inspect.signature(method).parameters.values()
            takes_doc = len(params) >= 2 or any(p.kind == p.VAR_POSITIONAL for p in params)
            self.theme.__dict__['_date_cell_takes_doc'] = takes_doc
        cell: str = method(timestamp, doc_id) if takes_doc else method(timestamp)
        return cell

    def _title(self, doc_id: str, properties: dict[str, Any]) -> str:
        if self.legacy:
            cell: str = self.theme.datatable_title_cell(doc_id, properties)
        else:
            cell = self.hook("datatable_title_cell")(self.doc(doc_id))
        return cell

    def _custom(self, doc_id: str, key: str) -> str | None:
        if self.legacy:
            cell: str | None = self.theme.datatable_custom_cell(doc_id, key)
        else:
            cell = self.hook("datatable_custom_cell")(self.doc(doc_id), key)
        return cell

    def _link(self, doc_id: str, properties: dict[str, Any], key: str, value: str) -> dict[str, str]:
        if self.legacy:
            link: dict[str, str] = self.theme.datatable_value_link(properties, key, value)
        else:
            link = self.hook("datatable_value_link")(self.doc(doc_id), key, value)
        return link

    # ----------------------------------------------------------- the table
    def render(self, headers: list[str] | None = None, doclist: list[str] | None = None,
               table_id: str = 'kb4it-datatable') -> str:
        """The HTML of a table of documents; the first column is the date when headers has 'Date'."""
        engine = self.engine
        tpl_link = engine.template(self.option("datatable_link_template"))
        tpl_header_item = engine.template('DATATABLE_HEADER_ITEM')
        if not headers:
            headers = engine.srvbes.get_dict('repo').get('datatable', list(self.option("datatable_default_headers")))

        datatable = {'table_id': table_id}
        datatable['header'] = ''.join(tpl_header_item.render(var={'item': item}) for item in headers)

        documents = {doc_id: self.properties(doc_id) for doc_id in doclist or []}
        rows = []
        for doc_id, properties in documents.items():
            if engine.srvdtb.is_system(doc_id):
                continue
            row = ['<tr>']
            if 'Date' in headers:
                row.append(self._date(doc_id))
                final_headers = headers[1:]
            else:
                final_headers = headers
            for key in final_headers:
                if key == 'Title':
                    row.append(self._title(doc_id, properties))
                    continue
                custom = self._custom(doc_id, key)
                if custom is not None:
                    row.append(custom)
                    continue
                try:
                    field = [tpl_link.render(var=self._link(doc_id, properties, key, value))
                             for value in properties[key]]
                except KeyError:
                    field = []
                row.append(f'<td class="">{", ".join(field)}</td>')
            row.append('</tr>')
            rows.append(''.join(row))
        datatable['rows'] = ''.join(rows)
        html: str = engine.template('DATATABLE').render(var=datatable)
        return html

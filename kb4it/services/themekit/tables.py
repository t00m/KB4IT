"""The document table (datatable) of the list pages: all, bookmarks, events, values."""

from html import escape

from kb4it.core.util import ellipsize_text


class TableMixin:
    """`build_datatable` and its hooks; needs `Builder.template`, `srvbes` and `srvdtb`."""

    #: Template of a value link in a cell.
    datatable_link_template = 'LINK_DATATABLE'
    #: Columns when neither the caller nor repo.json "datatable" names them.
    datatable_default_headers = ('Date', 'Title')

    def datatable_date_cell(self, timestamp):
        """Return the cell of the date column; `timestamp` is None when the document has none."""
        if timestamp is None:
            return '<td class="uk-text-left"></td>'
        ts_title = escape(timestamp[:16])
        ts_link = escape(f"events_{timestamp[:10].replace('-', '')}.html")
        return (f'<td class="uk-text-left"><a class="uk-link-heading" href="{ts_link}">'
                f'<span class="uk-text-left">{ts_title}</span></a></td>')

    def datatable_title_cell(self, docId, properties):
        """Return the cell of the Title column: the title, shortened, with a tooltip."""
        item = {}
        try:
            title = properties['Title']
            # Built as HTML here, printed raw by the template: escape the document title.
            item['title'] = f"<span uk-tooltip=\"{escape(str(title))}\">{escape(ellipsize_text(title, 80))}</span>"
            item['url'] = properties['Title_Url']
            return self.template('DATATABLE_BODY_ITEM').render(var=item)
        except (KeyError, AttributeError) as e:
            self.log.error(f"[THEME] DATATABLE_FAIL doc={docId} item={item} reason={e}")
            raise

    def datatable_value_link(self, properties, key, value):
        """Return the variables of the link to the page of a value; KeyError leaves the cell empty."""
        return {'class': 'uk-link-heading', 'title': value, 'url': properties[f'{key}_{value}_Url']}

    def build_datatable(self, headers=None, doclist=None, table_id='kb4it-datatable'):
        """Given a list of columns, it builds a datatable.

        First column is always a date field, which is got by using the
        method get_doc_timestamp from the database module. It means
        that, firstly, it will retrieve the first date property defined
        by the theme (or one of the next ones defined if the first isn't
        found). If none is found, it will retrieve the timestamp of the
        file from the OS).
        So, it is not necessary to pass a date property in the headers.
        """
        tpl_link = self.template(self.datatable_link_template)
        tpl_header_item = self.template('DATATABLE_HEADER_ITEM')
        if not headers:
            headers = self.srvbes.get_dict('repo').get('datatable', list(self.datatable_default_headers))

        datatable = {'table_id': table_id}
        datatable['header'] = ''.join(tpl_header_item.render(var={'item': item}) for item in headers)

        documents = {docId: self.srvdtb.get_doc_properties(docId) for docId in doclist or []}
        rows = []
        for docId, properties in documents.items():
            if self.srvdtb.is_system(docId):
                continue
            row = ['<tr>']
            if 'Date' in headers:
                row.append(self.datatable_date_cell(self.srvdtb.get_doc_timestamp(docId)))
                final_headers = headers[1:]
            else:
                final_headers = headers
            for key in final_headers:
                if key == 'Title':
                    row.append(self.datatable_title_cell(docId, properties))
                    continue
                try:
                    field = [tpl_link.render(var=self.datatable_value_link(properties, key, value))
                             for value in properties[key]]
                except KeyError:
                    field = []
                row.append(f'<td class="">{", ".join(field)}</td>')
            row.append('</tr>')
            rows.append(''.join(row))
        datatable['rows'] = ''.join(rows)
        return self.template('DATATABLE').render(var=datatable)

"""starter-docs: a document theme on DocumentTheme. Copy it with `kb4it new-theme <id>` and change what you need.

DocumentTheme gives the property pages, the table of all documents, the 404 page and the page
pipeline; the uikit template base gives the tables, the table of contents and the heading wrappers.
Add a kit (kb4it.services.themekit.navigation, filters, related, tocsidebar, gallery, diagrams) to the
class line for more. The hook reference lists every hook: https://t00m.github.io/KB4IT/reference-theme-hooks.html
"""

from html import escape

from kb4it.core.util import valid_filename
from kb4it.services.themekit import DocumentTheme


class Theme(DocumentTheme):
    properties_cloud = False  # properties.html is a table; True shows one tag cloud button per property
    datatable_link_template = 'LINK'  # the uikit base's link template, for the Title column of the tables

    def build(self):
        """Override: the pages this theme writes itself, besides the document and property pages."""
        self.build_page_index()
        self.build_page_properties()
        self.build_page_index_all()
        self.build_page_404()
        self.create_page_search()

    def build_page_index(self):
        """The home page: the ten newest documents. Change the number or the layout here and in PAGE_INDEX."""
        docs = [d for d in self.srvdtb.sort_by_date(list(self.srvdtb.get_documents())) if not self.srvdtb.is_system(d)]
        var = self.get_theme_var()
        var['datatable'] = self.build_datatable(['Date', 'Title'], docs[:10])
        self.add_system_page('index', 'Home', self.render_template('PAGE_INDEX', var))

    def datatable_date_cell(self, timestamp):
        """Override: this theme builds no event pages, so a date in a table is text, not a link to one."""
        return f'<td>{escape(timestamp[:10])}</td>' if timestamp else '<td></td>'

    def page_context(self, doc_id, var):
        """Override: add your own data for HTML_BODY here; this one adds the document's tags."""
        tags = [t for t in self.srvdtb.get_values(doc_id, 'Tag') or [] if t]
        var['starter'] = {'tags': [{'name': t, 'url': f'Tag_{valid_filename(t)}.html'} for t in tags]}
        return var

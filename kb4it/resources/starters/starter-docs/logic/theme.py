"""starter-docs: a document theme. Copy it with `kb4it new-theme <id>` and change what you need.

The "documents" feature gives the property pages, the table of all documents, the 404 page, the
table of contents and the page actions; the uikit template base gives their templates. Add more
features by name, such as "events", "stats", "bookmarks", "table_filter" or "related".
"Write a theme" in the help lists every feature and hook:
https://t00m.github.io/KB4IT/howto-create-theme.html
"""

from kb4it.theme import BaseTheme, Table


class Theme(BaseTheme):
    features = ("documents", "search")
    properties_cloud = False  # properties.html is a table; True shows one tag cloud button per property
    datatable_link_template = "LINK"  # the uikit base's link template, for the value columns of the tables

    def build(self, site):
        """The home page: the ten newest documents. Change the number or the layout here and in PAGE_INDEX."""
        latest = Table(documents=tuple(site.documents.latest(10)), columns=("Date", "Title"))
        site.page("index", "Home", self.render("PAGE_INDEX", datatable=site.table(latest)))

    def page_context(self, doc, var):
        """Add your own data for HTML_BODY here; this one adds the document's tags with their pages."""
        var["starter"] = {"tags": doc.links("Tag")}
        return var

"""starter-plain: a theme of plain pages. Copy it with `kb4it new-theme <id> --plain` and change what you need.

Every document page goes through the page pipeline of Builder: the body Markdown compiled to
HTML, the hooks below, then HTML_HEADER_COMMON + HTML_BODY + HTML_FOOTER. The hook reference
lists every hook you can fill: https://t00m.github.io/KB4IT/reference-theme-hooks.html
"""

from kb4it.core.util import html_id_for
from kb4it.services.builder import Builder


class Theme(Builder):
    page_pipeline = True  # build_page() runs the hooks; fill them instead of overriding build_page()

    def build(self):
        """Override: the pages this theme writes itself. Add your own with add_system_page()."""
        self.create_page_search()  # search.html, when theme.json has "search": true
        self.add_system_page("index", "Home", self.render_template("PAGE_INDEX", self.home_var()))

    def home_var(self) -> dict:
        """The home page data: every document, by title. Change the order or the fields here."""
        docs = [d for d in self.srvdtb.get_documents() if not self.srvdtb.is_system(d)]
        items = [{"title": self.page_title(d), "url": html_id_for(d)} for d in docs]
        var = self.get_theme_var()
        var["documents"] = sorted(items, key=lambda item: item["title"].lower())
        return var

    def page_context(self, doc_id, var):
        """Override: add your own data for HTML_BODY here, such as a property of the document."""
        var["starter"] = {"date": (self.srvdtb.get_values(doc_id, "Date") or [""])[0]}
        return var

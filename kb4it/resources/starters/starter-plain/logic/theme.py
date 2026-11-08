"""starter-plain: a theme of plain pages. Copy it with `kb4it new-theme <id> --plain` and change what you need.

Every document page is its compiled body between HTML_HEADER_COMMON, HTML_BODY and HTML_FOOTER.
The hooks below add data to the pages; "Write a theme" in the help lists every hook:
https://t00m.github.io/KB4IT/howto-create-theme.html
"""

from kb4it.theme import BaseTheme


class Theme(BaseTheme):
    features = ("search",)  # search.html, the search box and the search index

    def build(self, site):
        """The pages this theme writes itself: the home page, every document by title."""
        documents = [{"title": doc.title or self.untitled_label, "url": doc.url} for doc in site.documents]
        documents.sort(key=lambda item: item["title"].lower())
        site.page("index", "Home", self.render("PAGE_INDEX", documents=documents))

    def page_context(self, doc, var):
        """Add your own data for HTML_BODY here, such as a property of the document."""
        var["starter"] = {"date": doc.value("Date")}
        return var

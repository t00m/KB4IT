"""The 404 page of the document themes: a system page that no listing, search or feed knows."""

from __future__ import annotations

from kb4it.services.themekit.host import ThemeHost


class NotFoundMixin(ThemeHost):
    """Builds 404.html; needs `Builder`."""

    #: Source pages a document cannot take, because the theme writes a page of that name.
    #: Empty here; a theme that calls build_page_404() sets ("404.md",).
    reserved_pages: tuple[str, ...] = ()

    def build_page_404(self) -> None:
        """Create the 404 page; as a system page it stays out of listings, search, feed and sitemap."""
        var = self.get_theme_var()
        self.distribute_md("404", self.template("PAGE_404").render(var=var))
        self.srvdtb.add_document("404.md")
        self.srvdtb.add_document_key("404.md", "Title", "Page not found")
        self.srvdtb.add_document_key("404.md", "SystemPage", "Yes")

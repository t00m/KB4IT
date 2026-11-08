"""Feature all_documents: all.html, the table of every document."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Site


class AllDocuments(Feature):
    """all.html."""

    name = "all_documents"
    requires = ("table",)
    options = {"reuse_unchanged_pages": False}
    templates = ("PAGE_ALL",)

    def write(self) -> str | None:
        """Write all.html; the page, or None when the cached one is kept."""
        engine = self.engine
        if self.option("reuse_unchanged_pages") and \
                engine.reuse_cached_page('all', 'ncd', 'no_doc_changes', 'build_page_index_all'):
            return None
        var = engine.get_theme_var()
        var['content'] = engine.build_datatable([], list(engine.srvdtb.get_documents()))
        page: str = engine.template('PAGE_ALL').render(var=var)
        engine.distribute_md('all', page, listing=True)
        engine.add_system_page('all', 'All documents')
        return page

    def pages(self, site: Site) -> None:
        self.write()

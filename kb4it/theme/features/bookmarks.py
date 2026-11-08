"""Feature bookmarks: bookmarks.html, the documents with Bookmark set to Yes, True or On."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kb4it.core.documents import is_yes
from kb4it.core.log import q
from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Site


class Bookmarks(Feature):
    """bookmarks.html."""

    name = "bookmarks"
    requires = ("table",)
    options = {"reuse_unchanged_pages": False}
    templates = ("PAGE_BOOKMARKS",)

    def write(self) -> str | None:
        """Write bookmarks.html; the page, or None when the cached one is kept."""
        engine, db = self.engine, self.engine.srvdtb
        if self.option("reuse_unchanged_pages") and \
                engine.reuse_cached_page('bookmarks', 'ncd', 'no_doc_changes', 'build_page_bookmarks'):
            return None
        var = engine.get_theme_var()
        doclist = []
        for doc_id in db.get_documents():
            bookmark = (db.get_values(doc_id, 'Bookmark') or [''])[0]
            doc_bookmarked = is_yes(bookmark)
            engine.log.debug(f"[THEME] BOOKMARK_CHECK doc={q(doc_id)} bookmark={q(bookmark)} "
                             f"is_bookmarked={q(doc_bookmarked)}")
            if doc_bookmarked:
                doclist.append(doc_id)
        engine.log.debug(f"[THEME] BOOKMARKS_FOUND n={len(doclist)}")
        datatable = self.table_html(doclist, filterable=True)
        engine.add_system_page('bookmarks', 'Bookmarks')
        var['page']['title'] = 'Bookmarks'
        var['page']['dt_bookmarks'] = datatable
        page: str = engine.template('PAGE_BOOKMARKS').render(var=var)
        engine.distribute_md('bookmarks', page, listing=True)
        engine.log.debug("[THEME] BOOKMARKS_PAGE_CREATED")
        return page

    def pages(self, site: Site) -> None:
        self.write()

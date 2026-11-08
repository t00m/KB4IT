"""Feature search: the search page, the search box and target/search-index.js."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kb4it.services.builder import Builder
from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Doc, Site


class Search(Feature):
    """Full-text search over the documents, in the browser."""

    name = "search"
    hooks = ("search_documents", "search_record", "search_sections")
    options = {
        "search_index_var": "KB4IT_INDEX",          # global variable of target/search-index.js
        "search_index_warn_bytes": 2 * 1024 * 1024,  # size of the index that logs SEARCH INDEX_LARGE
        "search_own_page": False,                   # True: the theme writes search.html itself
        "search_optional": True,                    # repo.json "search": false turns search off
    }
    templates = ("PAGE_SEARCH", "HTML_SEARCH_BOX")
    assets = ("search",)
    theme_json = {"search": True}

    def pages(self, site: Site) -> None:
        if not self.option("search_own_page"):
            self.engine.create_page_search()

    def enabled(self) -> bool:
        """True when this build has search: always when search_optional is False."""
        if not self.option("search_optional"):
            return True
        return bool(Builder.search_enabled(self.engine))

    def write_index(self) -> None:
        """Stage 8: target/search-index.js (removed with search.html when search is off)."""
        if not self.option("search_optional"):
            self.engine.write_index_file(self.engine.srvbes.get_path("target"))
            return
        Builder.write_search_index(self.engine)  # type: ignore[no-untyped-call]

    # Defaults of the hooks: what Builder does.
    def search_documents(self) -> list[Any]:
        """The documents of the index, in index order (Docs or ids)."""
        return list(Builder.search_documents(self.engine))

    def search_record(self, doc: Doc) -> dict[str, Any] | None:
        """The index record of one document; None leaves it out."""
        record: dict[str, Any] = Builder.search_record(self.engine, doc.id)
        return record

    def search_sections(self, doc: Doc) -> list[Any]:
        """[[anchor, heading, text], ...] of one document."""
        return list(Builder.search_sections(self.engine, doc.id))

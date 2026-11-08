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
    options = {"search_index_var": "KB4IT_INDEX"}
    templates = ("PAGE_SEARCH", "HTML_SEARCH_BOX")
    assets = ("search",)
    theme_json = {"search": True}

    def pages(self, site: Site) -> None:
        self.engine.create_page_search()

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

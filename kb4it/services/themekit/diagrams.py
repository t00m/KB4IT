"""Diagrams kit (Layer 1): the Mermaid diagrams of every document, shown by the properties chosen in a filter panel.

Legacy API: the code lives in the diagrams feature (kb4it/theme/features/diagrams.py).
"""

from __future__ import annotations

from typing import Any

from kb4it.services.themekit.host import ThemeHost, feature_of
from kb4it.theme.features.diagrams import (HEADING_ID, HEADING_OR_DIAGRAM, MERMAID_FENCE, TAG, Diagrams,
                                           document_diagrams)

__all__ = ["HEADING_ID", "HEADING_OR_DIAGRAM", "MERMAID_FENCE", "TAG", "DiagramsMixin", "document_diagrams"]


class DiagramsMixin(ThemeHost):
    """The Diagrams page: the Gallery page, with the Mermaid diagrams of the documents instead of their images."""

    def diagram_html(self, doc_id: str) -> str:
        """The HTML of a document body with a mermaid fence, as the compiler makes it, so the heading ids match; else ''."""
        return feature_of(self, Diagrams).html_of(doc_id)

    def diagram_items(self, doc_id: str) -> list[dict[str, Any]]:
        """The diagrams of one document, each linked to its section."""
        return feature_of(self, Diagrams).items(doc_id)

    def build_page_diagrams(self) -> None:
        """The Diagrams page: no diagram at first; the browser draws the ones the filters choose."""
        feature_of(self, Diagrams).write()

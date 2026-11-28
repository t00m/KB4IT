"""Metadata of a document page: the property and value links, and the page actions.

Legacy API: the code lives in the metadata feature (kb4it/theme/features/metadata.py).
"""

from __future__ import annotations

from typing import Any

from kb4it.services.themekit.host import ThemeHost, feature_of
from kb4it.theme.features.metadata import Metadata


class MetadataMixin(ThemeHost):
    """Metadata section and page actions; needs `Builder.template` and `srvdtb`."""

    def get_page_actions(self, var: dict[str, Any]) -> str:
        """Return the html of the page actions (SECTION_ACTIONS)."""
        return feature_of(self, Metadata).actions(var)

    def get_labels(self, values: list[tuple[str, str]]) -> str:
        """Return the html links for (page, text) pairs; empty texts are left out."""
        return feature_of(self, Metadata).labels(values)

    def get_html_values_from_key(self, docId: str, key: str) -> list[tuple[str, str]]:
        """Return (page, value) pairs for the values of a property of a document; a date key has no page."""
        return feature_of(self, Metadata).values_of(docId, key)

    def build_metadata_section(self, docId: str) -> str:
        """Return a html block for displaying metadata (keys and values)."""
        return feature_of(self, Metadata).section_html(docId)

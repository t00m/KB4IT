"""Navigation kit (Layer 1): previous and next page in the theme's reading order.

Legacy API: the public API has the navigation feature (kb4it/theme/features/navigation.py).
"""

from __future__ import annotations

from kb4it.services.themekit.host import ThemeHost
from kb4it.theme.features.navigation import neighbours_in


class NavigationMixin(ThemeHost):
    """`ordered_pages` and `neighbours`; a theme fills `ordered_pages`."""

    def ordered_pages(self, doc_id: str) -> list[str]:
        """Doc ids of the reading sequence doc_id belongs to, in order (a whole help site, one book); default none."""
        return []

    def neighbours(self, doc_id: str) -> tuple[str | None, str | None]:
        """Previous and next doc id of doc_id in its sequence; (None, None) when it is not listed."""
        return neighbours_in(self.ordered_pages(doc_id), doc_id)

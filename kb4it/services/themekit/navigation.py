"""Navigation kit (Layer 1): previous and next page in the theme's reading order."""

from __future__ import annotations

from kb4it.services.themekit.host import ThemeHost


class NavigationMixin(ThemeHost):
    """`ordered_pages` and `neighbours`; a theme fills `ordered_pages`."""

    def ordered_pages(self, doc_id: str) -> list[str]:
        """Doc ids of the reading sequence doc_id belongs to, in order (a whole help site, one book); default none."""
        return []

    def neighbours(self, doc_id: str) -> tuple[str | None, str | None]:
        """Previous and next doc id of doc_id in its sequence; (None, None) when it is not listed."""
        order = self.ordered_pages(doc_id)
        if doc_id not in order:
            return None, None
        index = order.index(doc_id)
        prev = order[index - 1] if index > 0 else None
        nxt = order[index + 1] if index < len(order) - 1 else None
        return prev, nxt

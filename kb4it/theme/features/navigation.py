"""Feature navigation: previous and next page in the theme's reading order."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Doc


def neighbours_in(order: list[str], doc_id: str) -> tuple[str | None, str | None]:
    """Previous and next id of doc_id in order; (None, None) when it is not listed."""
    if doc_id not in order:
        return None, None
    index = order.index(doc_id)
    prev = order[index - 1] if index > 0 else None
    nxt = order[index + 1] if index < len(order) - 1 else None
    return prev, nxt


class Navigation(Feature):
    """neighbours(doc): the previous and next document of the reading sequence doc belongs to."""

    name = "navigation"
    hooks = ("ordered_pages",)

    def ordered_pages(self, doc: Doc) -> list[Any]:
        """The reading sequence doc belongs to, in order (Docs or ids); default none."""
        return []

    def neighbours(self, doc: Doc) -> tuple[Doc | None, Doc | None]:
        """The previous and next Doc of doc; None at either end or when doc is not in a sequence."""
        order = [d if isinstance(d, str) else d.id for d in self.hook("ordered_pages")(doc)]
        prev, nxt = neighbours_in(order, doc.id)
        return (self.doc(prev) if prev else None), (self.doc(nxt) if nxt else None)

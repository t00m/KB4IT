"""Navigation kit (Layer 1): previous and next page from the theme's reading order."""

from kb4it.services.builder import Builder
from kb4it.services.themekit.navigation import NavigationMixin


class _Theme(NavigationMixin, Builder):
    def ordered_pages(self, doc_id):
        """Override: one fixed sequence."""
        return ["a", "b", "c"]


def test_neighbours():
    theme = _Theme.__new__(_Theme)
    assert theme.neighbours("a") == (None, "b")
    assert theme.neighbours("b") == ("a", "c")
    assert theme.neighbours("c") == ("b", None)
    assert theme.neighbours("x") == (None, None)


def test_default_order_is_empty():
    theme = NavigationMixin()
    assert theme.ordered_pages("a") == []
    assert theme.neighbours("a") == (None, None)

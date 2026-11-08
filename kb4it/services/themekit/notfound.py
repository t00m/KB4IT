"""The 404 page of the document themes: a system page that no listing, search or feed knows.

Legacy API: the code lives in the not_found feature (kb4it/theme/features/notfound.py).
"""

from __future__ import annotations

from kb4it.services.themekit.host import ThemeHost, feature_of
from kb4it.theme.features.notfound import NotFound


class NotFoundMixin(ThemeHost):
    """Builds 404.html; needs `Builder`."""

    #: Source pages a document cannot take, because the theme writes a page of that name.
    #: Empty here; a theme that calls build_page_404() sets ("404.md",).
    reserved_pages: tuple[str, ...] = ()

    def build_page_404(self) -> None:
        """Create the 404 page; as a system page it stays out of listings, search, feed and sitemap."""
        feature_of(self, NotFound).write()

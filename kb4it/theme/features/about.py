"""Feature about: the About KB4IT and About this app pages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Site


class About(Feature):
    """about_kb4it.html, and about_app.html unless the site has its own about_app.md."""

    name = "about"
    templates = ("PAGE_ABOUT_KB4IT", "PAGE_ABOUT_APP")

    def pages(self, site: Site) -> None:
        self.engine.create_page_about_kb4it()
        self.engine.create_page_about_app()

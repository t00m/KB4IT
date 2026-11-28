"""Feature not_found: 404.html, a system page no listing, search or feed knows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Site


class NotFound(Feature):
    """The page web servers show for a missing page."""

    name = "not_found"
    templates = ("PAGE_404",)
    reserves = ("404.md",)

    def write(self) -> None:
        engine = self.engine
        var = engine.get_theme_var()
        engine.add_system_page("404", "Page not found", engine.template("PAGE_404").render(var=var))

    def pages(self, site: Site) -> None:
        self.write()

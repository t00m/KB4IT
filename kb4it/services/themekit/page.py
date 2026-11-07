"""Page pipeline hooks the document themes share."""

from __future__ import annotations

from typing import Any

from kb4it.services.themekit.host import ThemeHost


class DocumentPageMixin(ThemeHost):
    """Fills the page hooks of Builder.build_page() for techdoc, blog and bookshelf."""

    page_pipeline = True

    def page_toc(self, source_html: str) -> str:
        """The TOC of the compiled body, in the theme's markup."""
        return self.extract_toc(source_html)

    def page_actions(self, var: dict[str, Any]) -> str:
        """The page actions (SECTION_ACTIONS)."""
        return self.get_page_actions(var)

    def menu_contents(self, var: dict[str, Any]) -> str:
        """The header menu: disabled on a system page, the document contents otherwise."""
        if var['SystemPage']:
            return self.template('HTML_HEADER_MENU_CONTENTS_DISABLED').render()
        return self.template('HTML_HEADER_MENU_CONTENTS_ENABLED').render(var=var)

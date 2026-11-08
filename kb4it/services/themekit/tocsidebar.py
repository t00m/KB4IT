"""TOC sidebar kit (Layer 1): a second, sticky table of contents for long documents.

Legacy API: the code lives in the toc_sidebar feature (kb4it/theme/features/tocsidebar.py).
"""

from __future__ import annotations

from kb4it.services.themekit.host import ThemeHost
from kb4it.theme.features.tocsidebar import TOC_SIDEBAR_MIN_SECTIONS, sidebar_wanted

__all__ = ["TOC_SIDEBAR_MIN_SECTIONS", "TocSidebarMixin"]


class TocSidebarMixin(ThemeHost):
    """`toc_sidebar`; reads `toc_sidebar` from repo.json, else from the theme settings (`self.config`)."""

    def toc_sidebar(self, source_html: str) -> bool:
        """True when repo.json (else the theme settings) asks for the sidebar and the page has four or more sections."""
        return sidebar_wanted(self.srvbes.get_dict('repo') or {}, getattr(self, 'config', None), source_html)

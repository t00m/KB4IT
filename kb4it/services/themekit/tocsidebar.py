"""TOC sidebar kit (Layer 1): a second, sticky table of contents for long documents."""

from __future__ import annotations

import re

from kb4it.services.themekit.host import ThemeHost

TOC_SIDEBAR_MIN_SECTIONS = 4


class TocSidebarMixin(ThemeHost):
    """`toc_sidebar`; reads `toc_sidebar` from repo.json, else from the theme settings (`self.config`)."""

    def toc_sidebar(self, source_html: str) -> bool:
        """True when repo.json (else the theme settings) asks for the sidebar and the page has four or more sections."""
        repo = self.srvbes.get_dict('repo') or {}
        if isinstance(repo.get('toc_sidebar'), bool):
            wanted = repo['toc_sidebar']
        else:
            config = getattr(self, 'config', None)
            wanted = getattr(config, 'toc_sidebar', None) if not hasattr(config, 'get') else config.get('toc_sidebar')
            wanted = wanted is True
        return wanted and len(re.findall(r'<h2\b', source_html)) >= TOC_SIDEBAR_MIN_SECTIONS

"""Feature toc_sidebar: a second, sticky table of contents for long documents."""

from __future__ import annotations

import re
from typing import Any

from kb4it.theme.feature import Feature

TOC_SIDEBAR_MIN_SECTIONS = 4


def sidebar_wanted(repo: dict[str, Any], config: Any, source_html: str) -> bool:
    """True when repo.json (else the theme settings) asks for the sidebar and the page has four or more sections."""
    if isinstance(repo.get('toc_sidebar'), bool):
        wanted = repo['toc_sidebar']
    else:
        getter = getattr(config, 'get', None)
        wanted = (getter('toc_sidebar') if getter else getattr(config, 'toc_sidebar', None)) is True
    return bool(wanted) and len(re.findall(r'<h2\b', source_html)) >= TOC_SIDEBAR_MIN_SECTIONS


class TocSidebar(Feature):
    """wanted(html): whether a document page shows the side table of contents."""

    name = "toc_sidebar"
    requires = ("toc",)

    def wanted(self, source_html: str) -> bool:
        repo = self.engine.srvbes.get_dict('repo') or {}
        return sidebar_wanted(repo, getattr(self.theme, 'config', None), source_html)

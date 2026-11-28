"""Table of contents of a document page, in the theme's markup.

Legacy API: the code lives in the toc feature (kb4it/theme/features/toc.py).
"""

from __future__ import annotations

from kb4it.services.themekit.host import ThemeHost, feature_of
from kb4it.theme.features.toc import Toc


class TocMixin(ThemeHost):
    """`extract_toc`; needs `Builder.template` and `get_theme_var`."""

    def extract_toc(self, source: str) -> str:
        """Extract the TOC from compiled HTML in the theme's markup; '' when the source has none."""
        return feature_of(self, Toc).extract(source)

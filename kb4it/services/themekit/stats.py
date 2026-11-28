"""The stats page of the document themes.

Legacy API: the data comes from kb4it/core/stats.py and the page from the stats
feature (kb4it/theme/features/stats.py); the names below stay importable from here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from kb4it.core.stats import (FEW_PROPERTIES, LIST_LIMIT, MONTHS, NOT_METADATA, TOP_LINKED, TOP_VALUES, Bar, Capped,
                              CoverageRow, DocRef, RareKey, StatsData, ValueGroup, ValueRef, collect_stats)
from kb4it.services.themekit.host import ThemeHost, feature_of
from kb4it.theme.features.stats import Stats

__all__ = ["FEW_PROPERTIES", "LIST_LIMIT", "MONTHS", "NOT_METADATA", "TOP_LINKED", "TOP_VALUES", "Bar", "Capped",
           "CoverageRow", "DocRef", "RareKey", "StatsData", "StatsMixin", "ValueGroup", "ValueRef", "collect_stats"]


class StatsMixin(ThemeHost):
    """`build_page_stats`; needs `Builder`, `stats_keys` and the reuse helpers of `KeyPagesMixin`."""

    #: Properties left out of the stats page: free text says nothing as a count.
    stats_skip_keys: tuple[str, ...] = ('Summary',)

    if TYPE_CHECKING:
        def stats_keys(self) -> list[str]: ...

    def build_page_stats(self) -> None:
        """Create the stats page of the repository."""
        feature_of(self, Stats).write()

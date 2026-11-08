"""Related kit (Layer 1): other documents that share property values, the rarest values weighing most.

Legacy API: the code lives in the related feature (kb4it/theme/features/related.py).
"""

from __future__ import annotations

from typing import Any

from kb4it.services.themekit.host import ThemeHost, feature_of
from kb4it.theme.features.related import RELATED_KEYS, Related, related

__all__ = ["RELATED_KEYS", "RelatedMixin", "related"]


class RelatedMixin(ThemeHost):
    """`related_docs`; needs `srvdtb` and `srvbes.get_plan()`. A theme narrows the candidates with `related_candidates`."""

    related_keys = RELATED_KEYS

    def related_candidates(self) -> list[str]:
        """Documents that may be listed as related; default: every document that is not a system page."""
        return [d for d in feature_of(self, Related).related_candidates()]

    def related_docs(self, doc_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """related() of doc_id over the candidates; [] when doc_id is not one. The metadata is read once per build."""
        return feature_of(self, Related).related_ids(doc_id, limit)

"""Related kit (Layer 1): other documents that share property values, the rarest values weighing most."""

from __future__ import annotations

import math

from kb4it.services.themekit.host import ThemeHost

RELATED_KEYS = ('SID', 'Product', 'Transaction', 'Component', 'Tag')


def related(doc_id, meta, limit=5):
    """Return up to `limit` documents sharing a value of RELATED_KEYS with doc_id, best first.

    meta maps each document to its properties ({key: [values]}). A shared value scores
    log(N / df), where df is the number of documents with that value, so rare values count most.
    """
    total = len(meta)
    frequency = {}
    for props in meta.values():
        for key in RELATED_KEYS:
            for value in set(props.get(key) or []):
                frequency[(key, value)] = frequency.get((key, value), 0) + 1
    mine = {(key, v) for key in RELATED_KEYS for v in (meta.get(doc_id, {}).get(key) or []) if v}
    found = []
    for other, props in meta.items():
        if other == doc_id:
            continue
        shared = [(key, v) for key in RELATED_KEYS for v in (props.get(key) or []) if (key, v) in mine]
        if shared:
            score = sum(math.log(total / frequency[pair]) for pair in set(shared))
            grouped = {}
            for key, v in shared:
                grouped.setdefault(key, []).append(v)
            found.append({'doc': other, 'score': score,
                          'shared': [f"{key}: {', '.join(vals)}" for key, vals in grouped.items()]})
    found.sort(key=lambda item: (-item['score'], item['doc']))
    return found[:limit]


class RelatedMixin(ThemeHost):
    """`related_docs`; needs `srvdtb` and `srvbes.get_plan()`. A theme narrows the candidates with `related_candidates`."""

    related_keys = RELATED_KEYS

    def related_candidates(self) -> list:
        """Documents that may be listed as related; default: every document that is not a system page."""
        return [d for d in self.srvdtb.get_documents() if not self.srvdtb.is_system(d)]

    def related_docs(self, doc_id: str, limit: int = 5) -> list:
        """related() of doc_id over the candidates; [] when doc_id is not one. The metadata is read once per build."""
        plan = self.srvbes.get_plan()
        if getattr(self, '_related_plan', None) is not plan or not hasattr(self, '_related_meta'):
            self._related_meta = {d: {k: list(self.srvdtb.get_values(d, k)) for k in self.related_keys}
                                  for d in self.related_candidates()}
            self._related_plan = plan
        if doc_id not in self._related_meta:
            return []
        return related(doc_id, self._related_meta, limit)

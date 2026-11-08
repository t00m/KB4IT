"""Feature related: other documents that share property values, the rarest values weighing most."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Doc, Site

RELATED_KEYS = ('SID', 'Product', 'Transaction', 'Component', 'Tag')


def related(doc_id: str, meta: dict[str, dict[str, list[str]]], limit: int = 5,
            keys: tuple[str, ...] = RELATED_KEYS) -> list[dict[str, Any]]:
    """Return up to `limit` documents sharing a value of keys with doc_id, best first.

    meta maps each document to its properties ({key: [values]}). A shared value scores
    log(N / df), where df is the number of documents with that value, so rare values count most.
    """
    total = len(meta)
    frequency: dict[tuple[str, str], int] = {}
    for props in meta.values():
        for key in keys:
            for value in set(props.get(key) or []):
                frequency[(key, value)] = frequency.get((key, value), 0) + 1
    mine = {(key, v) for key in keys for v in (meta.get(doc_id, {}).get(key) or []) if v}
    found: list[dict[str, Any]] = []
    for other, props in meta.items():
        if other == doc_id:
            continue
        shared = [(key, v) for key in keys for v in (props.get(key) or []) if (key, v) in mine]
        if shared:
            score = sum(math.log(total / frequency[pair]) for pair in set(shared))
            grouped: dict[str, list[str]] = {}
            for key, v in shared:
                grouped.setdefault(key, []).append(v)
            found.append({'doc': other, 'score': score,
                          'shared': [f"{key}: {', '.join(vals)}" for key, vals in grouped.items()]})
    found.sort(key=lambda item: (-item['score'], item['doc']))
    return found[:limit]


class Related(Feature):
    """related(doc): the documents that share the rarest values with doc, best first."""

    name = "related"
    options = {"related_keys": RELATED_KEYS}
    hooks = ("related_candidates",)

    def __init__(self, theme: Any, engine: Any) -> None:
        super().__init__(theme, engine)
        self._meta: dict[str, dict[str, list[str]]] | None = None
        self._plan: Any = None

    def related_candidates(self) -> list[Any]:
        """Documents that may be listed as related (Docs or ids); default: every document."""
        db = self.engine.srvdtb
        return [d for d in db.get_documents() if not db.is_system(d)]

    def meta(self) -> dict[str, dict[str, list[str]]]:
        """{doc id: {key: [values]}} of the candidates, read once per build."""
        plan = self.engine.srvbes.get_plan()
        if self._meta is None or self._plan is not plan:
            db, keys = self.engine.srvdtb, self.option("related_keys")
            ids = [d if isinstance(d, str) else d.id for d in self.hook("related_candidates")()]
            self._meta = {d: {k: list(db.get_values(d, k)) for k in keys} for d in ids}
            self._plan = plan
        return self._meta

    def prepare(self, site: Site) -> None:
        self._meta = None
        self.meta()

    def related_ids(self, doc_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """related() of a document id over the candidates; [] when it is not one."""
        meta = self.meta()
        if doc_id not in meta:
            return []
        return related(doc_id, meta, limit, tuple(self.option("related_keys")))

    def related(self, doc: Doc, limit: int = 5) -> list[dict[str, Any]]:
        """[{doc, score, shared}] of the documents related to doc, best first; doc is a document id."""
        return self.related_ids(doc.id, limit)

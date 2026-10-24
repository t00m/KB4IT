"""techdoc related documents: other documents that share property values, the rarest values weighing most."""

import math

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

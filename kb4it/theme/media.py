"""Pages of the Gallery kind (Gallery, Diagrams): documents, their items and the filters to narrow them.

A plain helper module, not a feature: the gallery and diagrams features both call it, so neither
depends on the other. host is the engine (or a legacy theme): it needs srvdtb, srvbes, template()
and add_system_page(). Internal: not part of the public API.
"""

import json
from collections.abc import Callable
from typing import Any

from kb4it.core.util import html_id_for

# Keys that never become a filter: free text, or the page itself.
SKIP_KEYS = {'Summary', 'Bookmark'}

# The filter made from the year of Date, which is a blocked key.
YEAR = 'Year'

# (documents, items, filters), as media_data() returns them.
MediaData = tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]


def filter_keys(present: set[str], menu: list[str]) -> list[str]:
    """Order the filter keys: the menu keys of repo.json first, as listed there, then the rest by name."""
    first = [key for key in menu if key in present]
    return first + sorted(key for key in present if key not in first)


def media_data(host: Any, items_of: Callable[[str], list[dict[str, Any]]]) -> MediaData:
    """Return the documents with items, newest first, their items and the filters they can be narrowed by.

    items_of(doc_id) gives the items of one document (images, diagrams); a document without any is left out.
    """
    skip = set(SKIP_KEYS) | set(host.srvdtb.get_blocked_keys()) | set(host.srvdtb.get_ignored_keys())
    docs_sorted = [d for d in host.srvdtb.sort_by_date(list(host.srvdtb.get_documents())) if not host.srvdtb.is_system(d)]
    docs: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    values: dict[str, dict[str, int]] = {}
    for doc_id in docs_sorted:
        found = items_of(doc_id)
        if not found:
            continue
        props = {}
        for key in host.srvdtb.get_doc_keys(doc_id):
            if key in skip:
                continue
            vals = sorted({v for v in host.srvdtb.get_values(doc_id, key) if v})
            if vals:
                props[key] = vals
        year = (host.srvdtb.get_values(doc_id, 'Date') or [''])[0][:4]
        if year.isdigit():
            props[YEAR] = [year]
        title = (host.srvdtb.get_values(doc_id, 'Title') or [doc_id])[0]
        for item in found:
            items.append(dict(item, d=len(docs)))
        docs.append({'title': title, 'href': html_id_for(doc_id), 'props': props})
        for key, vals in props.items():
            for value in vals:
                values.setdefault(key, {}).setdefault(value, 0)
                values[key][value] += len(found)
    menu = (host.srvbes.get_dict('repo') or {}).get('menu') or []
    filters = []
    for key in filter_keys(set(values) - {YEAR}, menu) + ([YEAR] if YEAR in values else []):
        order = sorted(values[key], reverse=True) if key == YEAR else sorted(values[key], key=str.lower)
        filters.append({'key': key, 'values': [[v, values[key][v]] for v in order]})
    return docs, items, filters


def render_media_page(host: Any, name: str, title: str, kind: str, data: MediaData) -> None:
    """Write a page of the Gallery kind: kind is 'image' or 'diagram', data comes from media_data."""
    docs, items, filters = data
    page = host.template('PAGE_GALLERY').render(var={
        'kind': kind,
        'items': len(items),
        'docs': len(docs),
        'filters': filters,
        # JSON inside <script>: "<" escaped so a value cannot close the element.
        'json': json.dumps({'kind': kind, 'docs': docs, 'items': items, 'filters': filters},
                           ensure_ascii=False, sort_keys=True, separators=(',', ':')).replace('<', '\\u003c'),
    })
    host.add_system_page(name, title, page)

"""AppHelp navigation: sidebar sections, prev/next order and related pages."""


def build_sections(pages):
    """Group pages by Section, sort each by Order and order sections by their lowest Order."""
    groups = {}
    for page in pages:
        groups.setdefault(page.section, []).append(page)
    for entries in groups.values():
        entries.sort(key=lambda page: (page.order, page.doc_id))
    return sorted(groups.items(), key=lambda item: (item[1][0].order, item[0]))


def flatten(sections):
    return [page for _name, entries in sections for page in entries]


def neighbours(flat, doc_id):
    ids = [page.doc_id for page in flat]
    if doc_id not in ids:
        return None, None
    index = ids.index(doc_id)
    prev = flat[index - 1] if index > 0 else None
    nxt = flat[index + 1] if index < len(flat) - 1 else None
    return prev, nxt


def related_pages(page, pages, limit=5):
    """Pages listed in Related first, then the best scored by shared metadata."""
    by_id = {other.doc_id: other for other in pages}
    forced = [by_id[d] for d in dict.fromkeys(page.related) if d in by_id and d != page.doc_id]
    skip = {page.doc_id} | {other.doc_id for other in forced}
    scored = []
    for other in pages:
        if other.doc_id in skip:
            continue
        score = (3 * len(set(page.features) & set(other.features))
                 + 2 * len(set(page.keywords) & set(other.keywords))
                 + len(set(page.tags) & set(other.tags))
                 + (1 if other.section == page.section else 0))
        if score > 0:
            scored.append((-score, other.order, other.doc_id, other))
    scored.sort(key=lambda item: item[:3])
    return (forced + [item[3] for item in scored])[:limit]

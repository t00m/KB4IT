"""AppHelp search index: plain text per section, written as a script so it loads from file://."""

import json

import lxml.html

ARTICLE_ID = "ah-article-body"
SKIP_TAGS = {"script", "style", "button"}
SECTION_TEXT_MAX = 5000


def _add(section, text):
    if text:
        section["text"].append(text)


def extract_sections(page_html: str) -> list:
    """Split the article of a built page into sections with heading, id and plain text."""
    root = lxml.html.fromstring(page_html)
    found = root.xpath(f'//*[@id="{ARTICLE_ID}"]')
    if not found:
        return []
    article = found[0]
    sections = [{"id": "", "heading": "", "text": []}]
    heading_roots, inside = set(), set()
    for element in article.iter():
        if not isinstance(element.tag, str):
            _add(sections[-1], element.tail)
            continue
        heading = None
        if element.tag in ("h2", "h3") and element.get("id"):
            heading = element
        elif element.tag == "details" and element.get("id") and element.find("summary") is not None:
            heading = element.find("summary")
        if heading is not None:
            sections.append({"id": element.get("id"), "heading": " ".join(heading.text_content().split()),
                             "text": []})
            heading_roots.add(heading)
            inside.update(heading.iter())
        if element not in inside and element.tag not in SKIP_TAGS:
            _add(sections[-1], element.text)
        if element is not article and (element not in inside or element in heading_roots):
            _add(sections[-1], element.tail)
    result = []
    for section in sections:
        text = " ".join(" ".join(section["text"]).split())[:SECTION_TEXT_MAX]
        if section["id"] or text:
            result.append({"id": section["id"], "heading": section["heading"], "text": text})
    return result


def page_record(page, sections) -> dict:
    facets = {
        "Kind": [page.kind] if page.kind else [],
        "Feature": list(page.features),
        "Level": [page.level] if page.level else [],
        "Platform": list(page.platforms),
        "Plugin": [page.plugin] if page.plugin else [],
        "Since": [page.since] if page.since else [],
    }
    return {
        "u": page.url, "t": page.title, "s": page.summary, "k": page.kind, "c": page.section,
        "f": {name: values for name, values in facets.items() if values},
        "w": list(page.keywords), "g": list(page.tags),
        "x": [[s["id"], s["heading"], s["text"]] for s in sections],
    }


def render_index_js(records) -> str:
    payload = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    return f"window.APPHELP_INDEX = {payload};\n"

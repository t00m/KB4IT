"""AppHelp search index: plain text per section, written as a script so it loads from file://."""

from kb4it.core import search as core_search

ARTICLE_ID = "ah-article-body"
SECTION_TEXT_MAX = core_search.SECTION_TEXT_MAX


def extract_sections(page_html: str) -> list:
    """Split the article of a built page into sections with heading, id and plain text."""
    return core_search.extract_sections(page_html, ARTICLE_ID)


def page_record(page, sections) -> dict:
    facets = {
        "DocType": [page.doctype] if page.doctype else [],
        "Feature": list(page.features),
        "Level": [page.level] if page.level else [],
        "Platform": list(page.platforms),
        "Plugin": [page.plugin] if page.plugin else [],
        "Since": [page.since] if page.since else [],
    }
    return {
        "u": page.url, "t": page.title, "s": page.summary, "k": page.doctype, "c": page.section,
        "f": {name: values for name, values in facets.items() if values},
        "w": list(page.keywords), "g": list(page.tags),
        "x": [[s["id"], s["heading"], s["text"]] for s in sections],
    }


def render_index_js(records) -> str:
    return core_search.render_index_js(records, "APPHELP_INDEX")

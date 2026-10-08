#!/usr/bin/env python

"""
Full-text search index shared by the themes.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

A page is split into sections (heading, anchor, plain text) taken from one
container element. The index is written as a script that sets a global, so
search works from file:// as well as from a web server. The browser side is
kb4it/resources/common/js/kb4it-search.js.
"""

import json
import os
import shutil

import lxml.html

from kb4it.core.env import ENV

SKIP_TAGS = {"script", "style", "button"}
SECTION_TEXT_MAX = 5000
INDEX_WARN_BYTES = 5 * 1024 * 1024
ENGINE_JS = os.path.join(ENV["GPATH"]["COMMON"], "js", "kb4it-search.js")


def _add(section, text):
    if text:
        section["text"].append(text)


def extract_sections(page_html: str, container_id: str) -> list:
    """Split the element with id container_id into sections: [{id, heading, text}, ...]."""
    root = lxml.html.fromstring(page_html)
    found = root.xpath(f'//*[@id="{container_id}"]')
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


def render_index_js(records, var_name="KB4IT_INDEX") -> str:
    """The index as a script: window.<var_name> = [...]."""
    payload = json.dumps(records, ensure_ascii=False, separators=(",", ":"))
    return f"window.{var_name} = {payload};\n"


def copy_engine(dest):
    """Copy the search engine script to dest (a file path)."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(ENGINE_JS, dest)


DOC_CONTAINER = "kb4it-doc"


def sections_dir(root) -> str:
    """Per-document section cache: <repo>/var/search, kept between builds for unchanged documents."""
    return os.path.join(str(root), "var", "search")


def _cache_name(doc_id) -> str:
    return f"{doc_id}.json"


def save_doc_sections(root, doc_id, html_fragment):
    """Store the sections of one compiled document (called by the compiler)."""
    sections = extract_sections(f'<div id="{DOC_CONTAINER}">{html_fragment}</div>', DOC_CONTAINER)
    folder = sections_dir(root)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, _cache_name(doc_id)), "w", encoding="utf-8") as fh:
        json.dump(sections, fh, ensure_ascii=False)


def load_doc_sections(root, doc_id) -> list:
    try:
        with open(os.path.join(sections_dir(root), _cache_name(doc_id)), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return []


def prune_sections(root, keep):
    """Remove cached sections of documents that no longer exist."""
    folder = sections_dir(root)
    if not os.path.isdir(folder):
        return
    wanted = {_cache_name(doc) for doc in keep}
    for name in os.listdir(folder):
        if name not in wanted:
            os.unlink(os.path.join(folder, name))

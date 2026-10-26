#!/usr/bin/python
"""
Head meta service: description, Open Graph and canonical link of each page.

# File: headmeta.py
# Author: Tomás Vírseda
# License: GPL v3
"""

import html as htmllib
import re

from kb4it.core.documents import joined_value
from kb4it.core.mdrich import MATH_MARKS, MERMAID_MARK
from kb4it.core.publish import absolute
from kb4it.core.search import load_doc_sections
from kb4it.core.util import html_id_for

META_START = "<!-- kb4it:meta -->"
META_END = "<!-- /kb4it:meta -->"
HEAD_OPEN = re.compile(r"<head\b[^>]*>", re.IGNORECASE)
BASE_TAG = re.compile(r"<base\b[^>]*>\s*", re.IGNORECASE)


def short_text(text, limit) -> str:
    """text cut to limit characters at a word boundary, with an ellipsis when cut."""
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit - 1].rsplit(" ", 1)[0]
    return cut.rstrip(",;:.") + "\u2026"


class HeadMetaMixin:
    """Head meta methods of Builder."""

    def page_meta(self, page_name, html) -> dict:
        """Values for HTML_HEAD_META: description, Open Graph and canonical link of one page."""
        repo = self.srvbes.get_dict("repo") or {}
        base = getattr(self.srvbes, "site_url", None)
        if not hasattr(self, "_page_docs"):
            sources = self.srvbes.get_value("docs", "filenames") or []
            self._page_docs = {html_id_for(d): d for d in sources}
        doc_id = self._page_docs.get(page_name)
        values = (lambda key: [v for v in (self.srvdtb.get_values(doc_id, key) or []) if v]) if doc_id else (lambda key: [])
        if doc_id:
            sections = load_doc_sections(self.srvbes.get_path("root"), doc_id)
            text = joined_value(values("Summary")) or (sections[0]["text"] if sections else "")
            title = (values("Title") or [doc_id])[0]
        else:
            text, title = repo.get("tagline", ""), repo.get("title", "")
        head = html[:html.lower().find("</head>")].lower()
        image = repo.get("og_image")
        theme = self.srvbes.get_dict("theme") or {}
        theme_icon = f"resources/themes/{theme['id']}/{theme['favicon']}" if theme.get("id") and theme.get("favicon") else ""
        return {
            "title": title, "site_name": repo.get("title", ""), "type": "article" if doc_id else "website",
            "description": short_text(text, 160), "author": ", ".join(values("Author")),
            "url": absolute(base, page_name) if base else "",
            "image": absolute(base, image) if base and image else "",
            "favicon": repo.get("logo") or theme_icon, "mermaid": MERMAID_MARK in html, "math": any(mark in html for mark in MATH_MARKS),
            "feed": "feed.xml" if self.feed_enabled() else "",
            "has_description": '<meta name="description"' in head, "has_author": '<meta name="author"' in head,
        }

    def inject_head_meta(self, html, page_name) -> str:
        """Insert (or replace) the HTML_HEAD_META block before </head>."""
        start, end = html.find(META_START), html.find(META_END)
        if start >= 0 and end > start:
            html = html[:start] + html[end + len(META_END):]
        close = html.lower().find("</head>")
        if close < 0:
            return html
        if page_name == "404.html":
            html = self._with_base(html)
            close = html.lower().find("</head>")
        block = self.render_template("HTML_HEAD_META", {"meta": self.page_meta(page_name, html)}).strip()
        return html[:close] + block + "\n" + html[close:]

    def _with_base(self, html) -> str:
        """html with <base href> right after <head>, so the 404 page finds its files from any URL."""
        base = getattr(self.srvbes, "site_url", None)
        opening = HEAD_OPEN.search(html)
        if not base or not opening:
            return html
        head_end = html.lower().find("</head>")
        head = BASE_TAG.sub("", html[opening.end():head_end])
        tag = f'<base href="{htmllib.escape(base.rstrip("/") + "/", quote=True)}">\n'
        return html[:opening.end()] + "\n" + tag + head.lstrip("\n") + html[head_end:]

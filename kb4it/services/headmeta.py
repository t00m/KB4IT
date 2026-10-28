#!/usr/bin/python
"""
Head meta service: description, Open Graph, canonical link and structured data of each page.

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
from kb4it.core.structured import (DEFAULT_MAP, SeoSettings, document_node, graph, merged_map, render_jsonld,
                                   website_node)
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

    def seo_settings(self) -> SeoSettings:
        """The checked repo.json "seo" block (Backend loads it with the configuration)."""
        return getattr(self.srvbes, "seo", None) or SeoSettings()

    def page_lang(self) -> str:
        """Language of the generated pages: repo.json seo.lang, else English."""
        return self.seo_settings().lang or "en"

    def structured_defaults(self) -> dict:
        """schema.org type of a document without a known DocType, and the frontmatter key map of the theme."""
        return {"type": "TechArticle", "map": DEFAULT_MAP}

    def search_page(self) -> str:
        """Page that runs a search from ?q=, or empty when the site has none."""
        return "search.html" if self.search_enabled() else ""

    def structured_data(self, page_name, doc_id, title, description) -> str:
        """JSON-LD of one page: the document node, and the WebSite node on the home page."""
        seo = self.seo_settings()
        if not seo.structured_data:
            return ""
        repo = self.srvbes.get_dict("repo") or {}
        base = getattr(self.srvbes, "site_url", None) or ""
        lang = self.page_lang()
        website_id = f"{base}#website" if base else ""
        nodes = []
        if page_name == "index.html":
            search = self.search_page()
            nodes.append(website_node(name=repo.get("title", ""), description=short_text(repo.get("tagline", ""), 160),
                                      lang=lang, url=base, search_url=absolute(base, search) if base and search else ""))
        if doc_id and not self.srvdtb.is_system(doc_id):  # 404, about pages: not content
            defaults = self.structured_defaults()
            ignored = set(self.srvdtb.get_ignored_keys())
            mapping = {key: spec for key, spec in merged_map(defaults["map"], seo.map).items() if key not in ignored}
            values = {key: [v for v in (self.srvdtb.get_values(doc_id, key) or []) if v]
                      for key in [*mapping, "Date", "DocType"]}
            nodes.append(document_node(title=title, description=description, values=values, mapping=mapping,
                                       default_type=defaults["type"], lang=lang,
                                       url=absolute(base, page_name) if base else "", website_id=website_id))
        return render_jsonld(graph(nodes)) if nodes else ""

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
            "jsonld": "" if "application/ld+json" in head else self.structured_data(page_name, doc_id, title, short_text(text, 160)),
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

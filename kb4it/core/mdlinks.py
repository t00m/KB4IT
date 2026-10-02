"""Rewrite links to Markdown sources so they point to the compiled HTML pages."""

import re
from urllib.parse import unquote, urlsplit, urlunsplit

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

MD_PATH_RE = re.compile(r"\.(md|markdown)$", re.IGNORECASE)


def rewrite_md_href(href: str) -> str | None:
    """Return the .html form of a relative link to a Markdown file, or None if it is not one."""
    if not href or href.startswith(("#", "/")):
        return None
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or not MD_PATH_RE.search(parts.path):
        return None
    path = MD_PATH_RE.sub(".html", parts.path)
    return urlunsplit(("", "", path, parts.query, parts.fragment))


class _MdLinkProcessor(Treeprocessor):
    def run(self, root):
        for element in root.iter("a"):
            href = element.get("href", "")
            new_href = rewrite_md_href(href)
            if new_href is None:
                continue
            parts = urlsplit(href)
            self.md.kb4it_links.append((unquote(parts.path), parts.fragment))
            element.set("href", new_href)


class MdLinkExtension(Extension):
    """python-markdown extension: rewrite .md links and record them on md.kb4it_links."""

    def extendMarkdown(self, md):
        md.kb4it_links = []
        # Priority 5 runs after the inline processor (20), which creates the <a> elements.
        md.treeprocessors.register(_MdLinkProcessor(md), "kb4it_mdlinks", 5)

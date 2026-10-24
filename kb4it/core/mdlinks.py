"""Rewrite links to Markdown sources so they point to the compiled HTML pages."""

import os
import posixpath
import re
from urllib.parse import unquote, urlsplit, urlunsplit

from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

MD_PATH_RE = re.compile(r"\.(md|markdown)$", re.IGNORECASE)
ADOC_PATH_RE = re.compile(r"\.adoc$", re.IGNORECASE)


def rewrite_md_href(href: str) -> str | None:
    """Return the .html form of a relative link to a Markdown file, or None if it is not one."""
    if not href or href.startswith(("#", "/")):
        return None
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or not MD_PATH_RE.search(parts.path):
        return None
    path = MD_PATH_RE.sub(".html", parts.path)
    return urlunsplit(("", "", path, parts.query, parts.fragment))


def bare_link_path(href: str) -> str | None:
    """Return the path of a relative link written without an extension or to a .adoc file, else None."""
    if not href or href.startswith(("#", "/")):
        return None
    parts = urlsplit(href)
    path = parts.path
    if parts.scheme or parts.netloc or not path or path.endswith("/"):
        return None
    last = posixpath.basename(path)
    if "." in last and not ADOC_PATH_RE.search(last):
        return None
    return unquote(path)


def suggest_md(path: str, known: set[str]) -> str | None:
    """Return the source document a bare link most likely means, when it exists."""
    name = ADOC_PATH_RE.sub(".md", path) if ADOC_PATH_RE.search(path) else f"{path}.md"
    name = os.path.normpath(name).replace(os.sep, "/")
    return name if name in known else None


class _MdLinkProcessor(Treeprocessor):
    def run(self, root):
        for element in root.iter("a"):
            href = element.get("href", "")
            new_href = rewrite_md_href(href)
            if new_href is None:
                bare = bare_link_path(href)
                if bare is not None:
                    self.md.kb4it_bare_links.append(bare)
                continue
            parts = urlsplit(href)
            self.md.kb4it_links.append((unquote(parts.path), parts.fragment))
            element.set("href", new_href)


class MdLinkExtension(Extension):
    """python-markdown extension: rewrite .md links and record them on md.kb4it_links.

    Links written without an extension, or to a .adoc file, are left as written and
    recorded on md.kb4it_bare_links, so they are reported but never counted as backlinks.
    """

    def extendMarkdown(self, md):
        md.kb4it_links = []
        md.kb4it_bare_links = []
        # Priority 5 runs after the inline processor (20), which creates the <a> elements.
        md.treeprocessors.register(_MdLinkProcessor(md), "kb4it_mdlinks", 5)


def _body(text: str) -> str:
    """Markdown after the frontmatter and the H1 title line."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            line_end = text.find("\n", end + 4)
            text = text[line_end + 1:] if line_end >= 0 else ""
    return re.sub(r"^\s*#\s+[^\n]+\n?", "", text, count=1)


def _anchor_ids(tokens):
    for token in tokens:
        yield token["id"]
        yield from _anchor_ids(token.get("children", []))


def scan_document(path):
    """(links, anchors, bare links) of a Markdown source: [(target path, fragment), ...], its heading ids and [path, ...]."""
    import markdown
    from kb4it.core.util import SOURCE_ENCODING
    with open(path, encoding=SOURCE_ENCODING) as fh:
        text = _body(fh.read())
    md = markdown.Markdown(extensions=["extra", "admonition", "toc", "sane_lists", MdLinkExtension()])
    html = md.convert(text)
    anchors = set(_anchor_ids(md.toc_tokens)) | set(re.findall(r'\sid="([^"]+)"', html))
    return list(md.kb4it_links), anchors, list(md.kb4it_bare_links)

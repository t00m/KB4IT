"""Post-build checks (P7): the Problem type and the checks every theme gets.

Builder.checks(target) returns a list of Problem; Builder.run_checks() logs them as
[CHECK] lines and fails the build on an error, or on any problem with repo.json strict.
"""

import html
import os
import re
from dataclasses import dataclass
from urllib.parse import unquote, urlsplit

from kb4it.core.log import q

SEVERITIES = ("warning", "error")


@dataclass(frozen=True)
class Problem:
    """One finding: code, the page (or document) it is about, key=value detail, severity.

    label names the page in the text: "ANCHOR_MISSING from=a.html to=b.html#x" uses label "from".
    """
    code: str
    page: str
    detail: str
    severity: str = "warning"
    label: str = "page"

    def __str__(self):
        where = f" {self.label}={q(self.page)}" if self.page else ""
        return f"{self.code}{where} {self.detail}".rstrip()


# KB4IT writes quoted attributes; a scan of the text is ten times faster than parsing every page (P7 budget).
_ID = re.compile(r"""id=(["'])(.*?)\1""", re.DOTALL)  # starts with a literal, so the scan is fast
_LINK = re.compile(r"""<a\b[^<>]*?\shref\s*=\s*(["'])(.*?)\1""", re.DOTALL | re.IGNORECASE)
_SCRIPT = re.compile(r"<(script|style)\b.*?</\1\s*>", re.DOTALL | re.IGNORECASE)


def _read(path) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return _SCRIPT.sub("", fh.read())


def _ids(text) -> set:
    """Every id attribute in the text: id= right after white space ("data-id=" is not one)."""
    return {html.unescape(m.group(2)) for m in _ID.finditer(text) if m.start() and text[m.start() - 1].isspace()}


def page_ids(path) -> set:
    """Every id attribute of an HTML file."""
    return _ids(_read(path))


def target_exists(target_dir, page, anchor, cache) -> bool:
    """True when page exists in target_dir and, with an anchor, has an element with that id."""
    if page not in cache:
        path = os.path.join(target_dir, page)
        cache[page] = page_ids(path) if os.path.isfile(path) else None
    ids = cache[page]
    return ids is not None and (not anchor or anchor in ids)


def check_anchors(target_dir, pages) -> list[Problem]:
    """One ANCHOR_MISSING per internal link to a missing page or anchor.

    Only links between pages of the target root are checked: links with a scheme or host,
    absolute paths, links into or out of subfolders, non-HTML files and fragments with "=" are skipped.
    Each page is read once.
    """
    cache, links = {}, {}
    for name in pages:
        text = _read(os.path.join(target_dir, name))
        cache[name] = _ids(text)
        links[name] = [html.unescape(m.group(2)).strip() for m in _LINK.finditer(text)]
    broken = []
    for name in pages:
        for href in links[name]:
            parts = urlsplit(href)
            if not href or parts.scheme or parts.netloc or href.startswith("/"):
                continue
            path = unquote(parts.path) or name
            if not path.endswith(".html") or "/" in path:
                continue
            fragment = unquote(parts.fragment)
            if "=" in fragment:
                continue  # a route a script reads (add.html#new=person&title=...), not an element id
            if not target_exists(target_dir, path, fragment, cache):
                broken.append(Problem("ANCHOR_MISSING", name, f"to={q(href)}", label="from"))
    return broken


def html_pages(target_dir) -> list[str]:
    """Sorted names of the HTML pages in the target root."""
    if not os.path.isdir(target_dir):
        return []
    return sorted(name for name in os.listdir(target_dir) if name.endswith(".html"))

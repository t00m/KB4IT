"""AppHelp build checks: anchors behind links, help ids and the contract file."""

import json
import os
from urllib.parse import unquote, urlsplit

import lxml.html


def page_ids(path) -> set:
    root = lxml.html.parse(str(path)).getroot()
    return {el.get("id") for el in root.iter() if isinstance(el.tag, str) and el.get("id")}


def _target_exists(target_dir, page, anchor, cache):
    if page not in cache:
        path = os.path.join(target_dir, page)
        cache[page] = page_ids(path) if os.path.isfile(path) else None
    ids = cache[page]
    return ids is not None and (not anchor or anchor in ids)


def check_anchors(target_dir, pages) -> list:
    """Return (page, href) for each internal link to a missing page or a missing anchor."""
    cache, broken = {}, []
    for name in pages:
        root = lxml.html.parse(os.path.join(target_dir, name)).getroot()
        for link in root.iter("a"):
            href = link.get("href") or ""
            parts = urlsplit(href)
            if not href or parts.scheme or parts.netloc or href.startswith("/"):
                continue
            path = unquote(parts.path) or name
            if not path.endswith(".html") or "/" in path:
                continue
            if not _target_exists(target_dir, path, unquote(parts.fragment), cache):
                broken.append((name, href))
    return broken


def helpid_map(pages) -> dict:
    mapping = {}
    for page in pages:
        for ident, anchor in page.helpids:
            mapping[ident] = page.url + (f"#{anchor}" if anchor else "")
    return dict(sorted(mapping.items()))


def render_helpids_js(mapping) -> str:
    return "window.APPHELP_HELPIDS = " + json.dumps(mapping, ensure_ascii=False, sort_keys=True) + ";\n"


def check_helpids(target_dir, mapping) -> list:
    """Return the help ids whose page or anchor does not exist."""
    cache = {}
    return [ident for ident, url in mapping.items()
            if not _target_exists(target_dir, *url.partition("#")[::2], cache)]


def load_contract(path) -> list:
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        lines = [line.strip() for line in fh]
    return [line for line in lines if line and not line.startswith("#")]


def check_contract(entries, mapping, target_dir) -> list:
    """Return contract entries (help ids or page.html#anchor) that the site does not provide."""
    cache, missing = {}, []
    for entry in entries:
        if ".html" in entry:
            page, _, anchor = entry.partition("#")
            if not _target_exists(target_dir, page, anchor, cache):
                missing.append(entry)
        elif entry not in mapping:
            missing.append(entry)
    return missing

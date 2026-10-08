#!/usr/bin/env python

"""
Files and tags for publishing a site: site URL, sitemap.xml, robots.txt, Atom feed, page metadata.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

from urllib.parse import urlsplit

from kb4it.core.exceptions import ConfigError


def site_url(repo: dict):
    """The public base URL from repo.json, always ending with '/', or None when it is not set."""
    raw = repo.get("site_url")
    if raw in (None, ""):
        return None
    if not isinstance(raw, str):
        raise ConfigError("repo.json 'site_url' must be a URL such as https://example.org/docs/")
    parts = urlsplit(raw.strip())
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ConfigError(f"repo.json 'site_url' must start with http:// or https://, not {raw!r}")
    url = raw.strip()
    return url if url.endswith("/") else url + "/"


def absolute(base, path):
    """Absolute URL of a page path inside the site."""
    return base + path.lstrip("/").replace("\\", "/")


ROBOTS_MARK = "# Written by KB4IT"
SITEMAP_SKIP_DIRS = {"admin", "resources", "sources"}


def sitemap_xml(entries) -> str:
    """sitemap.xml for [(absolute url, 'YYYY-MM-DD'), ...]."""
    from xml.sax.saxutils import escape
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lastmod in entries:
        lines.append(f"  <url><loc>{escape(url)}</loc><lastmod>{lastmod}</lastmod></url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def robots_txt(base) -> str:
    return f"{ROBOTS_MARK}\nUser-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n"


def site_pages(target, exclude=()):
    """Relative paths ('a.html', 'sub/b.html') of the pages in target, skipping assets and admin folders."""
    import os
    pages = []
    for root, dirs, files in os.walk(target):
        rel_root = os.path.relpath(root, target)
        if rel_root == ".":
            dirs[:] = [d for d in dirs if d not in SITEMAP_SKIP_DIRS]
            rel_root = ""
        for name in files:
            rel = os.path.join(rel_root, name).replace(os.sep, "/")
            if name.endswith(".html") and rel not in exclude:
                pages.append(rel)
    return sorted(pages)

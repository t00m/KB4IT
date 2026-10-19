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


def atom_date(value) -> str:
    """'2026-10-08' or '2026-10-08 14:30:00' as an Atom timestamp (UTC)."""
    text = str(value).strip().replace("T", " ")
    date, _, time = text.partition(" ")
    return f"{date}T{(time or '00:00:00')[:8]}Z"


def atom_feed(title, base, entries, subtitle="") -> str:
    """Atom 1.0 feed. entries: dicts with title, url, updated, author, content (HTML)."""
    from xml.sax.saxutils import escape
    updated = max((e["updated"] for e in entries), default=atom_date("1970-01-01"))
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           f'<feed xmlns="http://www.w3.org/2005/Atom" xml:base="{escape(base)}">',
           f"  <title>{escape(title)}</title>"]
    if subtitle:
        out.append(f"  <subtitle>{escape(subtitle)}</subtitle>")
    out += [f'  <link href="{escape(base)}"/>',
            f'  <link rel="self" href="{escape(base)}feed.xml"/>',
            f"  <id>{escape(base)}</id>",
            f"  <updated>{updated}</updated>",
            '  <generator uri="https://github.com/t00m/KB4IT">KB4IT</generator>']
    for e in entries:
        out += ["  <entry>",
                f"    <title>{escape(e['title'])}</title>",
                f'    <link href="{escape(e["url"])}"/>',
                f"    <id>{escape(e['url'])}</id>",
                f"    <updated>{e['updated']}</updated>"]
        if e.get("author"):
            out.append(f"    <author><name>{escape(e['author'])}</name></author>")
        out.append(f'    <content type="html">{escape(e.get("content", ""))}</content>')
        out.append("  </entry>")
    out.append("</feed>")
    return "\n".join(out) + "\n"

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

#!/usr/bin/python
"""
Indexing service: robots tag of each page, sitemap.xml and robots.txt (repo.json seo.index, seo.noindex_keys).

# File: indexing.py
# Author: Tomás Vírseda
# License: GPL v3
"""

import os
import shutil
from datetime import datetime

from kb4it.core.publish import (ROBOTS_MARK, absolute, page_noindex, robots_block_txt, robots_txt, site_pages,
                                sitemap_xml)
from kb4it.core.util import html_id_for

# Pages no search engine should list, whatever the settings.
NOINDEX_PAGES = frozenset({"404.html", "add.html", "admin/index.html"})


def _written_by_kb4it(path) -> bool:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.readline().strip() == ROBOTS_MARK
    except OSError:
        return False


class IndexingMixin:
    """Indexing methods of Builder."""

    def is_listing_page(self, page_name) -> bool:
        """True for a page that lists documents (property, value, event, stats pages), not content.

        Themes mark these pages when they build them: distribute_md(..., listing=True).
        """
        return page_name in getattr(self, "listing_pages", ())

    def modified_date(self, doc_id) -> str:
        """dateModified of a document, as the processor resolved it (Modified, git, file time)."""
        plan = self.srvbes.get_plan()
        return (getattr(plan, "modified", None) or {}).get(doc_id, "")

    def page_robots(self, page_name) -> str:
        """Content of the robots meta tag of a page, or empty when it may be indexed."""
        seo = self.seo_settings()
        if seo.index is False:
            return "noindex, nofollow"
        if page_name in NOINDEX_PAGES:
            return "noindex"
        if seo.noindex_keys and self.is_listing_page(page_name):
            return "noindex, follow"
        return ""

    def sitemap_exclude(self) -> set:
        """Pages left out of sitemap.xml; themes may add their own."""
        return {"404.html", "search.html", "add.html"}

    def page_dates(self) -> dict:
        """'page.html' -> dateModified of each content document, the value its page head carries."""
        plan = self.srvbes.get_plan()
        return {html_id_for(doc_id): value for doc_id, value in (getattr(plan, "modified", None) or {}).items()}

    def _write_robots(self, path, content) -> None:
        """Write a generated robots.txt, unless the target holds one KB4IT did not write."""
        if os.path.exists(path) and not _written_by_kb4it(path):
            self.log.warning("[SITEMAP] ROBOTS_KEPT reason=not_written_by_kb4it")
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)

    def write_sitemap(self):
        """sitemap.xml and robots.txt, following seo.index; "sitemap": false turns them off."""
        target = self.srvbes.get_path("target")
        repo = self.srvbes.get_dict("repo") or {}
        base = getattr(self.srvbes, "site_url", None)
        seo = self.seo_settings()
        sitemap = os.path.join(target, "sitemap.xml")
        robots = os.path.join(target, "robots.txt")
        user_robots = os.path.join(self.srvbes.get_path("source"), "robots.txt")
        if seo.index is None:
            self.log.info("[SEO] INDEX_UNSET hint=set seo.index in repo.json to true or false")
        if seo.index is False:
            if os.path.exists(sitemap):
                os.unlink(sitemap)
            if os.path.isfile(user_robots):
                shutil.copyfile(user_robots, robots)
            else:
                self._write_robots(robots, robots_block_txt())
            self.log.info("[SITEMAP] SKIP reason=noindex")
            return
        if repo.get("sitemap") is False or base is None:
            if base is None and repo.get("sitemap") is not False:
                self.log.info("[SITEMAP] SKIP reason=no_site_url")
            for path in (sitemap, robots):
                if os.path.exists(path) and (path == sitemap or _written_by_kb4it(path)):
                    os.unlink(path)
            return
        dates = self.page_dates()
        entries = []
        for rel in site_pages(target, self.sitemap_exclude()):
            path = os.path.join(target, rel)
            if page_noindex(path):
                continue
            lastmod = dates.get(rel)
            if lastmod is None:
                lastmod = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")
            entries.append((absolute(base, rel), lastmod))
        with open(sitemap, "w", encoding="utf-8") as fh:
            fh.write(sitemap_xml(entries))
        if os.path.isfile(user_robots):
            shutil.copyfile(user_robots, robots)
        else:
            self._write_robots(robots, robots_txt(base))
        self.log.info(f"[SITEMAP] WRITTEN pages={len(entries)}")

#!/usr/bin/python
"""
Builder service.

# File: builder.py
# Author: Tomás Vírseda
# License: GPL v3
"""

import os
import shutil
import threading
from datetime import datetime

from mako.template import Template

from kb4it.core.env import ENV
from kb4it.core.exceptions import ThemeError
from kb4it.core.publish import ROBOTS_MARK, absolute, robots_txt, site_pages, sitemap_xml
from kb4it.core.search import (INDEX_WARN_BYTES, load_doc_sections, prune_sections,
                               render_index_js)
from kb4it.core.service import Service
from kb4it.core.util import get_human_datetime, html_id_for, valid_filename


REQUIRED_TEMPLATES = [
    "HTML_BODY",
    "PAGE_INDEX",
    "PAGE_KEY",
    "PAGE_KEY_VALUE",
]


def _template_candidates(template_name, theme_templates_dir, global_templates_dir):
    return [
        os.path.join(theme_templates_dir, f"{template_name}.tpl"),
        os.path.join(global_templates_dir, f"{template_name}.tpl"),
    ]


def _written_by_kb4it(path) -> bool:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.readline().strip() == ROBOTS_MARK
    except OSError:
        return False


class Builder(Service):
    """Build HTML blocks."""

    theme_var = {}
    _templates_lock = threading.Lock()
    _xform_lock = threading.Lock()

    _XFORM_NAMES = [
        'HTML_TAG_A', 'HTML_TAG_TOC',
        'HTML_TAG_SECT1', 'HTML_TAG_SECT2', 'HTML_TAG_SECT3', 'HTML_TAG_SECT4',
        'HTML_TAG_SECTIONBODY', 'HTML_TAG_PRE',
        'HTML_TAG_H2', 'HTML_TAG_H3', 'HTML_TAG_H4',
        'HTML_TAG_TABLE', 'HTML_TAG_TABLE_KB4IT',
        'HTML_TAG_ADMONITION_ICON_NOTE', 'HTML_TAG_ADMONITION_ICON_TIP',
        'HTML_TAG_ADMONITION_ICON_IMPORTANT', 'HTML_TAG_ADMONITION_ICON_CAUTION',
        'HTML_TAG_ADMONITION_ICON_WARNING',
        'HTML_TAG_ADMONITION_IMPORTANT', 'HTML_TAG_ADMONITION_CAUTION',
        'HTML_TAG_ADMONITION_NOTE', 'HTML_TAG_ADMONITION_TIP',
        'HTML_TAG_ADMONITION_WARNING',
        'HTML_TAG_IMG',
    ]

    def _initialize(self):
        """Initialize Builder class."""
        # Caches belong to this build. Class-level caches leaked templates from one
        # build into the next when the TUI or kb4it serve built twice in one process.
        self.templates = {}
        self._xform_pairs = None
        self.log.debug("[BUILDER] CACHE_RESET")
        self.get_services()

    def get_services(self):
        """Get services."""
        self.srvdtb = self.get_service("DB")
        self.srvbes = self.get_service("Backend")

    def apply_transformations(self, content):
        """Apply CSS transformations to the compiled page.

        Source patterns (_MD templates) match the HTML produced by the
        Markdown compile pipeline; target (_NEW) templates supply theme-
        specific replacements.
        """
        if self._xform_pairs is None:
            with self._xform_lock:
                if self._xform_pairs is None:
                    self._xform_pairs = [
                        (self.render_template(f'{n}_MD'),
                         self.render_template(f'{n}_NEW'))
                        for n in self._XFORM_NAMES
                    ]
        for old, new in self._xform_pairs:
            if old:
                content = content.replace(old, new)
        return content

    def generate_sources(self):
        """Generate sources.

        Custom themes must subclass it.
        """

    def post_activities(self):
        """Theme post activities.

        Custom themes must subclass it.
        """

    def site_signature(self) -> str:
        """Return a value that changes when every page must be rebuilt; empty turns the check off.

        Themes that render site-wide content (navigation, related pages) into every page override it.
        """
        return ""

    def post_deploy_activities(self):
        """Theme activities executed after the site has been deployed.

        Runs when the target directory already holds the final site, so it
        is the right place for anything that needs to read or package it.
        Custom themes must subclass it.
        """

    def distribute_html(self, mdId, htmlId):
        """Add compiled page to the target list."""
        shutil.copy(htmlId, self.srvbes.get_path("www"))
        self.srvbes.add_target(mdId, os.path.basename(htmlId))

    def distribute_md(self, name, content, as_html=True):
        """Distribute a theme-rendered system page to the temporary directory.

        When *as_html* is True (default), the file is tagged with a sentinel
        so the compiler treats it as ready-made HTML and skips
        python-markdown.  When *as_html* is False the content is treated as
        Markdown and goes through the normal compilation pipeline.
        """
        MD_NAME = f"{name}.md"
        PAGE_PATH = os.path.join(self.srvbes.get_path("tmp"), MD_NAME)
        with open(PAGE_PATH, "w", encoding="utf-8") as fpag:
            try:
                if as_html:
                    fpag.write("<!-- kb4it:theme-html -->\n" + content)
                else:
                    fpag.write(content)
            except Exception as error:
                self.log.error(f"[BUILDER] WRITE_FAIL doc={MD_NAME} error={error}")
        PAGE_NAME = html_id_for(MD_NAME)

        # Add compiled page to the target list
        self.srvbes.add_target(MD_NAME, PAGE_NAME)

    def template(self, template):
        """Return Mako Template object."""
        runtime = self.srvbes.get_dict("runtime")
        cached = self.templates.get(template)
        if cached is not None:
            return cached

        with self._templates_lock:
            cached = self.templates.get(template)
            if cached is not None:
                return cached

            theme = runtime["theme"]
            candidates = _template_candidates(
                template, theme["templates"], ENV["GPATH"]["TEMPLATES"]
            )
            for template_path in candidates:
                try:
                    tpl = Template(filename=template_path)
                    self.templates[template] = tpl
                    self.log.debug(f"[BUILDER] TEMPLATE_CANDIDATE_FOUND path={template_path}")
                    return tpl
                except Exception as err:
                    self.log.debug(f"[BUILDER] TEMPLATE_CANDIDATE_SKIP path={template_path} reason={err}")
                    continue

            self.log.error(f"[BUILDER] TEMPLATE_NOT_FOUND name={template}")
            raise ThemeError(f"Template not found: {template}")

    def render_template(self, name, var=None):
        """Render template according to dict var values."""
        if var is None:
            var = {}
        tpl = self.template(name)
        return tpl.render(var=var)

    def get_theme_var(self):
        """Create a new variable for rendering templates."""
        theme_var = {}
        theme_var["theme"] = self.srvbes.get_dict("theme")
        theme_var["repo"] = self.srvbes.get_dict("repo")
        theme_var["env"] = ENV
        theme_var["conf"] = self.app.get_params()
        theme_var["page"] = {}
        theme_var["page"]["title"] = ""
        theme_var["kb"] = {}
        theme_var["kb"]["keys"] = self.srvdtb.get_keys()
        theme_var["count_docs"] = self.srvdtb.get_documents_count()
        theme_var["repo"]["updated"] = get_human_datetime(datetime.now())

        # Only pass to theme those keys used by documents
        kbdict = self.srvbes.get_kb_dict()
        metadata = kbdict["metadata"]
        ignored_keys = set(self.srvdtb.get_ignored_keys())
        blocked_keys = set(self.srvdtb.get_blocked_keys())
        used_keys = set(metadata.keys())
        theme_var["kb"]["keys"]["menu"] = sorted(
            [{"name": k, "href": valid_filename(k)} for k in (used_keys - blocked_keys - ignored_keys)],
            key=lambda d: d["name"],
        )

        theme_var["search_box"] = self.search_box()
        return theme_var

    def search_enabled(self) -> bool:
        """Full-text search is on when the theme supports it ("search": true in theme.json)
        and repo.json does not turn it off with "search": false."""
        theme = self.srvbes.get_dict("theme") or {}
        repo = self.srvbes.get_dict("repo") or {}
        return theme.get("search") is True and repo.get("search", True) is not False

    def search_box(self) -> str:
        """Search box markup for the theme's header, or '' when search is off."""
        return self.render_template("HTML_SEARCH_BOX") if self.search_enabled() else ""

    def create_page_search(self):
        """Search page (search.html), built only when search is on."""
        if not self.search_enabled():
            return
        self.distribute_md("search", self.render_template("PAGE_SEARCH", self.get_theme_var()))
        self.srvdtb.add_document("search.md")
        self.srvdtb.add_document_key("search.md", "Title", "Search")
        self.srvdtb.add_document_key("search.md", "SystemPage", "Yes")

    def search_record(self, doc_id) -> dict:
        """Index record of one document; themes may override to add facets or a summary."""
        values = lambda key: [v for v in (self.srvdtb.get_values(doc_id, key) or []) if v]
        title = (values("Title") or [doc_id])[0]
        summary = (values("Summary") or [""])[0]
        facets = {key: values(key) for key in ("Category", "Tag") if values(key)}
        return {"u": html_id_for(doc_id), "t": title, "s": summary, "k": "", "c": "", "f": facets,
                "w": [], "g": [], "x": []}

    def write_search_index(self):
        """Write target/search-index.js from the sections the compiler recorded; remove it when search is off."""
        target = self.srvbes.get_path("target")
        root = self.srvbes.get_path("root")
        index_path = os.path.join(target, "search-index.js")
        if (self.srvbes.get_dict("theme") or {}).get("search") is not True:
            return  # the theme has no shared search (apphelp writes its own index)
        if not self.search_enabled():
            for name in ("search-index.js", "search.html"):
                path = os.path.join(target, name)
                if os.path.exists(path):
                    os.unlink(path)
            return
        known = set(self.srvdtb.get_documents())
        sources = self.srvbes.get_value("docs", "filenames") or []
        docs = [d for d in sources if d in known and not self.srvdtb.is_system(d)]
        records = []
        for doc_id in sorted(docs):
            record = self.search_record(doc_id)
            record["x"] = [[s["id"], s["heading"], s["text"]] for s in load_doc_sections(root, doc_id)]
            records.append(record)
        prune_sections(root, docs)
        content = render_index_js(records, "KB4IT_INDEX")
        with open(index_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        size = len(content.encode("utf-8"))
        if size > INDEX_WARN_BYTES:
            self.log.warning(f"[SEARCH] INDEX_LARGE size={size}")
        self.log.info(f"[SEARCH] INDEX_BUILT pages={len(records)} size={size}")

    def sitemap_exclude(self) -> set:
        """Pages left out of sitemap.xml; themes may add their own."""
        return {"404.html", "search.html"}

    def page_dates(self) -> dict:
        """'page.html' -> 'YYYY-MM-DD' for documents with a Date."""
        dates = {}
        for doc_id in self.srvdtb.get_documents():
            values = self.srvdtb.get_values(doc_id, "Date") or []
            if values and values[0]:
                dates[html_id_for(doc_id)] = str(values[0])[:10]
        return dates

    def write_sitemap(self):
        """sitemap.xml and robots.txt for sites with a site_url; "sitemap": false turns them off."""
        target = self.srvbes.get_path("target")
        repo = self.srvbes.get_dict("repo") or {}
        base = getattr(self.srvbes, "site_url", None)
        sitemap = os.path.join(target, "sitemap.xml")
        robots = os.path.join(target, "robots.txt")
        user_robots = os.path.join(self.srvbes.get_path("source"), "robots.txt")
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
            lastmod = dates.get(rel)
            if lastmod is None:
                lastmod = datetime.fromtimestamp(os.path.getmtime(os.path.join(target, rel))).strftime("%Y-%m-%d")
            entries.append((absolute(base, rel), lastmod))
        with open(sitemap, "w", encoding="utf-8") as fh:
            fh.write(sitemap_xml(entries))
        if os.path.isfile(user_robots):
            shutil.copyfile(user_robots, robots)
        else:
            with open(robots, "w", encoding="utf-8") as fh:
                fh.write(robots_txt(base))
        self.log.info(f"[SITEMAP] WRITTEN pages={len(entries)}")

    def page_hook_pre(self, var):
        """Insert html code before the content.

        This method can be overwriten by custom themes.
        """
        return var

    def page_hook_post(self, var):
        """Insert html code after the content.

        This method can be overwriten by custom themes.
        """
        return var

    def build_page_key(self, key, values):
        """Create page for a key."""

    def build_page(self, path_md):
        """Build the final HTML Page for a document.

        At this point, the Markdown document has been compiled successfully,
        and therefore the html page can be built. The Builder receives the
        source document filepath; another file with extension .html should
        also exist. The html page is built by inserting the html header at
        the beginning, appending the footer at the end, and applying the
        necessary transformations.

        Finally, the html page produced by the compiler is overwritten.
        This method must be overwritten by custom themes.
        """

    def build_page_key_value(self, kvpath):
        """
        Build the final HTML Page for a document key-value.

        This method must be overwriten by custom themes.
        """

    def create_page_about_kb4it(self):
        """About KB4IT page."""
        TPL_PAGE_ABOUT_KB4IT = self.template("PAGE_ABOUT_KB4IT")
        var = self.get_theme_var()
        self.distribute_md(
            "about_kb4it", TPL_PAGE_ABOUT_KB4IT.render(var=var),
            as_html=False)
        self.srvdtb.add_document("about_kb4it.md")
        self.srvdtb.add_document_key(
            "about_kb4it.md", "Title", "About KB4IT")
        self.srvdtb.add_document_key("about_kb4it.md", "SystemPage", "Yes")

    def create_page_about_app(self):
        """About this app page, generated only when the user repo has no about_app.md."""
        filenames = self.srvbes.get_value("docs", "filenames") or []
        if "about_app.md" in filenames:
            self.log.debug("[BUILDER] ABOUT_APP_SKIP reason=user_generated")
            return
        TPL_PAGE_ABOUT_APP = self.template("PAGE_ABOUT_APP")
        var = self.get_theme_var()
        self.distribute_md("about_app", TPL_PAGE_ABOUT_APP.render(var=var), as_html=False)
        self.srvdtb.add_document("about_app.md")
        self.srvdtb.add_document_key("about_app.md", "Title", "About this app")
        self.srvdtb.add_document_key("about_app.md", "SystemPage", "Yes")

    def create_page_help(self):
        """Help page,  generated only when the user repo has no help.md."""
        filenames = self.srvbes.get_value("docs", "filenames")
        if "help.md" in filenames:
            self.log.info("[BUILDER] HELP_SKIP reason=user_generated")
            return
        TPL_PAGE_HELP = self.template("PAGE_HELP")
        var = self.get_theme_var()
        self.distribute_md("help", TPL_PAGE_HELP.render(var=var), as_html=False)
        self.srvdtb.add_document("help.md")
        self.srvdtb.add_document_key("help.md", "Title", "Help")
        self.srvdtb.add_document_key("help.md", "SystemPage", "Yes")

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
from kb4it.core.publish import (ROBOTS_MARK, absolute, atom_date, atom_feed, robots_txt, site_pages,
                                sitemap_xml)
from kb4it.core.search import (INDEX_WARN_BYTES, load_doc_html, load_doc_sections, prune_sections,
                               render_index_js)
from kb4it.core.service import Service
from kb4it.core.util import get_human_datetime, html_id_for, valid_filename


REQUIRED_TEMPLATES = [
    "HTML_BODY",
    "PAGE_INDEX",
    "PAGE_KEY",
    "PAGE_KEY_VALUE",
]


def _template_candidates(template_name, theme_templates_dir, global_templates_dir, override_dir=None):
    """Files that may hold a template, first match wins: repository overrides, theme, common."""
    candidates = [
        os.path.join(theme_templates_dir, f"{template_name}.tpl"),
        os.path.join(global_templates_dir, f"{template_name}.tpl"),
    ]
    if override_dir:
        candidates.insert(0, os.path.join(override_dir, "templates", f"{template_name}.tpl"))
    return candidates


GIT_KEYS = ("git_server", "git_user", "git_repo", "git_branch")


def git_ready(repo) -> bool:
    """True when repo.json turns git links on and names server, user, repository and branch.

    git_path may stay empty (documents at the repository root). A "{placeholder}" counts as unset,
    so a sample configuration never produces edit links that lead nowhere.
    """
    if repo.get("git") is not True:
        return False
    values = [repo.get(key) for key in GIT_KEYS] + [repo.get("git_path") or ""]
    return all(isinstance(v, str) for v in values) and all(v.strip() for v in values[:4]) and \
        not any("{" in v for v in values)


META_START = "<!-- kb4it:meta -->"
META_END = "<!-- /kb4it:meta -->"


def short_text(text, limit) -> str:
    """text cut to limit characters at a word boundary, with an ellipsis when cut."""
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit - 1].rsplit(" ", 1)[0]
    return cut.rstrip(",;:.") + "\u2026"


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

    # Source patterns (common HTML_TAG_<name>_MD templates) that python-markdown's output, after
    # the compiler's section restructuring, can contain; tests/core/test_transformations.py checks it.
    _XFORM_NAMES = [
        'HTML_TAG_TOC',
        'HTML_TAG_SECT1', 'HTML_TAG_SECT2', 'HTML_TAG_SECT3', 'HTML_TAG_SECT4',
        'HTML_TAG_SECTIONBODY',
        'HTML_TAG_H2', 'HTML_TAG_H3', 'HTML_TAG_H4',
        'HTML_TAG_IMG',
    ]

    def _initialize(self):
        """Initialize Builder class."""
        # Caches belong to this build. Class-level caches leaked templates from one
        # build into the next when the TUI or kb4it serve built twice in one process.
        self.templates = {}
        self._template_errors = {}
        self._autoescape_warned = False
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
            override_dir = getattr(self.srvbes, "overrides_dir", None)
            candidates = _template_candidates(
                template, theme["templates"], ENV["GPATH"]["TEMPLATES"], override_dir
            )
            autoescape = self._theme_autoescape(theme)
            for template_path in candidates:
                if not os.path.isfile(template_path):
                    self.log.debug(f"[BUILDER] TEMPLATE_CANDIDATE_SKIP path={template_path} reason=missing")
                    continue
                # A template that exists but does not compile is an error, never a reason to fall back.
                failed = self._template_errors.get(template)
                if failed is not None:
                    raise failed
                # Every ${...} is HTML-escaped unless marked "| n": always in KB4IT's common
                # templates, and in a theme's own templates (and their overrides) when it opts in.
                common = os.path.dirname(os.path.abspath(template_path)) == os.path.abspath(ENV["GPATH"]["TEMPLATES"])
                filters = ["h"] if autoescape or common else ["str"]
                try:
                    tpl = Template(filename=template_path, default_filters=filters)
                except Exception as err:
                    reason = " ".join(str(err).split())  # Mako puts the line number on a line of its own
                    self.log.error(f"[BUILDER] TEMPLATE_COMPILE_FAIL name={template} path={template_path} error={reason}")
                    failed = ThemeError(f"Template {template} at {template_path}: {reason}")
                    self._template_errors[template] = failed
                    raise failed from err
                self.templates[template] = tpl
                self.log.debug(f"[BUILDER] TEMPLATE_CANDIDATE_FOUND path={template_path}")
                if override_dir and template_path == candidates[0]:
                    self.log.info(f"[BUILDER] TEMPLATE_OVERRIDE name={template} path={template_path}")
                return tpl

            self.log.error(f"[BUILDER] TEMPLATE_NOT_FOUND name={template}")
            raise ThemeError(f"Template not found: {template}")

    def _theme_autoescape(self, theme) -> bool:
        """True when theme.json has "autoescape": true; otherwise a custom theme is warned once per build."""
        if theme.get("autoescape") is True:
            return True
        bundled = os.path.abspath(ENV["GPATH"]["THEMES"])
        custom = os.path.dirname(os.path.abspath(str(theme.get("path", "")))) != bundled
        if custom and not self._autoescape_warned:
            self._autoescape_warned = True
            self.log.warning(f"[BUILDER] THEME_AUTOESCAPE_OFF theme={theme.get('id')}")
            self.log.warning('[BUILDER] HINT add "autoescape": true to theme.json and mark HTML values with | n')
        return False

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
        theme_var["git_ok"] = git_ready(theme_var["repo"])

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

    def target_subdir(self):
        """Folder inside target to build into, or None. apphelp uses it for versioned help."""
        return None

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

    def feed_settings(self):
        """Feed settings, or None when the theme has no feed. theme.json "feed": true turns it on by default."""
        theme = self.srvbes.get_dict("theme") or {}
        if "feed" not in theme:
            return None
        repo = self.srvbes.get_dict("repo") or {}
        conf = repo.get("feed") if isinstance(repo.get("feed"), dict) else {}
        return {"enabled": conf.get("enabled", theme["feed"] is True), "limit": int(conf.get("limit", 20)),
                "categories": conf.get("categories"), "full_content": conf.get("full_content", True)}

    def feed_enabled(self) -> bool:
        settings = self.feed_settings()
        return bool(settings and settings["enabled"] and getattr(self.srvbes, "site_url", None))

    def write_feed(self):
        """feed.xml (Atom) with the newest dated documents."""
        target = self.srvbes.get_path("target")
        path = os.path.join(target, "feed.xml")
        settings = self.feed_settings()
        if not settings or not settings["enabled"]:
            if os.path.exists(path):
                os.unlink(path)
            return
        base = getattr(self.srvbes, "site_url", None)
        if base is None:
            self.log.info("[FEED] SKIP reason=no_site_url")
            return
        root = self.srvbes.get_path("root")
        wanted = set(settings["categories"] or [])
        sources = self.srvbes.get_value("docs", "filenames") or []
        known = set(self.srvdtb.get_documents())
        dated = []
        for doc_id in sources:
            if doc_id not in known or self.srvdtb.is_system(doc_id):
                continue
            date = (self.srvdtb.get_values(doc_id, "Date") or [None])[0]
            categories = set(self.srvdtb.get_values(doc_id, "Category") or [])
            if not date or (wanted and not categories & wanted):
                continue
            dated.append((str(date), doc_id))
        entries = []
        for date, doc_id in sorted(dated, reverse=True)[:settings["limit"]]:
            if settings["full_content"]:
                content = load_doc_html(root, doc_id)
            else:
                sections = load_doc_sections(root, doc_id)
                summary = (self.srvdtb.get_values(doc_id, "Summary") or [""])[0]
                content = summary or (sections[0]["text"][:300] if sections else "")
            entries.append({"title": (self.srvdtb.get_values(doc_id, "Title") or [doc_id])[0],
                            "url": absolute(base, html_id_for(doc_id)), "updated": atom_date(date),
                            "author": ", ".join(self.srvdtb.get_values(doc_id, "Author") or []),
                            "content": content})
        repo = self.srvbes.get_dict("repo") or {}
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(atom_feed(repo.get("title", ""), base, entries, repo.get("tagline", "")))
        self.log.info(f"[FEED] WRITTEN entries={len(entries)}")

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
            text = (values("Summary") or [sections[0]["text"] if sections else ""])[0]
            title = (values("Title") or [doc_id])[0]
        else:
            text, title = repo.get("tagline", ""), repo.get("title", "")
        head = html[:html.lower().find("</head>")].lower()
        image = repo.get("og_image")
        return {
            "title": title, "site_name": repo.get("title", ""), "type": "article" if doc_id else "website",
            "description": short_text(text, 160), "author": ", ".join(values("Author")),
            "url": absolute(base, page_name) if base else "",
            "image": absolute(base, image) if base and image else "",
            "feed": "feed.xml" if self.feed_enabled() else "",
            "has_description": '<meta name="description"' in head, "has_author": '<meta name="author"' in head,
        }

    def inject_head_meta(self, html, page_name) -> str:
        """Insert (or replace) the HTML_HEAD_META block before </head>."""
        start, end = html.find(META_START), html.find(META_END)
        if start >= 0 and end > start:
            html = html[:start] + html[end + len(META_END):]
        close = html.lower().find("</head>")
        if close < 0:
            return html
        block = self.render_template("HTML_HEAD_META", {"meta": self.page_meta(page_name, html)}).strip()
        return html[:close] + block + "\n" + html[close:]

    def backlinks(self, doc_id) -> list:
        """[{title, href}] of the documents that link to doc_id; [] when "backlinks" is false."""
        repo = self.srvbes.get_dict("repo") or {}
        if repo.get("backlinks", True) is False:
            return []
        plan = self.srvbes.get_plan()
        found = (getattr(plan, "backlinks", None) or {}).get(doc_id, []) if plan is not None else []
        return [{"title": title, "href": html_id_for(source)} for title, source in found]

    def backlinks_html(self, doc_id) -> str:
        items = self.backlinks(doc_id)
        return self.render_template("HTML_BACKLINKS", {"backlinks": items}) if items else ""

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

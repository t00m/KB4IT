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
from kb4it.core.service import Service
from kb4it.core.util import get_human_datetime, html_id_for, valid_filename


class Builder(Service):
    """Build HTML blocks."""

    theme_var = {}
    templates = {}
    _templates_lock = threading.Lock()
    _xform_lock = threading.Lock()
    _xform_pairs = None

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
        if Builder._xform_pairs is None:
            with self._xform_lock:
                if Builder._xform_pairs is None:
                    Builder._xform_pairs = [
                        (self.render_template(f'{n}_MD'),
                         self.render_template(f'{n}_NEW'))
                        for n in self._XFORM_NAMES
                    ]
        for old, new in Builder._xform_pairs:
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
            candidates = [
                os.path.join(theme["templates"], "md", f"{template}.tpl"),
                os.path.join(theme["templates"], f"{template}.tpl"),
                os.path.join(ENV["GPATH"]["TEMPLATES"], "md", f"{template}.tpl"),
                os.path.join(ENV["GPATH"]["TEMPLATES"], f"{template}.tpl"),
            ]
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
            self.app.stop(error=True)
            raise RuntimeError(f"Template not found: {template}")

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

        return theme_var

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

    def create_page_help(self):
        """Help page — generated only when the user repo has no help.md."""
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

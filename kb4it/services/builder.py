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
from kb4it.core.util import get_human_datetime


class Builder(Service):
    """Build HTML blocks."""

    theme_var = {}
    templates = {}
    _templates_lock = threading.Lock()

    def _initialize(self):
        """Initialize Builder class."""
        self.get_services()

    def get_services(self):
        """Get services."""
        self.srvdtb = self.get_service("DB")
        self.srvbes = self.get_service("Backend")

    def generate_sources(self):
        """Generate sources.

        Custom themes must subclass it.
        """

    def post_activities(self):
        """Theme post activities.

        Custom themes must subclass it.
        """

    def distribute_html(self, adocId, htmlId):
        """Add compiled page to the target list."""
        shutil.copy(htmlId, self.srvbes.get_path("www"))
        self.srvbes.add_target(adocId, os.path.basename(htmlId))

    def distribute_adoc(self, name, content):
        """
        Distribute source file to temporary directory.

        Use this method when the source asciidoctor file doesn't have to
        be analyzed.
        """
        ADOC_NAME = f"{name}.adoc"
        # ~ self.log.debug(f"DOC[{ADOC_NAME}] received")
        PAGE_PATH = os.path.join(self.srvbes.get_path("tmp"), ADOC_NAME)
        with open(PAGE_PATH, "w", encoding="utf-8") as fpag:
            try:
                fpag.write(content)
            except Exception as error:
                self.log.error(f"[BUILDER] WRITE_FAIL doc={ADOC_NAME} error={error}")
        PAGE_NAME = ADOC_NAME.replace(".adoc", ".html")

        # Add compiled page to the target list
        self.srvbes.add_target(ADOC_NAME, PAGE_NAME)

    def template(self, template):
        """Return Mako Template object."""
        cached = self.templates.get(template)
        if cached is not None:
            return cached

        with self._templates_lock:
            cached = self.templates.get(template)
            if cached is not None:
                return cached

            runtime = self.srvbes.get_dict("runtime")
            theme = runtime["theme"]
            candidates = [
                os.path.join(theme["templates"], f"{template}.tpl"),
                os.path.join(ENV["GPATH"]["TEMPLATES"], f"{template}.tpl"),
            ]
            for template_path in candidates:
                try:
                    tpl = Template(filename=template_path)
                    self.templates[template] = tpl
                    return tpl
                except Exception:
                    continue

            self.log.error(f"[BUILDER] TEMPLATE_NOT_FOUND name={template}")
            self.app.stop(error=True)
            raise RuntimeError(f"Template not found: {template}")

    def render_template(self, name, var={}):
        """Render template according to dict var values."""
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
            list(used_keys - blocked_keys - ignored_keys)
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

    def build_page(self, path_adoc):
        """
        Build the final HTML Page for a document.

        At this point, the compilation for the asciidoc document has
        finished successfully, and therefore the html page can be built.
        The Builder receives the asciidoc document filepath. It means,
        that another file with extension .html should also exist.
        The html page is built by inserting the html header at the
        beguinning, appending the footer at the end, and applying the
        necessary transformations.

        Finally, the html page created by asciidoctor is overwritten.
        This method must be overwriten by custom themes.
        """

    def build_page_key_value(self, kvpath):
        """
        Build the final HTML Page for a document key-value.

        This method must be overwriten by custom themes.
        """

    def create_page_help(self):
        """KB4IT help page."""
        TPL_PAGE_HELP = self.template("PAGE_HELP")
        var = self.get_theme_var()
        self.distribute_adoc("help", TPL_PAGE_HELP.render(var=var))
        self.srvdtb.add_document("help.adoc")
        self.srvdtb.add_document_key("help.adoc", "Title", "KB4IT Help")
        self.srvdtb.add_document_key("help.adoc", "SystemPage", "Yes")

    def create_page_about_kb4it(self):
        """About KB4IT page."""
        TPL_PAGE_ABOUT_KB4IT = self.template("PAGE_ABOUT_KB4IT")
        var = self.get_theme_var()
        self.distribute_adoc(
            "about_kb4it", TPL_PAGE_ABOUT_KB4IT.render(var=var))
        self.srvdtb.add_document("about_kb4it.adoc")
        self.srvdtb.add_document_key(
            "about_kb4it.adoc", "Title", "About KB4IT")
        self.srvdtb.add_document_key("about_kb4it.adoc", "SystemPage", "Yes")

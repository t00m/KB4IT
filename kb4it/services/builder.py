#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Builder service.
# File: srv_builder.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: Create KB4IT pages
"""

import os
import shutil
from datetime import datetime

from mako.template import Template

from kb4it.core.env import ENV
from kb4it.core.service import Service
from kb4it.core.util import timeit
from kb4it.core.util import get_human_datetime


class Builder(Service):
    """Build HTML blocks"""
    theme_var = {}
    templates = {}

    def initialize(self):
        """Initialize Builder class."""
        self.get_services()

    def finalize(self):
        """Clean up."""
        pass

    def get_services(self):
        """Get services."""
        self.srvdtb = self.get_service('DB')
        self.srvbes = self.get_service('Backend')

    def generate_sources(self):
        """Custom themes can use this method to generate source documents"""
        pass

    def post_activities(self):
        pass

    def distribute_html(self, pagename):
        shutil.copy(pagename, self.srvbes.get_www_path())
        # Add compiled page to the target list
        self.srvbes.add_target(os.path.basename(pagename))
        self.log.debug("[BUILDER/DISTRIBUTE] - Page[%s] copied to temporary target directory", os.path.basename(pagename))

    @timeit
    def distribute_adoc(self, name, content):
        """
        Distribute source file to temporary directory.
        Use this method when the source asciidoctor file doesn't have to
        be analyzed.
        """
        ADOC_NAME = "%s.adoc" % name
        self.log.debug(f"[BUILDER/DISTRIBUTE] - Received Doc[{ADOC_NAME}]")
        PAGE_PATH = os.path.join(self.srvbes.get_temp_path(), ADOC_NAME)
        with open(PAGE_PATH, 'w') as fpag:
            try:
                fpag.write(content)
            except Exception as error:
                self.log.error(f"[BUILDER/DISTRIBUTE] - {error}")
        PAGE_NAME = ADOC_NAME.replace('.adoc', '.html')

        # Add compiled page to the target list
        self.srvbes.add_target(PAGE_NAME)
        self.log.debug("[BUILDER/DISTRIBUTE] - Page[%s] distributed to temporary path", PAGE_NAME)

    def template(self, template):
        """Return the template content from chosen theme"""
        runtime = self.srvbes.get_runtime_dict()
        theme = runtime['theme']
        current_theme = theme['id']

        # Try to get the template from cache
        try:
            return self.templates[template]
            # ~ self.log.debug("[BUILDER/TEMPLATES] - Template[%s] loaded from cache", template)

        except KeyError:
            templates = []
            templates.append(os.path.join(theme['templates'], "%s.tpl" % template))  # From theme
            templates.append(os.path.join(ENV['GPATH']['TEMPLATES'], "%s.tpl" % template))  # From common templates dir
            TEMPLATE_FOUND = False
            for template_path in templates:
                try:
                    self.templates[template] = Template(filename=template_path)
                    TEMPLATE_FOUND = True
                    self.log.debug("[BUILDER/TEMPLATES] - Template[%s] found and added to the cache", template)
                    break
                except:
                    self.templates[template] = Template("")
                    TEMPLATE_FOUND = False

        if not TEMPLATE_FOUND:
            self.log.error("[BUILDER/TEMPLATES] - Template[%s] not found", template)

        return self.templates[template]

    def render_template(self, name, var={}):
        tpl = self.template(name)
        return tpl.render(var=var)

    def get_theme_var(self):
        # FIXME: concurrent.futures MemoryError
        # https://stackoverflow.com/questions/37445540/memory-usage-with-concurrent-futures-threadpoolexecutor-in-python3
        """Create a new variable for rendering templates."""
        repo = self.srvbes.get_repo_parameters()
        theme_var = {}
        theme_var['theme'] = self.srvbes.get_theme_properties()
        theme_var['repo'] = self.srvbes.get_repo_parameters()
        theme_var['env'] = ENV
        theme_var['conf'] = self.app.get_params()
        theme_var['page'] = {}
        theme_var['page']['title'] = ''
        theme_var['kb'] = {}
        theme_var['kb']['keys'] = self.srvdtb.get_keys()
        theme_var['count_docs'] = self.srvdtb.get_documents_count()
        theme_var['repo']['updated'] = get_human_datetime(datetime.now())

        # Only pass to theme those keys used by documents
        kbdict = self.srvbes.get_kb_dict()
        metadata = kbdict['metadata']
        ignored_keys = set(self.srvdtb.get_ignored_keys())
        blocked_keys = set(self.srvdtb.get_blocked_keys())
        used_keys = set(metadata.keys())
        theme_var['kb']['keys']['menu'] = sorted(list(used_keys - blocked_keys - ignored_keys))
        # ~ self.log.info(f"Keys: {theme_var['kb']['keys']}")

        return theme_var

    def page_hook_pre(self, var):
        """ Insert html code before the content.
        This method can be overwriten by custom themes.
        """
        return var

    def page_hook_post(self, var):
        """ Insert html code after the content.
        This method can be overwriten by custom themes.
        """
        return var

    def build_page_key(self, key, values):
        """Create page for a key."""
        pass

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
        # ~ html = ''
        # ~ return html

    def build_page_key_value(self, kvpath):
        """
        Build the final HTML Page for a document key-value.
        This method must be overwriten by custom themes.
        """
        pass

    def create_page_help(self):
        """KB4IT help page."""
        TPL_PAGE_HELP = self.template('PAGE_HELP')
        var = self.get_theme_var()
        self.distribute_adoc('help', TPL_PAGE_HELP.render(var=var))
        self.srvdtb.add_document('help.adoc')
        self.srvdtb.add_document_key('help.adoc', 'Title', 'KB4IT Help')
        self.srvdtb.add_document_key('help.adoc', 'SystemPage', 'Yes')

    def create_page_about_kb4it(self):
        """About KB4IT page."""
        TPL_PAGE_ABOUT_KB4IT = self.template('PAGE_ABOUT_KB4IT')
        var = self.get_theme_var()
        self.distribute_adoc('about_kb4it', TPL_PAGE_ABOUT_KB4IT.render(var=var))
        self.srvdtb.add_document('about_kb4it.adoc')
        self.srvdtb.add_document_key('about_kb4it.adoc', 'Title', 'About KB4IT')
        self.srvdtb.add_document_key('about_kb4it.adoc', 'SystemPage', 'Yes')

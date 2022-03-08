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
import sys
import shutil
from datetime import datetime
try:
    import html5lib
    import webencodings
    from bs4 import BeautifulSoup as bs
    TIDY = True
except:
    TIDY = False
from kb4it.core.env import ENV  # APP, GPATH
from kb4it.core.service import Service
from mako.template import Template


class Builder(Service):
    """Build HTML blocks"""
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

    def distribute_html(self, pagename):
        shutil.copy(pagename, self.srvbes.get_www_path())
        # Add compiled page to the target list
        self.srvbes.add_target(os.path.basename(pagename))
        self.log.debug("[DISTRIBUTE] - Page[%s] copied to temporary target directory", os.path.basename(pagename))

    def distribute_adoc(self, name, content):
        """
        Distribute source file to temporary directory.
        Use this method when the source asciidoctor file doesn't have to
        be analyzed.
        """
        ADOC_NAME = "%s.adoc" % name
        self.log.debug("[DISTRIBUTE] - Received Doc[%s]", ADOC_NAME)
        PAGE_PATH = os.path.join(self.srvbes.get_temp_path(), ADOC_NAME)
        with open(PAGE_PATH, 'w') as fpag:
            try:
                fpag.write(content)
            except Exception as error:
                self.log.error("[DISTRIBUTE] - %s", error)
        PAGE_NAME = ADOC_NAME.replace('.adoc', '.html')

        # Add compiled page to the target list
        self.srvbes.add_target(PAGE_NAME)
        # ~ self.log.debug("[DISTRIBUTE] - Page[%s] distributed to temporary path", PAGE_NAME)

    def template(self, template):
        """Return the template content from chosen theme"""
        properties = self.srvbes.get_runtime()
        theme = properties['theme']
        current_theme = theme['id']

        # Try to get the template from cache
        try:
            tpl = self.templates[template]
            # ~ self.log.debug("[TEMPLATES] - Template[%s] loaded from cache", template)
            return tpl
        except KeyError:
            try:
                # Get template from theme
                template_path = os.path.join(theme['templates'], "%s.tpl" % template)
                self.templates[template] = Template(filename=template_path)
                # ~ self.log.debug("[TEMPLATES] - Template[%s] loaded for Theme[%s] and added to the cache", template, theme['id'])
            except FileNotFoundError as error:
                try:
                    # Try with global templates
                    template_path = os.path.join(ENV['GPATH']['TEMPLATES'], "%s.tpl" % template)
                    self.templates[template] = Template(filename=template_path)
                    # ~ self.log.debug("[TEMPLATES] - Global Template[%s] loaded and added to the cache", template)
                except FileNotFoundError as error:
                    self.templates[template] = Template("")
                    self.log.error("[TEMPLATES] - Template[%s] not found. Returning empty template!", template)

            return self.templates[template]

    def render_template(self, name, var={}):
        tpl = self.template(name)
        return tpl.render(var=var)

    def get_theme_var(self):
        """Create a new variable for rendering templates."""
        var = {}
        var['theme'] = self.srvbes.get_theme_properties()
        var['kbdict'] = self.srvbes.get_kb_dict()
        var['repo'] = self.srvbes.get_repo_parameters()
        var['conf'] = self.app.get_app_conf()
        var['page'] = {}
        var['page']['title'] = ''
        return var

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

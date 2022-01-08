#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: default theme script
"""

from kb4it.services.builder import Builder
from kb4it.core.util import valid_filename

class Theme(Builder):
    def generate_sources(self):
        pass

    def apply_transformations(self, content, var):
        """Apply CSS transformation to the compiled page."""
        tpl = self.render_template
        content = content.replace(tpl('HTML_TAG_A_ADOC'), tpl('HTML_TAG_A_NEW'))
        content = content.replace(tpl('HTML_TAG_TOC_ADOC'), tpl('HTML_TAG_TOC_NEW'))
        content = content.replace(tpl('HTML_TAG_SECT1_ADOC'), tpl('HTML_TAG_SECT1_NEW'))
        content = content.replace(tpl('HTML_TAG_SECT2_ADOC'), tpl('HTML_TAG_SECT2_NEW'))
        content = content.replace(tpl('HTML_TAG_SECT3_ADOC'), tpl('HTML_TAG_SECT3_NEW'))
        content = content.replace(tpl('HTML_TAG_SECT4_ADOC'), tpl('HTML_TAG_SECT4_NEW'))
        content = content.replace(tpl('HTML_TAG_SECTIONBODY_ADOC'), tpl('HTML_TAG_SECTIONBODY_NEW'))
        content = content.replace(tpl('HTML_TAG_PRE_ADOC'), tpl('HTML_TAG_PRE_NEW'))
        content = content.replace(tpl('HTML_TAG_H2_ADOC'), tpl('HTML_TAG_H2_NEW'))
        content = content.replace(tpl('HTML_TAG_H3_ADOC'), tpl('HTML_TAG_H3_NEW'))
        content = content.replace(tpl('HTML_TAG_H4_ADOC'), tpl('HTML_TAG_H4_NEW'))
        content = content.replace(tpl('HTML_TAG_TABLE_ADOC'), tpl('HTML_TAG_TABLE_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ICON_NOTE_ADOC'), tpl('HTML_TAG_ADMONITION_ICON_NOTE_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ICON_TIP_ADOC'), tpl('HTML_TAG_ADMONITION_ICON_TIP_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ICON_IMPORTANT_ADOC'), tpl('HTML_TAG_ADMONITION_ICON_IMPORTANT_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ICON_CAUTION_ADOC'), tpl('HTML_TAG_ADMONITION_ICON_CAUTION_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ICON_WARNING_ADOC'), tpl('HTML_TAG_ADMONITION_ICON_WARNING_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ADOC'), tpl('HTML_TAG_ADMONITION_NEW'))
        content = content.replace(tpl('HTML_TAG_IMG_ADOC'), tpl('HTML_TAG_IMG_NEW'))
        return content, var

    def transform(self, content, var):
        # ~ content, var = self.highlight_metadata_section(content, var)
        content, var = self.apply_transformations(content, var)
        return content, var

    def build(self):
        """Create standard pages for default theme"""
        self.log.debug("This is the Bootstrap theme")
        # ~ self.create_page_properties()
        # ~ self.create_page_stats()
        # ~ self.create_page_index_all()
        # ~ self.create_page_index()
        # ~ self.create_page_about_app()
        # ~ self.create_page_about_theme()
        # ~ self.create_page_about_kb4it()
        # ~ self.create_page_help()



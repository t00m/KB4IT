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
        # ~ runtime = self.srvbes.get_runtime()
        # ~ print(runtime)
        # ~ K_PATH = runtime['K_PATH']
        # ~ for kpath in K_PATH:
            # ~ key, values, COMPILE_KEY = kpath
            # ~ self.log.debug("[PAGE] - Key[%s] Values[%s] Compile[%s]", key, values, COMPILE_KEY)
            # ~ docname = "%s.adoc" % valid_filename(key)
            # ~ if COMPILE_KEY:
                # ~ fpath = os.path.join(runtime['dir']['tmp'], docname)
                # ~ html = self.srvthm.create_page_key(key, values)
                # ~ with open(fpath, 'w') as fkey:
                    # ~ fkey.write(html)
            # ~ self.srvbes.add_target(docname.replace('.adoc', '.html'))

    def highlight_metadata_section(self, content, var):
        """Apply CSS transformation to metadata section."""
        HTML_TAG_METADATA_ADOC = self.template('HTML_TAG_METADATA_ADOC').render(var=var)
        HTML_TAG_METADATA_NEW = self.template('HTML_TAG_METADATA_NEW').render(var=var)
        content = content.replace(HTML_TAG_METADATA_ADOC, HTML_TAG_METADATA_NEW, 1)
        self.log.debug("[TRANSFORM] - Page[%s]: Highlight metadata", var['basename_html'])
        return content, var

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

    def create_page_key(self, key, values):
        """Create key page."""
        TPL_PAGE_KEY = self.template('PAGE_KEY_KB4IT')
        var = {}

        # Title
        var['title'] = key

        # Tab Cloud
        # ~ cloud = self.create_tagcloud_from_key(key)

        # Tab Leader
        # ~ stats = ""
        # ~ var['leader'] = []
        # ~ for value in values:
            # ~ item = {}
            # ~ docs = self.srvdtb.get_docs_by_key_value(key, value)
            # ~ item['count'] = len(docs)
            # ~ item['vfkey'] = valid_filename(key)
            # ~ item['vfvalue'] = valid_filename(value)
            # ~ item['name'] = value
            # ~ var['leader'].append(item)
        # ~ var['cloud'] = cloud
        html = TPL_PAGE_KEY.render(var=var)
        # ~ self.log.debug("HTML PageKey[%s]:\n%s", key, html)
        return html

    def create_page_index(self, var):
        """Create key page."""
        var['title'] = 'Index'
        var['menu_contents'] = ''
        var['basename'] = ''
        var['meta_section'] = ''
        var['source_code'] = ''
        var['timestamp'] = ''
        TPL_PAGE_HEADER = self.template('HTML_HEADER_COMMON')
        TPL_PAGE_FOOTER  = self.template('HTML_FOOTER')
        TPL_PAGE_INDEX = self.template('PAGE_INDEX')
        head = TPL_PAGE_HEADER.render(var=var)
        body = TPL_PAGE_INDEX.render(var=var)
        foot = TPL_PAGE_FOOTER.render(var=var)
        page = head + body + foot
        self.distribute_html('index', page)

    def build(self):
        """Create standard pages for default theme"""
        var = self.get_theme_var()
        self.log.debug("This is the default theme")
        # ~ self.create_page_properties()
        # ~ self.create_page_stats()
        # ~ self.create_page_index_all()
        self.create_page_index(var)
        # ~ self.create_page_about_app()
        # ~ self.create_page_about_theme()
        # ~ self.create_page_about_kb4it()
        # ~ self.create_page_help()



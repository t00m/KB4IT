#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: default theme script
"""

from datetime import datetime

from kb4it.services.builder import Builder
from kb4it.core.util import valid_filename
from evcal import EventsCalendar

class Theme(Builder):
    def generate_sources(self):
        pass

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

    # ~ def create_page_key(self, key, values):
        # ~ """Create key page."""
        # ~ var = self.get_theme_var()
        # ~ var['title'] = key
        # ~ return self.template('PAGE_KEY_KB4IT').render(var=var)

    def create_page_index(self, var):
        """Create key page."""
        var = self.get_theme_var()
        # ~ TPL_INDEX = self.template('PAGE_INDEX')
        TPL_TABLE_EVENTS = self.template('TABLE_EVENT')
        TPL_TABLE_MONTH_OLD = self.template('TABLE_MONTH_OLD')
        TPL_TABLE_MONTH_NEW = self.template('TABLE_MONTH_NEW')
        timestamp = datetime.now()
        now = timestamp.date()
        result = self.srvcal.format_trimester(now.year, now.month)
        trimester = result.replace(TPL_TABLE_MONTH_OLD.render(), TPL_TABLE_MONTH_NEW.render())
        var['trimester'] = trimester
        page = self.template('PAGE_INDEX').render(var=var)
        self.distribute_adoc('index', page)

    def build(self):
        """Create standard pages for default theme"""
        var = self.get_theme_var()
        self.log.debug("This is the Techdoc theme")
        self.app.register_service('EvCal', EventsCalendar())
        self.srvcal = self.get_service('EvCal')
        self.create_page_properties()
        self.create_page_stats()
        self.create_page_index_all()
        self.create_page_index(var)
        # ~ self.create_page_about_app()
        # ~ self.create_page_about_theme()
        # ~ self.create_page_about_kb4it()
        # ~ self.create_page_help()

    def create_page_key(self, key, values):
        """Create page for a key."""
        TPL_PAGE_KEY = self.template('PAGE_KEY_KB4IT')
        var = {}

        # Title
        var['title'] = key
        var['key_values'] = {}
        for value in values:
            k_value = "%s_%s" % (valid_filename(key), valid_filename(value))
            var['key_values'][k_value] = {}
            docs = self.srvdtb.get_docs_by_key_value(key, value)
            var['key_values'][k_value]['count'] = len(docs)
            var['key_values'][k_value]['vfkey'] = valid_filename(key)
            var['key_values'][k_value]['vfvalue'] = valid_filename(value)
            var['key_values'][k_value]['name'] = value
        html = TPL_PAGE_KEY.render(var=var)
        # ~ self.log.debug("PageKey[%s]:\n%s", key, html)
        return html

    def page_hook_pre(self, var):
        var['related'] = ''
        var['metadata'] = ''
        var['source'] = ''
        var['actions'] = ''
        return var
        
        # ~ self.log.error("Page hook pre: %s", basename)
        # ~ basename = var['basename']
        # ~ html = ""
        # ~ try:
            # ~ properties = self.srvdtb.get_doc_properties(basename)
            # ~ if len(properties) > 0:
                # ~ category = ' and '.join(self.srvdtb.get_values(basename, 'Category'))
                # ~ scope = ' and '.join(self.srvdtb.get_values(basename, 'Scope'))
                # ~ author = ' and '.join(self.srvdtb.get_values(basename, 'Author'))
                # ~ when = ' and '.join(self.srvdtb.get_values(basename, 'Published'))
                # ~ notice = """<div class="uk-alert-primary uk-card uk-card-body uk-border-rounded" uk-alert>


    def page_hook_post(self, var):
        return var
        # ~ basename = var['basename']
        # ~ try:
            # ~ metadata_section = var['meta_section']
            # ~ source = var['source_code']
        # ~ except:
            # ~ metadata_section = ''

        # ~ html = ""
        # ~ try:
            # ~ properties = self.srvdtb.get_doc_properties(basename)
            # ~ if len(properties) > 0:
                # ~ tags = properties['Tag']
                # ~ docs = set()
                # ~ related = """<table id="kb4it-datatable" class="uk-table uk-table-responsive uk-table-striped uk-table-divider uk-table-hover">"""
                # ~ related += """<thead><tr><th class="uk-text-bold uk-text-primary"></th></tr></thead>"""
                # ~ related += """<tbody>"""
                # ~ for tag in tags:
                    # ~ for doc in self.srvdtb.get_docs_by_key_value('Tag', tag):
                        # ~ docs.add(doc)
                # ~ for doc in docs:
                    # ~ title = self.srvdtb.get_values(doc, 'Title')[0]
                    # ~ link = doc.replace('.adoc', '.html')
                    # ~ related += """<tr><td><a class="uk-link-toggle" href="%s">%s</a></td></tr>""" % (link, title)
                # ~ related += """</tbody></table>"""

                # ~ html = """
                # ~ </li>
                # ~ <li>
                # ~ %s
                # ~ </li>
                # ~ <li>%s</li>
                # ~ <li><pre>%s</pre></li>
                # ~ </ul>
                                    # ~ """ % (related, metadata_section, source)
        # ~ except KeyError as error:
            # ~ self.log.warning("Page '%s' has no metadata", basename)

        # ~ return html

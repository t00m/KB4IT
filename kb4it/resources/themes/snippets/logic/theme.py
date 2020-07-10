#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: snippet theme scripts
"""

import os

from kb4it.services.builder import KB4ITBuilder
from kb4it.core.util import valid_filename

class Theme(KB4ITBuilder):
    def generate_sources(self):
        pass

    def build(self):
        """Create standard pages for this theme"""
        self.create_page_properties()
        self.create_page_stats()
        self.create_page_index_all()
        self.create_page_index()
        self.create_page_about_app()
        self.create_page_about_theme()
        self.create_page_about_kb4it()
        self.create_page_help()

    def create_page_index(self):
        """Custom index page."""
        html = self.template('PAGE_INDEX')
        html_key = self.create_page_key_body('Module')
        source_dir = self.srvapp.get_source_path()
        lang = os.path.basename(source_dir)
        content = html % (lang, html_key)
        self.distribute('index', content)


    def create_metadata_section(self, doc):
        """Return a html block for displaying core and custom keys."""
        try:
            doc_path = os.path.join(self.srvapp.get_source_path(), doc)
            html = self.template('METADATA_SECTION_HEADER')
            ROW_CUSTOM_PROP = self.template('METADATA_ROW_CUSTOM_PROPERTY')
            ROW_CUSTOM_PROP_TIMESTAMP = self.template('METADATA_ROW_CUSTOM_PROPERTY_TIMESTAMP')
            custom_keys = self.srvdtb.get_custom_keys(doc)
            custom_props = ''
            for key in custom_keys:
                try:
                    values = self.get_html_values_from_key(doc, key)
                    labels = self.get_labels(values)
                    custom_props += ROW_CUSTOM_PROP % (valid_filename(key), key, labels)
                except Exception as error:
                    self.log.error("Key[%s]: %s", key, error)
            num_custom_props = len(custom_props)
            if  num_custom_props > 1:
                html += custom_props
            html += self.template('METADATA_SECTION_FOOTER')
        except Exception as error:
            msgerror = "%s -> %s" % (doc, error)
            self.log.error("\t\t%s", msgerror)
            html = ''
            raise

        return html

    def create_page_key_body(self, key):
        """Create key page."""
        source_dir = self.srvapp.get_source_path()
        values = self.srvdtb.get_all_values_for_key(key)
        num_values = len(values)
        html = self.template('BODY_KEY')

        # TAB Cloud
        cloud = self.create_tagcloud_from_key(key)

        # TAB Stats
        stats = ""
        leader_row = self.template('LEADER_ROW')
        for value in values:
            docs = self.srvdtb.get_docs_by_key_value(key, value)
            tpl_value_link = self.template('LEADER_ROW_VALUE_LINK')
            value_link = tpl_value_link % (valid_filename(key), valid_filename(value), value)
            stats += leader_row % (value_link, len(docs))

        return html % (cloud, stats)

    def get_doc_card(self, doc):
        """Get document card."""
        source_dir = self.srvapp.get_source_path()
        DOC_CARD = self.template('CARD_DOC')
        DOC_CARD_FOOTER = self.template('CARD_DOC_FOOTER')
        LINK = self.template('LINK')
        title = self.srvdtb.get_values(doc, 'Title')[0]
        category = self.srvdtb.get_values(doc, 'Category')[0]
        scope = self.srvdtb.get_values(doc, 'Scope')[0]
        tags = self.srvdtb.get_values(doc, 'Tag')
        link_title = LINK % ("uk-link-heading uk-text-meta", "%s.html" % valid_filename(doc).replace('.adoc', ''), "", title)
        if len(category) > 0 and len(scope) > 0:
            link_category = LINK % ("uk-link-heading uk-text-meta", "Category_%s.html" % valid_filename(category), "", category)
            link_scope = LINK % ("uk-link-heading uk-text-meta", "Scope_%s.html" % valid_filename(scope), "", scope)
            footer = DOC_CARD_FOOTER % (link_category, link_scope)
        else:
            footer = ''

        tooltip ="%s" % (title)
        return DOC_CARD % (tooltip, link_title, '', footer)

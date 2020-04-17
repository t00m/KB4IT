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
from kb4it.src.services.srv_builder import Builder
from kb4it.src.core.mod_utils import valid_filename

class Theme(Builder):
    def hello(self):
        self.log.debug("This is the theme snippets")

    def generate_sources(self):
        pass

    def build(self):
        # Default pages
        self.create_page_all_keys()
        self.create_page_properties()
        self.create_page_stats()
        self.create_page_index_all()
        self.create_page_index()
        self.create_page_about_app()
        self.create_page_about_theme()
        self.create_page_about_kb4it()
        self.create_page_help()

    def create_page_index(self):
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

    def get_doc_card(self, doc):
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
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
        TPL_PAGE_INDEX = self.template('PAGE_INDEX')
        html_key = self.create_page_key_body('Module')
        source_dir = self.srvapp.get_source_path()
        lang = os.path.basename(source_dir)

        page = {}
        page['title'] = "Repository for %s snippets" % lang
        page['content'] = html_key
        content = TPL_PAGE_INDEX.render(var=page)
        self.distribute('index', content)


    def create_metadata_section(self, doc):
        """Return a html block for displaying core and custom keys."""
        try:
            doc_path = os.path.join(self.srvapp.get_source_path(), doc)
            TPL_METADATA_SECTION = self.template('METADATA_SECTION')
            var = {}
            var['items'] = []
            custom_keys = self.srvdtb.get_custom_keys(doc)
            custom_props = []
            for key in custom_keys:
                try:
                    values = self.get_html_values_from_key(doc, key)
                    labels = self.get_labels(values)
                    custom = {}
                    custom['vfkey'] = valid_filename(key)
                    custom['key'] = key
                    custom['labels'] = labels
                    var['items'].append(custom)
                except Exception as error:
                    self.log.error("Key[%s]: %s", key, error)
            var['timestamp'] = self.srvdtb.get_doc_timestamp(doc)
            html = TPL_METADATA_SECTION.render(var=var)
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
        TPL_BODY_KEY = self.template('BODY_KEY')

        # TAB Cloud
        cloud = self.create_tagcloud_from_key(key)

        # TAB Stats
        leader_row = ""
        TPL_LEADER_ROW = self.template('LEADER_ROW')
        for value in values:
            docs = self.srvdtb.get_docs_by_key_value(key, value)
            TPL_VALUE_LINK = self.template('LEADER_ROW_VALUE_LINK')
            row = {}
            row['vfkey'] = valid_filename(key)
            row['vfvalue'] = valid_filename(value)
            row['title'] = value
            value_link = TPL_VALUE_LINK.render(var=row)

            leader = {}
            leader['url'] = value_link
            leader['count_docs'] = len(docs)
            leader_row += TPL_LEADER_ROW.render(var=leader)

        body = {}
        body['cloud'] = cloud
        body['leader'] = leader_row
        return TPL_BODY_KEY.render(var=body)

    def get_doc_card(self, doc):
        """Get card for a given doc"""
        var = {}
        TPL_DOC_CARD = self.template('CARD_DOC')
        TPL_DOC_CARD_CLASS = self.template('CARD_DOC_CLASS')
        LINK = self.template('LINK')

        title = self.srvdtb.get_values(doc, 'Title')[0]
        var['category'] = self.srvdtb.get_values(doc, 'Category')[0]
        var['scope'] = self.srvdtb.get_values(doc, 'Scope')[0]
        var['tags'] = []
        link = {}
        for tag in self.srvdtb.get_values(doc, 'Tag'):
            link['class'] = TPL_DOC_CARD_CLASS.render()
            link['url'] = "Tag_%s.html" % tag
            link['title'] = tag
            thistag = LINK.render(var=link)
            var['tags'].append(thistag)
        var['content'] = ''
        link = {}
        link['class'] = TPL_DOC_CARD_CLASS.render()
        link['url'] = valid_filename(doc).replace('.adoc', '.html')
        link['title'] = title
        var['title'] = LINK.render(var=link)
        # ~ link_title = LINK.render(var=link)
        if len(var['category']) > 0 and len(var['scope']) > 0:
            cat = {}
            cat['class'] = "uk-link-heading uk-text-meta"
            cat['url'] = "Category_%s.html" % valid_filename(var['category'])
            cat['title'] = var['category']
            var['link_category'] = LINK.render(var=cat)

            sco = {}
            sco['class'] = "uk-link-heading uk-text-meta"
            sco['url'] = "Category_%s.html" % valid_filename(var['scope'])
            sco['title'] = var['scope']
            var['link_scope'] = LINK.render(var=sco)
        else:
            var['link_category'] = ''
            var['link_scope'] = ''

        # ~ var['timestamp'] = self.srvdtb.get_doc_timestamp(doc)
        # ~ var['fuzzy_date'] = fuzzy_date_from_timestamp(var['timestamp'])
        var['tooltip'] = title
        DOC_CARD = TPL_DOC_CARD.render(var=var)
        # ~ self.log.error(DOC_CARD)
        return DOC_CARD

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
import math
import time
import datetime as dt
from datetime import datetime
from kb4it.src.core.mod_env import GPATH, VERSION
from kb4it.src.core.mod_srv import Service
from kb4it.src.core.mod_utils import valid_filename, guess_datetime
from kb4it.src.core.mod_utils import get_human_datetime, fuzzy_date_from_timestamp
from kb4it.src.core.mod_utils import set_max_frequency, get_font_size
from kb4it.src.services.srv_db import BLOCKED_KEYS

TEMPLATES = {}

class Builder(Service):
    """Build HTML blocks"""

    tmpdir = None
    srvdtb = None
    srvapp = None

    def initialize(self):
        """Initialize Builder class."""
        self.get_services()
        self.tmpdir = self.srvapp.get_temp_path()

    def get_services(self):
        """Get services."""
        self.srvdtb = self.get_service('DB')
        self.srvapp = self.get_service('App')

    def distribute(self, name, content):
        PAGE_NAME = "%s.adoc" % name
        PAGE_PATH = os.path.join(self.tmpdir, PAGE_NAME)

        if os.path.exists(PAGE_PATH):
            self.log.error("\t\t\t  Page '%s' already exists. Skip." % name)

        with open(PAGE_PATH, 'w') as fpag:
            fpag.write(content)
        # ~ self.log.debug("\t\t\t  Page '%s' saved in %s", name, PAGE_PATH)

    def create_tagcloud_from_key(self, key):
        """Create a tag cloud based on key values."""
        dkeyurl = {}
        for doc in self.srvdtb.get_documents():
            tags = self.srvdtb.get_values(doc, key)
            url = os.path.basename(doc)[:-5]
            for tag in tags:
                try:
                    urllist = dkeyurl[tag]
                    surllist = set(urllist)
                    surllist.add(url)
                    dkeyurl[tag] = list(surllist)
                except KeyError:
                    surllist = set()
                    surllist.add(url)
                    dkeyurl[tag] = list(surllist)


        max_frequency = set_max_frequency(dkeyurl)
        lwords = []

        for word in dkeyurl:
            len_word = len(word)
            if len_word > 0:
                lwords.append(word)

        len_words = len(lwords)
        if  len_words > 0:
            lwords.sort(key=lambda y: y.lower())

            WORDCLOUD = self.template('WORDCLOUD')
            WORDCLOUD_ITEM = self.template('WORDCLOUD_ITEM')
            items = ''
            for word in lwords:
                frequency = len(dkeyurl[word])
                size = get_font_size(frequency, max_frequency)
                url = "%s_%s.html" % (valid_filename(key), valid_filename(word))
                tooltip = "%d documents" % frequency
                item = WORDCLOUD_ITEM % (url, tooltip, size, word)
                items += item
            html = WORDCLOUD % items
        else:
            html = ''

        return html

    def create_index_all(self):
        """C0111: Missing function docstring (missing-docstring)."""
        doclist = self.srvdtb.get_documents()
        self.build_pagination('all', doclist)

    def create_recents_page(self):
        """Create recents page."""
        doclist = self.srvdtb.get_documents()[:60]
        self.build_pagination('recents', doclist, 'Recents')

    def build_pagination(self, basename, doclist, optional_title=None, custom_function='build_cardset', custom_pagination_template='PAGE_PAGINATION_HEAD'):
        PG_HEAD = self.template(custom_pagination_template)
        PG_CARD = self.template('CARD_PAGINATION')
        num_rel_docs = len(doclist)
        if num_rel_docs < 100:
            total_pages = 1
            k = math.ceil(num_rel_docs/total_pages)
        else:
            k = 12
            total_pages = math.ceil(num_rel_docs/k)
            if total_pages > 10:
                total_pages = 10
                k = math.ceil(num_rel_docs/total_pages)
                row = k % 3 # Always display rows with 3 elements at list
                while row != 0:
                    k += 1
                    row = k % 3
                total_pages = math.ceil(num_rel_docs/k)
            elif total_pages == 0:
                total_pages = 1
                k = math.ceil(num_rel_docs/total_pages)

        for current_page in range(total_pages):
            PAGINATION = self.template('PAGINATION_START')
            if total_pages > 0:
                for i in range(total_pages):
                    start = k*i # lower limit
                    end = k*i + k # upper limit
                    if i == current_page:
                        if total_pages - 1 == 0:
                            PAGINATION += self.template('PAGINATION_NONE')
                        else:
                            PAGINATION += self.template('PAGINATION_PAGE_ACTIVE') % (i, start, end, num_rel_docs,i)
                        cstart = start
                        cend = end
                    else:
                        if i == 0:
                            PAGE = "%s.adoc" % basename
                        else:
                            PAGE = "%s-%d.adoc" % (basename, i)
                        PAGINATION += self.template('PAGINATION_PAGE_INACTIVE') % (i, start, end, num_rel_docs, PAGE.replace('adoc','html'), i)
            PAGINATION += self.template('PAGINATION_END')

            if current_page == 0:
                name = "%s" % basename
            else:
                name = "%s-%d" % (basename, current_page)
            ps = cstart
            pe = cend

            if pe > 0:
                # get build_cardset custom function or default
                custom_build_cardset = "self.%s" % custom_function
                CARDS = eval(custom_build_cardset)(doclist[ps:pe])
            else:
                CARDS = ""

            if optional_title is None:
                title = basename.replace('_', ' ').title()
            else:
                title = optional_title
            content = PG_HEAD % (title, PAGINATION, CARDS)
            self.distribute(name, content)
        # ~ self.log.debug("\t\t\t  Created '%s' page (%d pages with %d cards in each page)", basename, total_pages, k)

    def build_cardset(self, doclist):
        CARD_DOC_FILTER_DATA_TITLE = self.template('CARD_DOC_FILTER_DATA_TITLE')
        CARDS = ""
        for doc in doclist:
            title = self.srvdtb.get_values(doc, 'Title')[0]
            doc_card = self.get_doc_card(doc)
            card_search_filter = CARD_DOC_FILTER_DATA_TITLE % (valid_filename(title), doc_card)
            CARDS += """%s""" % card_search_filter
        return CARDS

    def create_about_page(self):
        """C0111: Missing function docstring (missing-docstring)."""
        TPL_ABOUT = self.template('PAGE_ABOUT')
        self.distribute('about', TPL_ABOUT % VERSION)

    def create_help_page(self):
        """C0111: Missing function docstring (missing-docstring)."""
        TPL_HELP = self.template('PAGE_HELP')
        self.distribute('help', TPL_HELP)

    def create_index_page(self):
        """C0111: Missing function docstring (missing-docstring)."""
        TPL_INDEX = self.template('PAGE_INDEX')
        self.distribute('index', TPL_INDEX)

    def create_all_keys_page(self):
        """C0111: Missing function docstring (missing-docstring)."""
        content = self.template('PAGE_KEYS')
        all_keys = self.srvdtb.get_all_keys()
        for key in all_keys:
            cloud = self.create_tagcloud_from_key(key)
            len_cloud = len(cloud)
            if  len_cloud > 0:
                content += "\n\n== %s\n\n" % key
                content += "\n++++\n%s\n++++\n" % cloud
        self.distribute('keys', content)

    def get_maxkv_freq(self):
        maxkvfreq = 0
        all_keys = self.srvdtb.get_all_keys()
        for key in all_keys:
            if key not in BLOCKED_KEYS:
                values = self.srvdtb.get_all_values_for_key(key)
                if len(values) > maxkvfreq:
                    maxkvfreq = len(values)
        return maxkvfreq

    def create_properties_page(self):
        """Create properties page."""
        TPL_PROPS_PAGE = self.template('PAGE_PROPERTIES')
        TPL_KEY_MODAL_BUTTON = self.template('KEY_MODAL_BUTTON')
        max_frequency = self.get_maxkv_freq()
        all_keys = self.srvdtb.get_all_keys()
        custom_buttons = ''
        for key in all_keys:
            if key not in BLOCKED_KEYS:
                html = self.create_tagcloud_from_key(key)
                values = self.srvdtb.get_all_values_for_key(key)
                frequency = len(values)
                size = get_font_size(frequency, max_frequency)
                proportion = int(math.log((frequency * 100) / max_frequency))
                tooltip = "%d values" % len(values)
                button = TPL_KEY_MODAL_BUTTON % (valid_filename(key), tooltip, size, key, valid_filename(key), valid_filename(key), key, html)
                custom_buttons += button
        content = TPL_PROPS_PAGE % (custom_buttons)
        self.distribute('properties', content)

    def create_stats_page(self):
        TPL_STATS_PAGE = self.template('PAGE_STATS')
        item = self.template('KEY_LEADER_ITEM')
        numdocs = self.srvapp.get_numdocs()
        keys = self.srvdtb.get_all_keys()
        numkeys = len(keys)
        leader_items = ''
        for key in keys:
            values = self.srvdtb.get_all_values_for_key(key)
            leader_items += item % (valid_filename(key), key, valid_filename(key), len(values))
        stats = TPL_STATS_PAGE % (numdocs, numkeys, leader_items)
        self.distribute('stats', stats)


    def create_key_page(self, key, values):
        """Create key page."""
        source_dir = self.srvapp.get_source_path()
        num_values = len(values)
        html = self.template('PAGE_KEY')

        # TAB Cloud
        cloud = self.create_tagcloud_from_key(key)

        # TAB Stats
        stats = ""
        leader_row = self.template('LEADER_ROW')
        for value in values:
            docs = list(self.srvdtb.get_docs_by_key_value(key, value))
            tpl_value_link = self.template('LEADER_ROW_VALUE_LINK')
            value_link = tpl_value_link % (valid_filename(key), valid_filename(value), value)
            stats += leader_row % (value_link, len(docs))

        return html % (key, cloud, stats)

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
                    values = self.srvdtb.get_html_values_from_key(doc, key)
                    labels = self.get_labels(values)
                    custom_props += ROW_CUSTOM_PROP % (valid_filename(key), key, labels)
                except Exception as error:
                    self.log.error("Key[%s]: %s", key, error)
            timestamp = self.srvdtb.get_doc_timestamp(doc)
            custom_props += ROW_CUSTOM_PROP_TIMESTAMP % ('Timestamp', timestamp)
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

    def get_doc_link(self, doc):
        title = self.srvdtb.get_values(doc, 'Title')[0]
        link = "%s.html" % doc
        return """<a href="%s"><span>%s</span></a>""" % (link, title)

    def get_doc_card(self, doc):
        source_dir = self.srvapp.get_source_path()
        DOC_CARD = self.template('CARD_DOC')
        DOC_CARD_FOOTER = self.template('CARD_DOC_FOOTER')
        DOC_CARD_LINK = self.template('CARD_DOC_LINK')
        title = self.srvdtb.get_values(doc, 'Title')[0]
        category = self.srvdtb.get_values(doc, 'Category')[0]
        scope = self.srvdtb.get_values(doc, 'Scope')[0]
        link_title = DOC_CARD_LINK % (valid_filename(doc).replace('.adoc', ''), title)
        if len(category) > 0 and len(scope) >0:
            link_category = DOC_CARD_LINK % ("Category_%s" % valid_filename(category), category)
            link_scope = DOC_CARD_LINK % ("Scope_%s" % valid_filename(scope), scope)
            footer = DOC_CARD_FOOTER % (link_category, link_scope)
        else:
            footer = ''

        timestamp = self.srvdtb.get_doc_timestamp(doc)
        if type(timestamp) == str:
            timestamp = guess_datetime(timestamp)

        if timestamp is not None:
            human_ts = get_human_datetime(timestamp)
            fuzzy_date = fuzzy_date_from_timestamp(timestamp)
        else:
            timestamp = ''
            fuzzy_date = ''
            self.log.warning("No timestamp detected")
        tooltip ="%s" % (title)
        return DOC_CARD % (tooltip, link_title, timestamp, fuzzy_date, footer)

    def get_labels(self, values):
        """C0111: Missing function docstring (missing-docstring)."""
        label_links = ''
        value_link = self.template('METADATA_VALUE_LINK')
        for page, text in values:
            if len(text) != 0:
                label_links += value_link % (valid_filename(page), text)
        return label_links

    def template(self, template):
        """Return the template content from default theme or user theme"""

        properties = self.srvapp.get_runtime_properties()
        theme = properties['theme']
        current_theme = theme['id']

        # Try to get the template from cache
        try:
            return TEMPLATES[template]
        except KeyError:
            template_path = os.path.join(theme['templates'], "%s.tpl" % template)
            if not os.path.exists(template_path):
                current_theme = 'default'
                theme_default = os.path.join(GPATH['THEMES'], os.path.join('default', 'templates'))
                template_path = os.path.join(theme_default, "%s.tpl" % template)

            if not os.path.exists(template_path):
                self.log.error("Template '%s' not found in '%s'", template, template_path)
                return None
            # ~ self.log.debug("\t\tAdding template '%s' to cache from theme '%s'", template, current_theme)
            TEMPLATES[template] = open(template_path, 'r').read()
            return TEMPLATES[template]

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
import math
import datetime as dt
from datetime import datetime
from kb4it.src.core.mod_srv import Service
from kb4it.src.services.srv_db import IGNORE_KEYS, BLOCKED_KEYS # HEADER_KEYS,
from kb4it.src.core.mod_utils import template, valid_filename, get_labels
from kb4it.src.core.mod_utils import get_human_datetime, fuzzy_date_from_timestamp
from kb4it.src.core.mod_utils import set_max_frequency, get_font_size
from kb4it.src.core.mod_utils import get_author_icon
from kb4it.src.core.mod_utils import last_modification


class Builder(Service):
    """Build HTML blocks"""

    tmpdir = None
    srvdtb = None
    srvapp = None
    missing_icons = {}

    def initialize(self):
        """Initialize Builder class."""
        self.get_services()
        self.tmpdir = self.srvapp.get_temp_path()

    def get_services(self):
        """Get services."""
        self.srvdtb = self.get_service('DB')
        self.srvapp = self.get_service('App')

    def get_missing_icons(self):
        """Return list of missing author icons."""
        return self.missing_icons

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

            WORDCLOUD = template('WORDCLOUD')
            WORDCLOUD_ITEM = template('WORDCLOUD_ITEM')
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
        """Missing method docstring."""
        doclist = self.srvdtb.get_documents()
        self.build_pagination('All documents', 'all', doclist)


    def build_pagination(self, page_title, basename, doclist):
        PG_HEAD = template('PAGINATION_HEAD')
        PG_CARD = template('PAGINATION_CARD')
        DOC_CARD_FILTER_DATA_TITLE = template('DOC_CARD_FILTER_DATA_TITLE')
        k = 12
        num_rel_docs = len(doclist)
        total_pages = math.ceil(num_rel_docs/k)
        if total_pages > 10:
            total_pages = 10
            k = math.ceil(num_rel_docs/total_pages)
        elif total_pages == 0:
            total_pages = 1

        for current_page in range(total_pages):
            PAGINATION = """\n<ul class="uk-pagination uk-flex-center" uk-margin>\n"""
            # ~ self.log.debug("ALL - Current page: %d" % current_page)
            if total_pages > 0:
                for i in range(total_pages):
                    start = k*i # lower limit
                    end = k*i + k # upper limit
                    # ~ self.log.debug("\tLink %d in page %d" % (i, current_page))
                    if i == current_page:
                        if total_pages - 1 == 0:
                            PAGINATION += """\t<li class="uk-active"></li>\n"""
                        else:
                            PAGINATION += """\t<li class="uk-active"><span uk-tooltip="Page %d: %d-%d/%d">%d</span></li>\n""" % (i, start, end, num_rel_docs,i)
                        cstart = start
                        cend = end
                    else:
                        if i == 0:
                            PAGE = "%s.adoc" % basename
                        else:
                            PAGE = "%s-%d.adoc" % (basename, i)
                        PAGINATION += """\t<li uk-tooltip="Page %d: %d-%d/%d"><a href="%s"><span>%i</span></a></li>\n""" % (i, start, end, num_rel_docs, PAGE.replace('adoc','html'), i)
            PAGINATION += """</ul>\n"""
            # ~ self.log.debug(PAGINATION)

            if current_page == 0:
                DOCNAME_PATH = "%s/%s.adoc" % (self.tmpdir, basename)
            else:
                DOCNAME_PATH = "%s/%s-%d.adoc" % (self.tmpdir, basename, current_page)
            ps = cstart
            pe = cend
            with open(DOCNAME_PATH, 'w') as fall:
                n = ps
                # ~ self.log.debug("Displaying documents from %d to %d" % (ps, pe-1))
                CARDS = ""
                for doc in doclist[ps:pe]:
                    title = self.srvdtb.get_values(doc, 'Title')[0]
                    doc_card = self.get_doc_card(doc)
                    card_search_filter = DOC_CARD_FILTER_DATA_TITLE % (valid_filename(title), doc_card)
                    CARDS += """%s""" % card_search_filter
                    n += 1
                fall.write(PG_HEAD % (page_title, PAGINATION, CARDS))
        self.log.debug("\t\tCreated '%s' page (%d pages with %d in each page)", page_title, total_pages, k)


    def create_category_filter(self, categories):
        """Missing method docstring."""
        pass

    def create_index_page(self):
        """Missing method docstring."""
        TPL_INDEX = template('INDEX')
        TPL_KEY_MODAL_BUTTON = template('KEY_MODAL_BUTTON')

        with open('%s/index.adoc' % self.tmpdir, 'w') as findex:
            dir_res = os.path.join(self.srvapp.get_source_path(), 'resources')
            dir_tpl = os.path.join(dir_res, 'templates')
            custom_index_file = os.path.join(dir_tpl, 'index.adoc')
            if os.path.exists(custom_index_file):
                self.log.info("\t\tCustom index page found.")
                custom_index = open(custom_index_file, 'r').read()
            else:
                self.log.warning("\t\tNo custom index page found. Using default template.")
                custom_index = ''

            content = TPL_INDEX % (custom_index)
            findex.write(content)

    def create_all_keys_page(self):
        """Missing method docstring."""
        TPL_KEYS = template('KEYS')
        with open('%s/keys.adoc' % self.tmpdir, 'w') as fkeys:
            fkeys.write(TPL_KEYS)
            all_keys = self.srvdtb.get_all_keys()
            for key in all_keys:
                cloud = self.create_tagcloud_from_key(key)
                len_cloud = len(cloud)
                if  len_cloud > 0:
                    fkeys.write("\n\n== %s\n\n" % key)
                    fkeys.write("\n++++\n%s\n++++\n" % cloud)


    def create_recents_page(self):
        """Create recents page."""
        doclist = self.srvdtb.get_documents()[:60]
        self.build_pagination('Recents', 'recents', doclist)

    def create_bookmarks_page(self):
        """Create bookmarks page."""
        doclist = []
        for doc in self.srvdtb.get_documents():
            bookmark = self.srvdtb.get_values(doc, 'Bookmark')[0]
            if bookmark == 'Yes' or bookmark == 'True':
                doclist.append(doc)
        self.build_pagination('Bookmarks', 'bookmarks', doclist)


    def create_properties_page(self):
        """Create properties page."""
        TPL_PROPS_PAGE = template('PAGE_PROPERTIES')
        TPL_KEY_MODAL_BUTTON = template('KEY_MODAL_BUTTON')
        # Custom modal buttons
        all_keys = self.srvdtb.get_all_keys()
        custom_buttons = ''
        for key in all_keys:
            if key not in BLOCKED_KEYS:
                html = self.create_tagcloud_from_key(key)
                values = self.srvdtb.get_all_values_for_key(key)
                tooltip = "%d values" % len(values)
                button = TPL_KEY_MODAL_BUTTON % (valid_filename(key), tooltip, key, valid_filename(key), valid_filename(key), key, html)
                custom_buttons += button

        content = TPL_PROPS_PAGE % (custom_buttons)
        with open('%s/properties.adoc' % self.tmpdir, 'w') as fprops:
            fprops.write(content)

    def create_stats_page(self):
        TPL_STATS_PAGE = template('PAGE_STATS')
        item = template('KEY_LEADER_ITEM')
        numdocs = self.srvapp.get_numdocs()
        keys = self.srvdtb.get_all_keys()
        numkeys = len(keys)
        leader_items = ''
        for key in keys:
            values = self.srvdtb.get_all_values_for_key(key)
            leader_items += item % (valid_filename(key), key, valid_filename(key), len(values))
        stats = TPL_STATS_PAGE % (numdocs, numkeys, leader_items)

        with open('%s/stats.adoc' % self.tmpdir, 'w') as fstats:
            fstats.write(stats)

    def create_key_page(self, key, values):
        """Missing method docstring."""
        # ~ self.log.error("[%s]: %s", key, values)
        source_dir = self.srvapp.get_source_path()

        num_values = len(values)
        html = template('KEY_PAGE')

        # TAB Filter
        key_filter = '' #template('PROPERTY_FILTER')

        ## Build filter header
        key_filter_header_rows = ""
        for value in values:
            docs = self.srvdtb.get_docs_by_key_value(key, value)
            tpl_header_item = template('PROPERTY_FILTER_HEAD_ITEM')
            value_filter = value.replace(' ', '_')
            header_item = tpl_header_item % (valid_filename(key), \
                                             valid_filename(value_filter),
                                             value, len(docs))
            key_filter_header_rows += header_item

        ## Build filter body
        key_filter_docs = ""
        cardset = set()
        for value in values:
            docs = self.srvdtb.get_docs_by_key_value(key, value)
            for doc in docs:
                cardset.add(doc)

        for doc in cardset:
            objects = self.srvdtb.get_values(doc, key)
            data_objects = []

            for obj in objects:
                data_objects.append(valid_filename(obj))

            title = self.srvdtb.get_values(doc, 'Title')[0] # Only first match
            doc_card = self.get_doc_card(doc)
            tpl_key_filter_docs = template('DOC_CARD_FILTER_DATA_TITLE_PLUS_OTHER_DATA')
            key_filter_docs += tpl_key_filter_docs % (valid_filename(title), \
                                                      valid_filename(key), \
                                                      data_objects, \
                                                      doc_card)


        # TAB Cloud
        cloud = self.create_tagcloud_from_key(key)

        # TAB Stats
        stats = ""
        leader_row = template('LEADER_ROW')
        for value in values:
            docs = list(self.srvdtb.get_docs_by_key_value(key, value))
            tpl_value_link = template('LEADER_ROW_VALUE_LINK')
            value_link = tpl_value_link % (valid_filename(key), valid_filename(value), value)
            stats += leader_row % (value_link, len(docs))

        return html % (key, cloud, stats)

    def create_metadata_section(self, doc):
        """Return a html block for displaying core and custom keys."""
        try:
            doc_path = os.path.join(self.srvapp.get_source_path(), doc)
            html = template('METADATA_SECTION_HEADER')
            custom_keys = self.srvdtb.get_custom_keys(doc)
            custom_props = ''
            for key in custom_keys:
                try:
                    values = self.srvdtb.get_html_values_from_key(doc, key)
                    labels = get_labels(values)
                    row_custom_prop = template('METADATA_ROW_CUSTOM_PROPERTY')
                    custom_props += row_custom_prop % (valid_filename(key), key, labels)
                except Exception as error:
                    self.log.error("Key[%s]: %s", key, error)
            num_custom_props = len(custom_props)
            if  num_custom_props > 0:
                html += custom_props
            html += template('METADATA_SECTION_FOOTER')
        except Exception as error:
            msgerror = "%s -> %s" % (doc, error)
            self.log.error("\t\t%s", msgerror)
            html = ''
            raise

        return html


    # ~ def create_search_page(self):
        # ~ filename = 'search.adoc'
        # ~ search_page = os.path.join(self.tmpdir, filename)

        # ~ DOC_CARD_FILTER_DATA_TITLE = template('DOC_CARD_FILTER_DATA_TITLE')
        # ~ html = ''
        # ~ for doc in self.srvdtb.get_documents():
            # ~ title = self.srvdtb.get_values(doc, 'Title')[0]
            # ~ doc_card = self.get_doc_card(doc)
            # ~ card_search_filter = DOC_CARD_FILTER_DATA_TITLE % (valid_filename(title), doc_card)
            # ~ html += """%s""" % card_search_filter

        # ~ with open(search_page, 'w') as fsp:
            # ~ tpl = template('PAGE_SEARCH')
            # ~ fsp.write(tpl % html)

    def get_messages(self):
        msgs = ''
        msg = template('MESSAGE')
        found = False
        for doc in self.srvdtb.get_documents():
            category = self.srvdtb.get_values(doc, 'Category')[0]
            if category == 'Message':
                found = True
                break

        if found:
            return msgs + msg
        else:
            return ''


    def get_doc_card_blogpost(self, doc):
        source_dir = self.srvapp.get_source_path()
        DOC_CARD = template('DOC_CARD_BLOGPOST')
        DOC_CARD_TITLE = template('DOC_CARD_BLOGPOST_TITLE')
        DOC_CARD_LINK = template('DOC_CARD_LINK')
        title = self.srvdtb.get_values(doc, 'Title')[0]
        category = self.srvdtb.get_values(doc, 'Category')[0]
        scope = self.srvdtb.get_values(doc, 'Scope')[0]
        team = self.srvdtb.get_values(doc, 'Team')[0] # Only first match?
        author = self.srvdtb.get_values(doc, 'Author')[0]
        authors = ', '.join(self.srvdtb.get_values(doc, 'Author'))
        icon_path = get_author_icon(source_dir, author)
        if icon_path == "resources/images/authors/author_unknown.png":
            self.missing_icons[author] = os.path.join(source_dir, "%s.png" % valid_filename(author))
        link_title = DOC_CARD_TITLE % (valid_filename(doc).replace('.adoc', ''), title)
        link_category = DOC_CARD_LINK % ("Category_%s" % valid_filename(category), category)
        link_scope = DOC_CARD_LINK % ("Scope_%s" % valid_filename(scope), scope)
        link_team = DOC_CARD_LINK % ("Team_%s" % valid_filename(team), team)
        link_author = DOC_CARD_LINK % ("Author_%s" % valid_filename(author), author)
        link_image = "Author_%s.html" % valid_filename(author)
        timestamp = self.srvdtb.get_doc_timestamp(doc)
        human_ts = get_human_datetime(timestamp)
        return DOC_CARD % (link_title, timestamp, human_ts, link_scope)


    def get_doc_link(self, doc):
        title = self.srvdtb.get_values(doc, 'Title')[0]
        link = "%s.html" % doc
        return """<a href="%s"><span>%s</span></a>""" % (link, title)

    def get_doc_card(self, doc):
        source_dir = self.srvapp.get_source_path()
        DOC_CARD = template('DOC_CARD')
        DOC_CARD_FOOTER = template('DOC_CARD_FOOTER')
        DOC_CARD_LINK = template('DOC_CARD_LINK')
        title = self.srvdtb.get_values(doc, 'Title')[0]
        category = self.srvdtb.get_values(doc, 'Category')[0]
        scope = self.srvdtb.get_values(doc, 'Scope')[0]
        team = self.srvdtb.get_values(doc, 'Team')[0] # Only first match?
        author = self.srvdtb.get_values(doc, 'Author')[0]
        authors = ', '.join(self.srvdtb.get_values(doc, 'Author'))
        icon_path = get_author_icon(source_dir, author)
        if icon_path == "resources/images/authors/author_unknown.png":
            self.missing_icons[author] = os.path.join(source_dir, "%s.png" % valid_filename(author))
        link_title = DOC_CARD_LINK % (valid_filename(doc).replace('.adoc', ''), title)
        if len(category) > 0 and len(scope) >0:
            link_category = DOC_CARD_LINK % ("Category_%s" % valid_filename(category), category)
            link_scope = DOC_CARD_LINK % ("Scope_%s" % valid_filename(scope), scope)
            footer = DOC_CARD_FOOTER % (link_category, link_scope)
        else:
            footer = ''
        link_team = DOC_CARD_LINK % ("Team_%s" % valid_filename(team), team)
        link_author = DOC_CARD_LINK % ("Author_%s" % valid_filename(author), author)
        link_image = "Author_%s.html" % valid_filename(author)
        timestamp = self.srvdtb.get_doc_timestamp(doc)
        human_ts = get_human_datetime(timestamp)
        fuzzy_date = fuzzy_date_from_timestamp(timestamp)
        return DOC_CARD % (title, timestamp, link_title, timestamp, fuzzy_date, footer)

    def create_blog_page(self):
        doclist = []
        for doc in self.srvdtb.get_documents():
            category = self.srvdtb.get_values(doc, 'Category')[0]
            if category == 'Post':
                doclist.append(doc)
        self.build_pagination('Blog', 'blog', doclist)

    def create_events_page(self):
        doclist = set()
        for doc in self.srvdtb.get_documents():
            category = self.srvdtb.get_values(doc, 'Category')[0]
            if category == 'Event':
                doclist.add(doc)

        self.build_pagination('Events', 'events', list(doclist))
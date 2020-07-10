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
import shutil
import random
import threading
from datetime import datetime
from kb4it.core.env import APP, GPATH
from kb4it.core.service import Service
from kb4it.core.util import valid_filename
from kb4it.core.util import get_human_datetime, fuzzy_date_from_timestamp
from kb4it.core.util import set_max_frequency, get_font_size
from kb4it.core.util import delete_files, extract_toc
from kb4it.core.util import get_hash_from_file

TEMPLATES = {}


class KB4ITBuilder(Service):
    """Build HTML blocks"""

    tmpdir = None
    srvdtb = None
    srvapp = None
    temp_sources = []
    distributed = None

    def initialize(self):
        """Initialize Builder class."""
        self.get_services()
        self.tmpdir = self.srvapp.get_temp_path()
        self.srcdir = self.srvapp.get_source_path()
        self.now = datetime.now()
        self.distributed = {}

    def get_distributed(self):
        """Get a list of pages distributed"""
        return self.distributed

    def finalize(self):
        """Clean up temporary files"""
        # Delete temporary sources generated by themes
        delete_files(self.temp_sources)

    def get_services(self):
        """Get services."""
        self.srvdtb = self.get_service('DB')
        self.srvapp = self.get_service('App')

    def distribute(self, name, content):
        """
        Distribute source file to temporary directory.

        Use this method when the source asciidoctor file doesn't have to
        be analyzed.
        """
        PAGE_NAME = "%s.adoc" % name
        PAGE_PATH = os.path.join(self.tmpdir, PAGE_NAME)
        with open(PAGE_PATH, 'w') as fpag:
            fpag.write(content)
        self.log.debug("[BUILDER] - PAGE[%s] distributed to temporary path", os.path.basename(PAGE_PATH))
        self.distributed[PAGE_NAME] = get_hash_from_file(PAGE_PATH)
        self.srvapp.add_target(PAGE_NAME.replace('.adoc', '.html'))

    def distribute_to_source(self, name, content):
        """
        Distribute source file to user source directory.
        Use this method when the source asciidoctor file has to
        be analyzed to extract its properties.
        File path reference will be saved and deleted at the end of the
        execution.
        """
        PAGE_NAME = "%s.adoc" % name
        PAGE_PATH = os.path.join(self.srcdir, PAGE_NAME)
        self.temp_sources.append(PAGE_PATH)
        with open(PAGE_PATH, 'w') as fpag:
            fpag.write(content)
            self.log.debug("[BUILDER] - PAGE[%s] distributed to source path", name)

    def template(self, template):
        """Return the template content from default theme or user theme"""

        properties = self.srvapp.get_runtime_properties()
        theme = properties['theme']
        current_theme = theme['id']

        # Try to get the template from cache
        try:
            return TEMPLATES[template]
        except KeyError:
            # Get template from custom theme
            # If not found, get it from default theme
            template_path = os.path.join(theme['templates'], "%s.tpl" % template)
            if os.path.exists(template_path):
                self.log.debug("[BUILDER] - THEME[%s] TPL[%s] loaded", theme['id'], template)
            else:
                current_theme = 'default'
                theme_default = os.path.join(GPATH['THEMES'], os.path.join('default', 'templates'))
                template_path = os.path.join(theme_default, "%s.tpl" % template)

                if os.path.exists(template_path):
                    self.log.debug("[BUILDER] - THEME['default'] TPL[%s] loaded", template)
                else:
                    self.log.error("[BUILDER] - TPL[%s] not found. Exit.", template)
                    sys.exit()

            # If template found, add it to cache. Otherwise, exit.
            try:
                TEMPLATES[template] = open(template_path, 'r').read()
                return TEMPLATES[template]
            except FileNotFoundError as error:
                self.log.error("[BUILDER] - %s", error)
                sys.exit()

    def build_page(self, future):
        """
        Compile page from asciidoctor to HTML.
        """
        THEME_ID = self.srvapp.get_theme_property('id')
        HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
        HTML_HEADER_DOC = self.template('HTML_HEADER_DOC')
        HTML_HEADER_NODOC = self.template('HTML_HEADER_NODOC')
        now = datetime.now()
        timestamp = get_human_datetime(now)
        time.sleep(random.random())
        x = future.result()
        cur_thread = threading.current_thread().name
        if cur_thread != x:
            adoc, rc, j = x
            # Add header and footer to compiled doc
            htmldoc = adoc.replace('.adoc', '.html')
            basename = os.path.basename(adoc)
            if os.path.exists(htmldoc):
                adoc_title = open(adoc).readlines()[0]
                title = adoc_title[2:-1]
                htmldoctmp = "%s.tmp" % htmldoc
                shutil.move(htmldoc, htmldoctmp)
                source = open(htmldoctmp, 'r').read()
                toc = extract_toc(source)
                content = self.srvapp.apply_transformations(source)
                try:
                    if 'Metadata' in content:
                        content = highlight_metadata_section(content)
                except NameError as error:
                    # Sometimes, weird links in asciidoctor sources
                    # provoke compilation errors
                    self.log.error("[BUILDER] - ERROR!! Please, check source document '%s'.", basename)
                    self.log.error("[BUILDER] - ERROR!! It didn't compile successfully. Usually, it is because of malformed urls.")
                finally:
                    # Some pages don't have toc section. Ignore it.
                    pass

                with open(htmldoc, 'w') as fhtm:
                    len_toc = len(toc)
                    if len_toc > 0:
                        TOC = self.template('HTML_HEADER_MENU_CONTENTS_ENABLED') % toc
                    else:
                        TOC = self.template('HTML_HEADER_MENU_CONTENTS_DISABLED')

                    userdoc = os.path.join(os.path.join(self.srvapp.get_source_path(), basename))
                    if os.path.exists(userdoc):
                        source_code = open(userdoc, 'r').read()
                        self.srvthm = self.get_service('Theme')
                        meta_section = self.srvthm.create_metadata_section(basename)
                        PAGE = HTML_HEADER_COMMON % (title, THEME_ID, TOC) + HTML_HEADER_DOC % (title, basename, meta_section, basename, source_code)
                        fhtm.write(PAGE)
                    else:
                        PAGE = HTML_HEADER_COMMON % (title, THEME_ID, TOC) + HTML_HEADER_NODOC % (title)
                        fhtm.write(PAGE)
                    fhtm.write(content)
                    HTML_FOOTER = self.template('HTML_FOOTER')
                    fhtm.write(HTML_FOOTER % timestamp)
                os.remove(htmldoctmp)
                return x

    def build_pagination(self, pagination):
        """
        Create a page with documents.
        If amount of documents is greater than 100, split it in several pages
        """
        PG_HEAD = self.template(pagination['template'])
        num_rel_docs = len(pagination['doclist'])
        pagelist = []
        if num_rel_docs < 100:
            total_pages = 1
            k = math.ceil(num_rel_docs / total_pages)
        else:
            k = 12
            total_pages = math.ceil(num_rel_docs / k)
            if total_pages > 10:
                total_pages = 10
                k = math.ceil(num_rel_docs / total_pages)
                row = k % 3  # Always display rows with 3 elements at list
                while row != 0:
                    k += 1
                    row = k % 3
                total_pages = math.ceil(num_rel_docs / k)
            elif total_pages == 0:
                total_pages = 1
                k = math.ceil(num_rel_docs / total_pages)

        for current_page in range(total_pages):
            PAGINATION = self.template('PAGINATION_START')
            if total_pages > 0:
                for i in range(total_pages):
                    start = k * i  # lower limit
                    end = k * i + k  # upper limit
                    if i == current_page:
                        if total_pages - 1 == 0:
                            PAGINATION += self.template('PAGINATION_NONE')
                        else:
                            PAGINATION += self.template('PAGINATION_PAGE_ACTIVE') % (i, start, end, num_rel_docs, i)
                        cstart = start
                        cend = end
                    else:
                        if i == 0:
                            PAGE = "%s.adoc" % pagination['basename']
                        else:
                            PAGE = "%s-%d.adoc" % (pagination['basename'], i)
                        PAGINATION += self.template('PAGINATION_PAGE_INACTIVE') % (i, start, end, num_rel_docs, PAGE.replace('adoc', 'html'), i)
            PAGINATION += self.template('PAGINATION_END')

            if current_page == 0:
                name = "%s" % pagination['basename']
            else:
                name = "%s-%d" % (pagination['basename'], current_page)
            ps = cstart
            pe = cend

            if pe > 0:
                # get build_cardset custom function or default
                custom_build_cardset = "self.%s" % pagination['function']
                CARDS = eval(custom_build_cardset)(pagination['doclist'][ps:pe])
            else:
                CARDS = ""

            if pagination['title'] is None:
                title = pagination['basename'].replace('_', ' ')
            else:
                title = pagination['title']
            content = PG_HEAD % (title, PAGINATION, CARDS)
            if not pagination['fake']:
                self.distribute(name, content)
            pagelist.append(name)

        self.log.debug("[BUILDER] - Created pagination page '%s' (%d pages with %d cards in each page)", pagination['basename'], total_pages, k)

        return pagelist

    def build_cardset(self, doclist):
        """Default method to build pages paginated"""
        CARD_DOC_FILTER_DATA_TITLE = self.template('CARD_DOC_FILTER_DATA_TITLE')
        CARDS = ""
        for doc in doclist:
            title = self.srvdtb.get_values(doc, 'Title')[0]
            doc_card = self.get_doc_card(doc)
            card_search_filter = CARD_DOC_FILTER_DATA_TITLE % (valid_filename(title), doc_card)
            CARDS += """%s""" % card_search_filter
        return CARDS

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
        if len_words > 0:
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

    def create_page_index_all(self):
        """Create a page with all documents"""
        doclist = self.srvdtb.get_documents()
        pagination = {}
        pagination['basename'] = 'all'
        pagination['doclist'] = doclist
        pagination['title'] = 'All documents'
        pagination['function'] = 'build_cardset'
        pagination['template'] = 'PAGE_PAGINATION_HEAD'
        pagination['fake'] = False
        self.build_pagination(pagination)

    def create_page_recents(self):
        """Create a page with 60 documents sorted by date desc"""
        doclist = self.srvdtb.get_documents()[:60]
        pagination = {}
        pagination['basename'] = 'recents'
        pagination['doclist'] = doclist
        pagination['title'] = 'Recent documents'
        pagination['function'] = 'build_cardset'
        pagination['template'] = 'PAGE_PAGINATION_HEAD'
        pagination['fake'] = False
        self.build_pagination(pagination)

    def generate_sources(self):
        """Custom themes can use this method to generate source documents"""
        pass

    def create_page_help(self):
        """
        Create help page.
        To be replaced by custom code.
        """
        TPL_HELP = self.template('PAGE_HELP')
        self.distribute('help', TPL_HELP)

    def create_page_index(self):
        """Create index page.
        To be replaced by custom code.
        """
        TPL_INDEX = self.template('PAGE_INDEX')
        self.distribute('index', TPL_INDEX)

    def get_maxkv_freq(self):
        """Calculate max frequency for all keys"""
        maxkvfreq = 0
        all_keys = self.srvdtb.get_all_keys()
        for key in all_keys:
            blocked_keys = self.srvdtb.get_blocked_keys()
            if key not in blocked_keys:
                values = self.srvdtb.get_all_values_for_key(key)
                if len(values) > maxkvfreq:
                    maxkvfreq = len(values)
        return maxkvfreq

    def create_page_properties(self):
        """Create properties page"""
        TPL_PROPS_PAGE = self.template('PAGE_PROPERTIES')
        TPL_KEY_MODAL_BUTTON = self.template('KEY_MODAL_BUTTON')
        max_frequency = self.get_maxkv_freq()
        all_keys = self.srvdtb.get_all_keys()
        custom_buttons = ''
        for key in all_keys:
            ignored_keys = self.srvdtb.get_ignored_keys()
            if key not in ignored_keys:
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

    def create_page_stats(self):
        """Create stats page"""
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

    def create_page_key(self, key, values):
        """Create key page."""
        html = self.template('PAGE_KEY')

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

        return html % (key, cloud, stats)

    def get_html_values_from_key(self, doc, key):
        """Return the html link for a value."""
        html = []

        values = self.srvdtb.get_values(doc, key)
        for value in values:
            url = "%s_%s.html" % (key, value)
            html.append((url, value))
        return html

    def create_metadata_section(self, doc):
        """Return a html block for displaying metadata (keys and values)."""
        try:
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
                    self.log.error("[BUILDER] - Key[%s]: %s", key, error)
            timestamp = self.srvdtb.get_doc_timestamp(doc)
            custom_props += ROW_CUSTOM_PROP_TIMESTAMP % ('Timestamp', timestamp)
            num_custom_props = len(custom_props)
            if num_custom_props > 1:
                html += custom_props
            html += self.template('METADATA_SECTION_FOOTER')
        except Exception as error:
            msgerror = "%s -> %s" % (doc, error)
            self.log.error("[BUILDER] - %s", msgerror)
            html = ''
            raise

        return html

    def get_doc_card(self, doc):
        """Get card for a given doc"""
        DOC_CARD = self.template('CARD_DOC')
        DOC_CARD_FOOTER = self.template('CARD_DOC_FOOTER')
        LINK = self.template('LINK')
        title = self.srvdtb.get_values(doc, 'Title')[0]
        category = self.srvdtb.get_values(doc, 'Category')[0]
        scope = self.srvdtb.get_values(doc, 'Scope')[0]
        link_title = LINK % ("uk-link-heading uk-text-meta", "%s.html" % valid_filename(doc).replace('.adoc', ''), "", title)
        if len(category) > 0 and len(scope) > 0:
            link_category = LINK % ("uk-link-heading uk-text-meta", "Category_%s.html" % valid_filename(category), "", category)
            link_scope = LINK % ("uk-link-heading uk-text-meta", "Scope_%s.html" % valid_filename(scope), "", scope)
            footer = DOC_CARD_FOOTER % (link_category, link_scope)
        else:
            footer = ''

        timestamp = self.srvdtb.get_doc_timestamp(doc)
        fuzzy_date = fuzzy_date_from_timestamp(timestamp)

        tooltip = "%s" % (title)
        return DOC_CARD % (tooltip, link_title, timestamp, fuzzy_date, footer)

    def get_labels(self, values):
        """C0111: Missing function docstring (missing-docstring)."""
        label_links = ''
        value_link = self.template('METADATA_VALUE_LINK')
        for page, text in values:
            if len(text) != 0:
                label_links += value_link % (valid_filename(page), text)
        return label_links

    def create_page_about_app(self):
        """
        About app page.
        To be replaced by custom code.
        """
        page = self.template('PAGE_ABOUT_APP')
        srcdir = self.srvapp.get_source_path()
        about = os.path.join(srcdir, 'about.adoc')
        try:
            content = open(about, 'r').read()
        except:
            content = 'No info available'
        self.distribute('about_app', page % content)

    def create_page_about_theme(self):
        """About theme page."""
        page = self.template('PAGE_ABOUT_THEME')
        theme = self.srvapp.get_theme_properties()
        self.distribute('about_theme', page % (theme['name'], theme['description'], theme['version']))

    def create_page_about_kb4it(self):
        """About KB4IT page."""
        page = self.template('PAGE_ABOUT_KB4IT')
        self.distribute('about_kb4it', page % APP['version'])

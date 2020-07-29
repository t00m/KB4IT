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

from mako.template import Template


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
            try:
                fpag.write(content)
            except:
                raise
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
        try:
            with open(PAGE_PATH, 'w') as fpag:
                fpag.write(content)
                self.log.debug("[BUILDER] - PAGE[%s] distributed to source path", name)
        except OSError as error:
            self.log.error(error)

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
                self.log.debug("[BUILDER] - THEME['%s'] TPL['%s'] loaded", theme['id'], template)
            else:
                current_theme = 'default'
                theme_default = os.path.join(GPATH['THEMES'], os.path.join('default', 'templates'))
                template_path = os.path.join(theme_default, "%s.tpl" % template)

                if os.path.exists(template_path):
                    self.log.debug("[BUILDER] - THEME['default'] TPL['%s'] loaded", template)
                else:
                    self.log.error("[BUILDER] - TPL['%s'] not found. Exit.", template)
                    sys.exit()

            # If template found, add it to cache. Otherwise, exit.
            try:
                TEMPLATES[template] = Template(filename=template_path)
                return TEMPLATES[template]
            except FileNotFoundError as error:
                self.log.error("[BUILDER] - %s", error)
                sys.exit()

    def render_template(self, name):
        tpl = self.template(name)
        return tpl.render()

    def get_mako_var(self):
        var = {}
        var['theme'] = self.srvapp.get_theme_properties()
        return var

    def build_page(self, future):
        """
        Build the final HTML Page

        At this point, the Builder receives an HTML page but without
        header/footer. Then, it finishes the page.
        """
        THEME_ID = self.srvapp.get_theme_property('id')
        HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
        HTML_HEADER_DOC = self.template('HTML_HEADER_DOC')
        HTML_HEADER_NODOC = self.template('HTML_HEADER_NODOC')
        HTML_FOOTER = self.template('HTML_FOOTER')
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
                var = self.get_mako_var()
                # ~ var['page'] = {}
                # ~ var['page']['brand'] = 't00mlabs'
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
                        var['content'] = toc
                        TPL_HTML_HEADER_MENU_CONTENTS_ENABLED = self.template('HTML_HEADER_MENU_CONTENTS_ENABLED')
                        HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_ENABLED.render(var=var)
                    else:
                        TPL_HTML_HEADER_MENU_CONTENTS_DISABLED = self.template('HTML_HEADER_MENU_CONTENTS_DISABLED')
                        HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_DISABLED.render()

                    userdoc = os.path.join(os.path.join(self.srvapp.get_source_path(), basename))

                    var['title'] = title
                    # ~ var['page']['description'] = var['theme']['description']
                    # ~ var['page']['author'] = var['theme']['author']
                    # ~ var['page']['language'] = 'en'
                    # ~ var['page']['title'] = title
                    # ~ var['page']['brand'] = var['theme']['brand']
                    var['menu_contents'] = HTML_TOC
                    var['basename'] = basename
                    var['timestamp'] = timestamp
                    if os.path.exists(userdoc):
                        source_code = open(userdoc, 'r').read()
                        var['source_code'] = source_code
                        self.srvthm = self.get_service('Theme')
                        meta_section = self.srvthm.create_metadata_section(basename)
                        var['meta_section'] = meta_section
                        PAGE = HTML_HEADER_COMMON.render(var=var) + HTML_HEADER_DOC.render(var=var)
                        fhtm.write(PAGE)
                    else:
                        PAGE = HTML_HEADER_COMMON.render(var=var) + HTML_HEADER_NODOC.render(var=var)
                        fhtm.write(PAGE)
                    fhtm.write(content)

                    fhtm.write(HTML_FOOTER.render(var=var))
                os.remove(htmldoctmp)
                return x

    def build_pagination(self, pagination):
        """
        Create a page with documents.
        If amount of documents is greater than 100, split it in several pages
        """
        # ~ print("PG. TPL: %s" % pagination['template'])
        TPL_PG_HEAD = self.template(pagination['template'])
        var = {}

        # Pagination title
        if pagination['title'] is None:
            var['title'] = pagination['basename'].replace('_', ' ')
        else:
            var['title'] = pagination['title']

        # Pagination basename
        var['basename'] = pagination['basename']

        # Number of related docs
        var['num_rel_docs'] = len(pagination['doclist'])

        # List of pages returned
        pagelist = []

        # Calculate k:
        # k = 1 if number of documents < 100
        # k = 12 if all documents fit in <= 10 pages
        # k > 12 to fit all documents in 10 pages
        if var['num_rel_docs'] < 100:
            total_pages = 1
            k = math.ceil(var['num_rel_docs'] / total_pages)
        else:
            k = 12
            total_pages = math.ceil(var['num_rel_docs'] / k)
            if total_pages > 10:
                total_pages = 10
                k = math.ceil(var['num_rel_docs'] / total_pages)
                row = k % 3  # Always display rows with 3 elements at list
                while row != 0:
                    k += 1
                    row = k % 3
                total_pages = math.ceil(var['num_rel_docs'] / k)
            elif total_pages == 0:
                total_pages = 1
                k = math.ceil(var['num_rel_docs'] / total_pages)
        var['k'] = k
        var['total'] = total_pages

        var['pg-head-items'] = ''
        for current_page in range(total_pages):
            # ~ PAGINATION = self.template('PAGINATION_START')
            page = {}
            page['num'] = current_page
            # ~ page['pg-head-items'] = ''
            if total_pages > 0:
                for i in range(total_pages):
                    start = k * i  # lower limit
                    end = k * i + k  # upper limit
                    if i == current_page:
                        if total_pages - 1 == 0:
                            pagination_none = self.template('PAGINATION_NONE')
                            var['pg-head-items'] += pagination_none.render()
                        else:
                            TPL_PAGINATION_PAGE_ACTIVE = self.template('PAGINATION_PAGE_ACTIVE')
                            page = {}
                            page['page_num'] = i
                            page['page_start'] = start
                            page['page_end'] = end
                            page['page_count_docs'] = var['num_rel_docs']
                            var['pg-head-items'] +=  TPL_PAGINATION_PAGE_ACTIVE.render(var=page)
                        cstart = start
                        cend = end
                    else:
                        if i == 0:
                            PAGE = "%s.adoc" % pagination['basename']
                        else:
                            PAGE = "%s-%d.adoc" % (pagination['basename'], i)
                        TPL_PAGINATION_PAGE_INACTIVE = self.template('PAGINATION_PAGE_INACTIVE')
                        page = {}
                        page['page_num'] = i
                        page['page_start'] = start
                        page['page_end'] = end
                        page['page_count_docs'] = var['num_rel_docs']
                        page['page_link'] = PAGE.replace('adoc', 'html')
                        var['pg-head-items'] +=  TPL_PAGINATION_PAGE_INACTIVE.render(var=page) #i, start, end, num_rel_docs, PAGE.replace('adoc', 'html'), i)
            # ~ PAGINATION += self.template('PAGINATION_END')

            if current_page == 0:
                name = "%s" % pagination['basename']
            else:
                name = "%s-%d" % (pagination['basename'], current_page)
            ps = cstart
            pe = cend

            if pe > 0:
                # get build_cardset custom function or default
                custom_build_cardset = "self.%s" % pagination['function']
                var['pg-body-items'] = eval(custom_build_cardset)(pagination['doclist'][ps:pe])
            else:
                var['pg-body-items'] = ""

            html = TPL_PG_HEAD.render(var=var)
            if not pagination['fake']:
                self.distribute(name, html)
                # ~ print(html)
                # ~ print(var)
            pagelist.append(name)

        self.log.debug("[BUILDER] - Created pagination page '%s' (%d pages with %d cards in each page)", pagination['basename'], total_pages, k)

        return pagelist

    def build_cardset(self, doclist):
        """Default method to build pages paginated"""
        CARD_DOC_FILTER_DATA_TITLE = self.template('CARD_DOC_FILTER_DATA_TITLE')
        CARDS = ""
        for doc in doclist:
            title = self.srvdtb.get_values(doc, 'Title')[0]
            card = self.get_doc_card(doc)
            var = {}
            var['data-title'] = valid_filename(title)
            var['card_doc'] = card
            card_search_filter = CARD_DOC_FILTER_DATA_TITLE.render(var=var)
            CARDS += card_search_filter
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
            TPL_WORDCLOUD = self.template('WORDCLOUD')
            var = {}
            var['items'] = []
            # ~ html_items = ''
            for word in lwords:
                frequency = len(dkeyurl[word])
                size = get_font_size(frequency, max_frequency)
                url = "%s_%s.html" % (valid_filename(key), valid_filename(word))
                tooltip = "%d documents" % frequency
                item = {}
                item['url'] = url
                item['tooltip'] = tooltip
                item['size'] = size
                item['word'] = word
                var['items'].append(item)
            html = TPL_WORDCLOUD.render(var=var)
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
        TPL_PAGE_HELP = self.template('PAGE_HELP')
        self.distribute('help', TPL_PAGE_HELP.render())

    def create_page_index(self):
        """Create index page.
        To be replaced by custom code.
        """
        srcdir = self.srvapp.get_source_path()
        custom_index = os.path.join(srcdir, 'index.adoc')
        if not os.path.exists(custom_index):
            TPL_INDEX = self.template('PAGE_INDEX')
            var = {}
            var['title'] = 'Index'
            var['theme'] = self.srvapp.get_theme_properties()
            self.distribute('index', TPL_INDEX.render(var=var))

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
        var = {}
        var['buttons'] = []
        for key in all_keys:
            ignored_keys = self.srvdtb.get_ignored_keys()
            if key not in ignored_keys:
                vbtn = {}
                vbtn['content'] = self.create_tagcloud_from_key(key)
                values = self.srvdtb.get_all_values_for_key(key)
                frequency = len(values)
                size = get_font_size(frequency, max_frequency)
                proportion = int(math.log((frequency * 100) / max_frequency))
                vbtn['key'] = key
                vbtn['vfkey'] = valid_filename(key)
                vbtn['size'] = size
                vbtn['tooltip'] = "%d values" % len(values)
                button = TPL_KEY_MODAL_BUTTON.render(var=vbtn) # % (valid_filename(key), tooltip, size, key, valid_filename(key), valid_filename(key), key, html)
                var['buttons'].append(button)
        content = TPL_PROPS_PAGE.render(var=var)
        # ~ print(content)
        self.distribute('properties', content)

    def create_page_stats(self):
        """Create stats page"""
        TPL_PAGE_STATS = self.template('PAGE_STATS')
        # ~ TPL_ITEM = self.template('KEY_LEADER_ITEM')
        var = {}
        var['count_docs'] = self.srvapp.get_numdocs()
        keys = self.srvdtb.get_all_keys()
        var['count_keys'] = len(keys)
        var['leader_items'] = []
        for key in keys:
            values = self.srvdtb.get_all_values_for_key(key)
            item = {}
            item['key'] = key
            item['vfkey'] = valid_filename(key)
            item['count_values'] = len(values)
            var['leader_items'].append(item)
        stats = TPL_PAGE_STATS.render(var=var)
        self.distribute('stats', stats)


    def create_page_key(self, key, values):
        """Create key page."""
        TPL_PAGE_KEY = self.template('PAGE_KEY')
        var = {}

        # Title
        var['title'] = key

        # Tab Cloud
        cloud = self.create_tagcloud_from_key(key)

        # Tab Leader
        stats = ""
        var['leader'] = []
        for value in values:
            item = {}
            docs = self.srvdtb.get_docs_by_key_value(key, value)
            item['count'] = len(docs)
            item['vfkey'] = valid_filename(key)
            item['vfvalue'] = valid_filename(value)
            item['name'] = value
            var['leader'].append(item)
        var['cloud'] = cloud
        html = TPL_PAGE_KEY.render(var=var)
        return html

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
            TPL_METADATA_SECTION = self.template('METADATA_SECTION')
            custom_keys = self.srvdtb.get_custom_keys(doc)
            var = {}
            var['items'] = []
            for key in custom_keys:
                ckey = {}
                ckey['doc'] = doc
                ckey['key'] = key
                ckey['vfkey'] = valid_filename(key)
                try:
                    values = self.get_html_values_from_key(doc, key)
                    ckey['labels'] = self.get_labels(values)
                    var['items'].append(ckey)
                except Exception as error:
                    self.log.error("[BUILDER] - Key[%s]: %s", key, error)
                    raise
            var['timestamp'] = self.srvdtb.get_doc_timestamp(doc)
            html = TPL_METADATA_SECTION.render(var=var)
        except Exception as error:
            msgerror = "%s -> %s" % (doc, error)
            self.log.error("[BUILDER] - %s", msgerror)
            html = ''
            raise
        return html

    def get_doc_card(self, doc):
        """Get card for a given doc"""
        var = {}
        TPL_DOC_CARD = self.template('CARD_DOC')
        TPL_DOC_CARD_CLASS = self.template('CARD_DOC_CLASS')
        LINK = self.template('LINK')

        title = self.srvdtb.get_values(doc, 'Title')[0]
        var['category'] = self.srvdtb.get_values(doc, 'Category')[0]
        var['scope'] = self.srvdtb.get_values(doc, 'Scope')[0]
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
            sco['url'] = "Scope_%s.html" % valid_filename(var['scope'])
            sco['title'] = var['scope']
            var['link_scope'] = LINK.render(var=sco)
        else:
            var['link_category'] = ''
            var['link_scope'] = ''

        var['timestamp'] = self.srvdtb.get_doc_timestamp(doc)
        var['fuzzy_date'] = fuzzy_date_from_timestamp(var['timestamp'])
        var['tooltip'] = title
        DOC_CARD = TPL_DOC_CARD.render(var=var)
        # ~ self.log.error(DOC_CARD)
        return DOC_CARD

    def get_labels(self, values):
        """C0111: Missing function docstring (missing-docstring)."""
        var = {}
        label_links = ''
        TPL_METADATA_VALUE_LINK = self.template('METADATA_VALUE_LINK')
        for page, text in values:
            var['link_url'] = valid_filename(page)
            var['link_name'] = text
            if len(text) != 0:
                label_links += TPL_METADATA_VALUE_LINK.render(var=var)
        return label_links

    def create_page_about_app(self):
        """
        About app page.
        To be replaced by custom code.
        """
        PAGE_ABOUT_APP = self.template('PAGE_ABOUT_APP')
        srcdir = self.srvapp.get_source_path()
        about = os.path.join(srcdir, 'about.adoc')
        var = {}
        try:
            var['content'] = open(about, 'r').read()
        except:
            var['content'] = 'No info available'
        self.distribute('about_app', PAGE_ABOUT_APP.render(var=var))

    def create_page_about_theme(self):
        """About theme page."""
        TPL_PAGE_ABOUT_THEME = self.template('PAGE_ABOUT_THEME')
        var = {}
        var['theme'] = self.srvapp.get_theme_properties()
        content = TPL_PAGE_ABOUT_THEME.render(var=var)
        self.distribute('about_theme', content)

    def create_page_about_kb4it(self):
        """About KB4IT page."""
        TPL_PAGE_ABOUT_KB4IT = self.template('PAGE_ABOUT_KB4IT')
        var = {}
        var['kb4it_version'] = APP['version']
        self.distribute('about_kb4it', TPL_PAGE_ABOUT_KB4IT.render(var=var))

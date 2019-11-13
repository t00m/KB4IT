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
# ~ import datetime as dt
from datetime import datetime
from kb4it.src.core.mod_srv import Service
from kb4it.src.services.srv_db import HEADER_KEYS
from kb4it.src.core.mod_utils import template, valid_filename, get_labels
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
        self.tmpdir = self.srvapp.get_temp_dir()

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
        for doc in self.srvdtb.get_database():
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
                item = WORDCLOUD_ITEM % (url, size, word)
                items += item
            html = WORDCLOUD % items
        else:
            html = ''

        return html

    def create_index_all(self):
        """Missing method docstring."""
        docname = "%s/all.adoc" % (self.tmpdir)
        docdict = {}
        doclist = []
        for doc in self.srvdtb.get_database():
            title = self.srvdtb.get_values(doc, 'Title')[0]
            doclist.append(title)
            docdict[title] = doc
        doclist.sort(key=lambda y: y.lower())

        with open(docname, 'w') as fall:
            fall.write("= All documents\n\n")
            for title in doclist:
                fall.write(". <<%s#,%s>>\n" % (os.path.basename(valid_filename(docdict[title])[:-5]), title))

    def create_category_filter(self, categories):
        """Missing method docstring."""
        pass

    def create_index_page(self):
        """Missing method docstring."""
        TPL_INDEX = template('INDEX')
        TPL_KEY_MODAL_BUTTON = template('KEY_MODAL_BUTTON')

        # Breadcrumb
        now = datetime.now()
        mtime = now.strftime("%Y/%m/%d %H:%M")
        numdocs = self.srvapp.get_numdocs()

        # Core Modal buttons
        core_buttons = ''
        for key in sorted(HEADER_KEYS, key=lambda y: y.lower()):
            html = self.create_tagcloud_from_key(key)
            button = TPL_KEY_MODAL_BUTTON % (key, key, key, key, key, html)
            # ~ buttons += button.replace('++++', '')
            core_buttons += button

        # Core Modal buttons
        all_keys = self.srvdtb.get_all_keys()
        custom_buttons = ''
        for key in all_keys:
            if key not in HEADER_KEYS:
                html = self.create_tagcloud_from_key(key)
                button = TPL_KEY_MODAL_BUTTON % (key, key, key, key, key, html)
                # ~ buttons += button.replace('++++', '')
                custom_buttons += button

        # TAB Stats
        stats = template('INDEX_TAB_STATS')
        item = template('KEY_LEADER_ITEM')
        numdocs = self.srvapp.get_numdocs()
        keys = self.srvdtb.get_all_keys()
        numkeys = len(keys)
        leader_items = ''
        for key in keys:
            values = self.srvdtb.get_all_values_for_key(key)
            leader_items += item % (valid_filename(key), key, valid_filename(key), len(values))
        tab_stats = stats % (numdocs, numkeys, leader_items)
        with open('%s/index.adoc' % self.tmpdir, 'w') as findex:
            content = TPL_INDEX % (mtime, core_buttons, custom_buttons, tab_stats)
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


    # ~ def create_recents_page(self):
        # ~ """Create recents page.

        # ~ In order this page makes sense, this script should be
        # ~ executed periodically from crontab.
        # ~ """
        # ~ docname = "%s/%s" % (self.tmpdir, 'recents.adoc')
        # ~ with open(docname, 'w') as frec:
            # ~ relset = set()
            # ~ today = datetime.now()
            # ~ lastweek = today - dt.timedelta(weeks=1)
            # ~ lastmonth = today - dt.timedelta(days=31)
            # ~ strtoday = "%d-%02d-%02d" % (today.year, today.month, today.day)

            # ~ # TODAY
            # ~ docs = self.srvdtb.subjects(RDF['type'], URIRef(KB4IT['Document']))
            # ~ for doc in docs:
                # ~ revdate = self.srvdtb.value(doc, 'Revdate')
                # ~ if revdate == Literal(strtoday):
                    # ~ relset.add(doc)

            # ~ page = '= Last documents added\n\n'
            # ~ page += '== Today (%d)\n\n' % len(relset)
            # ~ page += """[options="header", width="100%", cols="60%,20%,20%"]\n"""
            # ~ page += "|===\n"
            # ~ page += "|Document |Category | Status\n"

            # ~ for doc in relset:
                # ~ title = self.srvdtb.value(doc, 'Title'])
                # ~ category = self.srvdtb.value(doc, 'Category'])
                # ~ status = self.srvdtb.value(doc, 'Status'])
                # ~ page += "|<<%s#,%s>>\n" % (doc, quote(title))
                # ~ page += "|<<Category_%s.adoc#,%s>>\n" % (category, quote(category))
                # ~ page += "|<<Status_%s.adoc#,%s>>\n" % (status, status)

            # ~ page += "|==="

            # ~ # WEEK
            # ~ for doc in docs:
                # ~ revdate = datetime.strptime(self.srvdtb.value(doc, 'Revdate']), "%Y-%m-%d")
                # ~ if revdate <= today and revdate >= lastweek:
                    # ~ relset.add(doc)

            # ~ page += '\n\n== This week (%d)\n\n' %  len(relset)
            # ~ page += """[options="header", width="100%", cols="60%,20%,20%"]\n"""
            # ~ page += "|===\n"
            # ~ page += "|Document |Category | Status\n"
            # ~ for doc in relset:
                # ~ title = self.srvdtb.value(doc, 'Title'])
                # ~ category = self.srvdtb.value(doc, 'Category'])
                # ~ status = self.srvdtb.value(doc, 'Status'])
                # ~ page += "|<<%s#,%s>>\n" % (doc, quote(title))
                # ~ page += "|<<%s#,%s>>\n" % (doc, quote(category))
                # ~ page += "|<<%s#,%s>>\n" % (doc, quote(status))
            # ~ page += "|==="

            # ~ # MONTH
            # ~ for doc in docs:
                # ~ revdate = datetime.strptime(self.srvdtb.value(doc, 'Revdate']), "%Y-%m-%d")
                # ~ if revdate <= today and revdate >= lastmonth:
                    # ~ relset.add(doc)

            # ~ page += '\n\n== This month (%d)\n\n' % len(relset)
            # ~ page += """[options="header", width="100%", cols="60%,20%,20%"]\n"""
            # ~ page += "|===\n"
            # ~ page += "|Document |Category | Status\n"
            # ~ for doc in relset:
                # ~ title = self.srvdtb.value(doc, 'Title'])
                # ~ category = self.srvdtb.value(doc, 'Category'])
                # ~ status = self.srvdtb.value(doc, 'Status'])
                # ~ page += "|<<%s#,%s>>\n" % (doc, quote(title))
                # ~ page += "|<<%s#,%s>>\n" % (doc, quote(category))
                # ~ page += "|<<%s#,%s>>\n" % (doc, quote(status))
            # ~ page += "|===\n\n"
            # ~ frec.write(page)

    def create_key_page(self, key, values):
        """Missing method docstring."""
        html = template('KEY_PAGE')
        source_dir = self.srvapp.get_source_path()

        # TAB Filter
        key_filter = template('PROPERTY_FILTER')

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

        key_filter = key_filter % (key_filter_header_rows, key_filter_docs)


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

        return html % (key, key_filter, cloud, stats)

    def create_metadata_section(self, doc):
        """Return a html block for displaying core and custom keys."""
        try:
            doc_path = os.path.join(self.srvapp.get_source_path(), doc)
            html = template('METADATA_SECTION_HEADER')
            author = self.srvdtb.get_html_values_from_key(doc, 'Author')
            category = self.srvdtb.get_html_values_from_key(doc, 'Category')
            scope = self.srvdtb.get_html_values_from_key(doc, 'Scope')
            status = self.srvdtb.get_html_values_from_key(doc, 'Status')
            team = self.srvdtb.get_html_values_from_key(doc, 'Team')
            priority = self.srvdtb.get_html_values_from_key(doc, 'Priority')
            tags = self.srvdtb.get_html_values_from_key(doc, 'Tag')

            METADATA_SECTION_BODY = template('METADATA_SECTION_BODY')
            html += METADATA_SECTION_BODY % (get_labels(author), get_labels(category), \
                                            get_labels(scope), get_labels(team), \
                                            get_labels(status), get_labels(priority), \
                                            get_labels(tags))

            custom_keys = self.srvdtb.get_custom_keys(doc)
            custom_props = ''
            for key in custom_keys:
                values = self.srvdtb.get_html_values_from_key(doc, key)
                labels = get_labels(values)
                row_custom_prop = template('METADATA_ROW_CUSTOM_PROPERTY')
                custom_props += row_custom_prop % (valid_filename(key), key, labels)

            num_custom_props = len(custom_props)
            if  num_custom_props > 0:
                html += custom_props

            METADATA_SECTION_FOOTER = template('METADATA_SECTION_FOOTER')
            source_dir = self.srvapp.get_source_path()
            source_path = os.path.join(source_dir, doc)
            html += METADATA_SECTION_FOOTER % (doc, \
                                               open(source_path, 'r').read())
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
        # ~ for doc in self.srvdtb.get_database():
            # ~ title = self.srvdtb.get_values(doc, 'Title')[0]
            # ~ doc_card = self.get_doc_card(doc)
            # ~ card_search_filter = DOC_CARD_FILTER_DATA_TITLE % (valid_filename(title), doc_card)
            # ~ html += """%s""" % card_search_filter

        # ~ with open(search_page, 'w') as fsp:
            # ~ tpl = template('PAGE_SEARCH')
            # ~ fsp.write(tpl % html)


    def get_doc_card(self, doc):
        source_dir = self.srvapp.get_source_path()
        DOC_CARD = template('DOC_CARD')
        DOC_CARD_LINK = template('DOC_CARD_LINK')
        title = self.srvdtb.get_values(doc, 'Title')[0]
        category = self.srvdtb.get_values(doc, 'Category')[0]
        scope = self.srvdtb.get_values(doc, 'Scope')[0]
        team = self.srvdtb.get_values(doc, 'Team')[0] # Only first match?
        author = self.srvdtb.get_values(doc, 'Author')[0]
        icon_path = get_author_icon(source_dir, author)
        self.log.debug("Author: %s -> %s", author, icon_path)
        if icon_path == "resources/images/authors/author_unknown.png":
            self.missing_icons[author] = os.path.join(source_dir, "%s.png" % valid_filename(author))
        link_title = DOC_CARD_LINK % (valid_filename(doc).replace('.adoc', ''), title)
        link_category = DOC_CARD_LINK % ("Category_%s" % valid_filename(category), category)
        link_scope = DOC_CARD_LINK % ("Scope_%s" % valid_filename(scope), scope)
        link_team = DOC_CARD_LINK % ("Team_%s" % valid_filename(team), team)
        link_author = DOC_CARD_LINK % ("Author_%s" % valid_filename(author), author)
        return DOC_CARD % (link_title, icon_path)


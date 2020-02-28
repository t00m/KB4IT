#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: techdoc theme scripts
"""

from pprint import pprint
from kb4it.src.core.mod_utils import get_human_datetime, fuzzy_date_from_timestamp
from kb4it.src.core.mod_utils import valid_filename, get_human_datetime
from kb4it.src.services.srv_builder import Builder

MONTH = {
            '01': 'January',
            '02': 'February',
            '03': 'March',
            '04': 'April',
            '05': 'May',
            '06': 'June',
            '07': 'July',
            '08': 'August',
            '09': 'September',
            '10': 'October',
            '11': 'November',
            '12': 'December',
        }

class Theme(Builder):
    def hello(self):
        self.log.debug("This is the theme techdoc")

    def build(self):
        self.create_about_page()
        self.create_help_page()
        self.create_all_keys_page()
        self.create_properties_page()
        self.create_stats_page()
        self.create_index_all()
        self.create_index_page()
        self.create_bookmarks_page()
        self.create_events_page()
        # ~ self.create_blog_page()
        self.create_recents_page()

    def get_doc_card_event(self, doc):
        source_dir = self.srvapp.get_source_path()
        DOC_CARD = self.template('CARD_DOC_EVENT')
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
        tooltip ="%s" % (title)
        return DOC_CARD % (tooltip, link_title, timestamp, fuzzy_date, footer)

    def build_events(self, doclist):
        self.log.debug("\t\t\t  Using custom build cardset function for events")
        CARDS = ""
        events = {}
        years = []
        months = []
        for doc in doclist:
            props = self.srvdtb.get_doc_properties(doc)
            timestamp = props['Timestamp']
            year = "%4d" % timestamp.year
            month = "%4d%02d" % (timestamp.year, timestamp.month)

            if not year in years:
                years.append(year)

            if not month in months:
                months.append(month)

            try:
                docs = events[year]
                docs.append(doc)
                events[year] = docs
            except:
                events[year] = []

            try:
                docs = events[month]
                docs.append(doc)
                events[month] = docs
            except:
                events[month] = []

        HTML = "" #self.template('BLOCK_EVENT_START')
        for year in years:
            self.build_pagination('docs-year-%s' % year, events[year], optional_title="Posted on %s" % year)
            EVENT_ROW_YEAR_START = self.template('BLOCK_EVENT_ROW_YEAR_START')
            HTML += EVENT_ROW_YEAR_START % (year, year)
            for month in months:
                if month.startswith(year):
                    self.build_pagination('docs-month-%s' % month, events[month], optional_title="Posted on %s %s" % (MONTH[month[4:]], year))
                    EVENT_ROW_MONTH_START = self.template('BLOCK_EVENT_ROW_MONTH_START')
                    HTML += EVENT_ROW_MONTH_START % (month, MONTH[month[4:]])
                    HTML += """<div class="uk-child-width-expand@s" uk-grid>"""
                    for doc in events[month]:
                        title = self.srvdtb.get_values(doc, 'Title')[0]
                        timestamp = self.srvdtb.get_values(doc, 'Timestamp')
                        CARD = self.get_doc_card_event(doc)
                        HTML += CARD
                        # ~ HTML += """\t\t\t<li class="uk-card uk-card-body uk-card-hover"><span class="uk-text-lead">%s - %s</span></li>\n""" % (timestamp, title)
                    HTML += "</div>\n"
            HTML += "\t</div></div>\n"
            HTML += """<div class="uk-card uk-card-body"></div>"""
        self.log.debug(HTML)
        return HTML

    # ~ def create_blog_page(self):
        # ~ doclist = []
        # ~ for doc in self.srvdtb.get_documents():
            # ~ category = self.srvdtb.get_values(doc, 'Category')[0]
            # ~ if category == 'Post':
                # ~ doclist.append(doc)
        # ~ self.build_pagination('blog', doclist, 'Blog', "build_events", "PAGE_PAGINATION_HEAD_EVENT")

    def create_events_page(self):
        doclist = set()
        for doc in self.srvdtb.get_documents():
            category = self.srvdtb.get_values(doc, 'Category')[0]
            if category == 'Event':
                doclist.add(doc)
        self.build_pagination('events', doclist, 'Events', "build_events", "PAGE_PAGINATION_HEAD_EVENT")

    def create_recents_page(self):
        """Create recents page."""
        doclist = self.srvdtb.get_documents()[:60]
        self.build_pagination('recents', doclist, 'Recents')

    def create_bookmarks_page(self):
        """Create bookmarks page."""
        doclist = []
        for doc in self.srvdtb.get_documents():
            bookmark = self.srvdtb.get_values(doc, 'Bookmark')[0]
            if bookmark == 'Yes' or bookmark == 'True':
                doclist.append(doc)
        self.build_pagination('bookmarks', doclist, 'Bookmarks')
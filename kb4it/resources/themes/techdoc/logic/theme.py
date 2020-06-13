#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: techdoc theme scripts
"""

import calendar
from calendar import HTMLCalendar
from datetime import datetime

from kb4it.services.builder import KB4ITBuilder
from kb4it.core.util import get_human_datetime, fuzzy_date_from_timestamp
from kb4it.core.util import valid_filename, get_human_datetime, guess_datetime
from evcal import EventsCalendar


class Theme(KB4ITBuilder):
    # ~ def initialize(self):
        # ~ self.log.debug("Hi, Ich bin Thema 'techdoc'")

    def generate_sources(self):
        self.log.warning("Oikos shouldn't call this method...")

    def build(self):
        self.create_page_about_app()
        self.create_page_about_theme()
        self.create_page_about_kb4it()
        self.create_page_help()
        self.create_page_properties()
        self.create_page_stats()
        self.create_page_index_all()
        self.create_page_index()
        self.create_page_bookmarks()
        self.create_page_authors()
        self.app.register_service('EvCal', EventsCalendar())
        self.srvcal = self.get_service('EvCal')
        self.create_page_events()
        # ~ self.create_page_blog()
        self.create_page_recents()

    def get_doc_card_event(self, doc):
        source_dir = self.srvapp.get_source_path()
        DOC_CARD = self.template('CARD_DOC_EVENT')
        DOC_CARD_FOOTER = self.template('CARD_DOC_FOOTER')
        LINK = self.template('LINK')
        title = self.srvdtb.get_values(doc, 'Title')[0]
        category = self.srvdtb.get_values(doc, 'Category')[0]
        scope = self.srvdtb.get_values(doc, 'Scope')[0]
        link_title = DOC_CARD_LINK % (valid_filename(doc).replace('.adoc', ''), title)
        if len(category) > 0 and len(scope) >0:
            link_category = LINK % ("uk-link-heading uk-text-meta", "Category_%s.html" % valid_filename(category), "", category)
            link_scope = LINK % ("uk-link-heading uk-text-meta", "Scope_%s.html" % valid_filename(scope), "", scope)
            footer = DOC_CARD_FOOTER % (link_category, link_scope)
        else:
            footer = ''

        timestamp = self.srvdtb.get_doc_timestamp(doc)
        fuzzy_date = fuzzy_date_from_timestamp(timestamp)
        tooltip ="%s" % (title)
        return DOC_CARD % (tooltip, link_title, timestamp, fuzzy_date, footer)

    def build_events(self, doclist):
        SORT = self.srvapp.get_runtime_parameter('sort_attribute')
        # ~ self.log.debug("\t\t\t  Using custom build cardset function for events")
        dey = {} # Dictionary of day events per year
        events_docs = {} # Dictionary storing a list of docs for a given date
        events_docs_html = {}

        # Get events dates
        for doc in doclist:
            props = self.srvdtb.get_doc_properties(doc)
            timestamp = self.srvdtb.get_doc_timestamp(doc)
            # Build dict of events for a given date as a list of tuples
            # (month, day) indexed by year
            # Also, build a dict to store those docs ocurring in that date
            try:
                timestamp = guess_datetime(timestamp)
                y = timestamp.year
                m = timestamp.month
                d = timestamp.day
                try:
                    days_events = dey[y]
                    days_events.append((m, d))
                except:
                    days_events = []
                    days_events.append((m, d))
                    dey[y] = days_events

                # Build dict of documents
                if not y in events_docs:
                    events_docs[y] = {}
                    events_docs_html[y] = {}

                if not m in events_docs[y]:
                    events_docs[y][m] = {}
                    events_docs_html[y][m] = {}

                if not d in events_docs[y][m]:
                    events_docs[y][m][d] = []
                    events_docs_html[y][m][d] = ''

                docs = events_docs[y][m][d]
                docs.append(doc)
                events_docs[y][m][d] = docs
            except Exception as error:
                # Doc doesn't have a valid date field. Skip it.
                self.log.error(error)
                raise
                # ~ pass

        # Build day event pages
        for year in events_docs:
            for month in events_docs[year]:
                for day in events_docs[year][month]:
                    docs = events_docs[year][month][day]
                    edt = guess_datetime("%4d.%02d.%02d" % (year, month, day))
                    title = edt.strftime("Events on %A, %B %d %Y")
                    EVENT_PAGE_DAY = "events_%4d%02d%02d" % (year, month, day)

                    # create html page
                    self.build_pagination(EVENT_PAGE_DAY, docs, title)

                    # Generate HTML to display into the modal window
                    # ~ events_docs_html[y][m][d] = self.build_html_events(docs)

        # Build month event pages
        for year in events_docs:
            for month in events_docs[year]:
                thismonth = []
                edt = guess_datetime("%4d.%02d.01" % (year, month))
                title = edt.strftime("Events on %B, %Y")
                EVENT_PAGE_MONTH = "events_%4d%02d" % (year, month)
                for day in events_docs[year][month]:
                    thismonth.extend(events_docs[year][month][day])

                # create html page
                self.build_pagination(EVENT_PAGE_MONTH, thismonth, title)

        for year in sorted(dey.keys(), reverse=True):
            HTML = self.srvcal.build_year_pagination(dey.keys())
            edt = guess_datetime("%4d.01.01" % year)
            title = edt.strftime("Events on %Y")
            PAGE = self.template('PAGE_EVENTS_YEAR')
            EVENT_PAGE_YEAR = "events_%4d" % year
            self.srvcal.set_events_days(dey[year])
            self.srvcal.set_events_docs(events_docs[year])
            self.srvcal.set_events_html(events_docs_html[year])
            HTML += self.srvcal.formatyearpage(year, 4)
            self.distribute(EVENT_PAGE_YEAR, PAGE % (title, HTML))

        return dey

    def load_events_days(self, events_days, year):
        events_set = set()
        for event_day in events_days:
            events_set.add(event_day)

        for month, day in events_set:
            adate = guess_datetime("%d.%02d.%02d" % (year, month, day))
            # ~ self.log.debug(adate)

    def create_page_events(self):
        self.log.debug("\t\tBuilding events")
        doclist = []
        ecats = {}
        theme = self.srvapp.get_theme_properties()
        try:
            event_types = theme['events']
        except:
            event_types = []
        self.log.info("\t\tEvent types registered for this theme: %s", ', '.join(event_types))
        for doc in self.srvdtb.get_documents():
            category = self.srvdtb.get_values(doc, 'Category')[0]
            if category in event_types:
                try:
                    docs = ecats[category]
                    docs.add(doc)
                    ecats[category] = docs
                except:
                    docs = set()
                    docs.add(doc)
                    ecats[category] = docs

                doclist.append(doc)
                title = self.srvdtb.get_values(doc, 'Title')[0]
        dey = self.build_events(doclist)
        HTML = self.srvcal.build_year_pagination(dey.keys())
        page = self.template('PAGE_EVENTS')
        self.distribute('events', page % HTML)

    def create_page_recents(self):
        """Create recents page."""
        doclist = self.srvdtb.get_documents()[:60]
        self.build_pagination('recents', doclist, 'Recents')

    def create_page_bookmarks(self):
        """Create bookmarks page."""
        doclist = []
        for doc in self.srvdtb.get_documents():
            bookmark = self.srvdtb.get_values(doc, 'Bookmark')[0]
            if bookmark == 'Yes' or bookmark == 'True':
                doclist.append(doc)
        self.build_pagination('bookmarks', doclist, 'Bookmarks')

    def create_page_authors(self):
        PAGE_AUTHOR = self.template('PAGE_AUTHOR')
        SECTION_ETYPE = self.template('PAGE_AUTHOR_SECTION_EVENT_TYPE')
        SWITCHER_ETYPE = self.template('PAGE_AUTHOR_SWITCHER_EVENT_TYPE')
        authors = self.srvdtb.get_all_values_for_key('Author')

        def tab_header(docs):
            author_etypes = set()
            event_types = self.srvapp.get_theme_property('events')
            for doc in docs:
                categories = self.srvdtb.get_values(doc, 'Category')
                for category in categories:
                    author_etypes.add(category)
            header = """<ul class="uk-flex-center" uk-tab>\n"""
            for etype in sorted(list(author_etypes)):
                header += """<li><a href="#">%s</a></li>\n""" % etype.title()
            # ~ header += """<li><a href="#">Others</a></li>\n"""
            header += """</ul>\n"""
            return sorted(list(author_etypes)), header

        for author in authors:
            docs = self.srvdtb.get_docs_by_key_value('Author', author)
            author_etypes, header = tab_header(docs)
            # ~ self.log.error ("%s -> %s", author, author_etypes)

            # Registered event types
            content_author = ''
            for etype in author_etypes:
                items = ''
                sect_items = 0
                for doc in docs:
                    category = self.srvdtb.get_values(doc, 'Category')
                    if etype in category:
                        items += self.get_doc_card_author(doc)
                        sect_items += 1
                content_author += SECTION_ETYPE % (sect_items, len(docs), items)

            # Others categories
            # ~ others = set(docs) - used
            # ~ items = ''
            # ~ for doc in others:
                # ~ items += self.get_doc_card_author(doc)
            # ~ content_author += SECTION_ETYPE % (len(others), items)
            content = SWITCHER_ETYPE % content_author
            PAGE = PAGE_AUTHOR % (author, header, content)
            # ~ self.log.error(content)
            self.distribute(valid_filename("Author_%s" % author), PAGE)


    def get_doc_card_author(self, doc):
        source_dir = self.srvapp.get_source_path()
        DOC_CARD = self.template('CARD_DOC_AUTHOR')
        DOC_CARD_FOOTER = self.template('CARD_DOC_AUTHOR_FOOTER')
        LINK = self.template('LINK')
        title = self.srvdtb.get_values(doc, 'Title')[0]
        category = self.srvdtb.get_values(doc, 'Category')[0]
        scope = self.srvdtb.get_values(doc, 'Scope')[0]
        link_title = LINK % ("uk-link-heading uk-text-meta", "%s.html" % valid_filename(doc).replace('.adoc', ''), "", title)
        link_category = LINK % ("uk-link-heading uk-text-meta", "Category_%s.html" % valid_filename(category), "", category)
        link_scope = LINK % ("uk-link-heading uk-text-meta", "Scope_%s.html" % valid_filename(scope), "", scope)

        timestamp = self.srvdtb.get_doc_timestamp(doc)
        fuzzy_date = fuzzy_date_from_timestamp(timestamp)

        tooltip ="%s" % (title)
        return DOC_CARD % (title, tooltip, link_title, timestamp, fuzzy_date, link_scope)

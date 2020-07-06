#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: techdoc theme scripts
"""

import os
import calendar
from calendar import HTMLCalendar, monthrange
from datetime import datetime, timedelta

from kb4it.services.builder import KB4ITBuilder
from kb4it.core.util import get_human_datetime, fuzzy_date_from_timestamp
from kb4it.core.util import valid_filename, get_human_datetime, guess_datetime
from kb4it.core.util import file_timestamp
from evcal import EventsCalendar


class Theme(KB4ITBuilder):
    dey = {} # Dictionary of day events per year
    events_docs = {} # Dictionary storing a list of docs for a given date

    def build(self):
        self.dey = {} # Dictionary of day events per year
        self.events_docs = {} # Dictionary storing a list of docs for a given date
        self.app.register_service('EvCal', EventsCalendar())
        self.srvcal = self.get_service('EvCal')
        self.create_page_events()
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
        # ~ self.create_page_events()
        # ~ self.create_page_blog()
        self.create_page_recents()

    def create_page_index(self):
        TPL_INDEX = self.template('PAGE_INDEX')
        TABLE_EVENTS = self.template('TABLE_EVENT')
        ROW_EVENT = self.template('TABLE_EVENT_ROW')
        OLD = """<table border="0" cellpadding="0" cellspacing="0" class="month">"""
        NEW = """<table border="0" cellpadding="0" cellspacing="0" width="100%" class="month">"""
        now = datetime.now().date()
        ldcm = now.replace(day = monthrange(now.year, now.month)[1]) # last day current month
        fdnm = ldcm + timedelta(days=1) # first day next month
        ldnm = fdnm.replace(day = monthrange(fdnm.year, fdnm.month)[1]) # last day next month

        trimester = self.srvcal.format_trimester(now.year, now.month)
        trimester = trimester.replace(OLD, NEW)

        next_events = ""
        ROWS_EVENTS = ''

        while now <= ldcm:
            try:
                for doc in self.events_docs[now.year][now.month][now.day]:
                    row = self.get_doc_event_row(doc)
                    ROWS_EVENTS += ROW_EVENT % (row['timestamp'], row['team'], row['title'], row['category'], row['scope'])
            except Exception as error:
                pass
            delta = timedelta(days=1)
            now += delta

        while fdnm < ldnm:
            try:
                for doc in self.events_docs[fdnm.year][fdnm.month][fdnm.day]:
                    row = self.get_doc_event_row(doc)
                    ROWS_EVENTS += ROW_EVENT % (row['timestamp'], row['team'], row['title'], row['category'], row['scope'])
            except Exception as error:
                pass
            delta = timedelta(days=1)
            fdnm += delta

        self.distribute('index', TPL_INDEX % (datetime.now().ctime(), trimester, TABLE_EVENTS % ROWS_EVENTS))

    def get_doc_event_row(self, doc):
        """Get card for a given doc"""
        row = {}
        LINK = self.template('LINK')
        title = self.srvdtb.get_values(doc, 'Title')[0]
        tooltip ="%s" % (title)
        category = self.srvdtb.get_values(doc, 'Category')[0]
        scope = self.srvdtb.get_values(doc, 'Scope')[0]
        team = self.srvdtb.get_values(doc, 'Team')[0]

        timestamp = self.srvdtb.get_doc_timestamp(doc)
        link_team = LINK % ("uk-link-heading uk-text-meta", "Team_%s.html" % valid_filename(team), '', team)
        link_title = LINK % ("uk-link-heading uk-text-meta", "%s.html" % valid_filename(doc).replace('.adoc', ''), '', title)
        link_category = LINK % ("uk-link-heading uk-text-meta", "Category_%s.html" % valid_filename(category), '', category)
        link_scope = LINK % ("uk-link-heading uk-text-meta", "Scope_%s.html" % valid_filename(scope), '', scope)

        row['timestamp'] = timestamp
        row['team'] = link_team
        row['title'] = link_title
        row['category'] = link_category
        row['scope'] = link_scope
        return row

    def build_events(self, doclist):
        SORT = self.srvapp.get_runtime_parameter('sort_attribute')

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
                    days_events = self.dey[y]
                    days_events.append((m, d))
                except:
                    days_events = []
                    days_events.append((m, d))
                    self.dey[y] = days_events

                # Build dict of documents
                if not y in self.events_docs:
                    self.events_docs[y] = {}

                if not m in self.events_docs[y]:
                    self.events_docs[y][m] = {}

                if not d in self.events_docs[y][m]:
                    self.events_docs[y][m][d] = []

                docs = self.events_docs[y][m][d]
                docs.append(doc)
                self.events_docs[y][m][d] = docs
            except Exception as error:
                # Doc doesn't have a valid date field. Skip it.
                self.log.debug("[THEME-TECHDOC] - %s", error)
                self.log.debug("[THEME-TECHDOC] - Doc doesn't have a valid date field. Skip it.")

        # Build day event pages
        for year in self.events_docs:
            for month in self.events_docs[year]:
                for day in self.events_docs[year][month]:
                    docs = self.events_docs[year][month][day]
                    edt = guess_datetime("%4d.%02d.%02d" % (year, month, day))
                    title = edt.strftime("Events on %A, %B %d %Y")
                    EVENT_PAGE_DAY = "events_%4d%02d%02d" % (year, month, day)

                    # create html page
                    pagination = {}
                    pagination['basename'] = EVENT_PAGE_DAY
                    pagination['doclist'] = docs
                    pagination['title'] = title
                    pagination['function'] = 'build_cardset'
                    pagination['template'] = 'PAGE_PAGINATION_HEAD'
                    pagination['fake'] = False
                    self.build_pagination(pagination)

        # Build month event pages
        for year in self.events_docs:
            for month in self.events_docs[year]:
                thismonth = []
                edt = guess_datetime("%4d.%02d.01" % (year, month))
                title = edt.strftime("Events on %B, %Y")
                EVENT_PAGE_MONTH = "events_%4d%02d" % (year, month)
                for day in self.events_docs[year][month]:
                    thismonth.extend(self.events_docs[year][month][day])

                # create html page
                pagination = {}
                pagination['basename'] = EVENT_PAGE_MONTH
                pagination['doclist'] = thismonth
                pagination['title'] = title
                pagination['function'] = 'build_cardset'
                pagination['template'] = 'PAGE_PAGINATION_HEAD'
                pagination['fake'] = False
                self.build_pagination(pagination)

        self.srvcal.set_events_days(self.dey)
        self.srvcal.set_events_docs(self.events_docs)

        for year in sorted(self.dey.keys(), reverse=True):
            HTML = self.srvcal.build_year_pagination(self.dey.keys())
            edt = guess_datetime("%4d.01.01" % year)
            title = edt.strftime("Events on %Y")
            PAGE = self.template('PAGE_EVENTS_YEAR')
            EVENT_PAGE_YEAR = "events_%4d" % year
            HTML += self.srvcal.formatyearpage(year, 4)
            self.distribute(EVENT_PAGE_YEAR, PAGE % (title, HTML))

        # ~ return self.dey

    def load_events_days(self, events_days, year):
        events_set = set()
        for event_day in events_days:
            events_set.add(event_day)

        for month, day in events_set:
            adate = guess_datetime("%d.%02d.%02d" % (year, month, day))

    def create_page_events(self):
        doclist = []
        ecats = {}
        theme = self.srvapp.get_theme_properties()
        try:
            event_types = theme['events']
        except:
            event_types = []
        self.log.debug("[THEME-TECHDOC] - Event types registered: %s", ', '.join(event_types))
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
        self.build_events(doclist)
        HTML = self.srvcal.build_year_pagination(self.dey.keys())
        page = self.template('PAGE_EVENTS')
        self.distribute('events', page % HTML)
        self.log.debug("[THEME-TECHDOC] - Built %d events", len(doclist))

    def create_page_recents(self):
        """Create recents page."""
        doclist = self.srvdtb.get_documents()[:60]
        pagination = {}
        pagination['basename'] = 'recents'
        pagination['doclist'] = doclist
        pagination['title'] = 'Recents'
        pagination['function'] = 'build_cardset'
        pagination['template'] = 'PAGE_PAGINATION_HEAD'
        pagination['fake'] = False
        self.build_pagination(pagination)

    def create_page_bookmarks(self):
        """Create bookmarks page."""
        doclist = []
        for doc in self.srvdtb.get_documents():
            bookmark = self.srvdtb.get_values(doc, 'Bookmark')[0]
            if bookmark == 'Yes' or bookmark == 'True':
                doclist.append(doc)
        pagination = {}
        pagination['basename'] = 'bookmarks'
        pagination['doclist'] = doclist
        pagination['title'] = 'Bookmarks'
        pagination['function'] = 'build_cardset'
        pagination['template'] = 'PAGE_PAGINATION_HEAD'
        pagination['fake'] = False
        self.build_pagination(pagination)

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
            header += """</ul>\n"""
            return sorted(list(author_etypes)), header

        for author in authors:
            docs = self.srvdtb.get_docs_by_key_value('Author', author)
            author_etypes, header = tab_header(docs)

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

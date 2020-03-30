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
import codecs
import calendar
from calendar import HTMLCalendar
from datetime import datetime
import chardet
import tempfile
import pprint
from kb4it.src.core.mod_srv import Service
from kb4it.src.core.mod_utils import get_human_datetime, fuzzy_date_from_timestamp
from kb4it.src.core.mod_utils import valid_filename, get_human_datetime, guess_datetime
from kb4it.src.services.srv_builder import Builder
from camt import CAMT




def get_file_encoding(src_file_path):
    """
    Get the encoding type of a file
    :param src_file_path: file path
    :return: str - file encoding type
    """

    with open(src_file_path) as src_file:
        return src_file.encoding


def get_file_encoding_chardet(file_path):
    """
    Get the encoding of a file using chardet package
    :param file_path:
    :return:
    """
    with open(file_path, 'rb') as f:

        result = chardet.detect(f.read())
        return result['encoding']

class EventsCalendar(Service, HTMLCalendar):
    """Credit to: https://github.com/garthhumphreys/How-to-Use-Python-To-Create-A-Beautiful-Web-Calendar"""

    def initialize(self):
        super(HTMLCalendar, self).__init__(calendar.MONDAY)
        self.current_year = None
        self.ml = {}
        self.get_services()
        print

    def set_events_days(self, events_days):
        """
        Attach the list of event days as a property, so we can access it
        anywhere.
        """
        self.events_days = events_days #
        for i in range(1,13):
            self.ml[i] = False
        for month, day in events_days:
            self.ml[month] = True

    def set_events_docs(self, docs):
        self.events_docs = docs

    def set_events_html(self, html):
        self.events_html = html

    def get_services(self):
        self.srvbld = self.get_service('Builder')

    def formatday(self, day, weekday):
        """Return a day as a table cell."""
        eday = 0 # var for checking if it's a event day
        cal_date = (self.month, day) # create a tuple of the calendar month and day
        EVENTCAL_TD_NODAY = self.srvbld.template('EVENTCAL_TD_NODAY')
        EVENTCAL_TD_DAY_LINK = self.srvbld.template('EVENTCAL_TD_DAY_LINK')
        EVENTCAL_TD_DAY_NOLINK = self.srvbld.template('EVENTCAL_TD_DAY_NOLINK')
        if cal_date in self.events_days: # check if current calendar tuple date exist in our list of events days
            eday = day # if it does exist set the event day var with it
        if day == 0:
            return EVENTCAL_TD_NODAY # day outside month
        elif day == eday: # check if this is one of the events days, then change the
            EVENT_PAGE = "events_%4d%02d%02d" % (self.current_year, self.month, day)
            EVENT_PAGE_VALID_FNAME = valid_filename(EVENT_PAGE)
            return EVENTCAL_TD_DAY_LINK % (self.cssclasses[weekday], EVENT_PAGE_VALID_FNAME, day)
        else:
            return EVENTCAL_TD_DAY_NOLINK % (self.cssclasses[weekday], day)

    def formatweek(self, theweek):
        """Return a complete week as a table row."""
        EVENTCAL_TR_WEEK = self.srvbld.template('EVENTCAL_TR_WEEK')
        s = ''.join(self.formatday(d, wd) for (d, wd) in theweek)
        return EVENTCAL_TR_WEEK % s

    def formatweekheader(self):
        """Return a header for a week as a table row."""
        EVENTCAL_TR_WEEK_HEADER = self.srvbld.template('EVENTCAL_TR_WEEK_HEADER')
        s = ''.join(self.formatweekday(i) for i in self.iterweekdays())
        return EVENTCAL_TR_WEEK_HEADER % s

    def formatmonthname(self, theyear, themonth, withyear=True):
        """Return a formatted month name."""
        LINK = self.srvbld.template('LINK')
        dt = guess_datetime("%4d-%02d-01" % (theyear, themonth))
        if withyear:
            month_name = datetime.strftime(dt, "%B %Y")
        else:
            month_name = datetime.strftime(dt, "%B")

        if self.ml[themonth]:
            link = LINK % ("uk-link", "events_%4d%02d.html" % (theyear, themonth), "", month_name)
        else:
            link = LINK % ("uk-link", "", "", month_name)
        return link

    def formatmonth(self, theyear, themonth, withyear=False):
        """Override in order to add the month as a property."""
        self.month = themonth
        month = super(EventsCalendar, self).formatmonth(theyear, themonth, withyear=False)
        return month

    def formatyear(self, theyear, width=3):
        """Return a formatted year as a table of tables."""
        EVENTCAL_TABLE_YEAR = self.srvbld.template('EVENTCAL_TABLE_YEAR')
        EVENTCAL_TABLE_YEAR_TR_MONTHROW = self.srvbld.template('EVENTCAL_TABLE_YEAR_TR_MONTHROW')
        EVENTCAL_TABLE_YEAR_TD_MONTH = self.srvbld.template('EVENTCAL_TABLE_YEAR_TD_MONTH')
        v = []
        width = max(width, 1)
        MONTHS = ''
        January = 1
        for i in range(January, January+12, width):
            months = range(i, min(i+width, 13))
            TD_YEAR_MONTH = ''
            for m in months:
                TD_YEAR_MONTH += EVENTCAL_TABLE_YEAR_TD_MONTH % self.formatmonth(theyear, m, withyear=False)
            MONTHS += EVENTCAL_TABLE_YEAR_TR_MONTHROW % TD_YEAR_MONTH
        v.append(EVENTCAL_TABLE_YEAR % MONTHS)
        return ''.join(v)

    def formatyearpage(self, theyear, width=3, css='calendar.css', encoding=None):
        """Return a formatted year as a complete HTML page."""
        self.current_year = theyear
        return self.formatyear(theyear, width)

    def build_year_pagination(self, years):
        EVENTCAL_YEAR_PAGINATION = self.srvbld.template('EVENTCAL_YEAR_PAGINATION')
        EVENTCAL_YEAR_PAGINATION_ITEM = self.srvbld.template('EVENTCAL_YEAR_PAGINATION_ITEM')
        ITEMS = ''
        for yp in sorted(years):
            ITEMS += EVENTCAL_YEAR_PAGINATION_ITEM % (yp, yp)
        return EVENTCAL_YEAR_PAGINATION % ITEMS

class Theme(Builder):
    def generate_sources(self):
        self.log.debug("Generating sources")
        source_path = self.srvapp.get_source_path()

        csvfile = os.path.join(source_path, 'operations.csv')
        encoding = get_file_encoding_chardet(csvfile)
        self.log.debug(encoding)
        if encoding.upper() != 'UTF-8':
            self.log.warning ("CSV file not in UTF-8")
            data = open(csvfile, 'rb').read()
            csvfile = os.path.join(source_path, 'opcamt.oikos')
            codecs.getwriter('utf-8')(open(csvfile,'wb')).write(data.decode("ISO-8859-1"))
            self.log.warning("CSV file saved as UTF-8 in a temporary file: %s", csvfile)
        else:
            self.log.warning ("CSV file is in UTF-8")

        camt = CAMT()
        data = camt.get_data(csvfile)
        camt.analyze(data)
        # ~ self.log.debug(camt.get_report())
        pprint.pprint(camt.get_operations())

    def build(self):
        self.create_about_page()
        self.create_help_page()
        self.create_all_keys_page()
        self.create_properties_page()
        self.create_stats_page()
        self.create_index_all()
        self.create_index_page()
        self.create_bookmarks_page()
        self.create_authors_page()
        self.app.register_service('EvCal', EventsCalendar())
        self.srvcal = self.get_service('EvCal')
        self.create_events_page()
        # ~ self.create_blog_page()
        self.create_recents_page()

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
            HTML += self.srvcal.formatyearpage(year, 3)
            self.distribute(EVENT_PAGE_YEAR, PAGE % (title, HTML))

        return dey

    def load_events_days(self, events_days, year):
        events_set = set()
        for event_day in events_days:
            events_set.add(event_day)

        for month, day in events_set:
            adate = guess_datetime("%d.%02d.%02d" % (year, month, day))
            # ~ self.log.debug(adate)

    def create_events_page(self):
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

    def create_authors_page(self):
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
            self.log.error ("%s -> %s", author, author_etypes)

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

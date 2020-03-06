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
from kb4it.src.core.mod_srv import Service
from kb4it.src.core.mod_utils import get_human_datetime, fuzzy_date_from_timestamp
from kb4it.src.core.mod_utils import valid_filename, get_human_datetime, guess_datetime
from kb4it.src.services.srv_builder import Builder

# Constants for months referenced later
January = 1


class EventsCalendar(Service, HTMLCalendar):
    """Credit to: https://github.com/garthhumphreys/How-to-Use-Python-To-Create-A-Beautiful-Web-Calendar"""

    def initialize(self):
        super(HTMLCalendar, self).__init__(calendar.MONDAY)
        self.current_year = None
        self.ml = {}
        self.get_services()

    def set_events_days(self, events_days):
        self.events_days = events_days # attach the list of event days as a property, so we can access it anywhere
        for i in range(1,13):
            self.ml[i] = False

        for month, day in events_days:
            self.ml[month] = True

        print(self.ml)

    def set_events_docs(self, docs):
        self.events_docs = docs

    def set_events_html(self, html):
        self.events_html = html

    def get_services(self):
        self.srvbld = self.get_service('Builder')

    def formatday(self, day, weekday):
        eday = 0 # var for checking if it's a event day
        cal_date = (self.month, day) # create a tuple of the calendar month and day

        if cal_date in self.events_days: # check if current calendar tuple date exist in our list of events days
            eday = day # if it does exist set the event day var with it

        """
          Return a day as a table cell.
        """
        if day == 0:
            return '<td class="noday day">&nbsp;</td>' # day outside month
        elif day == eday: # check if this is one of the events days, then change the
            EVENT_PAGE = "events_%4d%02d%02d" % (self.current_year, self.month, day)
            EVENT_PAGE_VALID_FNAME = valid_filename(EVENT_PAGE)
            EVENT_MODAL_BUTTON = self.srvbld.template('EVENT_DAY_MODAL')
            edt = guess_datetime("%4d.%02d.%02d" % (self.current_year, self.month, day))
            tooltip = ''
            fontsize = 10
            title = edt.strftime("Events on %A, %B %d %Y")
            content = ''
            # ~ button = EVENT_MODAL_BUTTON % (EVENT_PAGE_VALID_FNAME, tooltip, fontsize, day, EVENT_PAGE, EVENT_PAGE, title, content)
            self.log.debug("\t\t%s: %d", title, len(self.events_docs[self.month][day]))
            # ~ self.log.error(button)
            # ~ print(EVENT_PAGE)
            return """<td class="%s eventday day uk-text-bold uk-text-center uk-background-primary"><a class="uk-link-text uk-text-normal" href="%s.html" style="color: white;">%s</a></td>""" % (self.cssclasses[weekday], EVENT_PAGE_VALID_FNAME, day)
        else:
            return """<td class="%s day uk-text-center">%d</td>""" % (self.cssclasses[weekday], day)

    def formatweek(self, theweek):
        """
        Return a complete week as a table row.
        """
        s = ''.join(self.formatday(d, wd) for (d, wd) in theweek)
        return '<tr class="week">%s</tr>' % s

    def formatweekheader(self):
        """
        Return a header for a week as a table row.
        """
        s = ''.join(self.formatweekday(i) for i in self.iterweekdays())
        return '<tr class="weekheader">%s</tr>' % s

    # override in order to make months linkable
    def formatmonthname(self, theyear, themonth, withyear=True):
        """
        Return a formatted month name.
        """
        # ~ self.log.debug(self.events_days)
        dt = guess_datetime("%4d-%02d-01" % (theyear, themonth))
        if withyear:
            month_name = datetime.strftime(dt, "%B %Y")
        else:
            month_name = datetime.strftime(dt, "%B")

        if self.ml[themonth]:
            link = """<a class="uk-link" href="events_%4d%02d.html"><span class="">%s</span></a>""" % (theyear, themonth, month_name)
        else:
            link = """<span class="">%s</span>""" % (month_name)
        return link



    # override in order to add the month as a property
    def formatmonth(self, theyear, themonth, withyear=False):
        # ~ self.log.debug("%s (%s) -> %s (%s)", theyear, type(theyear), themonth, type(themonth))
        self.month = themonth
        month = super(EventsCalendar, self).formatmonth(theyear, themonth, withyear=False)
        # ~ self.log.debug(month)
        return month

    def formatyear(self, theyear, width=3):
        """
        Return a formatted year as a table of tables.
        """
        v = []
        a = v.append
        width = max(width, 1)
        a('<table class="uk-table uk-table-small" border="0" cellpadding="0" cellspacing="0" id="calendar">')
        a('\n')
        for i in range(January, January+12, width):
            # months in this row
            months = range(i, min(i+width, 13))
            a('<tr class="month-row">')
            for m in months:
                a('<td class="calendar-month uk-card-small uk-card-hover">')
                a(self.formatmonth(theyear, m, withyear=False))
                a('</td>')
            a('</tr>')
        a('</table>')
        return ''.join(v)

    def formatyearpage(self, theyear, width=3, css='calendar.css', encoding=None):
        """
        Return a formatted year as a complete HTML page.
        """
        self.current_year = theyear
        v = []
        v.append(self.formatyear(theyear, width))

        return ''.join(v)


class Theme(Builder):
    def build(self):
        self.create_about_page()
        self.create_help_page()
        self.create_all_keys_page()
        self.create_properties_page()
        self.create_stats_page()
        self.create_index_all()
        self.create_index_page()
        self.create_bookmarks_page()
        self.app.register_service('EvCal', EventsCalendar())
        self.srvcal = self.get_service('EvCal')
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
                    events_docs_html[y][m][d] = self.build_html_events(docs)

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

                # Generate HTML to display into the modal window
                # ~ events_docs_html[y][m][d] = self.build_html_events(docs)

        # Build year event pages
        lyears = []
        for year in dey:
            lyears.append(year)

        for year in sorted(lyears, reverse=True):
            # Year pagination
            HTML = """<div class="uk-flex uk-flex-center">\n"""
            for yp in sorted(lyears):
                HTML += """<div class="uk-card uk-card-body uk-card-small uk-card-hover"><a class="uk-link" href="events_%d.html"><span class="">%d</span></a></div>\n""" % (yp, yp)
            HTML += """</div>\n"""

            edt = guess_datetime("%4d.01.01" % year)
            title = edt.strftime("Events on %Y")
            PAGE = self.template('PAGE_EVENTS_YEAR')
            EVENT_PAGE_YEAR = "events_%4d" % year
            HTML += """<div class="uk-card uk-card-large uk-card-body">\n"""
            self.srvcal.set_events_days(dey[year])
            self.srvcal.set_events_docs(events_docs[year])
            self.srvcal.set_events_html(events_docs_html[year])
            HTML += self.srvcal.formatyearpage(year, 3)
            HTML += """</div>\n"""
            self.distribute(EVENT_PAGE_YEAR, PAGE % (title, HTML))

        return dey

    def build_html_events(self, docs):
        # ~ self.log.debug(docs)
        pass

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
        self.log.info("\t\tEvent types registered for this theme: %s", ','.join(event_types))
        for doc in self.srvdtb.get_documents():
            category = self.srvdtb.get_values(doc, 'Category')[0]
            # ~ self.log.debug("\t\tCategory '%s' is an event? %s", category, category in event_types)
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
        self.log.debug(ecats)

        dey = self.build_events(doclist)
        self.log.debug(dey)


        # Year pagination
        HTML = """<div class="uk-flex uk-flex-center">\n"""
        for yp in sorted(list(dey.keys())):
            HTML += """<div class="uk-card uk-card-body uk-card-small uk-card-hover"><a class="uk-link" href="events_%d.html"><span class="">%d</span></a></div>\n""" % (yp, yp)
        HTML += """</div>\n"""

        page = self.template('PAGE_EVENTS')
        self.distribute('events', page % HTML)
        # ~ self.build_pagination('events', doclist, 'Events', "build_events", "PAGE_PAGINATION_HEAD_EVENT")

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


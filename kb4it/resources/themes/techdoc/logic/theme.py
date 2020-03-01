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
from pprint import pprint
# ~ from kb4it.src.core.mod_srv import Service
from kb4it.src.core.mod_utils import get_human_datetime, fuzzy_date_from_timestamp
from kb4it.src.core.mod_utils import valid_filename, get_human_datetime, guess_datetime
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

# Constants for months referenced later
January = 1

class PayDayCalendar(HTMLCalendar):
    def __init__(self, pay_days):
            super(PayDayCalendar, self).__init__(calendar.SUNDAY)
            self.pay_days = pay_days # attach the list of paydays as a property, so we can access it anywhere

    def formatday(self, day, weekday):
        pday = 0 # var for checking if it's a payday
        cal_date = (self.month, day) # create a tuple of the calendar month and day

        if cal_date in self.pay_days: # check if current calendar tuple date exist in our list of pay days
            print('cal_date: ', cal_date, ' day: ', day)
            pday = day # if it does exist set the pay day var with it

        """
          Return a day as a table cell.
        """
        if day == 0:
            return '<td class="noday day">&nbsp;</td>' # day outside month
        elif day == pday: # check if this is one of the pay days, then change the class
            return '<td class="%s payday day uk-text-bold uk-text-right uk-background-primary" style="color: white;">%d</td>' % (self.cssclasses[weekday], day)
        else:
            return '<td class="%s day" align="right">%d</td>' % (self.cssclasses[weekday], day)

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

    # override in order to add the month as a property
    def formatmonth(self, theyear, themonth, withyear=True):
        self.month = themonth
        return super(PayDayCalendar, self).formatmonth(theyear, themonth, withyear=False)

    def formatyear(self, theyear, width=3):
        """
        Return a formatted year as a table of tables.
        """
        v = []
        a = v.append
        width = max(width, 1)
        a('<table class="uk-table" border="0" cellpadding="0" cellspacing="0" id="calendar">')
        a('\n')
        a('<tr id="calendar-year"><th colspan="%d" class="year">Government Pay Days for %s</th></tr>' % (width, theyear))
        for i in range(January, January+12, width):
            # months in this row
            months = range(i, min(i+width, 13))
            a('<tr class="month-row">')
            for m in months:
                a('<td class="calendar-month">')
                a(self.formatmonth(theyear, m, withyear=False))
                a('</td>')
            a('</tr>')
        a('</table>')
        return ''.join(v)

    def formatyearpage(self, theyear, width=3, css='calendar.css', encoding=None):
        """
        Return a formatted year as a complete HTML page.
        """
        v = []
        a = v.append
        # ~ a('<div id="wrapper">\n')
        a(self.formatyear(theyear, width))
        # ~ a('</div>\n')

        # output the HTML
        return ''.join(v)


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
        self.log.debug("EVENTS: %s", doclist)
        SORT = self.srvapp.get_runtime_parameter('sort_attribute')
        self.log.debug("\t\t\t  Using custom build cardset function for events")
        dey = {}
        HTML = '<ul uk-accordion>\n'
        for doc in doclist:
            props = self.srvdtb.get_doc_properties(doc)
            self.log.debug("\tPROPS: %s", props)
            try:
                timestamp = guess_datetime(props[SORT][0])
            except:
                timestamp = guess_datetime(props['Timestamp'])
            self.log.debug("TIMESTAMP: %s", timestamp)

            try:
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
            except Exception as error:
                self.log.error(error)

        for year in dey:
            HTML +="""<li><a class="uk-accordion-title uk-text-center uk-text-bolder" href="#">%s</a><div class="uk-accordion-content">""" % year
            HTML += PayDayCalendar(dey[year]).formatyearpage(year, 3)
            HTML += """</div></li>\n"""

        # ~ events = PayDayCalendar(calendar.SUNDAY)

        # ~ return myCal.formatyear(2020)
        HTML += "</u>"
        return HTML


    def create_events_page(self):
        doclist = []
        theme = self.srvapp.get_theme_properties()
        try:
            events = theme['event'].split(',')
        except:
            events = []
        self.log.info("Events registered for this theme: %s", ','.join(events))
        for doc in self.srvdtb.get_documents():
            category = self.srvdtb.get_values(doc, 'Category')[0]
            if category in events:
                doclist.append(doc)
                category = self.srvdtb.get_values(doc, 'Category')[0]
                title = self.srvdtb.get_values(doc, 'Title')[0]
                self.log.debug("Found '%s' event: '%s'", category, title)
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
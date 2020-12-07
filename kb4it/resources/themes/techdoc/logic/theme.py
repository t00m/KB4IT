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
        self.create_page_etype('Author', 'Category')
        self.create_page_etype('Category', 'Scope')
        self.create_page_etype('Team', 'Scope')
        self.create_page_recents()
        self.create_page_bookmarks()

    def create_page_index(self):
        var = {}
        TPL_INDEX = self.template('PAGE_INDEX')
        TPL_TABLE_EVENTS = self.template('TABLE_EVENT')
        TPL_TABLE_MONTH_OLD = self.template('TABLE_MONTH_OLD')
        TPL_TABLE_MONTH_NEW = self.template('TABLE_MONTH_NEW')
        timestamp = datetime.now()
        now = timestamp.date()
        ldcm = now.replace(day = monthrange(now.year, now.month)[1]) # last day current month
        fdnm = ldcm + timedelta(days=1) # first day next month
        ldnm = fdnm.replace(day = monthrange(fdnm.year, fdnm.month)[1]) # last day next month

        trimester = self.srvcal.format_trimester(now.year, now.month)
        trimester = trimester.replace(TPL_TABLE_MONTH_OLD.render(), TPL_TABLE_MONTH_NEW.render())

        next_events = ""
        ROWS_EVENTS = ''
        var['rows'] = []

        # FIXME: Get number of events to display from theme.conf
        max_events = 10
        n = 0
        for year in self.events_docs:
            for month in self.events_docs[year]:
                for day in self.events_docs[year][month]:
                    for doc in self.events_docs[year][month][day]:
                        try:
                            if n < max_events:
                                row = self.get_doc_event_row(doc)
                                var['rows'].append(row)
                                n = n + 1
                            else:
                                break
                        except Exception as error:
                            self.log.error(error)

        # ~ while now <= ldcm:
            # ~ try:
                # ~ for doc in self.events_docs[now.year][now.month][now.day]:
                    # ~ row = self.get_doc_event_row(doc)
                    # ~ var['rows'].append(row)
            # ~ except Exception as error:
                # ~ pass
            # ~ delta = timedelta(days=1)
            # ~ now += delta

        # ~ while fdnm < ldnm:
            # ~ try:
                # ~ for doc in self.events_docs[fdnm.year][fdnm.month][fdnm.day]:
                    # ~ row = self.get_doc_event_row(doc)
                    # ~ var['rows'].append(row)
            # ~ except Exception as error:
                # ~ pass
            # ~ delta = timedelta(days=1)
            # ~ fdnm += delta

        #FIXME: Get repository title from theme.conf
        var['title'] = 'My KB4IT Repostiroy'
        var['timestamp'] = timestamp.ctime()
        var['calendar_trimester'] = trimester
        var['table_trimester'] = TPL_TABLE_EVENTS.render(var=var)
        self.distribute('index', TPL_INDEX.render(var=var))


    def get_doc_event_row(self, doc):
        """Get card for a given doc"""
        row = {}
        LINK = self.template('LINK')
        link = {}
        link['class'] = "uk-link-heading uk-text-meta"

        # Date
        row['timestamp'] = self.srvdtb.get_doc_timestamp(doc)

        # Team
        team = self.srvdtb.get_values(doc, 'Team')[0]
        link['url'] = "Team_%s.html" % valid_filename(team)
        link['title'] = team
        row['team'] = LINK.render(var=link)

        # Title
        title = self.srvdtb.get_values(doc, 'Title')[0]
        link['url'] = "%s.html" % valid_filename(doc).replace('.adoc', '')
        link['title'] = title
        row['title'] = LINK.render(var=link)

        # Category
        category = self.srvdtb.get_values(doc, 'Category')[0]
        link['url'] = "Category_%s.html" % valid_filename(category)
        link['title'] = category
        row['category'] = LINK.render(var=link)

        # Scope
        scope = self.srvdtb.get_values(doc, 'Scope')[0]
        link['url'] = "Scope_%s.html" % valid_filename(scope)
        link['title'] = scope
        row['scope'] = LINK.render(var=link)

        # Status
        status = self.srvdtb.get_values(doc, 'Status')[0]
        link['url'] = "Status_%s.html" % valid_filename(status)
        link['title'] = status
        row['status'] = LINK.render(var=link)

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
            PAGE = self.template('PAGE_EVENTS_YEAR')
            page_name = "events_%4d" % year
            thisyear = {}
            html = self.srvcal.build_year_pagination(self.dey.keys())
            edt = guess_datetime("%4d.01.01" % year)
            title = edt.strftime("Events on %Y")
            thisyear['title'] = title
            html += self.srvcal.formatyearpage(year, 4)
            thisyear['content'] = html
            self.distribute(page_name, PAGE.render(var=thisyear))

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
        events = {}
        events['content'] = HTML
        page = self.template('PAGE_EVENTS')
        self.distribute('events', page.render(var=events))

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

    def create_page_etype(self, key, subkey):
        TPL_PAGE_ETYPE = self.template('PAGE_ETYPE')
        TPL_SECTION_ETYPE = self.template('PAGE_SECTION_EVENT_TYPE')
        TPL_SWITCHER_ETYPE = self.template('PAGE_SWITCHER_EVENT_TYPE')
        TPL_TAB_CENTER = self.template('TAB_CENTER')
        TPL_TAB_ITEM = self.template('TAB_ITEM')
        key_list = self.srvdtb.get_all_values_for_key(key.title())

        def tab_header(docs):
            etypes_set = set()
            event_types = self.srvapp.get_theme_property('events')
            for doc in docs:
                subkey_list = self.srvdtb.get_values(doc, subkey.title())
                for subkey_item in subkey_list:
                    etypes_set.add(subkey_item)
            items = ''
            for etype in sorted(list(etypes_set)):
                item = {}
                item['name'] = etype.title()
                items += TPL_TAB_ITEM.render(var=item)
            tab = {}
            tab['content'] = items
            header = TPL_TAB_CENTER.render(var=tab)
            key_list = sorted(list(etypes_set))
            return key_list, header

        for key_item in key_list:
            docs = self.srvdtb.get_docs_by_key_value(key.title(), key_item)
            etypes_set, header = tab_header(docs)

            # Registered event types
            content_key = ''
            for etype_item in etypes_set:
                section = {}
                items = ''
                sect_items = 0
                for doc in docs:
                    subkey_item = self.srvdtb.get_values(doc, subkey.title())
                    if etype_item in subkey_item:
                        items += self.get_doc_card(doc)
                        sect_items += 1
                section['count_items'] = sect_items
                section['count_docs'] = len(docs)
                section['items'] = items
                content_key += TPL_SECTION_ETYPE.render(var=section)

            page_key = {}
            page_key['content'] = content_key
            content = TPL_SWITCHER_ETYPE.render(var=page_key)
            page = {}
            page['title'] = key_item
            page['header'] = header
            page['content'] = content

            html = TPL_PAGE_ETYPE.render(var=page)
            basename = valid_filename("%s_%s" % (key.title(), key_item))
            self.distribute(basename, html)

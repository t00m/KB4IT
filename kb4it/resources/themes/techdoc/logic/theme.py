#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: default theme script
"""

import os
import sys
import math
import calendar as _calendar
from datetime import datetime, timedelta
from calendar import monthrange

from lxml import etree

from kb4it.services.builder import Builder
from kb4it.core.util import valid_filename
from kb4it.core.util import set_max_frequency
from kb4it.core.util import get_font_size
from kb4it.core.util import guess_datetime
from kb4it.core.util import get_human_datetime
from kb4it.core.util import get_human_datetime_day
from kb4it.core.util import get_human_datetime_month
from kb4it.core.util import get_human_datetime_year
from kb4it.core.util import ellipsize_text
from kb4it.core.util import get_year, get_month, get_day

from timeline import Timeline

parser = etree.HTMLParser()

class Theme(Builder):
    dey = {}
    events_docs = {}

    def _initialize(self):
        super()._initialize()
        self.dey = {}
        self.events_docs = {}

    def build_datatable(self, headers=[], doclist=[], table_id='kb4it-datatable'):
        """Given a list of columns, it builds a datatable.
        First column is always a date field, which is got by using the
        method get_doc_timestamp from the database module. It means
        that, firstly, it will retrieve the first date property defined
        by the theme (or one of the next ones defined if the first isn't
        found). If none is found, it will retrieve the timestamp of the
        file from the OS).
        So, it is not necessary to pass a date property in the headers.
        """
        #self.log.debug(f"DATATABLE HEADERS[{headers}] DOCLIST[{doclist}]")
        TPL_LINK = self.template('LINK')
        TPL_DATATABLE = self.template('DATATABLE')
        TPL_DATATABLE_HEADER_ITEM = self.template('DATATABLE_HEADER_ITEM')
        TPL_DATATABLE_BODY_ITEM = self.template('DATATABLE_BODY_ITEM')

        datatable = {}
        datatable['table_id'] = table_id
        repo = self.srvbes.get_dict('repo')
        sort_attribute = "Date"

        # Add datatable hearders
        datatable['header'] = ''
        if len(headers) == 0:
            headers = repo['datatable']
        # ~ sort_attr = repo['sort'][0]
        # ~ headers.insert(0, sort_attr)

        for item in headers:
            var = {}
            var['item'] = item
            datatable['header'] += TPL_DATATABLE_HEADER_ITEM.render(var=var)

        # Add datatable body
        documents = {}
        for docId in doclist:
            documents[docId] = self.srvdtb.get_doc_properties(docId)
        datatable['rows'] = ''
        for docId in documents:
            if self.srvdtb.is_system(docId):
                continue

            datatable['rows'] += '<tr>'
            if sort_attribute in headers:

                timestamp = self.srvdtb.get_doc_timestamp(docId)
                if timestamp is None:
                    continue
                ts_title = timestamp[:16]
                ts_link = f"events_{ts_title[:10].replace('-', '')}.html"
                datatable['rows'] += f"""<td class=""><a class="uk-link-heading" href="{ts_link}">{ts_title}</a></td>"""
                final_headers = headers[1:]
            else:
                final_headers = headers


            for key in final_headers:
                item = {}
                if key == 'Title':
                    try:
                        item['title'] = f"<div uk-tooltip=\"{documents[docId][key]}\">{ellipsize_text(documents[docId][key], 80)}</div>"
                        item['url'] = documents[docId]['%s_Url' % key]
                        datatable['rows'] += TPL_DATATABLE_BODY_ITEM.render(var=item)
                    except:
                        self.log.error(f"[THEME] DATATABLE_FAIL doc={docId} item={item}")
                        raise
                else:
                    link = {}
                    link['class'] = 'uk-link-heading'
                    field = []
                    try:
                        for value in documents[docId][key]:
                            link['title'] = value
                            link['url'] = documents[docId]['%s_%s_Url' % (key, value)]
                            field.append(TPL_LINK.render(var=link))
                    except KeyError:
                        field = ''
                    datatable['rows'] += """<td class="">%s</td>""" % ', '.join(field)
            datatable['rows'] += '</tr>'

        return TPL_DATATABLE.render(var=datatable)


    def build_page_index(self, var):
        """Create landing page."""
        repo = self.srvbes.get_dict('repo')
        runtime = self.srvbes.get_dict('runtime')
        filenames = runtime['docs']['filenames']
        now = datetime.now()
        var['dt_now'] = now

        if 'index.adoc' in filenames:
            self.log.info("[THEME] INDEX_SKIP reason=user_generated")
            return

        var['page']['title'] = var['repo']['title']
        var['page']['stats'] = self._build_index_stats()
        var['page']['alert_bar'] = self._build_index_alert_bar()
        var['page']['diataxis'] = self._build_index_diataxis()
        var['page']['trimester'] = self._build_index_trimester(now)
        var['page']['events_panel'] = self._build_index_events_panel(now)
        var['page']['recent_events'] = self._build_index_recent_events(now)

        page = self.template('PAGE_INDEX').render(var=var)
        self.distribute_adoc('index', page)

        self.srvdtb.add_document('index.adoc')
        self.srvdtb.add_document_key('index.adoc', 'Title', var['repo']['title'])
        self.srvdtb.add_document_key('index.adoc', 'SystemPage', 'Yes')

    def _build_index_stats(self):
        """Counters shown in the hero stats bar."""
        count_docs = 0
        count_bookmarks = 0
        for docId in self.srvdtb.get_documents():
            if self.srvdtb.is_system(docId):
                continue
            count_docs += 1
            bookmark = self.srvdtb.get_values(docId, 'Bookmark')[0]
            if bookmark in ('Yes', 'True'):
                count_bookmarks += 1

        count_authors = len(self.srvdtb.get_all_values_for_key('Author'))
        count_categories = len(self.srvdtb.get_all_values_for_key('Category'))

        count_events = 0
        for year in self.events_docs:
            for month in self.events_docs[year]:
                for day in self.events_docs[year][month]:
                    count_events += len(self.events_docs[year][month][day])

        return [
            {'num': count_docs,       'label': 'Documents',  'url': 'all.html'},
            {'num': count_authors,    'label': 'Authors',    'url': 'Author.html'},
            {'num': count_categories, 'label': 'Categories', 'url': 'Category.html'},
            {'num': count_events,     'label': 'Events',     'url': 'events.html'},
            {'num': count_bookmarks,  'label': 'Bookmarks',  'url': 'bookmarks.html'},
        ]

    def _build_index_alert_bar(self, limit=5):
        """Recent changes and incidents for the alert bar below the hero."""
        def _rows(category):
            rows = []
            for docId in self.srvdtb.get_docs_by_key_value('Category', category)[:limit]:
                props = self.srvdtb.get_doc_properties(docId)
                title = props.get('Title', docId)
                if isinstance(title, list):
                    title = title[0] if title else docId
                url = props.get('Title_Url', docId.replace('.adoc', '.html'))
                ts = self.srvdtb.get_doc_timestamp(docId)
                date = ''
                if ts:
                    try:
                        dt = guess_datetime(ts)
                        date = dt.strftime('%b %d') if dt else ts[:10]
                    except Exception:
                        date = ts[:10]
                rows.append({'date': date, 'title': title, 'url': url})
            return rows

        return {
            'changes': _rows('Change'),
            'incidents': _rows('Incident'),
        }

    def _build_index_diataxis(self):
        """Diátaxis cards — one per DocType value."""
        diataxis = [
            {'name': 'Tutorial',     'css': 'tutorial',    'icon': 'bolt',
             'label': 'Tutorials',
             'desc': 'Learning-oriented lessons that take you through a series of steps.'},
            {'name': 'How-to guide', 'css': 'howto',       'icon': 'cog',
             'label': 'How-to guides',
             'desc': 'Goal-oriented recipes to solve a specific problem.'},
            {'name': 'Reference',    'css': 'reference',   'icon': 'file-text',
             'label': 'Reference',
             'desc': 'Information-oriented technical descriptions of the machinery.'},
            {'name': 'Explanation',  'css': 'explanation', 'icon': 'comment',
             'label': 'Explanations',
             'desc': 'Understanding-oriented discussions that clarify a topic.'},
        ]
        key = 'DocType'
        for item in diataxis:
            docs = self.srvdtb.get_docs_by_key_value(key, item['name'])
            item['count'] = len(docs)
            item['url'] = "%s_%s.html" % (valid_filename(key), valid_filename(item['name'])) if docs else None
        return diataxis

    def _build_index_trimester(self, now):
        """Compact 3-month grid — prev, current, next."""
        cur_first = now.replace(day=1)
        prv_last = cur_first - timedelta(days=1)
        cur_last = cur_first.replace(day=monthrange(cur_first.year, cur_first.month)[1])
        nxt_first = cur_last + timedelta(days=1)

        months_data = [
            (prv_last.year, prv_last.month, False),
            (cur_first.year, cur_first.month, True),
            (nxt_first.year, nxt_first.month, False),
        ]
        cal = _calendar.Calendar(firstweekday=_calendar.MONDAY)
        months = []
        for year, month, is_current in months_data:
            dt = datetime(year, month, 1)
            weeks = []
            for week in cal.monthdayscalendar(year, month):
                row = []
                for day in week:
                    cell = {'n': day}
                    if day == 0:
                        cell['kind'] = 'empty'
                    else:
                        has_event = (
                            year in self.events_docs
                            and month in self.events_docs[year]
                            and day in self.events_docs[year][month]
                            and len(self.events_docs[year][month][day]) > 0
                        )
                        is_today = (year == now.year and month == now.month and day == now.day)
                        if is_today:
                            cell['kind'] = 'today'
                        elif has_event:
                            cell['kind'] = 'event'
                            cell['url'] = "events_%04d%02d%02d.html" % (year, month, day)
                        else:
                            cell['kind'] = 'day'
                    row.append(cell)
                weeks.append(row)
            months.append({
                'name': dt.strftime('%B %Y'),
                'current': is_current,
                'weeks': weeks,
            })
        title = "%s / %s / %s" % (
            datetime(months_data[0][0], months_data[0][1], 1).strftime('%b'),
            datetime(months_data[1][0], months_data[1][1], 1).strftime('%b'),
            datetime(months_data[2][0], months_data[2][1], 1).strftime('%b %Y'),
        )
        return {'title': title, 'months': months}

    def _build_index_events_panel(self, now):
        """Rows for current and next month events."""
        cur_first = now.replace(day=1)
        cur_last = cur_first.replace(day=monthrange(cur_first.year, cur_first.month)[1])
        nxt_first = cur_last + timedelta(days=1)

        today = now.date()

        def rows_for(year, month):
            rows = []
            try:
                days = self.events_docs[year][month]
            except KeyError:
                return rows
            for day in sorted(days.keys()):
                if datetime(year, month, day).date() < today:
                    continue
                for docId in days[day]:
                    props = self.srvdtb.get_doc_properties(docId)
                    title = props.get('Title', docId)
                    if isinstance(title, list):
                        title = title[0] if title else docId
                    url = props.get('Title_Url', docId.replace('.adoc', '.html'))
                    categories = self.srvdtb.get_values(docId, 'Category')
                    category = categories[0] if categories and categories[0] else ''
                    rows.append({
                        'date': datetime(year, month, day).strftime('%b %d'),
                        'title': title,
                        'url': url,
                        'category': category,
                    })
            return rows

        return {
            'current': {
                'label': '%s · Current' % cur_first.strftime('%B %Y'),
                'url': 'events_%04d%02d.html' % (cur_first.year, cur_first.month),
                'rows': rows_for(cur_first.year, cur_first.month),
            },
            'next': {
                'label': '%s · Next' % nxt_first.strftime('%B %Y'),
                'url': 'events_%04d%02d.html' % (nxt_first.year, nxt_first.month),
                'rows': rows_for(nxt_first.year, nxt_first.month),
            },
        }

    def _build_index_recent_events(self, now):
        """Events from yesterday back to one month ago, newest first."""
        yesterday = datetime(now.year, now.month, now.day) - timedelta(days=1)
        month_ago_month = now.month - 1 if now.month > 1 else 12
        month_ago_year = now.year if now.month > 1 else now.year - 1
        month_ago_day = min(now.day, monthrange(month_ago_year, month_ago_month)[1])
        month_ago = datetime(month_ago_year, month_ago_month, month_ago_day)

        rows = []
        for year in sorted(self.events_docs.keys()):
            for month in sorted(self.events_docs[year].keys()):
                for day in sorted(self.events_docs[year][month].keys()):
                    d = datetime(year, month, day)
                    if d < month_ago or d > yesterday:
                        continue
                    for docId in self.events_docs[year][month][day]:
                        props = self.srvdtb.get_doc_properties(docId)
                        title = props.get('Title', docId)
                        if isinstance(title, list):
                            title = title[0] if title else docId
                        url = props.get('Title_Url', docId.replace('.adoc', '.html'))
                        categories = self.srvdtb.get_values(docId, 'Category')
                        category = categories[0] if categories and categories[0] else ''
                        rows.append({
                            'date': d.strftime('%b %d'),
                            'title': title,
                            'url': url,
                            'category': category,
                        })
        rows.reverse()
        return rows

    def _build_year_calendar_html(self, year):
        """Generate a 12-month HTML calendar grid for events.html."""
        MONTH_NAMES = [
            'January', 'February', 'March', 'April',
            'May', 'June', 'July', 'August',
            'September', 'October', 'November', 'December',
        ]
        WEEKDAY_ABBR = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        now = datetime.now()
        cal = _calendar.Calendar(firstweekday=_calendar.MONDAY)

        parts = ['<div class="kb-evcal-grid">']
        for month in range(1, 13):
            mname = MONTH_NAMES[month - 1]
            has_month = (
                year in self.events_docs
                and month in self.events_docs[year]
            )
            if has_month:
                month_url = f'events_{year:04d}{month:02d}.html'
                caption = f'<a href="{month_url}">{mname}</a>'
            else:
                caption = mname

            parts.append('<div class="kb-evcal-month">')
            parts.append(f'<div class="kb-evcal-mname">{caption}</div>')
            parts.append('<table><thead><tr>')
            for wd in WEEKDAY_ABBR:
                parts.append(f'<th>{wd}</th>')
            parts.append('</tr></thead><tbody>')

            for week in cal.monthdayscalendar(year, month):
                parts.append('<tr>')
                for day in week:
                    if day == 0:
                        parts.append('<td></td>')
                        continue
                    has_event = (
                        year in self.events_docs
                        and month in self.events_docs[year]
                        and day in self.events_docs[year][month]
                    )
                    is_today = (
                        year == now.year
                        and month == now.month
                        and day == now.day
                    )
                    url = f'events_{year:04d}{month:02d}{day:02d}.html'
                    if has_event and is_today:
                        parts.append(f'<td class="kb-evcal-today-event"><a href="{url}">{day}</a></td>')
                    elif has_event:
                        parts.append(f'<td class="kb-evcal-event"><a href="{url}">{day}</a></td>')
                    elif is_today:
                        parts.append(f'<td class="kb-evcal-today">{day}</td>')
                    else:
                        parts.append(f'<td>{day}</td>')
                parts.append('</tr>')

            parts.append('</tbody></table></div>')
        parts.append('</div>')
        return ''.join(parts)

    def build_events(self, doclist):
        TPL_PAGE_EVENTS_DAYS = self.template('EVENTCAL_PAGE_EVENTS_DAYS')
        TPL_PAGE_EVENTS_MONTHS = self.template('EVENTCAL_PAGE_EVENTS_MONTHS')
        SORT = "Date"
        # Get events dates
        for docId in doclist:
            props = self.srvdtb.get_doc_properties(docId)
            timestamp = self.srvdtb.get_doc_timestamp(docId)
            if timestamp is None:
                continue
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
                docs.append(docId)
                self.events_docs[y][m][d] = docs
            except Exception as error:
                # Doc doesn't have a valid date field. Skip it.
                self.log.error(f"[THEME] DATE_INVALID doc={os.path.basename(docId)} timestamp={timestamp}")
                self.log.error(f"[THEME] ERROR {error}")

                raise

        kbdict = self.srvbes.get_kb_dict()
        base_var = self.get_theme_var()
        # Build day event pages
        must_compile_month = set()
        must_compile_year = set()
        for year in self.events_docs:
            for month in self.events_docs[year]:
                for day in self.events_docs[year][month]:
                    EVENT_PAGE_DAY = "events_%4d%02d%02d" % (year, month, day)
                    pagename = os.path.join(self.srvbes.get_path('cache'), "%s.html" % EVENT_PAGE_DAY)
                    doclist = self.events_docs[year][month][day]
                    must_compile_day = False
                    for docId in doclist:
                        doc_changed = kbdict['document'][docId]['compile']
                        doc_not_cached = not os.path.exists(pagename)
                        if doc_changed or doc_not_cached:
                            must_compile_day = True
                            break
                    #self.log.debug(f"[{EVENT_PAGE_DAY}.adoc] targeting PAGE[{os.path.basename(pagename)}] COMPILE[{must_compile_day}]")
                    if must_compile_day:
                        must_compile_month.add("%4d%02d" % (year, month))
                        must_compile_year.add("%4d" % (year))
                        edt = guess_datetime("%4d.%02d.%02d" % (year, month, day))
                        var = base_var
                        var['page'] = {}
                        headers = []
                        var['page']['datatable'] = self.build_datatable(headers, doclist)
                        var['page']['title'] = edt.strftime("Events on %A, %B %d %Y")
                        html = TPL_PAGE_EVENTS_DAYS.render(var=var)
                        self.distribute_adoc(EVENT_PAGE_DAY, html)

                        #FIXME
                        human_title = get_human_datetime_day(edt)
                        self.srvdtb.add_document(f"{EVENT_PAGE_DAY}.adoc")
                        self.srvdtb.add_document_key(f"{EVENT_PAGE_DAY}.adoc", 'Title', f"Events on {human_title}")
                        self.srvdtb.add_document_key(f"{EVENT_PAGE_DAY}.adoc", 'SystemPage', 'Yes')
                    else:
                        self.distribute_html(EVENT_PAGE_DAY, pagename)
                    self.srvbes.add_target(f"{EVENT_PAGE_DAY}.adoc", f"{EVENT_PAGE_DAY}.html")


        # Build month event pages
        for year in self.events_docs:
            for month in self.events_docs[year]:
                thismonth = "%4d%02d" % (year, month)
                EVENT_PAGE_MONTH = "events_%4d%02d" % (year, month)
                month_pagename = os.path.join(self.srvbes.get_path('cache'), "%s.html" % EVENT_PAGE_MONTH)
                if thismonth in must_compile_month or not os.path.exists(month_pagename):
                    var = base_var
                    var['page'] = {}
                    doclist = []
                    edt = guess_datetime("%4d.%02d.01" % (year, month))
                    for day in self.events_docs[year][month]:
                        doclist.extend(self.events_docs[year][month][day])
                    var['doclist'] = docs
                    headers = []
                    var['page']['datatable'] = self.build_datatable(headers, doclist)
                    var['page']['title'] = edt.strftime("Events on %B, %Y")
                    html = TPL_PAGE_EVENTS_MONTHS.render(var=var)
                    self.distribute_adoc(EVENT_PAGE_MONTH, html)

                    human_title = get_human_datetime_month(edt)
                    self.srvdtb.add_document(f"{EVENT_PAGE_MONTH}.adoc")
                    self.srvdtb.add_document_key(f"{EVENT_PAGE_MONTH}.adoc", 'Title', f"Events on {human_title}")
                    self.srvdtb.add_document_key(f"{EVENT_PAGE_MONTH}.adoc", 'SystemPage', 'Yes')

                else:
                    self.distribute_html(EVENT_PAGE_MONTH, month_pagename)
                self.srvbes.add_target(f"{EVENT_PAGE_MONTH}.adoc", f"{EVENT_PAGE_MONTH}.html")

        # Build year event pages
        for year in sorted(self.dey.keys(), reverse=True):
            var = base_var
            var['page'] = {}
            headers = []
            doclist = []
            EVENT_PAGE_YEAR = "events_%4d" % year
            PAGE = self.template('EVENTCAL_PAGE_EVENTS_YEARS')
            page_name = "events_%4d" % year
            year_pagename = os.path.join(self.srvbes.get_path('cache'), "%s.html" % EVENT_PAGE_YEAR)
            if str(year) in must_compile_year or not os.path.exists(year_pagename):
                for month in self.events_docs[year]:
                    for day in self.events_docs[year][month]:
                        doclist.extend(self.events_docs[year][month][day])
                var['page']['title'] = f"Archive / {year}"
                var['page']['datatable'] = self.build_datatable(headers, doclist)
                self.distribute_adoc(page_name, PAGE.render(var=var))
                self.srvdtb.add_document(f"{EVENT_PAGE_YEAR}.adoc")
                self.srvdtb.add_document_key(f"{EVENT_PAGE_YEAR}.adoc", 'Title', f"Archive / {year}")
                self.srvdtb.add_document_key(f"{EVENT_PAGE_YEAR}.adoc", 'SystemPage', 'Yes')

            else:
                self.distribute_html(EVENT_PAGE_YEAR, year_pagename)
            self.srvbes.add_target(f"{EVENT_PAGE_YEAR}.adoc", f"{EVENT_PAGE_YEAR}.html")

        return must_compile_year

    def build_year_pagination(self, years):
        EVENTCAL_YEAR_PAGINATION = self.template('EVENTCAL_YEAR_PAGINATION')
        EVENTCAL_YEAR_PAGINATION_ITEM = self.template('EVENTCAL_YEAR_PAGINATION_ITEM')
        var = {}
        var['items'] = ''
        ITEMS = ''
        for yp in sorted(years, reverse=True):
            item = {}
            item['year'] = yp

            total = 0
            for month in self.events_docs[yp]:
                for day in self.events_docs[yp][month]:
                    total += len(self.events_docs[yp][month][day])
            item['year_count'] = total
            ITEMS += EVENTCAL_YEAR_PAGINATION_ITEM.render(var=item)
        var['items'] = ITEMS
        return EVENTCAL_YEAR_PAGINATION.render(var=var)

    def build_page_events(self):
        doclist = []
        ecats = {}
        repo = self.srvbes.get_dict('repo')
        try:
            event_types = repo['events']
        except:
            event_types = []
        # ~ self.log.debug(" - Event types: %s", ', '.join(event_types))

        for docId in self.srvdtb.get_documents():
            if self.srvdtb.is_system(docId):
                continue
            category = self.srvdtb.get_values(docId, 'Category')[0]
            if category in event_types:
                try:
                    docs = ecats[category]
                    docs.add(docId)
                    ecats[category] = docs
                except:
                    docs = set()
                    docs.add(docId)
                    ecats[category] = docs

                doclist.append(docId)
                title = self.srvdtb.get_values(docId, 'Title')[0]
        must_compile_year = self.build_events(doclist)

        events_pagename = os.path.join(self.srvbes.get_path('cache'), 'events.html')
        if must_compile_year or not os.path.exists(events_pagename):
            years_data = []
            for year in sorted(self.dey.keys(), reverse=True):
                doclist_year = []
                for month in self.events_docs[year]:
                    for day in self.events_docs[year][month]:
                        doclist_year.extend(self.events_docs[year][month][day])
                total = len(doclist_year)
                calendar_html = self._build_year_calendar_html(year)
                datatable_html = self.build_datatable([], doclist_year, table_id=f'kb4it-datatable-{year}')
                years_data.append({
                    'year': year,
                    'count': total,
                    'calendar': calendar_html,
                    'datatable': datatable_html,
                })
            events = {'years': years_data}
            page = self.template('PAGE_EVENTS')
            self.distribute_adoc('events', page.render(var=events))
        else:
            self.distribute_html('events', events_pagename)

        self.srvdtb.add_document('events.adoc')
        self.srvdtb.add_document_key('events.adoc', 'Title', 'Events')
        self.srvdtb.add_document_key('events.adoc', 'SystemPage', 'Yes')

    def build(self):
        """Create standard pages for default theme"""
        var = self.get_theme_var()
        self.app.register_service('Timeline', Timeline())
        self.build_page_events()
        self.build_page_properties()
        self.build_page_stats()
        self.build_page_bookmarks()
        self.build_page_add()
        self.build_page_index(var)
        self.build_page_index_all()
        self.create_page_about_kb4it()
        self.create_page_help()

    def page_hook_pre(self, var):
        var['related'] = ''
        var['metadata'] = ''
        var['source'] = ''
        var['actions'] = ''
        return var

    def page_hook_post(self, var):
        return var

    def build_page_properties(self):
        """Create properties page"""
        #if self.srvbes.get_value('runtime', 'nck') == 0:
        #    func_name = sys._getframe().f_code.co_name
        #    self.log.debug(f"No changes in keys. Skip '{func_name}'")
        #    self.srvbes.add_target('properties.adoc', 'properties.html')
        #    return

        TPL_PROPS_PAGE = self.template('PAGE_PROPERTIES')
        TPL_KEY_MODAL_BUTTON = self.template('KEY_MODAL_BUTTON')
        max_frequency = self.get_maxkv_freq()
        all_keys = self.srvdtb.get_all_keys()
        var = self.get_theme_var()
        var['buttons'] = []
        log_max = math.log(1 + max_frequency) if max_frequency > 0 else 1
        for key in all_keys:
            ignored_keys = self.srvdtb.get_ignored_keys()
            if key not in ignored_keys:
                vbtn = {}
                vbtn['content'] = self.build_tagcloud_from_key(key)
                values = self.srvdtb.get_all_values_for_key(key)
                frequency = len(values)
                self.log.debug(f"[THEME] KEY key={key} frequency={frequency}")
                weight = math.log(1 + frequency) / log_max if log_max else 0.0
                vbtn['key'] = key
                vbtn['vfkey'] = valid_filename(key)
                vbtn['count'] = frequency
                vbtn['weight'] = round(weight, 3)
                vbtn['tooltip'] = "%d values" % frequency
                button = TPL_KEY_MODAL_BUTTON.render(var=vbtn)
                var['buttons'].append(button)
        content = TPL_PROPS_PAGE.render(var=var)
        self.distribute_adoc('properties', content)

        self.srvdtb.add_document('properties.adoc')
        self.srvdtb.add_document_key('properties.adoc', 'Title', 'Properties')
        self.srvdtb.add_document_key('properties.adoc', 'SystemPage', 'Yes')

    def build_tagcloud_from_key(self, key):
        """Create a tag cloud based on key values."""
        #if self.srvbes.get_value('runtime', 'nck') == 0:
        #    func_name = sys._getframe().f_code.co_name
        #    self.log.debug(f"No changes in keys. Skip '{func_name}'")
        #    return

        dkeyurl = {}
        for docId in self.srvdtb.get_documents():
            tags = self.srvdtb.get_values(docId, key)
            url = os.path.basename(docId)[:-5]
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
            var = self.get_theme_var()
            var['items'] = []
            log_max = math.log(1 + max_frequency) if max_frequency > 0 else 1
            for word in lwords:
                frequency = len(dkeyurl[word])
                weight = math.log(1 + frequency) / log_max if log_max else 0.0
                item = {}
                item['url'] = "%s_%s.html" % (valid_filename(key), valid_filename(word))
                item['tooltip'] = "%d documents" % frequency
                item['word'] = word
                item['count'] = frequency
                item['weight'] = round(weight, 3)
                var['items'].append(item)
            html = TPL_WORDCLOUD.render(var=var)
        else:
            html = ''

        return html

    def get_maxkv_freq(self):
        """Calculate max frequency for all keys"""
        maxkvfreq = 0
        for key in self.srvdtb.get_theme_keys():
            values = self.srvdtb.get_all_values_for_key(key)
            if len(values) > maxkvfreq:
                maxkvfreq = len(values)
        return maxkvfreq

    def build_page_stats(self):
        """Create stats page"""
        #if self.srvbes.get_value('runtime', 'nck') == 0:
        #    func_name = sys._getframe().f_code.co_name
        #    self.log.debug(f"No changes in keys. Skip '{func_name}'")
        #    self.srvbes.add_target('stats.adoc', 'stats.html')
        #    return

        TPL_PAGE_STATS = self.template('PAGE_STATS')
        var = self.get_theme_var()
        var['count_docs'] = self.srvdtb.get_documents_count()
        keys = self.srvdtb.get_theme_keys()
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
        self.distribute_adoc('stats', stats)

        self.srvdtb.add_document('stats.adoc')
        self.srvdtb.add_document_key('stats.adoc', 'Title', 'Stats')
        self.srvdtb.add_document_key('stats.adoc', 'SystemPage', 'Yes')

    def build_page_add(self):
        """Create the 'Add document' helper page with per-category skeletons."""
        TPL = self.template('PAGE_ADD')
        var = self.get_theme_var()
        var['page']['title'] = 'Add document'
        runtime = self.srvbes.get_dict("runtime")
        skeletons_dir = os.path.join(runtime["theme"]["templates"], "skeletons")
        category_ids = ['change', 'incident', 'meeting', 'note', 'post', 'procedure', 'report', 'task']
        skeletons = {}
        for cat_id in category_ids:
            skel_path = os.path.join(skeletons_dir, f"{cat_id.upper()}-SKELETON.adoc")
            try:
                with open(skel_path, encoding="utf-8") as fh:
                    skeletons[cat_id] = fh.read()
            except OSError:
                skeletons[cat_id] = f"= Title of the {cat_id.capitalize()}\n\n// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE\n\n== Overview\n\nDescribe here.\n"
        var['page']['skeletons'] = skeletons
        page = TPL.render(var=var)
        self.distribute_adoc('add', page)
        self.srvdtb.add_document('add.adoc')
        self.srvdtb.add_document_key('add.adoc', 'Title', 'Add document')
        self.srvdtb.add_document_key('add.adoc', 'SystemPage', 'Yes')

    def build_page_index_all(self):
        """Create a page with all documents"""
        #if self.srvbes.get_value('runtime', 'ncd') == 0:
        #    func_name = sys._getframe().f_code.co_name
        #    self.log.debug(f"No changes in documents. Skip '{func_name}'")
        #    self.srvbes.add_target('all.adoc', 'all.html')
        #    return

        TPL_PAGE_ALL = self.template('PAGE_ALL')
        var = self.get_theme_var()
        doclist = []
        for docId in self.srvdtb.get_documents():
            doclist.append(docId)
        headers = []
        datatable = self.build_datatable(headers, doclist)
        var['content'] = datatable
        page = TPL_PAGE_ALL.render(var=var)
        self.distribute_adoc('all', page)

        self.srvdtb.add_document('all.adoc')
        self.srvdtb.add_document_key('all.adoc', 'Title', 'All documents')
        self.srvdtb.add_document_key('all.adoc', 'SystemPage', 'Yes')

        return page

    def extract_toc(self, source):
        """Extract TOC from Asciidoctor generated HTML code and
        make it theme dependent."""
        toc = ''
        items = []
        lines = source.split('\n')
        s = e = n = 0
        var = self.get_theme_var()
        TOC_LI_TOP = self.template('HTML_TOC_LI')
        TOC_SECTLEVEL1 = self.template('HTML_TOC_SECTLEVEL1')
        TOC_SECTLEVEL2 = self.template('HTML_TOC_SECTLEVEL2')
        TOC_SECTLEVEL3 = self.template('HTML_TOC_SECTLEVEL3')
        TOC_SECTLEVEL4 = self.template('HTML_TOC_SECTLEVEL4')

        for line in lines:
            if line.find("toctitle") > 0:
                s = n + 1
            if s > 0:
                if line.startswith('</div>') and n > s:
                    e = n
                    break
            n = n + 1

        if s > 0 and e > s:
            for line in lines[s:e]:
                if line.startswith('<li><a href='):
                    line = line.replace("<li><a ", TOC_LI_TOP.render(var=var))
                else:
                    line = line.replace("sectlevel1", TOC_SECTLEVEL1.render(var=var))
                    line = line.replace("sectlevel2", TOC_SECTLEVEL2.render(var=var))
                    line = line.replace("sectlevel3", TOC_SECTLEVEL3.render(var=var))
                    line = line.replace("sectlevel4", TOC_SECTLEVEL4.render(var=var))
                items.append(line)
            toc = '\n'.join(items)
        return toc

    def build_page(self, path_adoc):
        """
        Build the final HTML Page

        At this point, the compilation for the asciidoc document has
        finished successfully, and therefore the html page can be built.

        The Builder receives the asciidoc document filepath. It means,
        that another file with extension .html should also exist.

        The html page is built by inserting the html header at the
        beguinning, appending the footer at the end, and applying the
        necessary transformations in the body.

        Finally, the html page created by asciidoctor is overwritten.
        """
        path_hdoc = path_adoc.replace('.adoc', '.html')
        basename_adoc = os.path.basename(path_adoc)
        basename_hdoc = os.path.basename(path_hdoc)
        exists_adoc = os.path.exists(path_adoc) # it should be true
        exists_hdoc = os.path.exists(path_hdoc) # it should be true

        if not exists_hdoc:
            self.log.error(f"[THEME] HTML_MISSING doc={basename_adoc}")
        else:
            #self.log.debug("DOC[%s] transformation started", basename_hdoc)
            THEME_ID = self.srvbes.get_value('theme', 'id')
            HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
            HTML_BODY = self.template('HTML_BODY')
            HTML_FOOTER = self.template('HTML_FOOTER')
            var = self.get_theme_var()
            now = datetime.now()
            timestamp = get_human_datetime(now)
            keys = self.srvdtb.get_doc_properties(basename_adoc)
            system_page = self.srvdtb.is_system(basename_adoc)

            with open(path_adoc, 'r') as fpa:
                source_adoc = fpa.read()

            with open(path_hdoc, 'r') as fph:
                source_html = fph.read()

            var['toc'] = self.extract_toc(source_html)
            var['has_toc'] = True

            # Do not show metadata for system pages
            if self.srvdtb.is_system(basename_adoc):
                var['SystemPage'] = True
                TPL_HTML_HEADER_MENU_CONTENTS_DISABLED = self.template('HTML_HEADER_MENU_CONTENTS_DISABLED')
                HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_DISABLED.render()
                var['metadata'] = ""
            else:
                var['SystemPage'] = False
                TPL_HTML_HEADER_MENU_CONTENTS_ENABLED = self.template('HTML_HEADER_MENU_CONTENTS_ENABLED')
                HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_ENABLED.render(var=var)
                var['metadata'] = self.build_metadata_section(basename_adoc)

            var['menu_contents'] = HTML_TOC
            var['keys'] = keys
            var['page']['title'] = 'No title found...'
            var['page']['title-tooltip'] = 'No title found...'
            try:
                var['page']['title'] = ellipsize_text(keys['Title'])
                var['page']['title-tooltip'] = keys['Title']
            except Exception as error:
                pass
            var['basename_adoc'] = basename_adoc
            var['basename_hdoc'] = basename_hdoc
            var['source_adoc'] = source_adoc
            var['source_html'] = self.apply_transformations(source_html) # <---
            actions = self.get_page_actions(var)
            var['actions'] = actions
            var['timestamp'] = timestamp

            HEADER = HTML_HEADER_COMMON.render(var=var)
            BODY = HTML_BODY.render(var=var)
            FOOTER = HTML_FOOTER.render(var=var)

            HTML = ""
            HTML += HEADER
            HTML += BODY
            HTML += FOOTER

            with open(path_hdoc, 'w') as fhtml:
                tree = etree.fromstring(HTML, parser)
                pretty_html = etree.tostring(tree, pretty_print=True, method="html").decode()
                fhtml.write(f"<!DOCTYPE html>\n{pretty_html}")

    def build_page_key(self, key, values):
        """Create page for a key."""
        TPL_PAGE_KEY = self.template('PAGE_KEY')
        var = self.get_theme_var()
        var['title'] = key
        var['cloud'] = self.build_tagcloud_from_key(key)
        var['leader'] = []
        var['key_values'] = {}
        for value in values:
            item = {}
            docs = self.srvdtb.get_docs_by_key_value(key, value)
            item['count'] = len(docs)
            item['vfkey'] = valid_filename(key)
            item['vfvalue'] = valid_filename(value)
            item['name'] = value
            var['leader'].append(item)

        adoc = TPL_PAGE_KEY.render(var=var)
        var['pagename'] = "%s" % valid_filename(key)
        self.distribute_adoc(var['pagename'], adoc)

        self.srvdtb.add_document(f"{var['pagename']}.adoc")
        self.srvdtb.add_document_key(f"{var['pagename']}.adoc", 'Title', f"{var['title']}")
        self.srvdtb.add_document_key(f"{var['pagename']}.adoc", 'SystemPage', 'Yes')

        self.log.debug(f"[THEME] KEY_TARGET key={key} resource={var['pagename']}")

    def build_page_key_value(self, kvpath):
        key, value, COMPILE_VALUE = kvpath
        TPL_PAGE_KEY_VALUE = self.template('PAGE_KEY_VALUE')
        docs = self.srvbes.get_kbdict_value(key, value, new=True)
        sorted_docs = self.srvdtb.sort_by_date(docs)
        pagename = "%s_%s" % (valid_filename(key), valid_filename(value))
        var = self.get_theme_var()
        var['key'] = key
        var['value'] = value
        var['vfkey'] = valid_filename(key)
        var['title'] = '%s: %s' % (key, value)
        var['pagename'] = pagename
        var['doclist'] = sorted_docs
        var['compile'] = COMPILE_VALUE
        var['has_toc'] = False

        datatable = self.build_datatable([], sorted_docs)
        var['page']['dt_documents'] = datatable

        if var['compile']:
            adoc = TPL_PAGE_KEY_VALUE.render(var=var)
            self.distribute_adoc(var['pagename'], adoc)

            self.srvdtb.add_document(f"{var['pagename']}.adoc")
            self.srvdtb.add_document_key(f"{var['pagename']}.adoc", 'Title', f"{var['title']}")
            self.srvdtb.add_document_key(f"{var['pagename']}.adoc", 'SystemPage', 'Yes')
            # ~ self.log.debug(f"KEY[{key}] VALUE[{value}] targets to RESOURCE[{var['pagename']}]")

    def build_page_bookmarks(self):
        """Create bookmarks page."""
        #if self.srvbes.get_value('runtime', 'ncd') == 0:
        #    func_name = sys._getframe().f_code.co_name
        #    self.log.debug(f"No changes in documents. Skip '{func_name}'")
        #    self.srvbes.add_target('bookmarks.adoc', 'bookmarks.html')
        #    return

        TPL_PAGE_BOOKMARKS = self.template('PAGE_BOOKMARKS')
        var = self.get_theme_var()
        doclist = []
        for docId in self.srvdtb.get_documents():
            bookmark = self.srvdtb.get_values(docId, 'Bookmark')[0]
            doc_bookmarked = bookmark == 'Yes' or bookmark == 'True'
            self.log.debug(f"[THEME] BOOKMARK_CHECK doc={docId} bookmark={bookmark} is_bookmarked={doc_bookmarked}")
            if doc_bookmarked:
                doclist.append(docId)

        self.log.debug(f"[THEME] BOOKMARKS_FOUND n={len(doclist)}")
        headers = []
        datatable = self.build_datatable(headers, doclist)

        self.srvdtb.add_document('bookmarks.adoc')
        self.srvdtb.add_document_key('bookmarks.adoc', 'Title', 'Bookmarks')
        self.srvdtb.add_document_key('bookmarks.adoc', 'SystemPage', 'Yes')

        var['page']['title'] = 'Bookmarks'
        var['page']['dt_bookmarks'] = datatable
        page = TPL_PAGE_BOOKMARKS.render(var=var)
        self.distribute_adoc('bookmarks', page)

        self.log.debug("[THEME] BOOKMARKS_PAGE_CREATED")

        return page

    def get_page_actions(self, var):
        TPL_SECTION_ACTIONS = self.template('SECTION_ACTIONS')
        return TPL_SECTION_ACTIONS.render(var=var)

    def get_related(self, docId):
        """Get a list of related documents for each tag"""
        # DISABLED:
        # Related section code works.
        # However, because of the workflow do not detect which sources
        # have been added or removed, if any of the remaining sources do
        # not change, the related section will not be rebuilt again.
        # As a consecuence, documents displayed in the related section
        # might not exist. Or the other way around, the new documents
        # might exist, but they are not referenced.
        # Workaround: just browse the metadata from the document menu

        TPL_SECTION_RELATED = self.template('SECTION_RELATED')
        blocked_keys = self.srvdtb.get_blocked_keys()
        doclist = set()
        doc_keys = self.srvdtb.get_doc_properties(docId)
        filtered_keys = [key for key in doc_keys if key not in blocked_keys]
        for key in filtered_keys:
            for value in self.srvdtb.get_values(docId, key):
                for docId in self.srvdtb.get_docs_by_key_value(key, value):
                    doclist.add(docId)

        doclist.remove(docId)
        self.log.debug(f"[THEME] RELATED_FOUND doc={docId} n={len(doclist)}")

        headers = []
        var = self.get_theme_var()
        var['datatable'] = self.build_datatable(headers, doclist)
        html_related = TPL_SECTION_RELATED.render(var=var)
        return html_related

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

    def get_html_values_from_key(self, docId, key):
        """Return the html link for a value."""
        html = []

        values = self.srvdtb.get_values(docId, key)
        for value in values:
            url = "%s_%s.html" % (key, value)
            html.append((url, value))
        return html

    def build_metadata_section(self, docId):
        """Return a html block for displaying metadata (keys and values)."""
        try:
            TPL_METADATA_SECTION = self.template('METADATA_SECTION')
            custom_keys = self.srvdtb.get_custom_keys(os.path.basename(docId))
            var = {}
            var['items'] = []
            for key in custom_keys:
                ckey = {}
                ckey['doc'] = docId
                ckey['key'] = key
                ckey['vfkey'] = valid_filename(key)
                try:
                    values = self.get_html_values_from_key(docId, key)
                    ckey['labels'] = self.get_labels(values)
                    var['items'].append(ckey)
                except Exception as error:
                    self.log.error(f"[THEME] KEY_FAIL key={key} error={error}")
                    raise
            html = TPL_METADATA_SECTION.render(var=var)
        except Exception as error:
            self.log.error(f"[THEME] METADATA_FAIL doc={docId} error={error}")
            html = ''
            raise
        return html

    def generate_sources(self):
        """This theme doesn't generate sources, yet."""
        # ~ self.log.debug("No sources generated by this theme")
        pass

    def check_config(self):
        go = True
        repo = self.app.get_repo_config_dict()
        self.log.debug("[THEME] CONFIG_CHECK_START")

        self.log.info(f"[THEME] CONFIG key=title value='{repo['title']}'")
        if len(repo['title']) == 0:
            self.log.error("[THEME] CONFIG_FAIL key=title reason=empty")
            go = False

        self.log.info(f"[THEME] CONFIG key=datatable n={len(repo['datatable'])}")
        if len(repo['datatable']) == 0:
            self.log.error("[THEME] CONFIG_FAIL key=datatable reason=empty")
            go = False

        self.log.info(f"[THEME] CONFIG key=events n={len(repo['events'])}")
        if len(repo['events']) == 0:
            self.log.error("[THEME] CONFIG_FAIL key=events reason=empty")
            go = False

        self.log.info(f"[THEME] CONFIG key=git value={repo['git']}")
        if repo['git']:
            git_props = ['git_branch', 'git_path', 'git_repo', 'git_server', 'git_user']
            for git_prop in sorted(git_props):
                if len(repo[git_prop]) == 0:
                    self.log.warning(f"[THEME] CONFIG_FAIL key={git_prop} reason=empty")

        self.log.info(f"[THEME] CONFIG key=ignored_keys n={len(repo['ignored_keys'])}")
        if len(repo['ignored_keys']) == 0:
            self.log.warning("[THEME] CONFIG_WARN key=ignored_keys reason=empty")

        self.log.info(f"[THEME] CONFIG key=logo value={repo['logo']}")
        if not os.path.exists(repo['logo']):
            self.log.warning(f"[THEME] CONFIG_WARN key=logo reason=missing path={repo['logo']}")

        self.log.info(f"[THEME] CONFIG key=logo_alt value='{repo['logo_alt']}'")
        if not os.path.exists(repo['logo_alt']):
            self.log.warning("[THEME] CONFIG_WARN key=logo_alt reason=missing")

        self.log.info(f"[THEME] CONFIG key=menu n={len(repo['menu'])}")
        if len(repo['menu']) == 0:
            self.log.warning("[THEME] CONFIG_WARN key=menu reason=empty")

        self.log.info("[THEME] CONFIG key=sort value=Date")

        self.log.info(f"[THEME] CONFIG key=source value='{repo['source']}'")
        if len(repo['source']) == 0:
            self.log.error("[THEME] CONFIG_FAIL key=source reason=empty")
            go = False
        elif not os.path.exists(repo['source']):
            self.log.error(f"[THEME] CONFIG_FAIL key=source reason=missing path={repo['source']}")
            go = False

        self.log.info(f"[THEME] CONFIG key=target value='{repo['target']}'")
        if len(repo['target']) == 0:
            self.log.error("[THEME] CONFIG_FAIL key=target reason=empty")
            go = False
        elif not os.path.exists(repo['target']):
            self.log.error(f"[THEME] CONFIG_FAIL key=target reason=missing path={repo['target']}")
            go = False

        self.log.info(f"[THEME] CONFIG key=webserver value={repo['webserver']}")
        if repo['webserver']:
            self.log.info(f"[THEME] CONFIG key=timeline n={len(repo['timeline'])}")
            if len(repo['timeline']) == 0:
                self.log.error("[THEME] CONFIG_FAIL key=timeline reason=empty")
                go = False

        if not go:
            example = os.path.join(ENV['GPATH']['THEMES'], 'techdoc', 'example', 'repo', 'config', 'repo.json')
            self.log.info(f"[THEME] CONFIG_EXAMPLE path={example}")

        self.log.debug("[THEME] CONFIG_CHECK_END")
        return go

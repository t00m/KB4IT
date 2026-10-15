#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: default theme script
"""

import calendar as _calendar
import json
import os
import shutil
import zipfile
from calendar import monthrange
from collections import Counter
from datetime import datetime, timedelta
from lxml import etree

from kb4it.core.util import (ellipsize_text, get_day, get_font_size,
                             get_human_datetime, get_human_datetime_day,
                             get_human_datetime_month, get_human_datetime_year,
                             get_month, get_source_docs, get_year,
                             guess_datetime, html_id_for, human_size,
                             slugify, source_ext,
                             valid_filename)
from kb4it.services.themekit import DocumentTheme

parser = etree.HTMLParser()

PRIORITY_RANK = {
    'Critical': 0,
    'Very high': 1,
    'High': 2,
    'Medium': 3,
    'Normal': 4,
    'Low': 5,
}

PRIORITY_CSS = {
    'Critical': 'uk-label-danger',
    'Very high': 'uk-label-danger',
    'High': 'uk-label-danger',
    'Medium': 'uk-label-warning',
    'Normal': 'uk-label-warning',
    'Low': 'kb-label-muted',
    'Unknown': 'kb-label-muted',
}

STATUS_CSS = {
    'New': 'uk-label-danger',
    'Open': 'uk-label-danger',
    'Draft': 'uk-label-warning',
    'Planned': 'uk-label-warning',
    'Completed': 'uk-label-success',
    'Finished': 'uk-label-success',
    'Released': 'uk-label-success',
    'Successful': 'uk-label-success',
    'Deprecated': 'kb-label-muted',
    'Obsolete': 'kb-label-muted',
}

OPEN_STATUSES = {'New', 'Open', 'Draft', 'Planned'}

OPEN_ITEM_CATEGORIES = ['Incident', 'Change', 'Task']


def priority_css(value):
    """Return the label modifier class for a Priority value."""
    return PRIORITY_CSS.get(value, 'kb-label-muted')


def status_css(value):
    """Return the label modifier class for a Status value."""
    return STATUS_CSS.get(value, 'kb-label-muted')


class Theme(DocumentTheme):
    dey = {}
    events_docs = {}

    def _initialize(self):
        super()._initialize()
        self.dey = {}
        self.events_docs = {}

    def datatable_value_link(self, properties, key, value):
        """Priority and Status values show as colored labels."""
        link = super().datatable_value_link(properties, key, value)
        if key == 'Priority' and value:
            link['class'] = 'uk-label kb-dt-label %s' % priority_css(value)
        elif key == 'Status' and value:
            link['class'] = 'uk-label kb-dt-label %s' % status_css(value)
        return link

    def build_page_index(self, var):
        """Create landing page."""
        repo = self.srvbes.get_dict('repo')
        runtime = self.srvbes.get_dict('runtime')
        filenames = runtime['docs']['filenames']
        now = datetime.now()
        var['dt_now'] = now

        if 'index.md' in filenames:
            self.log.info("[THEME] INDEX_SKIP reason=user_generated")
            return

        var['page']['title'] = var['repo']['title']
        var['page']['stats'] = self._build_index_stats()
        var['page']['open_items'] = self._build_index_open_items()
        var['page']['alert_bar'] = self._build_index_alert_bar()
        var['page']['diataxis'] = self._build_index_diataxis()
        var['page']['events_panel'] = self._build_index_events_panel(now)
        var['page']['recent_events'] = self._build_index_recent_events(now)
        var['page']['monitoring_panel'] = self._build_index_monitoring_panel()

        page = self.template('PAGE_INDEX').render(var=var)
        self.distribute_md('index', page)

        self.srvdtb.add_document('index.md')
        self.srvdtb.add_document_key('index.md', 'Title', var['repo']['title'])
        self.srvdtb.add_document_key('index.md', 'SystemPage', 'Yes')

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

    def _index_doc_row(self, docId):
        """Build one index row dict with badge data for a document."""
        props = self.srvdtb.get_doc_properties(docId)
        title = props.get('Title', docId)
        if isinstance(title, list):
            title = title[0] if title else docId
        url = props.get('Title_Url', html_id_for(docId))
        ts = self.srvdtb.get_doc_timestamp(docId)
        date = ''
        if ts:
            try:
                dt = guess_datetime(ts)
                date = dt.strftime('%b %d') if dt else ts[:10]
            except Exception:
                date = ts[:10]
        category = self.srvdtb.get_values(docId, 'Category')[0]
        priority = self.srvdtb.get_values(docId, 'Priority')[0]
        status = self.srvdtb.get_values(docId, 'Status')[0]
        return {
            'date': date,
            'timestamp': ts or '',
            'title': title,
            'url': url,
            'category': category,
            'priority': priority,
            'priority_css': priority_css(priority) if priority else '',
            'status': status,
            'status_css': status_css(status) if status else '',
        }

    def _build_index_alert_bar(self, limit=5):
        """Recent changes and incidents for the alert bar below the hero."""
        def _rows(category):
            rows = []
            for docId in self.srvdtb.get_docs_by_key_value('Category', category)[:limit]:
                rows.append(self._index_doc_row(docId))
            return rows

        return {
            'changes': _rows('Change'),
            'incidents': _rows('Incident'),
        }

    def _build_index_open_items(self, limit=7):
        """Incidents, changes and tasks whose Status is still open.

        Rows are ranked by Priority first, then by date, newest first.
        Documents without a Status never show up here, so repositories
        that do not use the property keep a clean index.
        """
        rows = []
        for category in OPEN_ITEM_CATEGORIES:
            for docId in self.srvdtb.get_docs_by_key_value('Category', category):
                if self.srvdtb.is_system(docId):
                    continue
                status = self.srvdtb.get_values(docId, 'Status')[0]
                if status not in OPEN_STATUSES:
                    continue
                rows.append(self._index_doc_row(docId))
        rows.sort(key=lambda r: r['timestamp'], reverse=True)
        rows.sort(key=lambda r: PRIORITY_RANK.get(r['priority'], len(PRIORITY_RANK)))
        return rows[:limit]

    def _build_index_diataxis(self):
        """Diátaxis cards,  one per DocType value."""
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
                    url = props.get('Title_Url', html_id_for(docId))
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
                        url = props.get('Title_Url', html_id_for(docId))
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

    def _build_index_monitoring_panel(self):
        """Articles with Topic=Monitoring, grouped by Periodicity."""
        monitoring_docs = self.srvdtb.get_docs_by_key_value('Topic', 'Monitoring')
        groups = {}
        for docId in monitoring_docs:
            if self.srvdtb.is_system(docId):
                continue
            props = self.srvdtb.get_doc_properties(docId)
            title = props.get('Title', docId)
            if isinstance(title, list):
                title = title[0] if title else docId
            url = props.get('Title_Url', html_id_for(docId))
            periodicities = self.srvdtb.get_values(docId, 'Periodicity')
            if not periodicities or not periodicities[0]:
                continue
            periodicity = periodicities[0]
            groups.setdefault(periodicity, []).append({'title': title, 'url': url})

        return [
            {
                'periodicity': p,
                'url': 'Periodicity_%s.html' % p.replace(' ', '_'),
                'rows': groups[p],
            }
            for p in sorted(groups.keys())
        ]

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
            quarter = (month - 1) // 3 + 1
            mname = MONTH_NAMES[month - 1]
            has_month = (
                year in self.events_docs
                and month in self.events_docs[year]
            )
            qlabel = f'<span class="kb-evcal-qlabel">Q{quarter}</span>'
            if has_month:
                month_url = f'events_{year:04d}{month:02d}.html'
                caption = f'<a href="{month_url}">{qlabel} {mname}</a>'
            else:
                caption = f'{qlabel} {mname}'

            parts.append(f'<div class="kb-evcal-month kb-evcal-q{quarter}">')
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
                self.dey.setdefault(y, []).append((m, d))

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
                    #self.log.debug(f"[{EVENT_PAGE_DAY}.md] targeting PAGE[{os.path.basename(pagename)}] COMPILE[{must_compile_day}]")
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
                        self.distribute_md(EVENT_PAGE_DAY, html)

                        #FIXME
                        human_title = get_human_datetime_day(edt)
                        self.srvdtb.add_document(f"{EVENT_PAGE_DAY}.md")
                        self.srvdtb.add_document_key(f"{EVENT_PAGE_DAY}.md", 'Title', f"Events on {human_title}")
                        self.srvdtb.add_document_key(f"{EVENT_PAGE_DAY}.md", 'SystemPage', 'Yes')
                    else:
                        self.distribute_html(EVENT_PAGE_DAY, pagename)
                    self.srvbes.add_target(f"{EVENT_PAGE_DAY}.md", f"{EVENT_PAGE_DAY}.html")


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
                    self.distribute_md(EVENT_PAGE_MONTH, html)

                    human_title = get_human_datetime_month(edt)
                    self.srvdtb.add_document(f"{EVENT_PAGE_MONTH}.md")
                    self.srvdtb.add_document_key(f"{EVENT_PAGE_MONTH}.md", 'Title', f"Events on {human_title}")
                    self.srvdtb.add_document_key(f"{EVENT_PAGE_MONTH}.md", 'SystemPage', 'Yes')

                else:
                    self.distribute_html(EVENT_PAGE_MONTH, month_pagename)
                self.srvbes.add_target(f"{EVENT_PAGE_MONTH}.md", f"{EVENT_PAGE_MONTH}.html")

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
                self.distribute_md(page_name, PAGE.render(var=var))
                self.srvdtb.add_document(f"{EVENT_PAGE_YEAR}.md")
                self.srvdtb.add_document_key(f"{EVENT_PAGE_YEAR}.md", 'Title', f"Archive / {year}")
                self.srvdtb.add_document_key(f"{EVENT_PAGE_YEAR}.md", 'SystemPage', 'Yes')

            else:
                self.distribute_html(EVENT_PAGE_YEAR, year_pagename)
            self.srvbes.add_target(f"{EVENT_PAGE_YEAR}.md", f"{EVENT_PAGE_YEAR}.html")

        return must_compile_year

    def build_page_events(self):
        doclist = []
        ecats = {}
        repo = self.srvbes.get_dict('repo')
        event_types = repo.get('events', [])
        # ~ self.log.debug(" - Event types: %s", ', '.join(event_types))

        for docId in self.srvdtb.get_documents():
            if self.srvdtb.is_system(docId):
                continue
            category = self.srvdtb.get_values(docId, 'Category')[0]
            if category in event_types:
                ecats.setdefault(category, set()).add(docId)

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
            self.distribute_md('events', page.render(var=events))
        else:
            self.distribute_html('events', events_pagename)

        self.srvdtb.add_document('events.md')
        self.srvdtb.add_document_key('events.md', 'Title', 'Events')
        self.srvdtb.add_document_key('events.md', 'SystemPage', 'Yes')

    def build(self):
        """Create standard pages for default theme"""
        var = self.get_theme_var()
        self.build_page_events()
        self.build_page_properties()
        self.build_page_stats()
        self.build_page_bookmarks()
        self.build_page_add()
        self.build_page_index(var)
        self.build_page_index_all()
        self.create_page_about_kb4it()
        self.create_page_about_app()
        self.create_page_help()
        self.create_page_search()

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
            skel_path = os.path.join(skeletons_dir, f"{cat_id.upper()}-SKELETON.md")
            try:
                with open(skel_path, encoding="utf-8") as fh:
                    skeletons[cat_id] = fh.read()
            except OSError:
                skeletons[cat_id] = f"---\nDate: YYYY-MM-DD\nVersion: 1.0\nCategory: {cat_id.capitalize()}\n---\n\n# Title of the {cat_id.capitalize()}\n\n## Overview\n\nDescribe here.\n"
        var['page']['skeletons'] = skeletons
        # Printed raw inside <script>: "<" as \u003c so no value can close the script element.
        var['page']['skeletons_json'] = json.dumps(skeletons, ensure_ascii=True).replace("<", "\\u003c")
        keys_data = {}
        all_docs = self.srvdtb.get_documents()
        for key in self.srvdtb.get_theme_keys():
            counter = Counter()
            for docId in all_docs:
                for val in self.srvdtb.get_values(docId, key):
                    if val:
                        counter[val] += 1
            if counter:
                keys_data[key] = [{'v': v, 'c': c} for v, c in sorted(counter.items())]
        var['page']['keys_json'] = json.dumps(keys_data, ensure_ascii=True).replace("<", "\\u003c")
        page = TPL.render(var=var)
        self.distribute_md('add', page)
        self.srvdtb.add_document('add.md')
        self.srvdtb.add_document_key('add.md', 'Title', 'Add document')
        self.srvdtb.add_document_key('add.md', 'SystemPage', 'Yes')

    def extract_toc(self, source):
        """Extract TOC from compiled HTML code and make it theme dependent."""
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

    def build_page(self, path_md):
        """Build the final HTML Page.

        At this point, the Markdown compilation has finished successfully and
        the html page can be built. The Builder receives the source filepath;
        another file with extension .html should also exist.

        The html page is built by inserting the html header at the beginning,
        appending the footer at the end, and applying the necessary
        transformations in the body.

        Finally, the html page produced by the compiler is overwritten.
        """
        path_hdoc = html_id_for(path_md)
        basename_md = os.path.basename(path_md)
        basename_hdoc = os.path.basename(path_hdoc)
        exists_hdoc = os.path.exists(path_hdoc)  # it should be true

        if not exists_hdoc:
            self.log.error(f"[THEME] HTML_MISSING doc={basename_md}")
        else:
            HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
            HTML_BODY = self.template('HTML_BODY')
            HTML_FOOTER = self.template('HTML_FOOTER')
            var = self.get_theme_var()
            now = datetime.now()
            timestamp = get_human_datetime(now)
            keys = self.srvdtb.get_doc_properties(basename_md)

            with open(path_md, 'r', encoding='utf-8') as fpa:
                source_md = fpa.read()

            with open(path_hdoc, 'r', encoding='utf-8') as fph:
                source_html = fph.read()

            var['toc'] = self.extract_toc(source_html)
            var['has_toc'] = True

            # Do not show metadata for system pages
            if self.srvdtb.is_system(basename_md):
                var['SystemPage'] = True
                TPL_HTML_HEADER_MENU_CONTENTS_DISABLED = self.template('HTML_HEADER_MENU_CONTENTS_DISABLED')
                HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_DISABLED.render()
                var['metadata'] = ""
            else:
                var['SystemPage'] = False
                TPL_HTML_HEADER_MENU_CONTENTS_ENABLED = self.template('HTML_HEADER_MENU_CONTENTS_ENABLED')
                HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_ENABLED.render(var=var)
                var['metadata'] = self.build_metadata_section(basename_md)

            var['menu_contents'] = HTML_TOC
            var['keys'] = keys
            var['page']['title'] = 'No title found...'
            var['page']['title-tooltip'] = 'No title found...'
            try:
                var['page']['title'] = ellipsize_text(keys['Title'])
                var['page']['title-tooltip'] = keys['Title']
            except Exception:
                pass
            var['basename_md'] = basename_md
            var['basename_hdoc'] = basename_hdoc
            var['source_md'] = source_md
            var['fmt'] = source_ext(basename_md) or "md"
            var['source_html'] = self.apply_transformations(source_html)
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

            with open(path_hdoc, 'w', encoding='utf-8') as fhtml:
                tree = etree.fromstring(HTML, parser)
                pretty_html = etree.tostring(tree, pretty_print=True, method="html").decode()
                fhtml.write(f"<!DOCTYPE html>\n{pretty_html}")

            # ~ self.log.debug(f"KEY[{key}] VALUE[{value}] targets to RESOURCE[{var['pagename']}]")

    def post_deploy_activities(self):
        """Build the admin area once the site has been deployed.

        Only runs when repo.json sets "admin": true. It writes an admin
        subdirectory in the target with a backup page and two zip files:
        one holding the source Markdown documents, another holding the
        whole compiled site.
        """
        repo = self.srvbes.get_dict('repo')
        if not repo.get('admin', False):
            self.log.debug("[ADMIN] DISABLED")
            return

        admin_dir = os.path.join(self.srvbes.get_path('target'), 'admin')
        os.makedirs(admin_dir, exist_ok=True)

        slug = slugify(repo.get('title', ''))
        if not slug:
            slug = valid_filename(os.path.basename(str(self.srvbes.get_path('root'))))
        zip_sources = os.path.join(admin_dir, f"{slug}_sources.zip")
        zip_site = os.path.join(admin_dir, f"{slug}_site.zip")

        self.clean_stale_backups(admin_dir, [zip_sources, zip_site])

        if self.backups_needed(zip_sources, zip_site):
            self.build_zip_sources(zip_sources)
            self.build_zip_site(zip_site, admin_dir)
        else:
            self.log.debug("[ADMIN] ZIP_SKIP reason=no_changes")

        self.build_page_admin(admin_dir, zip_sources, zip_site)

    def clean_stale_backups(self, admin_dir, keep):
        """Delete backups left behind by a previous repository title."""
        current = {os.path.basename(path) for path in keep}
        for filename in os.listdir(admin_dir):
            if filename in current:
                continue
            if filename.endswith(('_sources.zip', '_site.zip')):
                os.unlink(os.path.join(admin_dir, filename))
                self.log.debug(f"[ADMIN] STALE_BACKUP_DELETED file={filename}")

    def backups_needed(self, *paths):
        """Rebuild the backups on a forced build, when the build compiled
        something, or when any of the zip files is missing.
        """
        if self.srvbes.get_value('app', 'force'):
            return True
        for path in paths:
            if not os.path.exists(path):
                return True
        return (self.srvbes.get_value('runtime', 'ncd') or 0) > 0

    def get_tmp_zip_path(self, zip_path):
        """Return the temporary path a zip file is written to.

        Zip files are built in the temporary directory and moved into the
        target afterwards, so a half written file is never linked and the
        site zip never packs itself.
        """
        tmp_dir = self.srvbes.get_path('tmp')
        os.makedirs(tmp_dir, exist_ok=True)
        return os.path.join(tmp_dir, os.path.basename(zip_path))

    def build_zip_sources(self, zip_path):
        """Pack the source Markdown documents, without assets."""
        docs = sorted(get_source_docs(self.srvbes.get_path('source')))
        tmp_path = self.get_tmp_zip_path(zip_path)
        with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zfile:
            for doc in docs:
                zfile.write(doc, os.path.basename(doc))
        shutil.move(tmp_path, zip_path)
        self.log.info(f"[ADMIN] ZIP_BUILT file={os.path.basename(zip_path)} docs={len(docs)}")

    def build_zip_site(self, zip_path, admin_dir):
        """Pack the whole compiled site, excluding the admin directory."""
        target = self.srvbes.get_path('target')
        admin_real = os.path.realpath(admin_dir)
        tmp_path = self.get_tmp_zip_path(zip_path)
        count = 0
        with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zfile:
            for root, dirs, files in os.walk(target):
                dirs[:] = sorted(d for d in dirs
                                 if os.path.realpath(os.path.join(root, d)) != admin_real)
                for filename in sorted(files):
                    filepath = os.path.join(root, filename)
                    zfile.write(filepath, os.path.relpath(filepath, target))
                    count += 1
        shutil.move(tmp_path, zip_path)
        self.log.info(f"[ADMIN] ZIP_BUILT file={os.path.basename(zip_path)} files={count}")

    def get_backup_item(self, path, name, description):
        """Describe a backup file for the admin page."""
        item = {}
        item['name'] = name
        item['description'] = description
        item['filename'] = os.path.basename(path)
        item['href'] = f"admin/{os.path.basename(path)}"
        if os.path.exists(path):
            stat = os.stat(path)
            item['size'] = human_size(stat.st_size)
            item['timestamp'] = get_human_datetime(datetime.fromtimestamp(stat.st_mtime))
        else:
            item['size'] = 'n/a'
            item['timestamp'] = 'n/a'
        return item

    def relocate_links(self, tree, prefix='../'):
        """Prefix relative urls so the page works from a subdirectory."""
        for attribute in ('href', 'src'):
            for element in tree.xpath(f'//*[@{attribute}]'):
                url = element.get(attribute)
                if not url or url.startswith(('#', '/', '../')):
                    continue
                if ':' in url.split('/')[0]:  # http:, mailto:, javascript:, data:
                    continue
                element.set(attribute, prefix + url)

    def build_page_admin(self, admin_dir, zip_sources, zip_site):
        """Write the admin page with the same layout as any other page."""
        HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
        HTML_BODY = self.template('HTML_BODY')
        HTML_FOOTER = self.template('HTML_FOOTER')
        TPL_PAGE_ADMIN = self.template('PAGE_ADMIN')

        var = self.get_theme_var()
        var['page']['title'] = 'Admin'
        var['page']['title-tooltip'] = 'Admin'
        var['SystemPage'] = True
        var['has_toc'] = False
        var['toc'] = ''
        var['metadata'] = ''
        var['fmt'] = 'md'
        var['timestamp'] = get_human_datetime(datetime.now())
        var['actions'] = self.get_page_actions(var)
        var['backups'] = [
            self.get_backup_item(
                zip_sources, 'Documents only',
                'Every Markdown document in the repository. No assets.'),
            self.get_backup_item(
                zip_site, 'Full site',
                'The whole compiled site: documents, pages and assets.'),
        ]
        var['source_html'] = TPL_PAGE_ADMIN.render(var=var)

        HTML = HTML_HEADER_COMMON.render(var=var)
        HTML += HTML_BODY.render(var=var)
        HTML += HTML_FOOTER.render(var=var)

        page_path = os.path.join(admin_dir, 'index.html')
        tree = etree.fromstring(HTML, parser)
        self.relocate_links(tree)
        pretty_html = etree.tostring(tree, pretty_print=True, method="html").decode()
        with open(page_path, 'w', encoding='utf-8') as fhtml:
            fhtml.write(f"<!DOCTYPE html>\n{pretty_html}")
        self.log.info(f"[ADMIN] PAGE_BUILT path={page_path}")

    def generate_sources(self):
        """This theme doesn't generate sources, yet."""
        # ~ self.log.debug("No sources generated by this theme")
        pass


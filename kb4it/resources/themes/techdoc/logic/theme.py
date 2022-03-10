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
import math
import pprint
from datetime import datetime, timedelta
from calendar import monthrange

from kb4it.services.builder import Builder
from kb4it.core.util import valid_filename
from kb4it.core.util import set_max_frequency, get_font_size
from kb4it.core.util import guess_datetime
from kb4it.core.util import get_human_datetime
from kb4it.core.util import fuzzy_date_from_timestamp
from kb4it.core.util import get_asciidoctor_attributes
from kb4it.core.util import valid_filename

from evcal import EventsCalendar

class Theme(Builder):
    dey = {} # Dictionary of day events per year
    events_docs = {} # Dictionary storing a list of docs for a given date

    def highlight_metadata_section(self, content, var):
        """Apply CSS transformation to metadata section."""
        HTML_TAG_METADATA_ADOC = self.template('HTML_TAG_METADATA_ADOC').render(var=var)
        HTML_TAG_METADATA_NEW = self.template('HTML_TAG_METADATA_NEW').render(var=var)
        content = content.replace(HTML_TAG_METADATA_ADOC, HTML_TAG_METADATA_NEW, 1)
        self.log.debug("[TRANSFORM] - Page[%s]: Highlight metadata", var['basename_html'])
        return content, var

    def apply_transformations(self, var):
        """Apply CSS transformation to the compiled page."""
        tpl = self.render_template
        content = var['source_html']
        content = content.replace(tpl('HTML_TAG_A_ADOC'), tpl('HTML_TAG_A_NEW'))
        content = content.replace(tpl('HTML_TAG_TOC_ADOC'), tpl('HTML_TAG_TOC_NEW'))
        content = content.replace(tpl('HTML_TAG_SECT1_ADOC'), tpl('HTML_TAG_SECT1_NEW'))
        content = content.replace(tpl('HTML_TAG_SECT2_ADOC'), tpl('HTML_TAG_SECT2_NEW'))
        content = content.replace(tpl('HTML_TAG_SECT3_ADOC'), tpl('HTML_TAG_SECT3_NEW'))
        content = content.replace(tpl('HTML_TAG_SECT4_ADOC'), tpl('HTML_TAG_SECT4_NEW'))
        content = content.replace(tpl('HTML_TAG_SECTIONBODY_ADOC'), tpl('HTML_TAG_SECTIONBODY_NEW'))
        content = content.replace(tpl('HTML_TAG_PRE_ADOC'), tpl('HTML_TAG_PRE_NEW'))
        content = content.replace(tpl('HTML_TAG_H2_ADOC'), tpl('HTML_TAG_H2_NEW'))
        content = content.replace(tpl('HTML_TAG_H3_ADOC'), tpl('HTML_TAG_H3_NEW'))
        content = content.replace(tpl('HTML_TAG_H4_ADOC'), tpl('HTML_TAG_H4_NEW'))
        content = content.replace(tpl('HTML_TAG_TABLE_ADOC'), tpl('HTML_TAG_TABLE_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ICON_NOTE_ADOC'), tpl('HTML_TAG_ADMONITION_ICON_NOTE_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ICON_TIP_ADOC'), tpl('HTML_TAG_ADMONITION_ICON_TIP_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ICON_IMPORTANT_ADOC'), tpl('HTML_TAG_ADMONITION_ICON_IMPORTANT_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ICON_CAUTION_ADOC'), tpl('HTML_TAG_ADMONITION_ICON_CAUTION_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ICON_WARNING_ADOC'), tpl('HTML_TAG_ADMONITION_ICON_WARNING_NEW'))
        content = content.replace(tpl('HTML_TAG_ADMONITION_ADOC'), tpl('HTML_TAG_ADMONITION_NEW'))
        content = content.replace(tpl('HTML_TAG_IMG_ADOC'), tpl('HTML_TAG_IMG_NEW'))
        var['source_html'] = content
        return var

    def build_datatable(self, headers=[], doclist=[]):
        """Given a list of columns, it builds a datatable.
        First column is always a date field, which is got by using the
        method get_doc_timestamp from the database module. It means
        that, firstly, it will retrieve the first date property defined
        by the theme (or one of the next ones defined if the first isn't
        found). If none is found, it will retrieve the timestamp of the
        file from the OS).
        So, it is not necessary to pass a date property in the headers.
        """
        TPL_LINK = self.template('LINK')
        TPL_DATATABLE = self.template('DATATABLE')
        TPL_DATATABLE_HEADER_ITEM = self.template('DATATABLE_HEADER_ITEM')
        TPL_DATATABLE_BODY_ITEM = self.template('DATATABLE_BODY_ITEM')

        datatable = {}
        datatable['header'] = ''
        repo = self.srvbes.get_repo_parameters()
        sort_attr = repo['sort'][0]
        headers.insert(0, sort_attr)
        for item in headers:
            var = {}
            var['item'] = item
            datatable['header'] += TPL_DATATABLE_HEADER_ITEM.render(var=var)

        documents = {}
        for doc in doclist:
            documents[doc] = self.srvdtb.get_doc_properties(doc)
        datatable['rows'] = ''
        for doc in documents:
            datatable['rows'] += '<tr>'
            timestamp = self.srvdtb.get_doc_timestamp(doc)
            datatable['rows'] += """<td class="">%s</td>""" % timestamp
            for key in headers[1:]:
                item = {}
                if key == 'Title':
                    item['title'] = documents[doc][key]
                    item['url'] = documents[doc]['%s_Url' % key]
                    datatable['rows'] += TPL_DATATABLE_BODY_ITEM.render(var=item)
                else:
                    link = {}
                    link['class'] = 'uk-link-heading'
                    field = []
                    try:
                        for value in documents[doc][key]:
                            link['title'] = value
                            link['url'] = documents[doc]['%s_%s_Url' % (key, value)]
                            field.append(TPL_LINK.render(var=link))
                    except KeyError:
                        field = ''
                    datatable['rows'] += """<td class="">%s</td>""" % ', '.join(field)
            datatable['rows'] += '</tr>'

        return TPL_DATATABLE.render(var=datatable)


    def build_page_index(self, var):
        """Create key page."""
        # ~ TPL_INDEX = self.template('PAGE_INDEX')
        TPL_TABLE_EVENTS = self.template('EVENTCAL_TABLE_EVENT')
        TPL_TABLE_MONTH_OLD = self.template('EVENTCAL_TABLE_MONTH_OLD')
        TPL_TABLE_MONTH_NEW = self.template('EVENTCAL_TABLE_MONTH_NEW')
        timestamp = datetime.now()
        now = timestamp.date()
        result = self.srvcal.format_trimester(now.year, now.month)
        trimester = result.replace(TPL_TABLE_MONTH_OLD.render(), TPL_TABLE_MONTH_NEW.render())
        var['trimester'] = trimester

        dt_now = datetime.now().replace(day=1) # Current datetime
        ldpm = dt_now - timedelta(days=1) # Last day previous month
        fdpm = ldpm.replace(day=1, hour=0, minute=0, second=0, microsecond=1) # First moment of the first day of the previous month
        dt_cur_lastday = dt_now.replace(day = monthrange(dt_now.year, dt_now.month)[1]) # Last day current datetime
        fdnm = dt_cur_lastday + timedelta(days=1) # First day next month
        dt_nxt = fdnm.replace(day = monthrange(fdnm.year, fdnm.month)[1]) # Last day next month
        ldnm = dt_nxt.replace(hour=23, minute=59, second=59, microsecond=999999) # Last moment of the last day of the next month

        doclist = []
        for doc in self.srvdtb.get_documents():
            ts = guess_datetime(self.srvdtb.get_doc_timestamp(doc))
            if ts >= fdpm and ts <= ldnm:
                doclist.append(doc)
        headers = ['Title', 'Team', 'Category', 'Scope', 'Topic']
        datatable = self.build_datatable(headers, doclist)
        var['page']['dt_documents'] = datatable

        var['page']['title'] = var['repo']['title']
        page = self.template('PAGE_INDEX').render(var=var)
        self.distribute_adoc('index', page)

    def build_events(self, doclist):
        TPL_PAGE_EVENTS_DAYS = self.template('EVENTCAL_PAGE_EVENTS_DAYS')
        TPL_PAGE_EVENTS_MONTHS = self.template('EVENTCAL_PAGE_EVENTS_MONTHS')
        SORT = self.srvbes.get_runtime_parameter('sort_attribute')
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
                self.log.error("[THEME-TECHDOC] - %s", error)
                self.log.error("[THEME-TECHDOC] - Doc doesn't have a valid date field. Skip it.")

        kbdict = self.srvbes.get_kb_dict()
        # Build day event pages
        must_compile_month = set()
        must_compile_year = set()
        for year in self.events_docs:
            for month in self.events_docs[year]:
                for day in self.events_docs[year][month]:
                    EVENT_PAGE_DAY = "events_%4d%02d%02d" % (year, month, day)
                    pagename = os.path.join(self.srvbes.get_cache_path(), "%s.html" % EVENT_PAGE_DAY)
                    doclist = self.events_docs[year][month][day]
                    must_compile_day = False
                    for doc in doclist:
                        doc_changed = kbdict['document'][doc]['compile']
                        doc_not_cached = not os.path.exists(pagename)
                        if doc_changed or doc_not_cached:
                            must_compile_day = True
                            break
                    self.log.debug("[EVENTS] - Page[%s] Compile? %s (Changed? %s or not cached? %s)", os.path.basename(pagename), must_compile_day, doc_changed, doc_not_cached)
                    if must_compile_day:
                        must_compile_month.add("%4d%02d" % (year, month))
                        must_compile_year.add("%4d" % (year))
                        edt = guess_datetime("%4d.%02d.%02d" % (year, month, day))
                        var = self.get_theme_var()
                        headers = ['Title', 'Team', 'Category', 'Scope', 'Topic']
                        var['page']['datatable'] = self.build_datatable(headers, doclist)
                        var['page']['title'] = edt.strftime("Events on %A, %B %d %Y")
                        html = TPL_PAGE_EVENTS_DAYS.render(var=var)
                        self.distribute_adoc(EVENT_PAGE_DAY, html)
                    else:
                        self.distribute_html(pagename)


        # Build month event pages
        for year in self.events_docs:
            for month in self.events_docs[year]:
                thismonth = "%4d%02d" % (year, month)
                EVENT_PAGE_MONTH = "events_%4d%02d" % (year, month)
                if thismonth in must_compile_month:
                    var = self.get_theme_var()
                    doclist = []
                    edt = guess_datetime("%4d.%02d.01" % (year, month))
                    for day in self.events_docs[year][month]:
                        doclist.extend(self.events_docs[year][month][day])
                    var['doclist'] = docs
                    headers = ['Title', 'Team', 'Category', 'Scope', 'Topic']
                    var['page']['datatable'] = self.build_datatable(headers, doclist)
                    var['page']['title'] = edt.strftime("Events on %B, %Y")
                    html = TPL_PAGE_EVENTS_MONTHS.render(var=var)
                    self.distribute_adoc(EVENT_PAGE_MONTH, html)
                else:
                    pagename = os.path.join(self.srvbes.get_cache_path(), "%s.html" % EVENT_PAGE_MONTH)
                    self.distribute_html(pagename)

        self.srvcal.set_events_days(self.dey)
        self.srvcal.set_events_docs(self.events_docs)

        # Build year event pages
        for year in sorted(self.dey.keys(), reverse=True):
            EVENT_PAGE_YEAR = "events_%4d" % year
            PAGE = self.template('EVENTCAL_PAGE_EVENTS_YEARS')
            page_name = "events_%4d" % year
            # ~ self.log.info("Year[%d] in Years[%s]: %s", year, must_compile_year, year in must_compile_year)
            if str(year) in must_compile_year:
                thisyear = {}
                html = self.srvcal.build_year_pagination(self.dey.keys())
                edt = guess_datetime("%4d.01.01" % year)
                title = edt.strftime("Events on %Y")
                thisyear['title'] = title
                html += self.srvcal.formatyearpage(year, 4)
                thisyear['content'] = html
                self.distribute_adoc(page_name, PAGE.render(var=thisyear))
            else:
                pagename = os.path.join(self.srvbes.get_cache_path(), "%s.html" % EVENT_PAGE_YEAR)
                self.distribute_html(pagename)

    def load_events_days(self, events_days, year):
        events_set = set()
        for event_day in events_days:
            events_set.add(event_day)

        for month, day in events_set:
            adate = guess_datetime("%d.%02d.%02d" % (year, month, day))

    def build_page_events(self):
        doclist = []
        ecats = {}
        repo = self.srvbes.get_repo_parameters()
        self.log.debug("Repository parameters: %s", repo)
        try:
            event_types = repo['events']
        except:
            event_types = []
        self.log.debug("[THEME] - Event types: %s", ', '.join(event_types))

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
        self.distribute_adoc('events', page.render(var=events))

    def build(self):
        """Create standard pages for default theme"""
        var = self.get_theme_var()
        self.log.debug("This is the Techdoc theme")
        self.app.register_service('EvCal', EventsCalendar())
        self.srvcal = self.get_service('EvCal')
        self.build_page_events()
        self.build_page_properties()
        self.build_page_stats()
        self.build_page_bookmarks()
        # ~ self.build_page_index_all()
        self.build_page_index(var)
        # ~ self.create_page_about_app()
        # ~ self.create_page_about_theme()
        self.create_page_about_kb4it()
        # ~ self.create_page_help()

    def create_page_about_kb4it(self):
        """About KB4IT page."""
        TPL_PAGE_ABOUT_KB4IT = self.template('PAGE_ABOUT_KB4IT')
        var = self.get_theme_var()
        self.distribute_adoc('about_kb4it', TPL_PAGE_ABOUT_KB4IT.render(var=var))

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
        TPL_PROPS_PAGE = self.template('PAGE_PROPERTIES')
        TPL_KEY_MODAL_BUTTON = self.template('KEY_MODAL_BUTTON')
        max_frequency = self.get_maxkv_freq()
        all_keys = self.srvdtb.get_all_keys()
        custom_buttons = ''
        var = self.get_theme_var()
        var['buttons'] = []
        for key in all_keys:
            ignored_keys = self.srvbes.get_ignored_keys()
            if key not in ignored_keys:
                vbtn = {}
                vbtn['content'] = self.build_tagcloud_from_key(key)
                values = self.srvdtb.get_all_values_for_key(key)
                frequency = len(values)
                size = get_font_size(frequency, max_frequency)
                proportion = int(math.log((frequency * 100) / max_frequency))
                vbtn['key'] = key
                vbtn['vfkey'] = valid_filename(key)
                vbtn['size'] = size
                vbtn['tooltip'] = "%d values" % len(values)
                button = TPL_KEY_MODAL_BUTTON.render(var=vbtn)
                var['buttons'].append(button)
        content = TPL_PROPS_PAGE.render(var=var)
        # ~ print(content)
        self.distribute_adoc('properties', content)

    def build_tagcloud_from_key(self, key):
        """Create a tag cloud based on key values."""
        dkeyurl = {}
        for doc in self.srvdtb.get_documents():
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
        if len_words > 0:
            lwords.sort(key=lambda y: y.lower())
            TPL_WORDCLOUD = self.template('WORDCLOUD')
            var = self.get_theme_var()
            var['items'] = []
            # ~ html_items = ''
            for word in lwords:
                frequency = len(dkeyurl[word])
                size = get_font_size(frequency, max_frequency)
                url = "%s_%s.html" % (valid_filename(key), valid_filename(word))
                tooltip = "%d documents" % frequency
                item = {}
                item['url'] = url
                item['tooltip'] = tooltip
                item['size'] = size
                item['word'] = word
                var['items'].append(item)
            html = TPL_WORDCLOUD.render(var=var)
        else:
            html = ''

        return html

    def get_maxkv_freq(self):
        """Calculate max frequency for all keys"""
        maxkvfreq = 0
        all_keys = self.srvdtb.get_all_keys()
        for key in all_keys:
            blocked_keys = self.srvdtb.get_blocked_keys()
            if key not in blocked_keys:
                values = self.srvdtb.get_all_values_for_key(key)
                if len(values) > maxkvfreq:
                    maxkvfreq = len(values)
        return maxkvfreq

    def build_page_stats(self):
        """Create stats page"""
        TPL_PAGE_STATS = self.template('PAGE_STATS')
        var = self.get_theme_var()
        var['count_docs'] = self.srvbes.get_numdocs()
        keys = self.srvdtb.get_all_keys()
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

    def build_page_index_all(self):
        """Create a page with all documents"""
        doclist = self.srvdtb.get_documents()
        TPL_PAGE_ALL = self.template('PAGE_ALL')
        var = self.get_theme_var()
        page = TPL_PAGE_ALL.render(var=var)
        self.distribute_adoc('all', page)

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
        necessary transformations.

        Finally, the html page created by asciidoctor is overwritten.
        """
        path_hdoc = path_adoc.replace('.adoc', '.html')
        basename_adoc = os.path.basename(path_adoc)
        basename_hdoc = os.path.basename(path_hdoc)
        exists_adoc = os.path.exists(path_adoc) # it should be true
        exists_hdoc = os.path.exists(path_hdoc) # it should be true

        if not exists_hdoc:
            self.log.error("[BUILD] - Source[%s] not converted to HTML properly", basename_adoc)
        else:
            self.log.debug("[BUILD] - Page[%s] transformation started", basename_hdoc)
            THEME_ID = self.srvbes.get_theme_property('id')
            HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
            HTML_HEADER_DOC = self.template('HTML_HEADER_DOC')
            HTML_HEADER_NODOC = self.template('HTML_HEADER_NODOC')
            HTML_BODY = self.template('HTML_BODY')
            HTML_FOOTER = self.template('HTML_FOOTER')
            var = self.get_theme_var()
            now = datetime.now()
            timestamp = get_human_datetime(now)
            keys = get_asciidoctor_attributes(path_adoc)
            # ~ self.log.error("%s -> %s", path_adoc, keys)
            source_adoc = open(path_adoc, 'r').read()
            source_html = open(path_hdoc, 'r').read()
            toc = self.extract_toc(source_html)
            var['toc'] = toc
            if len(toc) > 0:
                var['has_toc'] = True
                TPL_HTML_HEADER_MENU_CONTENTS_ENABLED = self.template('HTML_HEADER_MENU_CONTENTS_ENABLED')
                HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_ENABLED.render(var=var)
                var['metadata'] = self.build_metadata_section(basename_adoc)
            else:
                var['has_toc'] = False
                TPL_HTML_HEADER_MENU_CONTENTS_DISABLED = self.template('HTML_HEADER_MENU_CONTENTS_DISABLED')
                HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_DISABLED.render()
                var['metadata'] = ""
            var['menu_contents'] = HTML_TOC
            var['keys'] = keys
            try:
                var['page']['title'] = ', '.join(keys['Title'])
            except:
                pass
            var['basename_adoc'] = basename_adoc
            var['basename_hdoc'] = basename_hdoc
            var['related'] = self.get_related(var)
            var['source_adoc'] = source_adoc
            var['source_html'] = source_html
            var['actions'] = self.get_page_actions(var)
            var['timestamp'] = timestamp
            var = self.apply_transformations(var)

            HEADER = HTML_HEADER_COMMON.render(var=var)
            BODY = HTML_BODY.render(var=var)
            FOOTER = HTML_FOOTER.render(var=var)

            HTML = ""
            HTML += HEADER
            HTML += BODY
            HTML += FOOTER

            with open(path_hdoc, 'w') as fhtml:
                fhtml.write(HTML)
                self.log.debug("[BUILD] Page[%s] saved to: %s", basename_hdoc, path_hdoc)

            self.log.debug("[BUILD] - Page[%s] transformation finished", basename_hdoc)

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
        # ~ html = TPL_PAGE_KEY.render(var=var)

        adoc = TPL_PAGE_KEY.render(var=var)
        var['pagename'] = "%s" % valid_filename(key)
        self.distribute_adoc(var['pagename'], adoc)
        self.log.debug("[BUILDER] - Created page key '%s'", var['pagename'])
        # ~ return html

    def build_page_key_value(self, kvpath):
        key, value, COMPILE_VALUE = kvpath
        TPL_PAGE_KEY_VALUE = self.template('PAGE_KEY_VALUE')
        docs = self.srvbes.get_kbdict_value(key, value, new=True)
        sorted_docs = self.srvdtb.sort_by_date(docs)
        pagename = "%s_%s" % (valid_filename(key), valid_filename(value))
        var = self.get_theme_var()
        var['key'] = key
        var['value'] = value
        var['title'] = '%s: %s' % (key, value)
        var['pagename'] = pagename
        var['doclist'] = sorted_docs
        var['compile'] = COMPILE_VALUE
        var['has_toc'] = False

        doclist = []
        for doc in sorted_docs:
            doclist.append(doc)
        headers = ['Title', 'Team', 'Category', 'Scope', 'Topic']
        datatable = self.build_datatable(headers, doclist)
        var['page']['dt_documents'] = datatable

        if var['compile']:
            adoc = TPL_PAGE_KEY_VALUE.render(var=var)
            self.distribute_adoc(var['pagename'], adoc)
            self.log.debug("[BUILDER] - Created page key-value '%s'", var['pagename'])

    def build_page_bookmarks(self):
        """Create bookmarks page."""
        TPL_PAGE_BOOKMARKS = self.template('PAGE_BOOKMARKS')
        var = self.get_theme_var()
        doclist = []
        for doc in self.srvdtb.get_documents():
            bookmark = self.srvdtb.get_values(doc, 'Bookmark')[0]
            if bookmark == 'Yes' or bookmark == 'True':
                doclist.append(doc)
        headers = ['Title', 'Team', 'Category', 'Scope', 'Topic']
        datatable = self.build_datatable(headers, doclist)

        var['page']['title'] = 'Bookmarks'
        var['page']['dt_bookmarks'] = datatable
        page = TPL_PAGE_BOOKMARKS.render(var=var)
        # ~ self.log.error("PAGE: %s", page)
        self.distribute_adoc('bookmarks', page)
        self.log.debug("[BUILDER] - Created page for bookmarks")
        return page

    def get_page_actions(self, var):
        TPL_SECTION_ACTIONS = self.template('SECTION_ACTIONS')
        this_doc = var['basename_adoc']
        actions = TPL_SECTION_ACTIONS.render(var=var)
        return actions

    def get_related(self, var):
        """Get a list of related documents for each tag"""
        TPL_SECTION_RELATED = self.template('SECTION_RELATED')
        this_doc = var['basename_adoc']
        properties = self.srvdtb.get_doc_properties(this_doc)
        var['has_tags'] = False
        var['has_docs'] = False
        var['related'] = {}

        if len(properties) > 0:
            try:
                tags = properties['Tag']
                var['has_tags'] = True
            except:
                tags = []

        doclist = set()
        if var['has_tags']:
            for tag in tags:
                for doc in self.srvdtb.get_docs_by_key_value('Tag', tag):
                    if doc != this_doc:
                        doclist.add(doc)
                        var['has_docs'] = True
        headers = ['Title', 'Team', 'Category', 'Scope', 'Topic']
        datatable = self.build_datatable(headers, doclist)
        var['page']['datatable'] = datatable
        related = TPL_SECTION_RELATED.render(var=var)
        return related

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

    def get_html_values_from_key(self, doc, key):
        """Return the html link for a value."""
        html = []

        values = self.srvdtb.get_values(doc, key)
        for value in values:
            url = "%s_%s.html" % (key, value)
            html.append((url, value))
        return html

    def build_metadata_section(self, doc):
        """Return a html block for displaying metadata (keys and values)."""
        try:
            TPL_METADATA_SECTION = self.template('METADATA_SECTION')
            custom_keys = self.srvdtb.get_custom_keys(doc)
            var = {}
            var['items'] = []
            for key in custom_keys:
                ckey = {}
                ckey['doc'] = doc
                ckey['key'] = key
                ckey['vfkey'] = valid_filename(key)
                try:
                    values = self.get_html_values_from_key(doc, key)
                    ckey['labels'] = self.get_labels(values)
                    var['items'].append(ckey)
                except Exception as error:
                    self.log.error("[BUILDER] - Key[%s]: %s", key, error)
                    raise
            var['timestamp'] = self.srvdtb.get_doc_timestamp(doc)
            html = TPL_METADATA_SECTION.render(var=var)
        except Exception as error:
            msgerror = "%s -> %s" % (doc, error)
            self.log.error("[BUILDER] - %s", msgerror)
            html = ''
            raise
        return html

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
import csv
import sys
import math
import requests
import tempfile
from string import Template
from datetime import datetime, timedelta
from calendar import monthrange

from kb4it.services.builder import Builder
from kb4it.core.env import ENV
from kb4it.core.util import valid_filename
from kb4it.core.util import set_max_frequency, get_font_size
from kb4it.core.util import guess_datetime
from kb4it.core.util import get_human_datetime
from kb4it.core.util import get_asciidoctor_attributes

from evcal import EventsCalendar

TPL_MENU = """= $title

:Lunch: $lunch
:Dinner: $dinner
:Ingredient: $ingredients
:Lunch: $lunch
:Served: $served


// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE

== Notes

$notes
"""

class Theme(Builder):
    dey = {}  # Dictionary of day events per year
    events_docs = {}  # Dictionary storing a list of docs for a given date

    # ~ def initialize(self):
        # ~ pass

    def get_sheet(self, url, outDir, outFile):
        response = requests.get(url)

        # Download sheet
        if response.status_code == 200:
            filepath = os.path.join(outDir, outFile)
            tmp_filepath = os.path.join(outDir, f'tmp_{outFile}')
            with open(tmp_filepath, 'wb') as f:
                f.write(response.content)
                self.log.info(f'Temporay CSV file saved to: {tmp_filepath}')

            # Save CSV with quotes and use semicolon as delimiter
            with open(tmp_filepath, 'r') as csv_in, \
                 open(filepath, 'w', newline='') as csv_out:
                reader = csv.reader(csv_in)
                writer = csv.writer(csv_out, delimiter=';')
                for row in reader:
                    writer.writerow(row)
            self.log.info(f'Final CSV file saved to: {filepath}')
        else:
            self.log.error(f'Error downloading Google Sheet: {response.status_code}')
            filepath = None
        return filepath

    def get_ingredients(self, meals, dingredients):
        ingredients = ''
        singredients = set()
        lingredients = []
        for meal in meals.split(','):
            meal = meal.strip()
            if len(meal) == 0:
                continue
            else:
                try:
                    ingredients = dingredients[meal]
                except Exception as error:
                    lingredients = []

                for ingredient in ingredients:
                    singredients.add(ingredient)

                if len(lingredients) == 0:
                    self.log.warning(f"Meal '{meal}' doesn't have any ingredient")

                lingredients += list(singredients)

        return lingredients

    def generate_sources(self):
        """Custom themes can use this method to generate source documents"""
        self.log.info("[THEME] - Generating sources...")
        data_dir = tempfile.mkdtemp(dir=ENV['LPATH']['TMP'], suffix='')
        repo_config = self.srvbes.get_repo_parameters()
        source_dir = repo_config['source']
        url_meals = repo_config['meals']
        url_ingredients = repo_config['ingredients']
        self.log.info(f"[THEME] - Meals: {url_meals}")
        self.log.info(f"[THEME] - Ingredients: {url_ingredients}")
        self.log.info(f"[THEME] - Temporary data dir: {data_dir}")
        fmeals = self.get_sheet(url_meals, data_dir, "meals.csv")
        fingredients = self.get_sheet(url_ingredients, data_dir, "ingredients.csv")
        self.log.info(f'Meals data: {fmeals}')
        self.log.info(f'Ingredients data: {fingredients}')

        dingredients = {}
        with open(fingredients, 'r') as csv_ing:
            lines = csv_ing.readlines()
            n = 0
            for line in lines:
                if n > 0:
                    row = line.split(';')
                    meals = row[0]
                    ingredients = row[1]

                    for meal in meals.split(','):
                        try:
                            dingredients[meal]
                        except:
                            dingredients[meal] = [ingredient.strip() for ingredient in ingredients.split(',')]

                n += 1

        with open(fmeals, 'r') as csv_meals:
            lines = csv_meals.readlines()
            menu = Template(TPL_MENU)
            n = 0
            for line in lines:
                if n > 0:
                    row = line.split(';')
                    try:
                        sdate = f'{row[0]}'
                    except:
                        continue

                    # Lunch
                    try:
                        lunches = f'{row[1]}'
                        lingredients = self.get_ingredients(lunches, dingredients)
                    except Exception as error:
                        lunches = ''
                    have_lunch = len(lunches) > 0
                    # ~ self.log.info(f"Lunch on {sdate}: {lunches}")

                    # Dinner
                    try:
                        dinners = f'{row[2]}'
                        lingredients += self.get_ingredients(dinners, dingredients)
                    except:
                        dinners = ''
                    have_dinner = len(dinners) > 0
                    # ~ self.log.info(f"Dinner on {sdate}: {dinners}")

                    try:
                        notes = f'{row[3]}'
                    except:
                        notes = ''

                    meals = set()
                    for meal in lunches.split(','):
                        if len(meal) > 0:
                            meals.add(meal)
                    for meal in dinners.split(','):
                        if len(meal) > 0:
                            meals.add(meal)

                    write_entry = have_lunch or have_dinner
                    if write_entry:
                        td = datetime.strptime(sdate, "%d/%m/%Y")
                        filename = td.strftime("%Y%m%d.adoc")
                        source_file = os.path.join(source_dir, filename)
                        with open(source_file, 'w') as fmenu:
                            this_menu = menu.substitute(title=sdate, lunch=lunches, dinner=dinners, meal=', '.join(list(meals)), ingredients=', '.join(lingredients), served=sdate, notes=notes)
                            fmenu.write(this_menu)
                    # ~ self.log.info(f"{sdate}\t - Lunch ({have_lunch}) / Dinner ({have_dinner})\t> Write entry? {write_entry}")
                n += 1
        # ~ sys.exit(0)

    def highlight_metadata_section(self, content, var):
        """Apply CSS transformation to metadata section."""
        HTML_TAG_METADATA_ADOC = self.template('HTML_TAG_METADATA_ADOC').render(var=var)
        HTML_TAG_METADATA_NEW = self.template('HTML_TAG_METADATA_NEW').render(var=var)
        content = content.replace(HTML_TAG_METADATA_ADOC, HTML_TAG_METADATA_NEW, 1)
        self.log.debug("[TRANSFORM] - Page[%s]: Highlight metadata", var['basename_html'])
        return content, var

    def apply_transformations(self, content):
        """Apply CSS transformation to the compiled page."""
        content = content.replace(self.render_template('HTML_TAG_A_ADOC'), self.render_template('HTML_TAG_A_NEW'))
        content = content.replace(self.render_template('HTML_TAG_TOC_ADOC'), self.render_template('HTML_TAG_TOC_NEW'))
        content = content.replace(self.render_template('HTML_TAG_SECT1_ADOC'), self.render_template('HTML_TAG_SECT1_NEW'))
        content = content.replace(self.render_template('HTML_TAG_SECT2_ADOC'), self.render_template('HTML_TAG_SECT2_NEW'))
        content = content.replace(self.render_template('HTML_TAG_SECT3_ADOC'), self.render_template('HTML_TAG_SECT3_NEW'))
        content = content.replace(self.render_template('HTML_TAG_SECT4_ADOC'), self.render_template('HTML_TAG_SECT4_NEW'))
        content = content.replace(self.render_template('HTML_TAG_SECTIONBODY_ADOC'), self.render_template('HTML_TAG_SECTIONBODY_NEW'))
        content = content.replace(self.render_template('HTML_TAG_PRE_ADOC'), self.render_template('HTML_TAG_PRE_NEW'))
        content = content.replace(self.render_template('HTML_TAG_H2_ADOC'), self.render_template('HTML_TAG_H2_NEW'))
        content = content.replace(self.render_template('HTML_TAG_H3_ADOC'), self.render_template('HTML_TAG_H3_NEW'))
        content = content.replace(self.render_template('HTML_TAG_H4_ADOC'), self.render_template('HTML_TAG_H4_NEW'))
        content = content.replace(self.render_template('HTML_TAG_TABLE_ADOC'), self.render_template('HTML_TAG_TABLE_NEW'))
        content = content.replace(self.render_template('HTML_TAG_TABLE_KB4IT_ADOC'), self.render_template('HTML_TAG_TABLE_KB4IT_NEW'))
        content = content.replace(self.render_template('HTML_TAG_ADMONITION_ICON_NOTE_ADOC'), self.render_template('HTML_TAG_ADMONITION_ICON_NOTE_NEW'))
        content = content.replace(self.render_template('HTML_TAG_ADMONITION_ICON_TIP_ADOC'), self.render_template('HTML_TAG_ADMONITION_ICON_TIP_NEW'))
        content = content.replace(self.render_template('HTML_TAG_ADMONITION_ICON_IMPORTANT_ADOC'), self.render_template('HTML_TAG_ADMONITION_ICON_IMPORTANT_NEW'))
        content = content.replace(self.render_template('HTML_TAG_ADMONITION_ICON_CAUTION_ADOC'), self.render_template('HTML_TAG_ADMONITION_ICON_CAUTION_NEW'))
        content = content.replace(self.render_template('HTML_TAG_ADMONITION_ICON_WARNING_ADOC'), self.render_template('HTML_TAG_ADMONITION_ICON_WARNING_NEW'))
        content = content.replace(self.render_template('HTML_TAG_ADMONITION_ADOC'), self.render_template('HTML_TAG_ADMONITION_NEW'))
        content = content.replace(self.render_template('HTML_TAG_IMG_ADOC'), self.render_template('HTML_TAG_IMG_NEW'))
        return content

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
        # ~ self.log.info(f"Sort attribute: {sort_attr}")
        headers.insert(0, sort_attr)
        for item in headers:
            var = {}
            var['item'] = item
            datatable['header'] += TPL_DATATABLE_HEADER_ITEM.render(var=var)

        documents = {}
        for doc in sorted(doclist, reverse=True):
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
        fdpm = ldpm.replace(day=1, hour=0, minute=0, second=0, microsecond=1) # First day of the previous month
        dt_cur_lastday = dt_now.replace(day = monthrange(dt_now.year, dt_now.month)[1]) # Last day current datetime
        fdnm = dt_cur_lastday + timedelta(days=1) # First day next month
        dt_nxt = fdnm.replace(day = monthrange(fdnm.year, fdnm.month)[1]) # Last day next month
        ldnm = dt_nxt.replace(hour=23, minute=59, second=59, microsecond=999999) # Last moment of the last day of the next month
        self.log.info(f"Choosing documents between '{fdpm}' and '{ldnm}'")
        self.srvdtb.sort_database()
        doclist = []
        for doc in self.srvdtb.get_documents():
            ts = guess_datetime(self.srvdtb.get_doc_timestamp(doc))
            if ts >= fdpm and ts <= ldnm:
                doclist.append(doc)
        # ~ doclist = self.srvdtb.sort_by_date(doclist)
        headers = ['Lunch', 'Dinner']
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
                self.log.error("[THEME-RESTAURANT] - %s", error)
                self.log.error("[THEME-RESTAURANT] - Doc doesn't have a valid date field. Skip it.")

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
                        headers = ['Lunch', 'Dinner']
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
                    headers = ['Lunch', 'Dinner']
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
        self.log.info("[THEME] - Repository parameters: %s", repo)
        try:
            event_types = repo['events']
        except:
            event_types = []
        self.log.info("[THEME] - Event types: %s", ', '.join(event_types))

        for doc in self.srvdtb.get_documents():
            doclist.append(doc)
            title = self.srvdtb.get_values(doc, 'Title')[0]
        self.build_events(doclist)
        HTML = self.srvcal.build_year_pagination(self.dey.keys())
        events = {}
        events['content'] = HTML
        page = self.template('PAGE_EVENTS')
        self.distribute_adoc('events', page.render(var=events))

    # ~ def generate_sources(self):
        # ~ url_meals = 'https://docs.google.com/spreadsheets/d/16rx5NVDmyBGXl3L0Se1iPoUAT5mF_3GqOSVAUYJbCaE/export?format=csv&gid=0'
        # ~ url_ingredients = 'https://docs.google.com/spreadsheets/d/16rx5NVDmyBGXl3L0Se1iPoUAT5mF_3GqOSVAUYJbCaE/export?format=csv&gid=298692532'

        # ~ outDir = 'tmp/'
        # ~ os.makedirs(outDir, exist_ok = True)
        # ~ fmeals = get_sheet(url_meals, outDir, "meals.csv")
        # ~ print(f'Meals: {fmeals}')
        # ~ fingredients = get_sheet(url_ingredients, outDir, "ingredients.csv")
        # ~ print(f'Ingredients: {fingredients}')

        # ~ with open(fmeals, 'r') as csv_meals:
            # ~ reader = csv.reader(csv_meals)
            # ~ menu = Template(TPL_MENU)
            # ~ n = 0
            # ~ for line in reader:
                # ~ if n > 0:
                    # ~ row = line[0].split(';')
                    # ~ print(menu.substitute(title=row[0], lunch=row[1]))
                # ~ n += 1


    def build(self):
        """Create standard pages for default theme"""
        var = self.get_theme_var()
        self.log.info("This is the Restaurant theme")
        self.app.register_service('EvCal', EventsCalendar())
        self.srvcal = self.get_service('EvCal')
        self.build_page_events()
        # ~ self.build_page_properties()
        self.build_page_stats()
        self.build_page_lunches()
        self.build_page_dinners()
        self.build_page_index(var)
        self.build_page_index_all()
        # ~ self.create_page_about_theme()
        self.create_page_about_kb4it()
        # ~ self.create_page_help()

    def page_hook_pre(self, var):
        # ~ var['related'] = ''
        # ~ var['metadata'] = ''
        # ~ var['source'] = ''
        # ~ var['actions'] = ''
        # ~ return var
        pass


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
        TPL_PAGE_ALL = self.template('PAGE_ALL')
        var = self.get_theme_var()
        doclist = []
        for doc in self.srvdtb.get_documents():
            doclist.append(doc)
        headers = ['Lunch', 'Dinner']
        datatable = self.build_datatable(headers, doclist)
        var['content'] = datatable
        page = TPL_PAGE_ALL.render(var=var)
        self.distribute_adoc('all', page)
        # ~ self.log.debug("[BUILDER] - Created page for bookmarks")
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

            with open(path_adoc, 'r') as fpa:
                source_adoc = fpa.read()

            with open(path_hdoc, 'r') as fph:
                source_html = fph.read()

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
            var['related'] = self.get_related(basename_adoc)
            var['source_adoc'] = source_adoc
            var['source_html'] = self.apply_transformations(source_html) # <---
            actions = self.get_page_actions(var)
            var['actions'] = actions
            var['timestamp'] = timestamp
            # ~ var = self.apply_transformations(var)
            # ~ self.log.error("MEMVAR[%s] = %s", basename_adoc, get_process_memory())

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
        self.log.info("[BUILDER] - Created page key '%s'", var['pagename'])
        #self.log.error("K-MEMVAR[%s] = %s", var['pagename'], get_process_memory())
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
        headers = ['Lunch', 'Dinner']
        datatable = self.build_datatable(headers, doclist)
        var['page']['dt_documents'] = datatable

        if var['compile']:
            adoc = TPL_PAGE_KEY_VALUE.render(var=var)
            self.distribute_adoc(var['pagename'], adoc)
            self.log.debug("[BUILDER] - Created page key-value '%s'", var['pagename'])
        #self.log.error("KV-MEMVAR[%s] = %s", var['pagename'], get_process_memory())

    def build_page_lunches(self):
        """Create lunches page."""
        TPL_PAGE_LUNCHES = self.template('PAGE_LUNCHES')
        var = self.get_theme_var()
        doclist = []
        for doc in self.srvdtb.get_documents():
            lunch = self.srvdtb.get_values(doc, 'Lunch')[0]
            if len(lunch) > 0:
                doclist.append(doc)
        self.log.info("Found %d lunches", len(doclist))
        headers = ['Lunch']
        datatable = self.build_datatable(headers, doclist)

        var['page']['title'] = 'Lunches'
        var['page']['dt_lunches'] = datatable
        page = TPL_PAGE_LUNCHES.render(var=var)
        self.distribute_adoc('lunches', page)
        self.log.debug("[BUILDER] - Created page for lunches")
        return page

    def build_page_dinners(self):
        """Create dinners page."""
        TPL_PAGE_DINNERS = self.template('PAGE_DINNERS')
        var = self.get_theme_var()
        doclist = []
        for doc in self.srvdtb.get_documents():
            lunch = self.srvdtb.get_values(doc, 'Dinner')[0]
            if len(lunch) > 0:
                doclist.append(doc)
        self.log.info("Found %d dinners", len(doclist))
        headers = ['Dinner']
        datatable = self.build_datatable(headers, doclist)

        var['page']['title'] = 'Dinners'
        var['page']['dt_dinners'] = datatable
        page = TPL_PAGE_DINNERS.render(var=var)
        self.distribute_adoc('dinners', page)
        self.log.debug("[BUILDER] - Created page for dinners")
        return page

    def get_page_actions(self, var):
        TPL_SECTION_ACTIONS = self.template('SECTION_ACTIONS')
        return TPL_SECTION_ACTIONS.render(var=var)

    def get_related(self, doc):
        """Get a list of related documents for each tag"""
        TPL_SECTION_RELATED = self.template('SECTION_RELATED')
        properties = self.srvdtb.get_doc_properties(doc)
        has_tags = False
        has_docs = False
        var = {}

        if len(properties) > 0:
            try:
                tags = properties['Tag']
                has_tags = True
            except:
                tags = []

        doclist = set()
        if has_tags:
            for tag in tags:
                for this_doc in self.srvdtb.get_docs_by_key_value('Tag', tag):
                    if doc != this_doc:
                        doclist.add(this_doc)
                        has_docs = True
        headers = ['Lunch', 'Dinner']
        var['datatable'] = self.build_datatable(headers, doclist)
        return TPL_SECTION_RELATED.render(var=var)

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

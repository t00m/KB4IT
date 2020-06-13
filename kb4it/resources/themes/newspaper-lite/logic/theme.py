#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Custom theme module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: newspaper theme scripts
"""

import os
import sys
import glob
import uuid
from urllib.parse import urlparse
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor as Executor

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from dateutil.parser import parse
import feedparser

from kb4it.services.builder import KB4ITBuilder
from kb4it.core.util import valid_filename, guess_datetime
from kb4it.core.util import sort_dictionary

IGNORE = set()
for token in tuple(nltk.corpus.stopwords.words('french')):
    IGNORE.add(token.lower())

for token in tuple(nltk.corpus.stopwords.words('english')):
    IGNORE.add(token.lower())

for token in tuple(nltk.corpus.stopwords.words('spanish')):
    IGNORE.add(token.lower())

tokens = list(IGNORE)
tokens.sort()


def get_tags(text):
    # word stemming and polishing
    mylist = set()
    ps = PorterStemmer()
    words = word_tokenize(text)
    for word in words:
        stem_word = ps.stem(word)
        if stem_word not in words:
            stem_word = words[0]
        mylist.add(stem_word)

    # FIlter tags according basic rules
    stags = set()
    for w in mylist:
        if w.lower() not in IGNORE:
            if w.startswith('LG_'):
                stags.add(w)
            else:
                if not w.isdigit():
                    if w.isalnum() and len(w) > 3:
                        stags.add(w.lower())
    ltags = list(stags)
    ltags.sort()
    return ltags

class Theme(KB4ITBuilder):
    feeds = {}

    def clean_source_dir(self):
        source_path = self.srvapp.get_source_path()
        adocs = glob.glob(os.path.join(source_path, "*.adoc"))
        for adoc in adocs:
            # ~ self.log.debug("Deleting %s", adoc)
            os.unlink(adoc)

    def generate_sources(self):
        self.log.debug("\t\tClean source directory from previous executions")
        self.clean_source_dir()

        self.log.info("\t\tCreating sources from rss")
        source_path = self.srvapp.get_source_path()
        rss_file = os.path.join(source_path, 'rss.txt')
        if os.path.exists(rss_file):
            sources = open(rss_file, 'r').read().splitlines()
            self.process_feeds(sources)
            self.validate_rss_feeds()
            self.create_newspapers_page()
        else:
            self.log.error ("RSS file path doesn't exist. Exit.")
            exit(-1)

    def build(self):
        # Default pages
        self.create_all_keys_page()
        self.create_properties_page()
        self.create_stats_page()
        self.create_index_all()
        self.create_index_page()
        self.create_about_page()
        self.create_help_page()

    def get_doc_card_np_entry_short(self, rss, eid):
        try:
            CARD_NP_ENTRY = self.template('CARD_DOC_NEWSPAPER_ENTRY_SHORT')
            # ~ thumbnail = self.feeds[rss]['entries'][eid]['thumbnail']
            title = self.feeds[rss]['entries'][eid]['title']
            summary = self.feeds[rss]['entries'][eid]['summary']
            updated = self.feeds[rss]['entries'][eid]['updated']
            link = self.feeds[rss]['entries'][eid]['link']
            thumbnail = self.get_favicon_url(link)
            tags = self.feeds[rss]['entries'][eid]['tags']
            card = CARD_NP_ENTRY % (thumbnail, link, title, updated)
            # ~ self.log.debug(card)
            return card
        except:
            # ~ self.log.error("RSS[%s] - EID[%s]", rss, eid)
            # ~ self.log.error(self.feeds[rss]['entries'])
            return ''

    def get_news(self, dtu, dtl):
        NEWS = ''
        d = {}
        for rss in self.feeds:
            for eid in self.feeds[rss]['entries']:
                updated = self.feeds[rss]['entries'][eid]['updated']
                dt = guess_datetime(updated)
                if dt is not None:
                    if dt > dtl and dt < dtu:
                        key = "%s#-#%s" % (rss, eid)
                        d[key] = dt

        alist = sort_dictionary(d)
        for key, updated in alist:
            sep = key.find('#-#')
            rss = key[:sep]
            eid = key[sep+3:]
            NEWS += self.get_doc_card_np_entry_short(rss, eid)

        if len(NEWS) == 0:
            NEWS = """<div class="uk-text-lead">No news available</div>"""

        return NEWS

    def create_index_page(self):
        PAGE_INDEX = self.template('PAGE_INDEX')

        ## TODAY ###
        adate = datetime.now()
        upper = "%4d-%02d-%02d 23:59:59" % (adate.year, adate.month, adate.day)
        lower = "%4d-%02d-%02d 00:00:00" % (adate.year, adate.month, adate.day)
        dtu = datetime.strptime(upper, "%Y-%m-%d %H:%M:%S")
        dtl = datetime.strptime(lower, "%Y-%m-%d %H:%M:%S")

        NEWS_TODAY = self.get_news(dtu, dtl)
        PAGE_TODAY = self.template('PAGE_NEWS')
        self.distribute('today', PAGE_TODAY % ('Today', NEWS_TODAY))

        ## YESTERDAY ##
        adate = datetime.today() - timedelta(days=1)
        upper = "%4d-%02d-%02d 23:59:59" % (adate.year, adate.month, adate.day)
        lower = "%4d-%02d-%02d 00:00:00" % (adate.year, adate.month, adate.day)
        dtu = datetime.strptime(upper, "%Y-%m-%d %H:%M:%S")
        dtl = datetime.strptime(lower, "%Y-%m-%d %H:%M:%S")

        NEWS_YESTERDAY = self.get_news(dtu, dtl)
        PAGE_YESTERDAY = self.template('PAGE_NEWS')
        self.distribute('yesterday', PAGE_YESTERDAY % ('Yesterday', NEWS_YESTERDAY))

        ### THIS WEEK ###
        now = datetime.now()
        adate = datetime.today() - timedelta(days=datetime.today().isoweekday() % 7)
        upper = "%4d-%02d-%02d 23:59:59" % (now.year, now.month, now.day)
        lower = "%4d-%02d-%02d 00:00:00" % (adate.year, adate.month, adate.day)
        dtu = datetime.strptime(upper, "%Y-%m-%d %H:%M:%S")
        dtl = datetime.strptime(lower, "%Y-%m-%d %H:%M:%S")

        NEWS_WEEK = self.get_news(dtu, dtl)
        PAGE_WEEK = self.template('PAGE_NEWS')
        self.distribute('week', PAGE_WEEK % ('This week', NEWS_WEEK))

        ### THIS MONTH ###
        adate = datetime.now()
        upper = "%4d-%02d-%02d 23:59:59" % (now.year, now.month, now.day)
        lower = "%4d-%02d-01 00:00:00" % (adate.year, adate.month)
        dtu = datetime.strptime(upper, "%Y-%m-%d %H:%M:%S")
        dtl = datetime.strptime(lower, "%Y-%m-%d %H:%M:%S")
        NEWS_MONTH = self.get_news(dtu, dtl)
        PAGE_MONTH = self.template('PAGE_NEWS')
        self.distribute('month', PAGE_MONTH % ('This month', NEWS_MONTH))

        ### PAST MONTH ###
        today = datetime.today()
        first = today.replace(day=1)
        pastmonth = first - timedelta(days=1)
        firstpast = pastmonth.replace(day=1)
        upper = "%4d-%02d-%02d 23:59:59" % (pastmonth.year, pastmonth.month, pastmonth.day)
        lower = "%4d-%02d-%02d 00:00:00" % (firstpast.year, firstpast.month, firstpast.day)
        dtu = datetime.strptime(upper, "%Y-%m-%d %H:%M:%S")
        dtl = datetime.strptime(lower, "%Y-%m-%d %H:%M:%S")
        NEWS_PAST = self.get_news(dtu, dtl)
        PAGE_PAST = self.template('PAGE_NEWS')
        self.distribute('past', PAGE_PAST % ('Past month', NEWS_PAST))

        # ~ self.distribute_to_source('index', PAGE_INDEX % (NEWS_TODAY, NEWS_YESTERDAY, NEWS_WEEK))
        self.distribute('index', PAGE_INDEX % (NEWS_TODAY, NEWS_YESTERDAY, NEWS_WEEK, NEWS_MONTH, NEWS_PAST))

    def get_favicon_url(self, link):
        o = urlparse(link)
        rss_scheme = o.scheme
        rss_host = o.netloc
        favicon = "https://www.google.com/s2/favicons?domain=%s" % o.netloc
        # ~ favicon = "%s://%s/favicon.ico" % (rss_scheme, rss_host)
        return favicon

    def get_homepage(self, link):
        o = urlparse(link)
        rss_scheme = o.scheme
        rss_host = o.netloc
        homepage = "%s://%s" % (rss_scheme, rss_host)
        return homepage

    def get_website(self, link):
        o = urlparse(link)
        return o.netloc

    def create_newspaper_page(self, rss):
        PAGE_NP = self.template('PAGE_NEWSPAPER')
        PAGE_NP_ENTRY = self.template('PAGE_NEWSPAPER_ENTRY')
        CARD_NP_ENTRY = self.template('CARD_DOC_NEWSPAPER_ENTRY')
        rss_title = self.feeds[rss]['header']['title']
        rss_summary = self.feeds[rss]['header']['summary']
        rss_link = self.feeds[rss]['header']['link']
        # ~ rss_updated = self.feeds[rss]['header']['updated']

        rss_properties = ''
        # ~ rss_properties += ':Updated: %s\n' % rss_updated
        rss_favicon = self.get_favicon_url(rss_link)

        NEWS = ''
        for eid in self.feeds[rss]['entries']:
            thumbnail = self.feeds[rss]['entries'][eid]['thumbnail']
            title = self.feeds[rss]['entries'][eid]['title']
            summary = self.feeds[rss]['entries'][eid]['summary']
            updated = self.feeds[rss]['entries'][eid]['updated']
            link = self.feeds[rss]['entries'][eid]['link']
            tags = self.feeds[rss]['entries'][eid]['tags']
            NEWS += CARD_NP_ENTRY % (thumbnail, link, title, updated, summary)

            # RSS ENTRY PAGE
            properties = ''
            properties += ':RSSFeed: %s\n' % rss # RSS
            properties += ':Website: %s\n' % self.get_website(rss_link) # Website
            # ~ properties += ':Tag: %s\n' % tags # Tags
            properties += ':Updated: %s\n' % updated

            PAGE_NAME_ENTRY = self.get_page_id()
            PAGE_CONTENT_ENTRY = PAGE_NP_ENTRY % (title, properties, thumbnail, link, title, updated, summary)
            self.distribute_to_source(PAGE_NAME_ENTRY, PAGE_CONTENT_ENTRY)

        PAGE_NAME = self.feeds[rss]['header']['pageid']
        PAGE_CONTENT = PAGE_NP % (rss_title, rss_properties, rss_favicon, rss_link, rss_title, rss_summary, NEWS)
        self.distribute_to_source(PAGE_NAME, PAGE_CONTENT)

    def create_newspapers_page(self):
        CARD = self.template('CARD_DOC_NEWSPAPER')
        PAGE_NPS = self.template('PAGE_NEWSPAPERS')
        CARDS = ''
        for rss in self.feeds:
            rss_is_valid = self.feeds[rss]['header']['valid']
            if rss_is_valid:
                # Create newspaper page
                self.create_newspaper_page(rss)
                self.log.info("\t\tRSS valid: %s" % rss)
                link = self.feeds[rss]['header']['link']
                title = self.feeds[rss]['header']['title']
                summary = self.feeds[rss]['header']['summary']
                favicon = self.get_favicon_url(link)
                homepage = self.get_homepage(link)
                npurl = "%s.html" % self.feeds[rss]['header']['pageid']
                CARDS += CARD % (favicon, npurl, title, summary)
            else:
                self.log.warning("RSS not valid: %s" % rss)

        # Create page for all newspapers
        PAGE_CONTENT = PAGE_NPS % CARDS
        PAGE_NAME = 'newspapers'
        self.distribute(PAGE_NAME, PAGE_CONTENT)

    def validate_field(self, rss, field):
        try:
            value = self.feeds[rss]['header'][field]
            found = True
        except:
            found = False

        # ~ self.log.debug("RSS[%s][%s] = %s", rss, field, found)
        return found

    def validate_rss_feeds(self):
        core_fields = ['title', 'link', 'updated']
        for rss in self.feeds:
            has_title = self.validate_field(rss, 'title')
            has_summary = self.validate_field(rss, 'summary')
            has_link = self.validate_field(rss, 'link')
            # ~ has_update = self.validate_field(rss, 'updated')
            if has_title and has_summary and has_link:
                self.feeds[rss]['header']['valid'] = True
            else:
                self.feeds[rss]['header']['valid'] = False

    def create_newspaper(self):
        pass
        # ~ self.log.info("\t\t<-- Creating newspaper")
        # ~ source_path = self.srvapp.get_source_path()
        # ~ rss_file = os.path.join(source_path, 'rss.txt')
        # ~ if os.path.exists(rss_file):
            # ~ sources = open(rss_file, 'r').read().splitlines()
            # ~ self.process_feeds(sources)
            # ~ self.validate_feeds()
            # ~ self.create_newspapers_page()
        # ~ else:
            # ~ self.log.error ("RSS file path doesn't exist. Exit.")
            # ~ exit(-1)
        # ~ self.log.info("\t\tNewspaper created -->")


    def get_rss_data(self, rss):
        try:
            f = feedparser.parse(rss)
            return rss, f['feed'], f['entries']
        except:
            self.log.error("Error while getting data from: %s" % rss)
            return None

    def get_chanel_info(self, channel):
        header = {}
        for field in channel:
            # Only strings
            # ~ if isinstance(channel[field], str):
                # ~ header[field] = channel[field]
            # All fields:
            header[field] = channel[field]
        return header

    def get_field_value(self, entry, field):
        try:
            return entry[field]
        except:
            return ''

    def get_page_id(self):
        return str(uuid.uuid1())
        # ~ o = urlparse(link)
        # ~ rss_host = o.netloc
        # ~ rss_path = o.path
        # ~ return "%s_%s" % (valid_filename(rss_host.replace('.', '_')), valid_filename(rss_path))

    def process_feeds(self, sources):
        self.log.info("\t\tProcessing feeds")
        fieldsets = []
        with Executor(max_workers=5) as exe:
            jobs = []
            for rss in sources:
                if rss.startswith('#'):
                    continue
                job = exe.submit(self.get_rss_data, rss)
                jobs.append(job)
                # ~ self.log.debug("\t\tQuerying feed: %s" % rss)

            for job in jobs:
                rss, channel, entries = job.result()
                # ~ self.log.debug ("\t\tReceiving data from: %s" % channel['title'])

                # Process feed
                self.feeds[rss] = {}
                fieldset = set()

                ## Process feed header
                self.feeds[rss]['header']={}
                for field in channel:
                    fieldset.add(field)
                    if isinstance(channel[field], str):
                        self.feeds[rss]['header'][field] = channel[field]
                    elif isinstance(channel[field], feedparser.FeedParserDict):
                        pass

                ### Adjust summary field
                try:
                    summary = self.feeds[rss]['header']['subtitle']
                    self.feeds[rss]['header']['summary'] = summary
                    del(self.feeds[rss]['header']['subtitle'])
                except Exception as error:
                    self.log.error(error)
                    pass #sys.exit()

                ### Generate page id
                try:
                    pageid = self.get_page_id()#self.get_page_id(self.feeds[rss]['header']['link'])
                    self.feeds[rss]['header']['pageid'] = pageid
                except Exception as error:
                    self.log.error(error)
                    sys.exit()

                # ~ self.log.debug(self.feeds[rss]['header'])
                fieldsets.append(fieldset)

                ## Process feed entries
                self.feeds[rss]['entries']={}
                self.log.debug("RSS[%s]: processing entries", rss)
                for entry in entries:
                    eid = self.get_page_id() #entry['id']
                    try:
                        self.feeds[rss]['entries'][eid] = {}
                        self.feeds[rss]['entries'][eid]['RSSFeed'] = rss
                        self.feeds[rss]['entries'][eid]['title'] = self.get_field_value(entry, 'title')
                        self.feeds[rss]['entries'][eid]['summary'] = self.get_field_summary(entry)
                        self.feeds[rss]['entries'][eid]['thumbnail'] = self.get_field_value(entry, 'thumbnail')
                        self.feeds[rss]['entries'][eid]['link'] = self.get_field_value(entry, 'link')
                        self.feeds[rss]['entries'][eid]['updated'] = self.get_field_updated(entry)
                        tags = get_tags(self.feeds[rss]['entries'][eid]['title'])
                        self.feeds[rss]['entries'][eid]['tags'] = ', '.join(tags)
                        self.log.debug("RSS[%s]: Entry %s added", rss, eid)
                    except Exception as error:
                        self.log.warning("Error while parsing entry for RSS: %s", rss)
                        del(self.feeds[rss]['entries'][eid])


    def get_field_summary(self, entry):
        found = False
        fields = ['description', 'subtitle', 'summary']
        for field in entry:
            # ~ self.log.debug("Checking field: %s", field)
            if field in fields:

                try:
                    summary = entry[field]
                    found = True
                    break;
                except Exception as error:
                    self.log.error(", ".join(field for field in entry))

        if found:
            return summary
        else:
            return ''

    def get_field_updated(self, entry):
        found = False
        date_fields = ['updated', 'published', 'date', 'pubDate']
        for field in entry:
            if field in date_fields:
                try:
                    updated = entry[field]
                    found = True
                    break;
                except Exception as error:
                    self.log.error(", ".join(field for field in entry))

        if found:
            dt = parse(updated)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return None

        # ~ common_fields = set.intersection(*fieldsets)
        # ~ print ("Common fields for all RSS feeds: ")
        # ~ print(common_fields)
        # ~ {'links', 'subtitle', 'title', 'title_detail', 'subtitle_detail', 'link'}
        # ~ for rss in self.feeds:
            # ~ pageid = self.feeds[rss]['header']['pageid']
            # ~ self.distribute(pageid, str(self.feeds[rss]))
            # ~ self.log.debug("%s (%s)" % (self.feeds[rss]['header']['title'], self.feeds[rss]['header']['link']))
            # ~ for eid in self.feeds[rss]['entries']:
                # ~ title = self.feeds[rss]['entries'][eid]['title']
                # ~ published = self.feeds[rss]['entries'][eid]['published']
                # ~ link = self.feeds[rss]['entries'][eid]['link']
                # ~ self.log.debug("\t* %s (%s) via %s" % (title, published, link))
            # ~ print ("\t%s" % feeds[rss]['header']['subtitle'])
            # ~ print ("\t%s" % feeds[rss]['header']['link'])
            # ~ print ("")
        # ~ print(self.feeds)

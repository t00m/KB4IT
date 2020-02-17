#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: techdoc theme scripts
"""

from pprint import pprint
from kb4it.src.core.mod_utils import valid_filename, get_human_datetime
from kb4it.src.services.srv_builder import Builder

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
        self.create_blog_page()
        self.create_recents_page()

    def build_blog(self, doclist):
        self.log.debug("\t\t\t  Using custom build cardset function for blog posts")
        # ~ CARD = self.template('CARD_DOC_BLOG')
        CARDS = ""
        blog = {}
        years = []
        months = []
        for doc in doclist:
            post = self.srvdtb.get_doc_properties(doc)
            timestamp = post['Timestamp']
            year = "%4d" % timestamp.year
            month = "%4d%02d" % (timestamp.year, timestamp.month)

            if not year in years:
                years.append(year)

            if not month in months:
                months.append(month)

            try:
                posts = blog[year]
                posts.append(doc)
                blog[year] = posts
            except:
                blog[year] = []

            try:
                posts = blog[month]
                posts.append(doc)
                blog[month] = posts
            except:
                blog[month] = []

        HTML = "<ul>\n"
        for year in years:
            HTML += "\t<li>%s</li>\n" % year
            for month in months:
                if month.startswith(year):
                    HTML += "\t<ul>\n\t\t<li>%s</li>\n" % month[4:]
                    HTML += "\t\t<ul>\n"
                    for doc in blog[month]:
                        title = self.srvdtb.get_values(doc, 'Title')[0]
                        timestamp = self.srvdtb.get_values(doc, 'Timestamp')
                        HTML += "\t\t\t<li>%s - %s</li>\n" % (timestamp, title)
                    HTML += "\t\t</ul>\n"
            HTML += "\t</ul>\n"
        HTML += "</ul>\n"
        self.log.debug(HTML)
        return HTML

    def create_blog_page(self):
        doclist = []
        for doc in self.srvdtb.get_documents():
            category = self.srvdtb.get_values(doc, 'Category')[0]
            if category == 'Post':
                doclist.append(doc)
        self.build_pagination('blog', doclist, 'Blog', "build_blog")

    def create_events_page(self):
        doclist = set()
        for doc in self.srvdtb.get_documents():
            category = self.srvdtb.get_values(doc, 'Category')[0]
            if category == 'Event':
                doclist.add(doc)
        self.log.debug("Events: %d", len(doclist))
        self.build_pagination('events', doclist, 'Events')

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
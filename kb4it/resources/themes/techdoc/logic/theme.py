#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: techdoc theme scripts
"""

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
        CARD = self.template('CARD_DOC_BLOG')
        CARDS = ""
        for doc in doclist:
            title = self.srvdtb.get_values(doc, 'Title')[0]
            doc_card = self.get_doc_card(doc)
            card_search_filter = CARD % (valid_filename(title), doc_card)
            CARDS += """%s""" % card_search_filter
        return CARDS

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
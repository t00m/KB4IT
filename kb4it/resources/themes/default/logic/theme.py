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
        # Default pages
        self.create_all_keys_page()
        self.create_recents_page()
        self.create_properties_page()
        self.create_stats_page()
        self.create_index_all()
        self.create_index_page()
        self.create_about_page()
        self.create_help_page()

        # ~ # On steroids
        # ~ self.create_bookmarks_page()
        # ~ self.create_events_page()
        # ~ self.create_blog_page()
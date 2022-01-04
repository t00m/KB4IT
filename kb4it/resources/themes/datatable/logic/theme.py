#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: default theme script
"""

from kb4it.services.builder import Builder

class Theme(Builder):
    def generate_sources(self):
        pass

    def build(self):
        """Create standard pages for default theme"""
        # ~ self.create_page_properties()
        # ~ self.create_page_stats()
        # ~ self.create_page_index_all()
        self.create_page_index()
        # ~ self.create_page_about_app()
        # ~ self.create_page_about_theme()
        # ~ self.create_page_about_kb4it()
        # ~ self.create_page_help()

    def create_page_index(self):
        srcdir = self.srvbes.get_source_path()
        custom_index = os.path.join(srcdir, 'index.adoc')
        if not os.path.exists(custom_index):
            TPL_INDEX = self.template('PAGE_INDEX')
            var = {}
            var['title'] = 'Index'
            var['theme'] = self.srvbes.get_theme_properties()
            self.distribute('index', TPL_INDEX.render(var=var))

    # ~ def build_page(self, future):
        # ~ """
        # ~ Build the final HTML Page
        # ~ """
        # ~ now = datetime.now()
        # ~ timestamp = get_human_datetime(now)
        # ~ time.sleep(random.random())
        # ~ x = future.result()
        # ~ cur_thread = threading.current_thread().name
        # ~ if cur_thread != x:
            # ~ adoc, rc, j = x
            # ~ self.log.debug("[BUILD] - Page[%s]", adoc)
        # ~ return x
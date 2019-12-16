#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSS module.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: module for creating RSS feeds
"""

import os
from datetime import datetime
from kb4it.src.core.mod_srv import Service
from kb4it.src.core.mod_utils import last_ts_rss

DEFAULT_RSS_LOGO = "resources/images/rss-logo.png"

RSS_HEADER = """<?xml version="1.0"?>
<rss version="2.0">

<channel>
    <title>KB4IT</title>
    <link>index.html</link>
    <language>en</language>
    <description>RSS Feed for KB4IT</description>
    <pubDate>%s</pubDate>"""

RSS_FOOTER = """
</channel>
</rss>"""

RSS_ITEM = """
<item>
    <title>%s</title>
    <guid>%s</guid>
    <link>%s</link>
    <description>%s</description>
    <pubDate>%s</pubDate>
</item>"""


class RSS(Service):
    """Class for creating RSS feeds."""

    def initialize(self):
        """Initialize module."""
        self.get_services()

    def get_services(self):
        """Get services to be used in this module."""
        self.srvapp = self.app.get_service('App')
        self.srvdtb = self.app.get_service('DB')

    def generate_rss_main(self, lastdocs):
        """Create main RSS feed."""
        db = self.srvdtb.get_database()
        tmp_path = self.srvapp.get_temp_path()
        rss_file = os.path.join(tmp_path, 'rss.xml')
        now = datetime.now()
        items = ''
        for doc, timestamp in lastdocs:
            title = db[doc]['Title'][0]
            guid = doc
            link = ''
            description = ''
            adate = datetime.strptime(timestamp, "%Y/%m/%d %H:%M:%S")
            items += RSS_ITEM % (title, guid, link, description, last_ts_rss(adate))
        rss_content = RSS_HEADER % last_ts_rss(now) + items + RSS_FOOTER
        with open(rss_file, 'w') as frss:
            frss.write(rss_content)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RSS module.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: module for creating RSS feeds
"""

import os
from kb4it.src.core.mod_srv import Service

DEFAULT_RSS_LOGO = "resources/images/rss-logo.png"

RSS_HEADER = """<?xml version="1.0" ?>
<rss version="2.0">
<channel>
<title>KB4IT Repository</title>
<link>index.html</link>"""

RSS_ITEM = """
<item>
<title>%s</title>
<link>%s</link>
<description>%s</description>
</item>"""

RSS_FOOTER = """
</channel>
</rss>"""



class RSS(Service):
    """Class for creating RSS feeds."""

    def initialize(self):
        """Initialize module."""
        self.get_services()

    def get_services(self):
        """Get services to be used in this module."""
        self.srvapp = self.app.get_service('App')

    def generate_rss_main(self):
        """Create main RSS feed."""
        tmp_path = self.srvapp.get_temp_path()
        rss_file = os.path.join(tmp_path, 'rss.xml')
        rss_content = RSS_HEADER + RSS_FOOTER
        with open(rss_file, 'w') as frss:
            frss.write(rss_content)

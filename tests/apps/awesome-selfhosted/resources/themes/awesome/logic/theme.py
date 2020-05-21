#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: KB4IT demo app. Download index project Awesome Selfhosted
#              and build a KB4IT website
"""

import os
import re
import requests

from kb4it.src.core.mod_env import LPATH
from kb4it.src.core.mod_utils import valid_filename
from kb4it.src.services.srv_builder import Builder

TAG_START = """<!-- BEGIN SOFTWARE LIST -->"""
TAG_END = """<!-- END SOFTWARE LIST -->"""

AWESOME_README_INTERNET = 'https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md'

class Theme(Builder):
    def hello(self):
        self.log.debug("This is the theme techdoc")

    def generate_sources(self):
        """Generate pages from Awesome Selfhosted README.md"""

        if not os.path.exists('src'):
            os.makedirs('src')

        TMPDIR = self.srvapp.get_temp_path()
        AWESOME_README_LOCAL = os.path.join(TMPDIR, 'awesome-selfhosted.md')

        self.download(AWESOME_README_INTERNET, AWESOME_README_LOCAL)

        with open(AWESOME_README_LOCAL, 'r') as fin:
            lines = fin.read().splitlines()
            n = 0
            for line in lines:
                if line.startswith(TAG_START):
                    s = n + 1
                if line.startswith(TAG_END):
                    e = n
                n += 1

        for line in lines[s:e]:
            # Get topic, category and subcategory
            if line.startswith('#'):
                header = line[:line.find(' ')]
                if len(header) == 2:
                    topic = line[line.find(' ')+1:]
                    category = ""
                    subcategory = ""
                if len(header) == 3:
                    category = line[line.find(' ')+1:]
                    subcategory = ""
                if len(header) == 4:
                    subcategory = line[line.find(' ')+1:]

            # Get awesome selfhosted solutions properties
            if line.startswith('- '):
                solution = {}
                solution['topic'] = topic
                solution['category'] = category
                solution['subcategory'] = subcategory

                # Language
                sl = line[:-1].rfind('`')
                lang = line[sl+1:-1]
                line = line[:sl-1]
                solution['language'] = lang

                # License
                sl = line[:-1].rfind('`')
                lic = line[sl+1:-1]
                line = line[:sl-1]
                solution['license'] = lic

                # Demo and Source Code links
                ssd = line.rfind('[Demo]')
                has_demo = ssd > 0

                ssc = line.rfind('[Source Code]')
                has_code = ssc > 0

                if has_demo or has_code:
                    if has_demo and has_code:
                        eol = ssd
                        links = line[ssd:-1]
                        eud = links.find(')')
                        url_demo = links[7:eud]
                        url_code = links[eud+17:-1]
                    else:
                        if has_demo:
                            eol = ssd
                            links = line[ssd:-1]
                            url_demo = links[7:-1]
                            url_code = ""
                        if has_code:
                            eol = ssc
                            links = line[ssc:-1]
                            url_demo = ""
                            url_code = links[14:-1]
                else:
                    eol = None
                    url_demo = ""
                    url_code = ""

                solution['url_demo'] = url_demo
                solution['url_code'] = url_code

                if eol is not None:
                    line = line[:eol-1]

                # Solution name and url
                es = line.find(')')
                core = line[:es]
                name = core[core.find('[')+1:core.find(']')]
                url = core[len(name)+5:es]
                solution['name'] = name
                solution['url'] = url

                # Description
                line = line[es+1:]
                ed = line.find('(')
                if ed < 0:
                    ed = line.find('`')
                description = line[2:ed].strip()
                solution['description'] = description
                self.write_page(solution)


    def build(self):
        # Default pages
        self.create_page_properties()
        self.create_page_stats()
        self.create_page_index_all()
        self.create_page_index()
        self.create_page_about_app()
        self.create_page_about_theme()
        self.create_page_about_kb4it()
        # ~ self.create_page_help()
        pass


    def download(self, url, filename):
        r = requests.get(url, allow_redirects=True, stream=True)
        with open(filename, 'wb') as fout:
            bytes_recvd = fout.write(r.content)


    def write_page(self, solution):
        PAGE = self.template('PAGE')
        NAME = valid_filename(solution['name'])
        CONTENT = PAGE % (
                            solution['name'],
                            solution['language'],
                            solution['license'],
                            solution['topic'],
                            solution['category'],
                            solution['subcategory'],
                            solution['description'],
                            solution['url'], solution['name'],
                            solution['url_code'], solution['url_code'],
                            solution['url_demo'], solution['url_demo']
                        )
        self.distribute_to_source(NAME, CONTENT)


    def create_page_index(self):
        PAGE = self.template('PAGE_INDEX')
        CONTENT = PAGE
        self.distribute_to_source('index', CONTENT)

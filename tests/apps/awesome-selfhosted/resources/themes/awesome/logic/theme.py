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
import math
import requests

from kb4it.src.core.mod_env import LPATH
from kb4it.src.core.mod_utils import valid_filename, get_font_size
from kb4it.services.builder import KB4ITBuilder

TAG_START = """<!-- BEGIN SOFTWARE LIST -->"""
TAG_END = """<!-- END SOFTWARE LIST -->"""

AWESOME_README_INTERNET = 'https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md'

class Theme(KB4ITBuilder):
    index = ""
    solutions = {}

    def hello(self):
        self.log.debug("This is the theme techdoc")

    def generate_sources(self):
        """Generate pages from Awesome Selfhosted README.md"""

        adoc = ""

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
                len_header = len(header)
                if len_header == 2:
                    topic = line[line.find(' ')+1:]
                    category = ""
                    subcategory = ""
                if len_header == 3:
                    category = line[line.find(' ')+1:]
                    subcategory = ""
                if len_header == 4:
                    subcategory = line[line.find(' ')+1:]

                # Fix wrong levels
                if category == '' and subcategory != '':
                    category = subcategory
                    subcategory = ''

                if len_header == 2:
                    adoc += ". <<%s#, %s>>\n" % (valid_filename("Topic_%s" % topic), topic)
                elif len_header == 3:
                    adoc += ".. <<%s#, %s>>\n" % (valid_filename("Category_%s" % category), category)
                elif len_header == 4:
                    adoc += "... <<%s#, %s>>\n" % (valid_filename("Subcategory_%s" % subcategory), subcategory)

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
                name = core[core.find('[')+1:core.find(']')].strip()
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
                self.solutions[name] = solution
                self.write_page(solution)

        self.index = adoc



    def build(self):
        # Default pages
        self.create_page_properties()
        self.create_page_stats()
        self.create_page_index_all()
        self.create_page_index()
        self.create_page_about_app()
        self.create_page_about_theme()
        self.create_page_about_kb4it()


    def download(self, url, filename):
        try:
            r = requests.get(url, allow_redirects=True, stream=True)
            with open(filename, 'wb') as fout:
                bytes_recvd = fout.write(r.content)
        except Exception as error:
            self.log.error(error)
            exit()


    def write_page(self, solution):
        PAGE = self.template('PAGE')
        NAME = valid_filename(solution['name'])
        CONTENT = PAGE % (
                            solution['name'],
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

    def create_page_properties(self):
        """Create properties page"""
        self.properties = {}
        TPL_PROPS_PAGE = self.template('PAGE_PROPERTIES')
        TPL_KEY_MODAL_BUTTON = self.template('KEY_MODAL_BUTTON')
        max_frequency = self.get_maxkv_freq()
        all_keys = self.srvdtb.get_all_keys()
        custom_buttons = ''
        for key in all_keys:
            ignored_keys = self.srvdtb.get_ignored_keys()
            if key not in ignored_keys:
                html = self.create_tagcloud_from_key(key)
                values = self.srvdtb.get_all_values_for_key(key)
                frequency = len(values)
                size = get_font_size(frequency, max_frequency)
                proportion = int(math.log((frequency * 100) / max_frequency))
                tooltip = "%d values" % len(values)
                button = TPL_KEY_MODAL_BUTTON % (valid_filename(key), tooltip, size, key, valid_filename(key), valid_filename(key), key, html)
                custom_buttons += button
                self.properties[key] = html
        content = TPL_PROPS_PAGE % (custom_buttons)
        self.distribute('properties', content)

    def create_page_about_app(self):
        """About app page."""
        CONTENT = self.template('PAGE_ABOUT_APP')
        self.distribute('about_app', CONTENT)

    def create_page_index(self):
        PAGE = self.template('PAGE_INDEX')
        CONTENT = PAGE % (self.index, self.properties['Topic'])
        self.distribute('index', CONTENT)


    def get_doc_card(self, doc):
        """Get card for a given doc"""
        source_dir = self.srvapp.get_source_path()
        DOC_CARD = self.template('CARD_DOC')
        DOC_CARD_FOOTER = self.template('CARD_DOC_FOOTER')
        LINK = self.template('LINK')
        name = self.srvdtb.get_values(doc, 'Name')[0]
        title = self.srvdtb.get_values(doc, 'Title')[0]
        topic = self.srvdtb.get_values(doc, 'Scope')[0]
        category = self.srvdtb.get_values(doc, 'Category')[0]
        subcategory = self.srvdtb.get_values(doc, 'Subategory')[0]
        link_title = LINK % ("uk-link-heading uk-text-meta", "%s.html" % valid_filename(doc).replace('.adoc', ''), "", title)
        link_topic = LINK % ("uk-link-heading uk-text-meta", "Topic_%s.html" % valid_filename(doc).replace('.adoc', ''), "", topic)
        tooltip ="%s" % (title)

        try:
            description = self.solutions[name]['description']
        except:
            description = ''
        return DOC_CARD % (tooltip, link_title, topic, description)

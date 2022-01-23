#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Builder service.

# File: srv_builder.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: Create KB4IT pages
"""

import os
import sys
import math
import shutil
from datetime import datetime
try:
    import html5lib
    import webencodings
    from bs4 import BeautifulSoup as bs
    TIDY = True
except:
    TIDY = False
from kb4it.core.env import APP, GPATH
from kb4it.core.service import Service
from kb4it.core.util import valid_filename
from kb4it.core.util import get_human_datetime, fuzzy_date_from_timestamp
from kb4it.core.util import set_max_frequency, get_font_size
from kb4it.core.util import delete_files
from kb4it.core.util import get_hash_from_file, load_kbdict
from kb4it.core.util import get_asciidoctor_attributes

from mako.template import Template


TEMPLATES = {}


class Builder(Service):
    """Build HTML blocks"""

    tmpdir = None
    srvdtb = None
    backend = None
    temp_sources = []
    distributed = None

    def initialize(self):
        """Initialize Builder class."""
        self.get_services()
        self.tmpdir = self.srvbes.get_temp_path()
        self.srcdir = self.srvbes.get_source_path()
        self.now = datetime.now()
        self.distributed = {}

    def get_distributed(self):
        """Get a list of pages distributed"""
        return self.distributed

    def finalize(self):
        """Clean up temporary files"""
        # Delete temporary sources generated by themes
        delete_files(self.temp_sources)

    def get_services(self):
        """Get services."""
        self.srvdtb = self.get_service('DB')
        self.srvbes = self.get_service('Backend')

    def distribute_adoc(self, name, content):
        """
        Distribute source file to temporary directory.

        Use this method when the source asciidoctor file doesn't have to
        be analyzed.
        """
        self.log.debug("[DIST-ADOC] %s", name) 
        PAGE_NAME = "%s.adoc" % name
        PAGE_PATH = os.path.join(self.tmpdir, PAGE_NAME)
        with open(PAGE_PATH, 'w') as fpag:
            try:
                fpag.write(content)
            except Exception as error:
                self.log.error("[DISTRIBUTE] - %s", error)
        self.distributed[PAGE_NAME] = get_hash_from_file(PAGE_PATH)
        self.srvbes.add_target(PAGE_NAME.replace('.adoc', '.html'))
        self.log.debug("[DISTRIBUTE] - Page[%s] distributed to temporary path", os.path.basename(PAGE_PATH))

    def distribute_html(self, name, content, var):
        """
        Distribute html file to the temporary directory.
        """
        var['menu_contents'] = ''
        HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
        HTML_HEADER_DOC = self.template('HTML_HEADER_DOC')
        HTML_HEADER_NODOC = self.template('HTML_HEADER_NODOC')
        HTML_FOOTER = self.template('HTML_FOOTER')

        HTML = ""
        HEADER = HTML_HEADER_COMMON.render(var=var)
        FOOTER = HTML_FOOTER.render(var=var)

        HTML += HEADER
        HTML += content
        HTML += FOOTER

        PAGE_NAME = "%s.html" % name
        PAGE_PATH = os.path.join(self.tmpdir, PAGE_NAME)
        with open(PAGE_PATH, 'w') as fpag:
            try:
                fpag.write(HTML)
            except Exception as error:
                self.log.error("[DISTRIBUTE] - %s", error)
        self.distributed[PAGE_NAME] = get_hash_from_file(PAGE_PATH)
        self.srvbes.add_target(PAGE_NAME)
        self.log.debug("[DISTRIBUTE] - Page[%s] distributed to temporary path", os.path.basename(PAGE_PATH))

    def distribute_to_source(self, name, content):
        """
        Distribute source file to user source directory.
        Use this method when the source asciidoctor file has to
        be analyzed to extract its properties.
        File path reference will be saved and deleted at the end of the
        execution.
        """
        PAGE_NAME = "%s.adoc" % name
        PAGE_PATH = os.path.join(self.srcdir, PAGE_NAME)
        self.temp_sources.append(PAGE_PATH)
        try:
            with open(PAGE_PATH, 'w') as fpag:
                fpag.write(content)
                self.log.debug("[BUILDER] - PAGE[%s] distributed to source path", name)
        except OSError as error:
            self.log.error(error)

    def template(self, template):
        """Return the template content from default theme or user theme"""

        properties = self.srvbes.get_runtime()
        theme = properties['theme']
        current_theme = theme['id']

        # Try to get the template from cache
        try:
            tpl = TEMPLATES[template]
            # ~ self.log.debug("[TEMPLATES] - Template[%s] loaded from cache", template)
            return tpl
        except KeyError:
            try:
                # Get template from theme
                template_path = os.path.join(theme['templates'], "%s.tpl" % template)
                TEMPLATES[template] = Template(filename=template_path)
                self.log.debug("[TEMPLATES] - Template[%s] loaded for Theme[%s] and added to the cache", template, theme['id'])
            except FileNotFoundError as error:
                try:
                    # Try with global templates
                    template_path = os.path.join(GPATH['TEMPLATES'], "%s.tpl" % template)
                    TEMPLATES[template] = Template(filename=template_path)
                    self.log.debug("[TEMPLATES] - Global Template[%s] loaded and added to the cache", template)
                except FileNotFoundError as error:
                    TEMPLATES[template] = Template("")
                    self.log.warning("[TEMPLATES] - Template[%s] not found. Returning empty template!", template)

            return TEMPLATES[template]

    def render_template(self, name):
        tpl = self.template(name)
        return tpl.render()
        
    def get_theme_var(self):
        var = {}
        var['theme'] = self.srvbes.get_theme_properties()
        var['kbdict'] = self.srvbes.get_kb_dict()
        return var

    def page_hook_pre(self, basename):
        """ Insert html code before the content.
        This method can be overwriten by custom themes.
        """
        return """<!-- Page hook pre -->"""

    def page_hook_post(self, var):
        """ Insert html code after the content.
        This method can be overwriten by custom themes.
        """
        return """<!-- Page hook post -->"""

    def extract_toc(self, source):
        """Extract TOC from Asciidoctor generated HTML code and
        make it theme dependent."""
        toc = ''
        items = []
        lines = source.split('\n')
        s = e = n = 0
        var = {}
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

    def create_page_key(self, key, values):
        """Create page for a key."""
        TPL_PAGE_KEY = self.template('PAGE_KEY_KB4IT')
        var = {}

        # Title
        var['title'] = key
        var['key_values'] = {}
        for value in values:
            k_value = "%s_%s" % (valid_filename(key), valid_filename(value))
            var['key_values'][k_value] = {}
            docs = self.srvdtb.get_docs_by_key_value(key, value)
            var['key_values'][k_value]['count'] = len(docs)
            var['key_values'][k_value]['vfkey'] = valid_filename(key)
            var['key_values'][k_value]['vfvalue'] = valid_filename(value)
            var['key_values'][k_value]['name'] = value
        html = TPL_PAGE_KEY.render(var=var)
        # ~ self.log.debug("PageKey[%s]:\n%s", key, html)
        return html

    def transform(self, content, var):
        """Transform output document HTML source code.
        This method can be overwriten by custom themes.
        """
        self.log.debug("[BUILD] - Page[%s] - No transformation invoked", var['basename_html'])
        return content, var

    def build_page(self, adoc):
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
        
        hdoc = adoc.replace('.adoc', '.html')
        basename_adoc = os.path.basename(adoc)
        basename_hdoc = os.path.basename(hdoc)
        exists_adoc = os.path.exists(adoc) # it should be true
        exists_hdoc = os.path.exists(hdoc) # it should be true


        if not exists_hdoc:
            self.log.error("[BUILD] - Source[%s] not converted to HTML properly", basename_adoc)
        else:
            self.log.debug("[BUILD] - Page[%s] transformation started", basename_hdoc)
            THEME_ID = self.srvbes.get_theme_property('id')
            HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
            HTML_HEADER_DOC = self.template('HTML_HEADER_DOC')
            HTML_HEADER_NODOC = self.template('HTML_HEADER_NODOC')
            HTML_FOOTER = self.template('HTML_FOOTER')
            var = self.get_theme_var()
            now = datetime.now()
            timestamp = get_human_datetime(now)
            keys = get_asciidoctor_attributes(adoc)
            source = open(hdoc, 'r').read()
            toc = self.extract_toc(source)
            var['toc'] = toc
            if len(toc) > 0:
                var['has_toc'] = True
                TPL_HTML_HEADER_MENU_CONTENTS_ENABLED = self.template('HTML_HEADER_MENU_CONTENTS_ENABLED')
                HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_ENABLED.render(var=var)
            else:
                var['has_toc'] = False
                TPL_HTML_HEADER_MENU_CONTENTS_DISABLED = self.template('HTML_HEADER_MENU_CONTENTS_DISABLED')
                HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_DISABLED.render()
            var['menu_contents'] = HTML_TOC
            var['keys'] = keys
            var['title'] = ', '.join(keys['Title'])
            var['basename'] = basename_adoc
            var['basename_hdoc'] = basename_hdoc
            var['meta_section'] = ""
            var['source_code'] = ""
            var['timestamp'] = timestamp

            HTML = ""
            content = open(hdoc, 'r').read()
            BODY, var = self.transform(content, var)
            HEADER = HTML_HEADER_COMMON.render(var=var)
            FOOTER = HTML_FOOTER.render(var=var)

            HTML += HEADER
            HTML += BODY
            HTML += FOOTER

            with open(hdoc, 'w') as fhtml:
                fhtml.write(HTML)
            self.log.debug("[BUILD] - Page[%s] transformation finished", basename_hdoc)

    def create_page_properties(self):
        """Create properties page"""
        TPL_PROPS_PAGE = self.template('PAGE_PROPERTIES')
        TPL_KEY_MODAL_BUTTON = self.template('KEY_MODAL_BUTTON')
        max_frequency = self.get_maxkv_freq()
        all_keys = self.srvdtb.get_all_keys()
        custom_buttons = ''
        var = {}
        var['buttons'] = []
        for key in all_keys:
            ignored_keys = self.srvdtb.get_ignored_keys()
            if key not in ignored_keys:
                vbtn = {}
                vbtn['content'] = self.create_tagcloud_from_key(key)
                values = self.srvdtb.get_all_values_for_key(key)
                frequency = len(values)
                size = get_font_size(frequency, max_frequency)
                proportion = int(math.log((frequency * 100) / max_frequency))
                vbtn['key'] = key
                vbtn['vfkey'] = valid_filename(key)
                vbtn['size'] = size
                vbtn['tooltip'] = "%d values" % len(values)
                button = TPL_KEY_MODAL_BUTTON.render(var=vbtn) # % (valid_filename(key), tooltip, size, key, valid_filename(key), valid_filename(key), key, html)
                var['buttons'].append(button)
        content = TPL_PROPS_PAGE.render(var=var)
        # ~ print(content)
        self.distribute_adoc('properties', content)

    def create_tagcloud_from_key(self, key):
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
            var = {}
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

    def create_page_stats(self):
        """Create stats page"""
        TPL_PAGE_STATS = self.template('PAGE_STATS')
        var = {}
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

    def create_page_index_all(self):
        """Create a page with all documents"""
        doclist = self.srvdtb.get_documents()
        TPL_PAGE_ALL = self.template('PAGE_ALL')
        var = self.get_theme_var()        
        page = TPL_PAGE_ALL.render(var=var)
        self.distribute_adoc('all', page)
        
    def generate_sources(self):
        """Custom themes can use this method to generate source documents"""
        pass

    def generate_pages(self):
        """Custom themes can use this method to generate final pages"""
        pass

    def build_page_key_value(self, var):
        pagelist = []
        TPL_PAGE_KEY_VALUE = self.template(var['template'])
        adoc = TPL_PAGE_KEY_VALUE.render(var=var)
        # ~ self.log.debug(adoc)
        if not var['fake']:
            self.distribute_adoc(var['basename'], adoc)
        pagelist.append(var['basename'])
        self.log.debug("[BUILDER] - Created page key-value '%s'", var['basename'])

        return pagelist
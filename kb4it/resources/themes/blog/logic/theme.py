#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# Author: Tomás Vírseda
# License: GPL v3
# Description: Theme Blog for KB4IT
"""

import os
import sys
import threading
from html import escape

from kb4it.core.util import (extract_sections_from_md, get_font_size, get_human_datetime_year, guess_datetime,
                             valid_filename)
from kb4it.core.structured import DEFAULT_MAP
from kb4it.services.themekit import DocumentTheme
from kb4it.core.log import q


class Theme(DocumentTheme):
    properties_title = 'Metadata'
    reserved_pages = ('404.md',)  # build() writes 404.html
    add_page = True   # create_page_add() runs in build()
    reuse_unchanged_pages = True
    datatable_link_template = 'LINK'

    def _post_author(self, post, metadata):
        """The first Author of a post, with the link to its page and the tooltip of its profile, for the post header."""
        author = next((v for v in metadata.get('Author') or [] if v), '')
        if author:
            post['Author_0_Url'] = metadata.get(f'Author_{author}_Url') or f"Author_{valid_filename(author)}.html"
            post['Author_0_Tip'] = self.person_tip('Author', author)

    def _initialize(self):
        super()._initialize()
        self._undated = set()
        self._undated_lock = threading.Lock()

    def structured_defaults(self):
        """Override: a post is a BlogPosting and its Category is the section of the blog."""
        return {'type': 'BlogPosting', 'map': {**DEFAULT_MAP, 'Category': 'articleSection'}}

    def note_undated(self, doc, dates):
        """Log once a post without a usable Date: it is listed after the dated ones, without a calendar line."""
        stamp = (dates or [None])[0]
        if stamp and guess_datetime(stamp) is not None:
            return
        with self._undated_lock:
            if doc in self._undated:
                return
            self._undated.add(doc)
        self.log.warning(f"[THEME] DOC_UNDATED doc={q(doc)}")

    # ~ @timeit
    def datatable_date_cell(self, timestamp):
        """Blog's date cell: a link to the day's page, no alignment class."""
        if timestamp is None:
            return '<td class=""></td>'
        ts_title = escape(timestamp[:16])
        ts_link = escape(f"events_{timestamp[:10].replace('-', '')}.html")
        return f"""<td class=""><a class="uk-link-heading" href="{ts_link}">{ts_title}</a></td>"""

    def build_page_index(self):
        """Create blog index page.

        At this point, all posts have been already converted to HTML, so
        instead of recompiling them, the body code is extracted from the
        Markdown source and reinjected in the index page.
        """
        if self.srvbes.get_value('runtime', 'ncd') == 0:
            func_name = sys._getframe().f_code.co_name
            cached = os.path.join(self.srvbes.get_path('cache'), 'index.html')
            if os.path.exists(cached):
                self.log.debug(f"[THEME] SKIP reason=no_doc_changes func={q(func_name)}")
                self.srvbes.add_target('index.md', 'index.html')
                return

        var = self.get_theme_var()
        TPL_POST = self.template('POST_MD_INDEX')
        TPL_INDEX = self.template('PAGE_INDEX')
        repo = self.srvbes.get_dict('repo')
        sort_by = "Date"
        try:
            nip = repo['index_posts']  # Number of posts to display in index
        except KeyError:
            nip = 10  # Default number of post in index page
        var['page']['title'] = "Index"

        doclist = self.srvdtb.get_documents()
        html_parts = [TPL_INDEX.render(var=var)]
        for post in doclist[:nip]:
            var['post'] = {}
            var['post']['filename'] = post
            metadata = self.srvdtb.get_doc_properties(post)
            for prop in metadata:
                var['post'][prop] = metadata[prop]
            self._post_author(var['post'], metadata)
            md_filepath = os.path.join(self.srvbes.get_path('source'), post)
            with open(md_filepath, 'r', encoding='utf-8') as fmd:
                md_content = fmd.read()
            sections = extract_sections_from_md(md_filepath)
            if 'Excerpt' in sections:
                s = sections['Excerpt']['start']
                e = sections['Excerpt']['end']
                lines = md_content.splitlines()
                text = '\n'.join(lines[s:e])
                var['post']['Excerpt'] = "\n".join(
                    [f"<p>{line}</p>" if line.strip() else line
                     for line in text.strip().splitlines()]
                )
            else:
                var['post']['Excerpt'] = "<p>Excerpt missing</p>"
            self.note_undated(post, var['post'].get(sort_by))
            var['basename_md'] = post
            var['metadata'] = self.build_metadata_section(post)
            var['source_md'] = md_content
            try:
                html_parts.append(TPL_POST.render(var=var))
                self.log.debug(f"[THEME] INDEX_ADD doc={q(post)}")
            except Exception as error:
                self.log.warning(f"[THEME] INDEX_SKIP doc={q(post)} error={q(error)}")

        html = ''.join(html_parts)
        self.add_system_page('index', 'Index', html)

    def build_year_pagination(self, years):
        EVENTCAL_YEAR_PAGINATION = self.template('EVENTCAL_YEAR_PAGINATION')
        EVENTCAL_YEAR_PAGINATION_ITEM = self.template('EVENTCAL_YEAR_PAGINATION_ITEM')
        var = {}
        items = []
        for yp in sorted(years, reverse=True):
            item = {}
            item['year'] = yp

            total = 0
            for month in self.events_docs[yp]:
                for day in self.events_docs[yp][month]:
                    total += len(self.events_docs[yp][month][day])
            item['year_count'] = total
            items.append(EVENTCAL_YEAR_PAGINATION_ITEM.render(var=item))
        var['items'] = ''.join(items)
        return EVENTCAL_YEAR_PAGINATION.render(var=var)

    def build_page_events(self):
        doclist = []
        ecats = {}
        repo = self.srvbes.get_dict('repo')
        event_types = repo.get('events', [])

        for docId in self.srvdtb.get_documents():
            if self.srvdtb.is_system(docId):
                continue
            category = self.srvdtb.get_values(docId, 'Category')[0]
            doclist.append(docId)
            title = self.srvdtb.get_values(docId, 'Title')[0]
        self.build_events(doclist)
        HTML = self.build_year_pagination(self.dey.keys())

        if self.srvbes.get_value('runtime', 'ncd') == 0:
            func_name = sys._getframe().f_code.co_name
            cached = os.path.join(self.srvbes.get_path('cache'), 'events.html')
            if os.path.exists(cached):
                self.log.debug(f"[THEME] SKIP reason=no_doc_changes func={q(func_name)}")
                self.srvbes.add_target('events.md', 'events.html')
                return

        events = {}
        events['content'] = HTML
        page = self.template('PAGE_EVENTS')
        self.add_system_page('events', 'Archive', page.render(var=events))

    def post_activities(self):
        self.log.debug("[THEME] POST_START")
        # ~ var = self.get_theme_var()
        # ~ self.build_page_index(var)
        self.log.debug("[THEME] POST_END")

    def build(self):
        """Create standard pages for default theme"""
        self.build_page_index()
        self.build_page_events()
        self.build_page_properties()
        self.build_page_stats()
        self.build_page_bookmarks()
        self.build_page_404()
        self.build_page_index_all()
        self.create_page_about_kb4it()
        self.create_page_about_app()
        self.create_page_search()
        self.create_page_add()

    def page_context(self, doc_id, var):
        """Override: the post, the property counts, topics and tags, the header menu and the metadata."""
        var['count_docs'] = self.srvdtb.get_documents_count()
        keys = self.srvdtb.get_all_keys()
        var['count_keys'] = len(keys)
        var['leader_items'] = [{'key': key, 'vfkey': valid_filename(key),
                                'count_values': len(self.srvdtb.get_all_values_for_key(key))}
                               for key in keys if key != 'Date']
        var['post'] = dict(var['keys'])
        self._post_author(var['post'], var['keys'])
        if not var['SystemPage']:
            self.note_undated(doc_id, var['post'].get('Date'))
        var['topics'] = self.srvdtb.get_all_values_for_key('Topic')
        var['tags'] = self.srvdtb.get_all_values_for_key('Tag')
        var['menu_contents'] = self.menu_contents(var)
        var['metadata'] = self.build_metadata_section(doc_id)
        return var

    def page_body_template(self, doc_id, var):
        """Override: a document is a post; with repo.json strict only a document whose Category is Post."""
        if var['SystemPage']:
            return 'HTML_BODY'
        if (self.srvbes.get_dict('repo') or {}).get('strict', False):
            return 'POST_HTML_SINGLE' if 'Post' in var['post']['Category'] else 'HTML_BODY'
        return 'POST_HTML_SINGLE'

    def render_page(self, doc_id, var):
        """Override: a body template that fails (a document without Date or Category) falls back to HTML_BODY."""
        header = self.template('HTML_HEADER_COMMON').render(var=var)
        name = 'POST_HTML_SINGLE'  # the only choice that can fail
        try:
            name = self.page_body_template(doc_id, var)
            body = self.template(name).render(var=var)
        except Exception as error:
            self.log.warning(f"[THEME] POST_TEMPLATE_FALLBACK doc={q(doc_id)} template={q(name)} "
                             f"error={q(' '.join(str(error).split()) or type(error).__name__)}")
            body = self.template('HTML_BODY').render(var=var)
        return header + body + self.template('HTML_FOOTER').render(var=var)

    def get_related(self, docId):
        """Get a list of related documents for each tag"""
        # DISABLED:
        # Related section code works.
        # However, because of the workflow do not detect which sources
        # have been added or removed, if any of the remaining sources do
        # not change, the related section will not be rebuilt again.
        # As a consecuence, documents displayed in the related section
        # might not exist. Or the other way around, the new documents
        # might exist, but they are not referenced.
        # Workaround: just browse the metadata from the document menu

        TPL_SECTION_RELATED = self.template('SECTION_RELATED')
        blocked_keys = self.srvdtb.get_blocked_keys()
        doclist = set()
        doc_keys = self.srvdtb.get_doc_properties(docId)
        filtered_keys = [key for key in doc_keys if key not in blocked_keys]
        for key in filtered_keys:
            for value in self.srvdtb.get_values(docId, key):
                for rel_docId in self.srvdtb.get_docs_by_key_value(key, value):
                    doclist.add(rel_docId)

        doclist.discard(docId)
        self.log.debug(f"[THEME] RELATED_FOUND doc={q(docId)} n={len(doclist)}")

        headers = []
        var = self.get_theme_var()
        var['datatable'] = self.build_datatable(headers, doclist)
        html_related = TPL_SECTION_RELATED.render(var=var)
        return html_related

    def cloud_measure(self, frequency, max_frequency):
        """Blog sizes property buttons and tag cloud words by font size."""
        return {'size': get_font_size(frequency, max_frequency)}

    def frequency_keys(self):
        """Blog sizes the property buttons against every property that is not blocked."""
        blocked_keys = self.srvdtb.get_blocked_keys()
        return [key for key in self.srvdtb.get_all_keys() if key not in blocked_keys]

    def stats_keys(self):
        """Blog lists every property on the stats page."""
        return self.srvdtb.get_all_keys()

    def generate_sources(self):
        """This theme doesn't generate sources, yet."""
        # ~ self.build_page_index()
        self.log.debug("[THEME] NO_SOURCES_GENERATED")

    def get_theme_var(self):
        var = super().get_theme_var()
        # The footer prints the tagline; an empty line when repo.json has none.
        var['repo'].setdefault('tagline', '')
        return var


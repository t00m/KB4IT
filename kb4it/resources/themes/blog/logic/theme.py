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
from datetime import datetime
from html import escape

from kb4it.core.env import ENV
from kb4it.core.util import (ellipsize_text, extract_sections_from_md,
                             get_font_size, get_human_datetime,
                             get_human_datetime_year, guess_datetime,
                             html_id_for, valid_filename)
from kb4it.services.themekit import DocumentTheme


class Theme(DocumentTheme):
    properties_title = 'Metadata'
    reuse_unchanged_pages = True
    datatable_link_template = 'LINK'
    events_rebuild_all = True

    def _initialize(self):
        super()._initialize()
        self._undated = set()
        self._undated_lock = threading.Lock()

    def note_undated(self, doc, dates):
        """Log once a post without a usable Date: it is listed after the dated ones, without a calendar line."""
        stamp = (dates or [None])[0]
        if stamp and guess_datetime(stamp) is not None:
            return
        with self._undated_lock:
            if doc in self._undated:
                return
            self._undated.add(doc)
        self.log.warning(f"[THEME] DOC_UNDATED doc={doc}")

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
                self.log.debug(f"[THEME] SKIP reason=no_doc_changes func={func_name}")
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
                self.log.debug(f"[THEME] INDEX_ADD doc={post}")
            except Exception as error:
                self.log.warning(f"[THEME] INDEX_SKIP doc={post} error={error}")

        html = ''.join(html_parts)
        self.distribute_md('index', html)
        self.srvdtb.add_document('index.md')
        self.srvdtb.add_document_key('index.md', 'Title', 'Index')
        self.srvdtb.add_document_key('index.md', 'SystemPage', 'Yes')

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
                self.log.debug(f"[THEME] SKIP reason=no_doc_changes func={func_name}")
                self.srvbes.add_target('events.md', 'events.html')
                return

        events = {}
        events['content'] = HTML
        page = self.template('PAGE_EVENTS')
        self.distribute_md('events', page.render(var=events))

        self.srvdtb.add_document('events.md')
        self.srvdtb.add_document_key('events.md', 'Title', 'Archive')
        self.srvdtb.add_document_key('events.md', 'SystemPage', 'Yes')

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
        self.build_page_index_all()
        self.create_page_about_kb4it()
        self.create_page_about_app()
        self.create_page_search()

    def page_hook_pre(self, var):
        var['related'] = ''
        var['metadata'] = ''
        var['source'] = ''
        var['actions'] = ''
        return var

    def page_hook_post(self, var):
        return var

    def build_page(self, path_md, var={}):
        """Build the final HTML Page.

        At this point, the Markdown compilation has finished successfully,
        and therefore the html page can be built. The Builder receives the
        source filepath; another file with extension .html should also
        exist.

        The html page is built by inserting the html header at the beginning,
        appending the footer at the end, and applying the necessary
        transformations in the body.

        Finally, the html page produced by the compiler is overwritten.
        """
        path_hdoc = html_id_for(path_md)
        basename_md = os.path.basename(path_md)
        basename_hdoc = os.path.basename(path_hdoc)
        exists_hdoc = os.path.exists(path_hdoc)  # it should be true
        repo = self.srvbes.get_dict('repo')
        try:
            strict = repo['strict']
        except KeyError:
            strict = False

        if not exists_hdoc:
            self.log.error("[THEME] HTML_MISSING doc=%s", basename_md)
            self.log.error(f"[THEME] PATH doc={basename_md} path={path_md}")
            self.log.error(f"[THEME] PATH doc={basename_hdoc} path={path_hdoc}")
            return

        HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
        HTML_BODY = self.template('HTML_BODY')
        HTML_BODY_POST = self.template('POST_HTML_SINGLE')
        HTML_FOOTER = self.template('HTML_FOOTER')

        if len(var) == 0:
            var = self.get_theme_var()

        var['count_docs'] = self.srvdtb.get_documents_count()
        keys = self.srvdtb.get_all_keys()
        var['count_keys'] = len(keys)
        var['leader_items'] = []
        for key in keys:
            if key == 'Date':
                continue
            values = self.srvdtb.get_all_values_for_key(key)
            item = {}
            item['key'] = key
            item['vfkey'] = valid_filename(key)
            item['count_values'] = len(values)
            var['leader_items'].append(item)

        var['post'] = {}
        metadata = self.srvdtb.get_doc_properties(basename_md)
        for prop in metadata:
            var['post'][prop] = metadata[prop]
        if not self.srvdtb.is_system(basename_md):
            self.note_undated(basename_md, var['post'].get('Date'))
        var['topics'] = self.srvdtb.get_all_values_for_key('Topic')
        var['tags'] = self.srvdtb.get_all_values_for_key('Tag')
        now = datetime.now()
        timestamp = get_human_datetime(now)
        keys = self.srvdtb.get_doc_properties(basename_md)

        with open(path_md, 'r', encoding='utf-8') as fpa:
            source_md = fpa.read()

        with open(path_hdoc, 'r', encoding='utf-8') as fph:
            source_html = fph.read()

        var['toc'] = self.extract_toc(source_html)
        var['has_toc'] = True

        # Do not show metadata for system pages
        if self.srvdtb.is_system(basename_md):
            var['SystemPage'] = True
            TPL_HTML_HEADER_MENU_CONTENTS_DISABLED = self.template('HTML_HEADER_MENU_CONTENTS_DISABLED')
            HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_DISABLED.render()
            var['metadata'] = ""
        else:
            var['SystemPage'] = False
            TPL_HTML_HEADER_MENU_CONTENTS_ENABLED = self.template('HTML_HEADER_MENU_CONTENTS_ENABLED')
            HTML_TOC = TPL_HTML_HEADER_MENU_CONTENTS_ENABLED.render(var=var)
        var['metadata'] = self.build_metadata_section(basename_md)

        var['menu_contents'] = HTML_TOC
        try:
            var['keys'] = keys
            if 'Post' in keys['Category']:
                for key in keys:
                    var['post'][key] = keys[key]
                var['page']['title'] = var['post']['title']
        except Exception as error:
            var['keys'] = keys
        try:
            var['page']['title'] = ellipsize_text(keys['Title'])
            var['page']['title-tooltip'] = keys['Title']
        except Exception as error:
            # ~ self.log.error(error)
            pass
        var['basename_md'] = basename_md
        var['basename_hdoc'] = basename_hdoc
        var['source_md'] = source_md
        var['source_html'] = self.apply_transformations(source_html)
        actions = self.get_page_actions(var)
        var['actions'] = actions
        var['timestamp'] = timestamp

        HEADER = HTML_HEADER_COMMON.render(var=var)
        try:
            if self.srvdtb.is_system(basename_md):
                # Index, property and key pages are not posts. (They used to reach the plain
                # body only because the post template failed on their missing Date.)
                BODY = HTML_BODY.render(var=var)
            elif strict:
                if 'Post' in var['post']['Category']:
                    BODY = HTML_BODY_POST.render(var=var)
                else:
                    BODY = HTML_BODY.render(var=var)
            else:
                BODY = HTML_BODY_POST.render(var=var)
        except Exception:
            BODY = HTML_BODY.render(var=var)
        FOOTER = HTML_FOOTER.render(var=var)

        HTML = ""
        HTML += HEADER
        HTML += BODY
        HTML += FOOTER

        with open(path_hdoc, 'w', encoding='utf-8') as fhtml:
            fhtml.write(HTML)

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
        self.log.debug(f"[THEME] RELATED_FOUND doc={docId} n={len(doclist)}")

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

    def check_config(self):
        go = True
        repo = self.app.get_repo_config_dict()
        self.log.debug("[THEME] CONFIG_CHECK_START")

        self.log.info(f"[THEME] CONFIG key=title value='{repo['title']}'")
        if len(repo['title']) == 0:
            self.log.error("[THEME] CONFIG_FAIL key=title reason=empty")
            go = False

        self.log.info(f"[THEME] CONFIG key=datatable n={len(repo['datatable'])}")
        if len(repo['datatable']) == 0:
            self.log.error("[THEME] CONFIG_FAIL key=datatable reason=empty")
            go = False

        self.log.info(f"[THEME] CONFIG key=events n={len(repo['events'])}")
        if len(repo['events']) == 0:
            self.log.error("[THEME] CONFIG_FAIL key=events reason=empty")
            go = False

        self.log.info(f"[THEME] CONFIG key=git value={repo.get('git')}")
        if repo.get('git'):
            git_props = ['git_branch', 'git_path', 'git_repo', 'git_server', 'git_user']
            for git_prop in sorted(git_props):
                if len(repo[git_prop]) == 0:
                    self.log.warning(f"[THEME] CONFIG_FAIL key={git_prop} reason=empty")

        self.log.info(f"[THEME] CONFIG key=ignored_keys n={len(repo['ignored_keys'])}")
        if len(repo['ignored_keys']) == 0:
            self.log.warning("[THEME] CONFIG_WARN key=ignored_keys reason=empty")

        self.log.info(f"[THEME] CONFIG key=logo value={repo['logo']}")
        if not os.path.exists(repo['logo']):
            self.log.warning(f"[THEME] CONFIG_WARN key=logo reason=missing path={repo['logo']}")

        self.log.info(f"[THEME] CONFIG key=logo_alt value='{repo['logo_alt']}'")
        if not os.path.exists(repo['logo_alt']):
            self.log.warning("[THEME] CONFIG_WARN key=logo_alt reason=missing")

        self.log.info(f"[THEME] CONFIG key=menu n={len(repo['menu'])}")
        if len(repo['menu']) == 0:
            self.log.warning("[THEME] CONFIG_WARN key=menu reason=empty")

        self.log.info("[THEME] CONFIG key=sort value=Date")

        # Use the paths resolved against the repository root, not the raw repo.json values.
        for key in ('source', 'target'):
            path = self.srvbes.get_path(key) or ''
            self.log.info(f"[THEME] CONFIG key={key} value='{path}'")
            if len(path) == 0:
                self.log.error(f"[THEME] CONFIG_FAIL key={key} reason=empty")
                go = False
            elif not os.path.exists(path):
                self.log.error(f"[THEME] CONFIG_FAIL key={key} reason=missing path={path}")
                go = False

        self.log.info(f"[THEME] CONFIG key=webserver value={repo['webserver']}")
        if repo['webserver']:
            self.log.info(f"[THEME] CONFIG key=timeline n={len(repo['timeline'])}")
            if len(repo['timeline']) == 0:
                self.log.error("[THEME] CONFIG_FAIL key=timeline reason=empty")
                go = False

        if not go:
            example = os.path.join(ENV['GPATH']['THEMES'], 'techdoc', 'apps', 'default', 'config', 'repo.json')
            self.log.info(f"[THEME] CONFIG_EXAMPLE path={example}")

        self.log.debug("[THEME] CONFIG_CHECK_END")
        return go

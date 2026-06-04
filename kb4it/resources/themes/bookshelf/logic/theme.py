#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bookshelf theme.

# File: theme.py
# Author: Tomas Virseda
# License: GPL v3
# Description: A study companion theme that organizes a knowledge base as
#              Book > Part > Chapter for certification preparation.
"""

import math
import os
import re
from collections import Counter, OrderedDict
from datetime import datetime

from kb4it.core.util import (ellipsize_text, get_human_datetime,
                             guess_datetime, html_id_for, valid_filename)
from kb4it.services.builder import Builder


# Status -> study bucket. Anything not matched falls into 'todo'.
STATUS_DONE = {'done', 'published', 'completed', 'complete', 'closed', 'final'}
STATUS_READING = {'review', 'in progress', 'in-progress', 'inprogress',
                  'reading', 'wip', 'ongoing'}

# Book spine palettes, cycled by book order (see theme.css .s-* / .cover-*).
PALETTES = [
    ('s-red',   'linear-gradient(95deg,#cc0000,#a30000)'),
    ('s-slate', 'linear-gradient(95deg,#3c4655,#2a313c)'),
    ('s-olive', 'linear-gradient(95deg,#5b6133,#42471f)'),
    ('s-clay',  'linear-gradient(95deg,#8a4b2f,#693620)'),
]

ROMAN_MAP = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'd': 500, 'm': 1000}


def roman_to_int(value):
    """Convert a Roman numeral string to an int. Fall back to a plain int.

    Returns a large number for unparseable values so they sort last.
    """
    if value is None:
        return 9999
    raw = str(value).strip()
    if raw == '':
        return 9999
    digits = re.findall(r'\d+', raw)
    letters = re.sub(r'[^IVXLCDMivxlcdm]', '', raw)
    if letters:
        total = 0
        prev = 0
        for ch in reversed(letters.lower()):
            cur = ROMAN_MAP.get(ch, 0)
            if cur < prev:
                total -= cur
            else:
                total += cur
                prev = cur
        if total > 0:
            return total
    if digits:
        return int(digits[0])
    return 9999


def status_bucket(status):
    """Map a raw Status value to one of done / reading / todo."""
    s = (status or '').strip().lower()
    if s in STATUS_DONE:
        return 'done'
    if s in STATUS_READING:
        return 'reading'
    return 'todo'


class Theme(Builder):
    """Builder for the Bookshelf theme."""

    books = OrderedDict()
    doc_index = {}
    _context_ready = False

    def _initialize(self):
        super()._initialize()
        self.books = OrderedDict()
        self.doc_index = {}
        self._context_ready = False

    # ------------------------------------------------------------------ data
    def _first(self, docId, key, default=''):
        values = self.srvdtb.get_values(docId, key)
        if values and values[0]:
            return values[0]
        return default

    def _list(self, docId, key):
        return [v for v in self.srvdtb.get_values(docId, key) if v]

    def _ensure_context(self):
        """Build the Book > Part > Chapter model once, on first use.

        Key/value pages (the Book overview kanban) are generated in
        ``step_02_transformation`` (stage 3), which runs before
        ``theme.build()`` (stage 4). Building the context lazily makes the
        model available to whichever stage needs it first.
        """
        if not self._context_ready:
            self._build_book_context()
            self._context_ready = True

    def _build_book_context(self):
        """Compute the Book > Part > Chapter model from document properties."""
        chapters = []
        for docId in self.srvdtb.get_documents():
            if self.srvdtb.is_system(docId):
                continue
            book = self._first(docId, 'Book', 'Unfiled')
            part_raw = self._first(docId, 'Part', '')
            chapter_raw = self._first(docId, 'Chapter', '')
            try:
                chapter = int(re.findall(r'\d+', str(chapter_raw))[0])
            except (IndexError, ValueError):
                chapter = 9999
            status = self._first(docId, 'Status', '')
            info = {
                'docId': docId,
                'url': html_id_for(docId),
                'book': book,
                'part_raw': part_raw,
                'part_num': roman_to_int(part_raw),
                'part_title': self._first(docId, 'PartTitle', ''),
                'chapter': chapter,
                'cnum': '%02d' % chapter if chapter < 9999 else '--',
                'title': self._first(docId, 'Title', docId),
                'status': status or 'Draft',
                'bucket': status_bucket(status),
                'doctype': self._first(docId, 'DocType', ''),
                'author': self._first(docId, 'Author', ''),
                'date': self.srvdtb.get_doc_timestamp(docId) or '',
                'commands': self._list(docId, 'Command'),
                'tags': self._list(docId, 'Tag'),
            }
            chapters.append(info)
            self.doc_index[os.path.basename(docId)] = info

        by_book = OrderedDict()
        for info in chapters:
            by_book.setdefault(info['book'], []).append(info)

        self.books = OrderedDict()
        for idx, book_title in enumerate(sorted(by_book.keys(), key=lambda b: b.lower())):
            book_chapters = sorted(by_book[book_title], key=lambda c: (c['part_num'], c['chapter']))
            self._assemble_book(book_title, book_chapters, PALETTES[idx % len(PALETTES)])

        self._mark_reading_state()
        self._assign_spine_heights()
        self.log.debug(f"[BOOKSHELF] CONTEXT books={len(self.books)} chapters={len(chapters)}")

    def _assemble_book(self, book_title, book_chapters, palette):
        """Build one book record with its parts and per-part stats."""
        parts = OrderedDict()
        for info in book_chapters:
            pkey = info['part_num']
            if pkey not in parts:
                parts[pkey] = {
                    'num': pkey,
                    'roman': info['part_raw'] or str(pkey),
                    'title': info['part_title'],
                    'chapters': [],
                }
            parts[pkey]['chapters'].append(info)
            if not parts[pkey]['title'] and info['part_title']:
                parts[pkey]['title'] = info['part_title']

        for part in parts.values():
            total = len(part['chapters'])
            done = sum(1 for c in part['chapters'] if c['bucket'] == 'done')
            part['total'] = total
            part['done'] = done
            part['percent'] = round(done / total * 100) if total else 0

        total = len(book_chapters)
        done = sum(1 for c in book_chapters if c['bucket'] == 'done')
        authors = Counter(c['author'] for c in book_chapters if c['author'])
        code = ''
        m = re.search(r'EX[-\s]?\d+', book_title, re.IGNORECASE)
        if m:
            code = m.group(0).upper().replace(' ', '').replace('-', '')

        self.books[book_title] = {
            'title': book_title,
            'short': ellipsize_text(book_title, 34),
            'author': authors.most_common(1)[0][0] if authors else '',
            'code': code,
            'palette': palette[0],
            'gradient': palette[1],
            'parts': parts,
            'chapters': book_chapters,
            'total': total,
            'done': done,
            'percent': round(done / total * 100) if total else 0,
            'part_count': len(parts),
            'current': None,
            'url': 'Book_%s.html' % valid_filename(book_title),
            'height': 200,
        }

    def _mark_reading_state(self):
        """Pick the 'reading' chapter per book and the current chapter."""
        for book in self.books.values():
            chapters = book['chapters']
            explicit = [c for c in chapters if c['bucket'] == 'reading']
            current = None
            if explicit:
                current = min(explicit, key=lambda c: c['chapter'])
            else:
                pending = [c for c in chapters if c['bucket'] != 'done']
                if pending:
                    current = max(pending, key=lambda c: (self._sortable_date(c['date']), -c['chapter']))
                    current['bucket'] = 'reading'
            if current is None:
                current = chapters[-1] if chapters else None
            book['current'] = current
            for part in book['parts'].values():
                part['is_current'] = bool(current and part['num'] == current['part_num'])

    def _sortable_date(self, date):
        dt = guess_datetime(date) if date else None
        return dt or datetime.min

    def _assign_spine_heights(self):
        """Map each book length to a spine height between 160 and 214 px."""
        totals = [b['total'] for b in self.books.values()] or [0]
        lo, hi = min(totals), max(totals)
        for book in self.books.values():
            if hi == lo:
                book['height'] = 200
            else:
                book['height'] = round(160 + (book['total'] - lo) / (hi - lo) * 54)

    # ----------------------------------------------------------- nav helpers
    def _reading_context(self, basename_md):
        """Build the left-nav, prev/next and rail data for a chapter page."""
        info = self.doc_index.get(basename_md)
        if not info:
            return None
        book = self.books.get(info['book'])
        if not book:
            return None

        ordered = book['chapters']
        idx = next((i for i, c in enumerate(ordered) if c['docId'] == info['docId']), None)
        prev_info = ordered[idx - 1] if idx not in (None, 0) else None
        next_info = ordered[idx + 1] if idx is not None and idx < len(ordered) - 1 else None

        part = book['parts'].get(info['part_num'], {})
        siblings = []
        for c in part.get('chapters', []):
            siblings.append({
                'cnum': c['cnum'],
                'title': c['title'],
                'url': c['url'],
                'bucket': c['bucket'],
                'is_current': c['docId'] == info['docId'],
            })

        part_label = 'Part %s' % info['part_raw'] if info['part_raw'] else 'Chapters'
        return {
            'info': info,
            'book': book,
            'part_label': part_label,
            'part_title': part.get('title', ''),
            'siblings': siblings,
            'prev': prev_info,
            'next': next_info,
            'commands': info['commands'],
            'tags': info['tags'],
        }

    # ------------------------------------------------------------- theme var
    def get_theme_var(self):
        self._ensure_context()
        var = super().get_theme_var()
        var['bk'] = self._library_summary()
        return var

    def _library_summary(self):
        books = []
        total_parts = total_chapters = chapters_read = 0
        command_values = set()
        for book in self.books.values():
            total_parts += book['part_count']
            total_chapters += book['total']
            chapters_read += book['done']
            for c in book['chapters']:
                command_values.update(c['commands'])
            current = book['current']
            books.append({
                'title': book['title'],
                'short': book['short'],
                'author': book['author'],
                'code': book['code'],
                'palette': book['palette'],
                'gradient': book['gradient'],
                'percent': book['percent'],
                'done': book['done'],
                'total': book['total'],
                'part_count': book['part_count'],
                'height': book['height'],
                'url': book['url'],
                'current_part': ('Part %s' % current['part_raw']) if current and current['part_raw'] else 'Not started',
                'current_bucket': current['bucket'] if current else 'todo',
                'started': book['done'] > 0 or bool(current and current['bucket'] == 'reading'),
            })
        return {
            'books': books,
            'current_book': self._current_book(),
            'stats': {
                'books': len(books),
                'parts': total_parts,
                'chapters': total_chapters,
                'read': chapters_read,
                'commands': len(command_values),
            },
        }

    def _current_book(self):
        """The book whose current chapter is being read (for the top switch)."""
        best = None
        for book in self.books.values():
            current = book['current']
            if current is None:
                continue
            dt = self._sortable_date(current['date'])
            if best is None or dt > best[0]:
                best = (dt, book, current)
        if best is None:
            return None
        _, book, current = best
        return {
            'title': book['title'],
            'short': book['short'],
            'url': book['url'],
            'gradient': book['gradient'],
            'bucket': current['bucket'],
            'chapter': current['chapter'],
            'cnum': current['cnum'],
            'chapter_title': current['title'],
            'chapter_url': current['url'],
            'part_label': ('Part %s' % current['part_raw']) if current['part_raw'] else '',
            'part_title': book['parts'].get(current['part_num'], {}).get('title', ''),
        }

    # ---------------------------------------------------------------- build
    def build(self):
        self._ensure_context()
        var = self.get_theme_var()
        self.build_page_properties()
        self.build_page_stats()
        self.build_page_bookmarks()
        self.build_page_all()
        self.build_page_index(var)
        self.create_page_about_kb4it()
        self.create_page_help()

    def build_page_index(self, var):
        runtime = self.srvbes.get_dict('runtime')
        if 'index.md' in runtime['docs']['filenames']:
            self.log.info("[BOOKSHELF] INDEX_SKIP reason=user_generated")
            return
        var['page']['title'] = var['repo']['title']
        page = self.template('PAGE_INDEX').render(var=var)
        self.distribute_md('index', page)
        self.srvdtb.add_document('index.md')
        self.srvdtb.add_document_key('index.md', 'Title', var['repo']['title'])
        self.srvdtb.add_document_key('index.md', 'SystemPage', 'Yes')

    def build_page_key_value(self, kvpath):
        self._ensure_context()
        key, value, COMPILE_VALUE = kvpath
        pagename = "%s_%s" % (valid_filename(key), valid_filename(value))

        # The Book overview is a specialized kanban rendering of Book_<value>.
        if key == 'Book' and value in self.books and COMPILE_VALUE:
            var = self.get_theme_var()
            var['has_toc'] = False
            var['page']['title'] = value
            var['book'] = self._book_view(value)
            adoc = self.template('PAGE_BOOK').render(var=var)
            self.distribute_md(pagename, adoc)
            self.srvdtb.add_document(f"{pagename}.md")
            self.srvdtb.add_document_key(f"{pagename}.md", 'Title', value)
            self.srvdtb.add_document_key(f"{pagename}.md", 'SystemPage', 'Yes')
            return

        # Default: a plain key/value listing.
        docs = self.srvbes.get_kbdict_value(key, value, new=True)
        sorted_docs = self.srvdtb.sort_by_date(docs)
        var = self.get_theme_var()
        var['key'] = key
        var['value'] = value
        var['vfkey'] = valid_filename(key)
        var['title'] = f'{key}: {value}'
        var['pagename'] = pagename
        var['doclist'] = sorted_docs
        var['compile'] = COMPILE_VALUE
        var['has_toc'] = False
        var['page']['dt_documents'] = self.build_datatable([], sorted_docs)
        if var['compile']:
            adoc = self.template('PAGE_KEY_VALUE').render(var=var)
            self.distribute_md(pagename, adoc)
            self.srvdtb.add_document(f"{pagename}.md")
            self.srvdtb.add_document_key(f"{pagename}.md", 'Title', var['title'])
            self.srvdtb.add_document_key(f"{pagename}.md", 'SystemPage', 'Yes')

    def _book_view(self, book_title):
        """Shape a single book for the kanban (Book overview) template."""
        book = self.books[book_title]
        current = book['current']
        columns = []
        for pkey in sorted(book['parts'].keys()):
            part = book['parts'][pkey]
            cards = []
            for c in part['chapters']:
                cards.append({
                    'cnum': c['cnum'],
                    'title': c['title'],
                    'url': c['url'],
                    'bucket': c['bucket'],
                    'is_current': bool(current and c['docId'] == current['docId']),
                })
            columns.append({
                'roman': part['roman'],
                'title': part['title'],
                'is_current': part.get('is_current', False),
                'done': part['done'],
                'total': part['total'],
                'percent': part['percent'],
                'cards': cards,
            })
        return {
            'title': book['title'],
            'author': book['author'],
            'code': book['code'],
            'gradient': book['gradient'],
            'part_count': book['part_count'],
            'total': book['total'],
            'done': book['done'],
            'percent': book['percent'],
            'columns': columns,
        }

    # ------------------------------------------------------------ doc pages
    def build_page(self, path_md):
        path_hdoc = html_id_for(path_md)
        basename_md = os.path.basename(path_md)
        basename_hdoc = os.path.basename(path_hdoc)
        if not os.path.exists(path_hdoc):
            self.log.error(f"[BOOKSHELF] HTML_MISSING doc={basename_md}")
            return

        HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
        HTML_BODY = self.template('HTML_BODY')
        HTML_FOOTER = self.template('HTML_FOOTER')
        var = self.get_theme_var()
        var['timestamp'] = get_human_datetime(datetime.now())
        var['keys'] = self.srvdtb.get_doc_properties(basename_md)

        with open(path_md, 'r') as fpa:
            source_md = fpa.read()
        with open(path_hdoc, 'r') as fph:
            source_html = fph.read()

        var['toc'] = self.extract_toc(source_html)
        var['has_toc'] = len(var['toc']) > 0
        var['read_min'] = max(1, round(len(source_md.split()) / 200))

        if self.srvdtb.is_system(basename_md):
            var['SystemPage'] = True
            var['metadata'] = ''
            var['reading'] = None
        else:
            var['SystemPage'] = False
            var['metadata'] = self.build_metadata_section(basename_md)
            var['reading'] = self._reading_context(basename_md)

        var['page']['title'] = 'Untitled'
        try:
            var['page']['title'] = ellipsize_text(var['keys']['Title'])
        except Exception:
            pass
        var['basename_md'] = basename_md
        var['basename_hdoc'] = basename_hdoc
        var['source_md'] = source_md
        var['source_html'] = self.apply_transformations(source_html)
        var['actions'] = self.get_page_actions(var)

        HTML = (HTML_HEADER_COMMON.render(var=var)
                + HTML_BODY.render(var=var)
                + HTML_FOOTER.render(var=var))
        with open(path_hdoc, 'w', encoding='utf-8') as fhtml:
            fhtml.write(HTML)

    def build_page_key(self, key, values):
        TPL_PAGE_KEY = self.template('PAGE_KEY')
        var = self.get_theme_var()
        var['title'] = key
        var['cloud'] = self.build_tagcloud_from_key(key)
        var['leader'] = []
        for value in values:
            docs = self.srvdtb.get_docs_by_key_value(key, value)
            var['leader'].append({
                'count': len(docs),
                'vfkey': valid_filename(key),
                'vfvalue': valid_filename(value),
                'name': value,
            })
        adoc = TPL_PAGE_KEY.render(var=var)
        pagename = valid_filename(key)
        self.distribute_md(pagename, adoc)
        self.srvdtb.add_document(f"{pagename}.md")
        self.srvdtb.add_document_key(f"{pagename}.md", 'Title', key)
        self.srvdtb.add_document_key(f"{pagename}.md", 'SystemPage', 'Yes')

    def build_page_all(self):
        TPL_PAGE_ALL = self.template('PAGE_ALL')
        var = self.get_theme_var()
        var['content'] = self.build_datatable([], list(self.srvdtb.get_documents()))
        self.distribute_md('all', TPL_PAGE_ALL.render(var=var))
        self.srvdtb.add_document('all.md')
        self.srvdtb.add_document_key('all.md', 'Title', 'All documents')
        self.srvdtb.add_document_key('all.md', 'SystemPage', 'Yes')

    def build_page_properties(self):
        TPL_PROPS_PAGE = self.template('PAGE_PROPERTIES')
        TPL_KEY_MODAL_BUTTON = self.template('KEY_MODAL_BUTTON')
        max_frequency = self.get_maxkv_freq()
        var = self.get_theme_var()
        var['buttons'] = []
        log_max = math.log(1 + max_frequency) if max_frequency > 0 else 1
        for key in self.srvdtb.get_all_keys():
            if key in self.srvdtb.get_ignored_keys():
                continue
            values = self.srvdtb.get_all_values_for_key(key)
            frequency = len(values)
            weight = math.log(1 + frequency) / log_max if log_max else 0.0
            var['buttons'].append(TPL_KEY_MODAL_BUTTON.render(var={
                'content': self.build_tagcloud_from_key(key),
                'key': key,
                'vfkey': valid_filename(key),
                'count': frequency,
                'weight': round(weight, 3),
                'tooltip': f"{frequency} values",
            }))
        self.distribute_md('properties', TPL_PROPS_PAGE.render(var=var))
        self.srvdtb.add_document('properties.md')
        self.srvdtb.add_document_key('properties.md', 'Title', 'Properties')
        self.srvdtb.add_document_key('properties.md', 'SystemPage', 'Yes')

    def build_tagcloud_from_key(self, key):
        dkeyurl = {}
        for docId in self.srvdtb.get_documents():
            url = os.path.basename(docId)[:-5]
            for tag in self.srvdtb.get_values(docId, key):
                if tag:
                    dkeyurl.setdefault(tag, set()).add(url)
        max_frequency = max((len(v) for v in dkeyurl.values()), default=1)
        lwords = sorted((w for w in dkeyurl if len(w) > 0), key=lambda y: y.lower())
        if not lwords:
            return ''
        TPL_WORDCLOUD = self.template('WORDCLOUD')
        var = self.get_theme_var()
        var['items'] = []
        log_max = math.log(1 + max_frequency) if max_frequency > 0 else 1
        for word in lwords:
            freq = len(dkeyurl[word])
            weight = math.log(1 + freq) / log_max if log_max else 0.0
            var['items'].append({
                'url': f"{valid_filename(key)}_{valid_filename(word)}.html",
                'tooltip': f"{freq} documents",
                'word': word,
                'count': freq,
                'weight': round(weight, 3),
            })
        return TPL_WORDCLOUD.render(var=var)

    def get_maxkv_freq(self):
        maxkvfreq = 0
        for key in self.srvdtb.get_theme_keys():
            values = self.srvdtb.get_all_values_for_key(key)
            if len(values) > maxkvfreq:
                maxkvfreq = len(values)
        return maxkvfreq

    def build_page_stats(self):
        TPL_PAGE_STATS = self.template('PAGE_STATS')
        var = self.get_theme_var()
        var['count_docs'] = self.srvdtb.get_documents_count()
        keys = self.srvdtb.get_theme_keys()
        var['count_keys'] = len(keys)
        var['leader_items'] = []
        for key in keys:
            values = self.srvdtb.get_all_values_for_key(key)
            var['leader_items'].append({
                'key': key,
                'vfkey': valid_filename(key),
                'count_values': len(values),
            })
        self.distribute_md('stats', TPL_PAGE_STATS.render(var=var))
        self.srvdtb.add_document('stats.md')
        self.srvdtb.add_document_key('stats.md', 'Title', 'Stats')
        self.srvdtb.add_document_key('stats.md', 'SystemPage', 'Yes')

    def build_page_bookmarks(self):
        TPL_PAGE_BOOKMARKS = self.template('PAGE_BOOKMARKS')
        var = self.get_theme_var()
        doclist = []
        for docId in self.srvdtb.get_documents():
            bm = self.srvdtb.get_values(docId, 'Bookmark')
            if bm and bm[0] in ('Yes', 'True'):
                doclist.append(docId)
        var['page']['title'] = 'Bookmarks'
        var['page']['dt_bookmarks'] = self.build_datatable([], doclist)
        self.distribute_md('bookmarks', TPL_PAGE_BOOKMARKS.render(var=var))
        self.srvdtb.add_document('bookmarks.md')
        self.srvdtb.add_document_key('bookmarks.md', 'Title', 'Bookmarks')
        self.srvdtb.add_document_key('bookmarks.md', 'SystemPage', 'Yes')

    # --------------------------------------------------------------- shared
    def extract_toc(self, source):
        toc = ''
        items = []
        lines = source.split('\n')
        s = e = n = 0
        var = self.get_theme_var()
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

    def get_page_actions(self, var):
        return self.template('SECTION_ACTIONS').render(var=var)

    def build_datatable(self, headers=None, doclist=None):
        if headers is None:
            headers = []
        if doclist is None:
            doclist = []
        TPL_LINK = self.template('LINK')
        TPL_DATATABLE = self.template('DATATABLE')
        TPL_DATATABLE_HEADER_ITEM = self.template('DATATABLE_HEADER_ITEM')
        repo = self.srvbes.get_dict('repo')
        sort_attribute = 'Date'
        if len(headers) == 0:
            headers = repo.get('datatable', ['Date', 'Title', 'Chapter'])

        datatable = {'header': '', 'rows': ''}
        for item in headers:
            datatable['header'] += TPL_DATATABLE_HEADER_ITEM.render(var={'item': item})

        documents = {docId: self.srvdtb.get_doc_properties(docId) for docId in doclist}
        for docId in documents:
            if self.srvdtb.is_system(docId):
                continue
            datatable['rows'] += '<tr>'
            if sort_attribute in headers:
                timestamp = self.srvdtb.get_doc_timestamp(docId)
                if timestamp is None:
                    continue
                datatable['rows'] += f'<td class="bk-td-date">{timestamp[:16]}</td>'
                final_headers = headers[1:]
            else:
                final_headers = headers
            for key in final_headers:
                if key == 'Title':
                    try:
                        title = documents[docId][key]
                        url = documents[docId].get(f'{key}_Url', html_id_for(docId))
                        datatable['rows'] += f'<td class="bk-td-title"><a href="{url}">{ellipsize_text(title, 80)}</a></td>'
                    except (KeyError, AttributeError):
                        datatable['rows'] += '<td></td>'
                else:
                    field = []
                    try:
                        for value in documents[docId][key]:
                            field.append(TPL_LINK.render(var={
                                'class': 'bk-link',
                                'title': value,
                                'url': documents[docId].get(f'{key}_{value}_Url', '#'),
                            }))
                    except KeyError:
                        field = []
                    datatable['rows'] += f'<td class="">{", ".join(field)}</td>'
            datatable['rows'] += '</tr>'
        return TPL_DATATABLE.render(var=datatable)

    def get_labels(self, values):
        label_links = ''
        TPL_METADATA_VALUE_LINK = self.template('METADATA_VALUE_LINK')
        for page, text in values:
            if text:
                label_links += TPL_METADATA_VALUE_LINK.render(var={
                    'link_url': valid_filename(page), 'link_name': text})
        return label_links

    def get_html_values_from_key(self, docId, key):
        return [(f"{key}_{value}.html", value) for value in self.srvdtb.get_values(docId, key)]

    def build_metadata_section(self, docId):
        try:
            TPL_METADATA_SECTION = self.template('METADATA_SECTION')
            custom_keys = self.srvdtb.get_custom_keys(os.path.basename(docId))
            var = {'items': []}
            for key in custom_keys:
                values = self.get_html_values_from_key(docId, key)
                var['items'].append({
                    'doc': docId,
                    'key': key,
                    'vfkey': valid_filename(key),
                    'labels': self.get_labels(values),
                })
            html = TPL_METADATA_SECTION.render(var=var)
        except Exception as error:
            self.log.error(f"[BOOKSHELF] METADATA_FAIL doc={docId} error={error}")
            html = ''
        return html

    def generate_sources(self):
        pass

    def post_activities(self):
        self.log.debug("[BOOKSHELF] POST_END")

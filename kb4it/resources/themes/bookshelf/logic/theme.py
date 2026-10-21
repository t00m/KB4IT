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

import os
import re
from collections import Counter, OrderedDict
from datetime import datetime
from html import escape

from kb4it.core.util import (ellipsize_text, get_human_datetime,
                             guess_datetime, html_id_for, valid_filename)
from kb4it.services.themekit import DocumentTheme


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


class Theme(DocumentTheme):
    """Builder for the Bookshelf theme."""

    tagcloud_scale_skips_empty = True
    reserved_pages = ('404.md',)  # build() writes 404.html
    datatable_link_template = 'LINK'
    datatable_default_headers = ('Date', 'Title', 'Chapter')

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
        self.build_page_404()
        self.build_page_index_all()
        self.build_page_index(var)
        self.create_page_about_kb4it()
        self.create_page_about_app()
        self.create_page_help()
        self.create_page_search()

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
        """Override: the page of a Book value is the book overview (PAGE_BOOK), not a document list."""
        self._ensure_context()
        key, value, COMPILE_VALUE = kvpath
        pagename = "%s_%s" % (valid_filename(key), valid_filename(value))

        # The Book overview is a specialized kanban rendering of Book_<value>.
        if key == 'Book' and value in self.books and COMPILE_VALUE:
            var = self.get_theme_var()
            var['has_toc'] = False
            var['page']['title'] = value
            var['book'] = self._book_view(value)
            content = self.template('PAGE_BOOK').render(var=var)
            self.distribute_md(pagename, content)
            self.srvdtb.add_document(f"{pagename}.md")
            self.srvdtb.add_document_key(f"{pagename}.md", 'Title', value)
            self.srvdtb.add_document_key(f"{pagename}.md", 'SystemPage', 'Yes')
            return
        super().build_page_key_value(kvpath)

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

        with open(path_md, 'r', encoding='utf-8') as fpa:
            source_md = fpa.read()
        with open(path_hdoc, 'r', encoding='utf-8') as fph:
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

    # --------------------------------------------------------------- shared
    def datatable_date_cell(self, timestamp):
        """Bookshelf's date cell: the date only, no link."""
        if timestamp is None:
            return '<td class="bk-td-date"></td>'
        return f'<td class="bk-td-date">{escape(timestamp[:16])}</td>'

    def datatable_title_cell(self, docId, properties):
        """Bookshelf's title cell: a plain link, empty when the document has no title."""
        try:
            title = properties['Title']
            url = properties.get('Title_Url', html_id_for(docId))
            # Built as HTML here and printed raw: escape what comes from the document.
            return f'<td class="bk-td-title"><a href="{escape(url)}">{escape(ellipsize_text(title, 80))}</a></td>'
        except (KeyError, AttributeError):
            return '<td></td>'

    def datatable_value_link(self, properties, key, value):
        """Bookshelf's value link: its own class, and "#" when the value has no page."""
        return {'class': 'bk-link', 'title': value, 'url': properties.get(f'{key}_{value}_Url', '#')}

    def build_metadata_section(self, docId):
        """Override: a study page is still built when its metadata fails; the section is left empty."""
        try:
            return super().build_metadata_section(docId)
        except Exception as error:
            self.log.error(f"[BOOKSHELF] METADATA_FAIL doc={docId} error={error}")
            return ''

    def post_activities(self):
        self.log.debug("[BOOKSHELF] POST_END")

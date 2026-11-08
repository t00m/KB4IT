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

import re
from collections import Counter, OrderedDict
from datetime import datetime
from html import escape

from kb4it.core.structured import DEFAULT_MAP
from kb4it.core.util import ellipsize_text, guess_datetime
from kb4it.theme import BaseTheme, page_name, q


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

# Chapters without a Book property go to this shelf. It has no Book page of
# its own, so it links to the list of all chapters.
UNFILED = 'Unfiled'

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


class Theme(BaseTheme):
    """The Bookshelf theme."""

    features = ("documents", "stats", "bookmarks", "navigation", "search", "about", "editor")
    tagcloud_scale_skips_empty = True
    datatable_link_template = 'LINK'
    datatable_default_headers = ('Date', 'Title', 'Chapter')

    log_area = 'BOOKSHELF'
    untitled_label = 'Untitled'

    def setup(self):
        self.books = OrderedDict()
        self.doc_index = {}
        self._filed = set()

    # ------------------------------------------------------------------ data
    def structured_defaults(self):
        """A note is a Chapter of its Book; Status is reading progress, not the state of the text."""
        return {'type': 'Chapter', 'map': {**DEFAULT_MAP, 'Book': 'isPartOf:Book', 'Chapter': 'position',
                                          'Command': 'mentions:DefinedTerm', 'Status': None}}

    def prepare(self, site):
        """Compute the Book > Part > Chapter model before any page is built: the Book pages need it."""
        chapters = []
        self._filed = set()
        people = site.people
        for doc in site.documents:
            book = doc.value('Book')
            if book:
                self._filed.add(book)
            else:
                book = UNFILED
            part_raw = doc.value('Part')
            chapter_raw = doc.value('Chapter')
            try:
                chapter = int(re.findall(r'\d+', str(chapter_raw))[0])
            except (IndexError, ValueError):
                chapter = 9999
            status = doc.value('Status')
            author = doc.value('Author')
            info = {
                'docId': doc.id,
                'url': doc.url,
                'book': book,
                'part_raw': part_raw,
                'part_num': roman_to_int(part_raw),
                'part_title': doc.value('PartTitle'),
                'chapter': chapter,
                'cnum': '%02d' % chapter if chapter < 9999 else '--',
                'title': doc.value('Title', doc.id),
                'status': status or 'Draft',
                'bucket': status_bucket(status),
                'doctype': doc.value('DocType'),
                'author': author,
                'author_tip': people.tip(author) if 'Author' in people.keys and author else '',
                'date': doc.date or '',
                'commands': list(doc.values('Command')),
                'tags': list(doc.values('Tag')),
            }
            chapters.append(info)
            self.doc_index[doc.id] = info

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
            'url': self._book_url(book_title),
            'height': 200,
        }

    def _book_url(self, book_title):
        """The Book page of a book, or the list of all chapters for the unfiled shelf."""
        if book_title in self._filed:
            return page_name('Book', book_title)
        return 'all.html'

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
    def ordered_pages(self, doc):
        """The chapters of the book doc belongs to, in reading order."""
        info = self.doc_index.get(doc.id)
        book = self.books.get(info['book']) if info else None
        return [c['docId'] for c in book['chapters']] if book else []

    def _reading_context(self, doc):
        """Build the left-nav, prev/next and rail data for a chapter page."""
        info = self.doc_index.get(doc.id)
        if not info:
            return None
        book = self.books.get(info['book'])
        if not book:
            return None

        prev_doc, next_doc = self.site.features.navigation.neighbours(doc)
        prev_info = self.doc_index.get(prev_doc.id) if prev_doc else None
        next_info = self.doc_index.get(next_doc.id) if next_doc else None

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
    def base_var(self):
        """Every page gets the shelf: var['bk']."""
        var = super().base_var()
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
    def build(self, site):
        """The home page: the shelf, unless the site has its own index.md."""
        if 'index.md' in site.documents:
            self.log.info("[BOOKSHELF] INDEX_SKIP reason=user_generated")
            return
        var = self.base_var()
        var['page']['title'] = var['repo']['title']
        site.page('index', var['repo']['title'], self.template('PAGE_INDEX').render(var=var))

    def value_page(self, key, value, docs):
        """The page of a Book value is the book overview (PAGE_BOOK), not a document list."""
        if key != 'Book' or value not in self.books:
            self.site.features.property_pages.value_page(key, value, docs)
            return
        var = self.base_var()
        var['has_toc'] = False
        var['page']['title'] = value
        var['book'] = self._book_view(value)
        self.site.page(page_name(key, value), value, self.template('PAGE_BOOK').render(var=var), listing=True)

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
    def page_context(self, doc, var):
        """Reading time, and the metadata and reading position of a chapter."""
        var['has_toc'] = len(var['toc']) > 0
        var['read_min'] = max(1, round(len(var['source_md'].split()) / 200))
        if var['SystemPage']:
            var['metadata'] = ''
            var['reading'] = None
        else:
            var['metadata'] = self.site.features.metadata.section(doc)
            var['reading'] = self._reading_context(doc)
        return var

    # --------------------------------------------------------------- shared
    def datatable_date_cell(self, doc):
        """Bookshelf's date cell: the date only, no link."""
        if doc.date is None:
            return '<td class="bk-td-date"></td>'
        return f'<td class="bk-td-date">{escape(doc.date[:16])}</td>'

    def datatable_title_cell(self, doc):
        """Bookshelf's title cell: a plain link, empty when the document has no title."""
        if 'Title' not in doc.properties:
            return '<td></td>'
        # Built as HTML here and printed raw: escape what comes from the document.
        return f'<td class="bk-td-title"><a href="{escape(doc.url)}">{escape(ellipsize_text(doc.title, 80))}</a></td>'

    def datatable_value_link(self, doc, key, value):
        """Bookshelf's value link: its own class."""
        return {'class': 'bk-link', 'title': value, 'url': page_name(key, value)}

    def build_metadata_section(self, doc):
        """A study page is still built when its metadata fails; the section is left empty."""
        try:
            return self.site.features.metadata.build_metadata_section(doc)
        except Exception as error:
            self.log.error(f"[BOOKSHELF] METADATA_FAIL doc={q(doc.id)} error={q(error)}", exc_info=True)
            return ''

    def after_build(self, site):
        self.log.debug("[BOOKSHELF] POST_END")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
techdoc: the default theme, for technical documentation.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: features, the hooks techdoc fills, its home and events pages and its document pages
"""

import os

from lxml import etree

from kb4it.core.util import source_ext
from kb4it.theme import BaseTheme, Table, q
from kb4it.theme.html import enhance_blocks, enhance_images

from .admin import Admin
from .config import TechdocConfig
from .dashboard import Dashboard, priority_css, status_css
from .docpage import banners, header_strip, info_groups, summary
from .quality import TIER_LABELS
from .qualityfeature import Quality
from .records import event_type

EVENTS_TABLE = 'kb4it-events-table'


class Theme(BaseTheme):
    # Quality and Admin are techdoc's own features (logic/qualityfeature.py, logic/admin.py).
    features = ("documents", "events", "stats", "bookmarks", "table_filter", "related", "toc_sidebar", "gallery",
                "diagrams", "search", "about", "editor", Quality, Admin)
    properties_cloud = False  # properties.html is a table of the properties
    datatable_hidden = ('Scope',)  # never a column, even when repo.json lists it
    untitled_label = 'No title found...'
    ellipsize_titles = False  # the top bar cuts the title with CSS
    config_class = TechdocConfig  # header_keys, info_groups, info_tabs, toc_sidebar, table_filter, quality

    # ---------------------------------------------------------------- tables
    def datatable_columns(self, columns, docs):
        """Document tables leave out the hidden columns and those empty in every row; Date and Title always stay."""
        columns = [key for key in columns if key not in self.datatable_hidden]
        if docs:
            quality = bool(self.site.features.quality.scores)
            columns = [key for key in columns if key in ('Date', 'Title') or (key == 'Quality' and quality)
                       or any(doc.values(key) for doc in docs)]
        return columns

    def datatable_custom_cell(self, doc, key):
        """The Quality column: a five-square meter with the tier as its tooltip, sorted by score; retired documents last.

        The tier is not printed, but data-search keeps it findable with the table's search box. A retired
        document has no meaningful score, so it shows the word "Retired" instead of a meter.
        """
        assessment = self.site.features.quality.scores.get(doc.id) if key == 'Quality' else None
        if assessment is None:
            return None
        tier = assessment.tier
        if tier == 'retired':
            return '<td data-order="-1"><span class="kb-q-chip kb-q-retired">Retired</span></td>'
        on = 5 if tier == 'exemplary' else min(5, assessment.score // 20)
        squares = '<i class="on"></i>' * on + '<i></i>' * (5 - on)
        label = f'{TIER_LABELS[tier]}, score {assessment.score}'
        return (f'<td data-order="{assessment.score}" data-search="{TIER_LABELS[tier]}">'
                f'<span class="kb-q-meter kb-q-{tier}" role="img" aria-label="{label}" title="{label}" data-uk-tooltip>'
                f'{squares}</span></td>')

    def datatable_date_cell(self, doc):
        """The date cell gets a class, so the date stays on one line and the time wraps below it."""
        cell = self.site.features.table.datatable_date_cell(doc)
        return cell.replace('<td class="uk-text-left">', '<td class="uk-text-left kb-dt-date">', 1)

    def datatable_value_link(self, doc, key, value):
        """Priority and Status values show as colored labels."""
        link = self.site.features.table.datatable_value_link(doc, key, value)
        if key == 'Priority' and value:
            link['class'] = 'uk-label kb-badge kb-dt-label %s' % priority_css(value)
        elif key == 'Status' and value:
            link['class'] = 'uk-label kb-badge kb-dt-label %s' % status_css(value)
        return link

    # ---------------------------------------------------------------- events
    def event_documents(self):
        """The documents whose type of work (else first Category) is listed in repo.json "events"."""
        event_types = self.site.repo.get('events', [])
        db = self.internals.db
        return [doc for doc in self.site.documents if event_type(db, doc.id) in event_types]

    def build_page_events(self, site):
        """events.html: a calendar panel beside one table of every event, which the calendar and the filter bar filter."""
        events = site.features.events
        backend, builder = self.internals.backend, self.internals.builder
        before = backend.get_events_before()
        # A day page that disappeared rebuilds no year page, but the table here must lose its link.
        pages_changed = before is None or set(before) != set(backend.get_kb_dict().get('events') or {})
        cached = os.path.join(backend.get_path('cache'), 'events.html')
        if events.built_years or pages_changed or not os.path.exists(cached):
            days = events.days()
            docs = sorted(days, key=days.get, reverse=True)
            datatable = site.table(Table(documents=tuple(docs), id=EVENTS_TABLE, filterable=True, dates=days))
            var = {'table_id': EVENTS_TABLE, 'datatable': datatable, 'data': events.calendar(days)}
            site.page('events', 'Events', self.template('PAGE_EVENTS').render(var=var))
        else:
            # Unchanged: the cached page goes into this build as it is.
            builder.distribute_html('events', cached)
            builder.add_system_page('events', 'Events')

    # ----------------------------------------------------------------- build
    def build(self, site):
        """The theme's own pages: events.html and the home page; the features wrote the others."""
        var = self.base_var()
        self.build_page_events(site)
        Dashboard(self, site).build_page_index(var)

    def search_record(self, doc):
        """The shared search carries the quality tier, so readers can pick the better page."""
        record = self.site.features.search.search_record(doc)
        assessment = self.site.features.quality.scores.get(doc.id)
        if assessment is not None:
            record['q'] = {
                'score': assessment.score,
                'tier': assessment.tier,
                'label': TIER_LABELS.get(assessment.tier, assessment.tier.title()),
            }
        return record

    def backlinks_html(self, doc):
        """techdoc shows the documents that link here in the Related tab of the info card, not after the body."""
        return ''

    def related_candidates(self):
        """Retired documents are never suggested as related."""
        scores = self.site.features.quality.scores
        return [doc for doc in self.site.features.related.related_candidates()
                if scores.get(doc) is None or scores[doc].tier != 'retired']

    def related_view(self, doc):
        """Linked from and related documents for the Related tab, each with the tier of its target."""
        tiers = (self.site.features.quality.stats or {}).get('docs', {})

        def chip(page):
            tier = tiers.get(page, {}).get('tier')
            return {'tier': tier, 'label': TIER_LABELS[tier]} if tier else None

        backlinks = doc.backlinks if self.site.repo.get('backlinks', True) is not False else []
        linked = [{'title': item['title'], 'href': item['url'], 'chip': chip(item['url'])} for item in backlinks]
        similar = []
        for item in self.site.features.related.related(doc):
            other = self.site.doc(item['doc'])
            similar.append({'title': other.value('Title', other.id), 'href': other.url,
                            'shared': ', '.join(item['shared']), 'chip': chip(other.url)})
        return {'linked': linked, 'similar': similar} if linked or similar else None

    # ------------------------------------------------------------ doc pages
    def page_context(self, doc, var):
        """The header menu, and for a document its header, info card, quality and TOC sidebar."""
        site = self.site
        var['toc_sidebar'] = False
        var['menu_contents'] = site.features.toc.menu_contents(var)
        var['fmt'] = source_ext(doc.id) or "md"
        if var['SystemPage']:
            var['metadata'] = ""
            return var
        db = self.internals.db
        day_page = site.features.events.has_day_page(doc)
        var['toc_sidebar'] = site.features.toc_sidebar.wanted(var['source_html'])
        doc_summary = summary(db, doc.id)
        quality_doc = site.features.quality.view(doc.id)
        var['has_quality'] = quality_doc is not None
        var['page']['exemplary'] = bool(quality_doc) and quality_doc['tier'] == 'exemplary'
        var['doc_header'] = self.template('DOC_HEADER').render(var={
            'quality': quality_doc,
            'strip': header_strip(db, doc.id, self.config.header_keys, day_page),
            'summary': doc_summary,
            'banners': banners(db, doc.id),
        })
        info_tabs = self.config.info_tabs
        people = site.people
        var['info_card'] = self.template('INFO_CARD').render(var={'card': {
            'open': not doc_summary,
            'groups': info_groups(db, doc.id, self.config.info_groups, var['source_md'],
                                  lambda key, value: people.tip(value) if key in people.keys else '', day_page),
            'history': {
                'date': (db.get_values(doc.id, 'Date') or [''])[0],
                'source': doc.id,
                'built': var['timestamp'],
                'edit_url': var['edit_url'],
                'editor': bool(var.get('editor')),
            },
            'print': {name: info_tabs.get(name, {}).get('print', name == 'details')
                      for name in ('details', 'quality', 'related', 'history')},
            'related': self.related_view(doc),
            'quality_html': self.template('QUALITY_PANEL').render(var={'q': quality_doc}) if quality_doc else '',
        }})
        return var

    def body_transforms(self, doc, var):
        """After the heading transformations, the images of a document and the code and table blocks."""
        steps = super().body_transforms(doc, var)
        if not var['SystemPage']:
            steps.append(lambda html: self._enhance_images(doc, html))
        steps.append(lambda html: enhance_blocks(html, self.config.table_filter))
        return steps

    def _enhance_images(self, doc, html):
        html, missing = enhance_images(html, self.site.paths.source)
        for src in missing:
            self.log.warning(f"[THEME] IMAGE_MISSING doc={q(doc.id)} src={q(src)}")
        return html

    def finalize_html(self, html):
        """techdoc writes pretty-printed HTML with a doctype."""
        tree = etree.fromstring(html, etree.HTMLParser())  # one parser per page: lxml parsers are not thread-safe
        pretty_html = etree.tostring(tree, pretty_print=True, method="html", encoding="unicode")
        return f"<!DOCTYPE html>\n{pretty_html}"

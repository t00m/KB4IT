#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Server module.

# File: theme.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: default theme script
"""

import calendar as _calendar
import os
import re
import shutil
import zipfile
from datetime import datetime

from lxml import etree
from techdoc_admin import AdminMixin
from techdoc_blocks import enhance_blocks
from techdoc_dashboard import DashboardMixin, priority_css, status_css
from techdoc_docpage import banners, header_strip, info_groups, summary
from techdoc_media import enhance_images
from techdoc_quality import (DIM_LABELS, DIMENSIONS, MAXIMA, TIER_LABELS, DocInput, assess, checklist, index_js,
                             load_skeletons, peer_stats, profile)
from techdoc_quality_guide import CHECKS as GUIDE_CHECKS
from techdoc_quality_page import duplicates, quick_wins, tier_mix
from techdoc_quality_guide import DIMS as GUIDE_DIMS
from techdoc_records import event_type, work_type
from techdoc_related import RELATED_KEYS, related

from kb4it.core.util import (
    get_human_datetime,
    get_source_docs,
    html_id_for,
    human_size,
    slugify,
    source_ext,
    valid_filename,
)
from kb4it.services.themekit import DocumentTheme

parser = etree.HTMLParser()


class Theme(AdminMixin, DashboardMixin, DocumentTheme):
    reserved_pages = ('404.md', 'quality-guide.md', 'quality.md')  # pages build() writes
    add_page = True   # create_page_add() runs in build()

    def build_datatable(self, headers=None, doclist=None, table_id='kb4it-datatable'):
        """Override: document tables leave out the columns that are empty in every row; Date and Title always stay."""
        if not headers:
            headers = (self.srvbes.get_dict('repo') or {}).get('datatable', list(self.datatable_default_headers))
        docs = [d for d in doclist or [] if not self.srvdtb.is_system(d)]
        if docs:
            quality = bool(self.ensure_quality())
            headers = [key for key in headers if key in ('Date', 'Title') or (key == 'Quality' and quality)
                       or any(v for d in docs for v in self.srvdtb.get_values(d, key))]
        return super().build_datatable(headers, doclist, table_id)

    def datatable_custom_cell(self, doc_id, key):
        """The Quality column: a five-square meter and the tier chip, sorted by score; retired documents last."""
        assessment = self.ensure_quality().get(doc_id) if key == 'Quality' else None
        if assessment is None:
            return None
        tier = assessment.tier
        if tier == 'retired':
            return '<td data-order="-1"><span class="kb-q-chip kb-q-retired">Retired</span></td>'
        on = 5 if tier == 'exemplary' else min(5, assessment.score // 20)
        squares = '<i class="on"></i>' * on + '<i></i>' * (5 - on)
        return (f'<td data-order="{assessment.score}"><span class="kb-q-meter kb-q-{tier}">{squares}</span>'
                f'<span class="kb-q-chip kb-q-{tier}">{TIER_LABELS[tier]}</span></td>')

    def datatable_date_cell(self, timestamp):
        """The date cell gets a class, so the date stays on one line and the time wraps below it."""
        return super().datatable_date_cell(timestamp).replace('<td class="uk-text-left">', '<td class="uk-text-left kb-dt-date">', 1)

    def datatable_value_link(self, properties, key, value):
        """Priority and Status values show as colored labels."""
        link = super().datatable_value_link(properties, key, value)
        if key == 'Priority' and value:
            link['class'] = 'uk-label kb-badge kb-dt-label %s' % priority_css(value)
        elif key == 'Status' and value:
            link['class'] = 'uk-label kb-badge kb-dt-label %s' % status_css(value)
        return link

    def _build_year_calendar_html(self, year):
        """Generate a 12-month HTML calendar grid for events.html."""
        MONTH_NAMES = [
            'January', 'February', 'March', 'April',
            'May', 'June', 'July', 'August',
            'September', 'October', 'November', 'December',
        ]
        WEEKDAY_ABBR = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
        now = datetime.now()
        cal = _calendar.Calendar(firstweekday=_calendar.MONDAY)

        parts = ['<div class="kb-evcal-grid">']
        for month in range(1, 13):
            quarter = (month - 1) // 3 + 1
            mname = MONTH_NAMES[month - 1]
            has_month = (
                year in self.events_docs
                and month in self.events_docs[year]
            )
            qlabel = f'<span class="kb-evcal-qlabel">Q{quarter}</span>'
            if has_month:
                month_url = f'events_{year:04d}{month:02d}.html'
                caption = f'<a href="{month_url}">{qlabel} {mname}</a>'
            else:
                caption = f'{qlabel} {mname}'

            parts.append(f'<div class="kb-evcal-month kb-evcal-q{quarter}">')
            parts.append(f'<div class="kb-evcal-mname">{caption}</div>')
            parts.append('<table><thead><tr>')
            for wd in WEEKDAY_ABBR:
                parts.append(f'<th>{wd}</th>')
            parts.append('</tr></thead><tbody>')

            for week in cal.monthdayscalendar(year, month):
                parts.append('<tr>')
                for day in week:
                    if day == 0:
                        parts.append('<td></td>')
                        continue
                    has_event = (
                        year in self.events_docs
                        and month in self.events_docs[year]
                        and day in self.events_docs[year][month]
                    )
                    is_today = (
                        year == now.year
                        and month == now.month
                        and day == now.day
                    )
                    url = f'events_{year:04d}{month:02d}{day:02d}.html'
                    if has_event and is_today:
                        parts.append(f'<td class="kb-evcal-today-event"><a href="{url}">{day}</a></td>')
                    elif has_event:
                        parts.append(f'<td class="kb-evcal-event"><a href="{url}">{day}</a></td>')
                    elif is_today:
                        parts.append(f'<td class="kb-evcal-today">{day}</td>')
                    else:
                        parts.append(f'<td>{day}</td>')
                parts.append('</tr>')

            parts.append('</tbody></table></div>')
        parts.append('</div>')
        return ''.join(parts)

    def build_page_events(self):
        doclist = []
        ecats = {}
        repo = self.srvbes.get_dict('repo')
        event_types = repo.get('events', [])
        # ~ self.log.debug(" - Event types: %s", ', '.join(event_types))

        for docId in self.srvdtb.get_documents():
            if self.srvdtb.is_system(docId):
                continue
            category = event_type(self.srvdtb, docId)
            if category in event_types:
                ecats.setdefault(category, set()).add(docId)

                doclist.append(docId)
                title = self.srvdtb.get_values(docId, 'Title')[0]
        must_compile_year = self.build_events(doclist)

        events_pagename = os.path.join(self.srvbes.get_path('cache'), 'events.html')
        if must_compile_year or not os.path.exists(events_pagename):
            years_data = []
            for year in sorted(self.dey.keys(), reverse=True):
                doclist_year = []
                for month in self.events_docs[year]:
                    for day in self.events_docs[year][month]:
                        doclist_year.extend(self.events_docs[year][month][day])
                total = len(doclist_year)
                calendar_html = self._build_year_calendar_html(year)
                datatable_html = self.build_datatable([], doclist_year, table_id=f'kb4it-datatable-{year}')
                years_data.append({
                    'year': year,
                    'count': total,
                    'calendar': calendar_html,
                    'datatable': datatable_html,
                })
            events = {'years': years_data}
            page = self.template('PAGE_EVENTS')
            self.distribute_md('events', page.render(var=events))
        else:
            self.distribute_html('events', events_pagename)

        self.srvdtb.add_document('events.md')
        self.srvdtb.add_document_key('events.md', 'Title', 'Events')
        self.srvdtb.add_document_key('events.md', 'SystemPage', 'Yes')

    def toc_sidebar(self, source_html):
        """Show the sticky table of contents only when theme.json asks for it and the page has four or more sections."""
        theme = self.srvbes.get_dict('theme') or {}
        return theme.get('toc_sidebar') is True and len(re.findall(r'<h2\b', source_html)) >= 4

    def quality_on(self):
        """Quality scores are on unless repo.json sets "quality": false or theme.json turns them off."""
        repo = self.srvbes.get_dict('repo') or {}
        return repo.get('quality', True) is not False and profile(self.srvbes.get_dict('theme')).get('enabled', True)

    def search_record(self, doc_id):
        """Override: the shared search carries the quality tier, so readers can pick the better page."""
        record = super().search_record(doc_id)
        assessment = (self.ensure_quality() or {}).get(doc_id)
        if assessment is not None:
            record['q'] = {
                'score': assessment.score,
                'tier': assessment.tier,
                'label': TIER_LABELS.get(assessment.tier, assessment.tier.title()),
            }
        return record

    def quality_view(self, doc_id):
        """What the header, the note and the Quality tab show for a document; None when there is no score."""
        assessment = (getattr(self, 'quality', None) or {}).get(doc_id)
        if assessment is None or assessment.tier == 'retired':
            return None
        peer = assessment.peer
        return {
            'score': assessment.score,
            'tier': assessment.tier,
            'label': TIER_LABELS[assessment.tier],
            'peer': peer,
            'peer_name': 'document' if peer == 'Other' else peer.lower(),
            'page': html_id_for(doc_id),
            'dims': [{'key': d, 'label': DIM_LABELS[d], 'points': round(assessment.dims[d]), 'max': MAXIMA[d],
                      'percent': round(100 * assessment.dims[d] / MAXIMA[d]), 'tip': GUIDE_DIMS[d][1]} for d in DIMENSIONS],
            'checklist': checklist(assessment),
        }

    def backlinks_html(self, doc_id):
        """Override: techdoc shows the documents that link here in the Related tab of the info card, not after the body."""
        return ''

    def related_view(self, doc_id):
        """Linked from and related documents for the Related tab, each with the tier of its target."""
        plan = self.srvbes.get_plan()
        if getattr(self, '_related_plan', None) is not plan:
            docs = [d for d in self.srvdtb.get_documents() if not self.srvdtb.is_system(d)
                    and (self.quality.get(d) is None or self.quality[d].tier != 'retired')]
            self._related_meta = {d: {k: list(self.srvdtb.get_values(d, k)) for k in RELATED_KEYS} for d in docs}
            self._related_plan = plan
        tiers = (getattr(self, 'quality_stats', None) or {}).get('docs', {})

        def chip(page):
            tier = tiers.get(page, {}).get('tier')
            return {'tier': tier, 'label': TIER_LABELS[tier]} if tier else None

        linked = [dict(item, chip=chip(item['href'])) for item in self.backlinks(doc_id)]
        similar = []
        if doc_id in self._related_meta:
            for item in related(doc_id, self._related_meta):
                page = html_id_for(item['doc'])
                title = (self.srvdtb.get_values(item['doc'], 'Title') or [item['doc']])[0]
                similar.append({'title': title, 'href': page, 'shared': ', '.join(item['shared']), 'chip': chip(page)})
        return {'linked': linked, 'similar': similar} if linked or similar else None

    def ensure_quality(self):
        """Score the documents once per build, whichever page needs the scores first (key pages come before build())."""
        plan = self.srvbes.get_plan()
        if getattr(self, '_quality_plan', None) is not plan:
            self.assess_documents()
            self._quality_plan = plan
        return self.quality

    def assess_documents(self):
        """Score every document once per build; build_page and quality-index.js read the results."""
        self.quality, self.quality_stats = {}, {}
        if not self.quality_on():
            return
        prof = profile(self.srvbes.get_dict('theme'))
        theme_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skeletons = load_skeletons(os.path.join(theme_dir, 'templates', 'skeletons'))
        source_dir = self.srvbes.get_path('source')
        plan = self.srvbes.get_plan()
        backlinks = (getattr(plan, 'backlinks', None) or {}) if plan is not None else {}
        docs = [d for d in self.srvdtb.get_documents() if not self.srvdtb.is_system(d)]
        known = set(docs)
        today = datetime.now().date()
        for doc_id in docs:
            path = os.path.join(source_dir, doc_id)
            try:
                with open(path, encoding='utf-8') as fh:
                    text = fh.read()
            except OSError:
                continue
            meta = {key: list(self.srvdtb.get_values(doc_id, key)) for key in self.srvdtb.get_doc_keys(doc_id)}
            doc = DocInput(text, meta, len(backlinks.get(doc_id, [])), known, source_dir, work_type(self.srvdtb, doc_id))
            self.quality[doc_id] = assess(doc, prof, skeletons, today)
        self.quality_stats = peer_stats(self.quality)
        tiers = [a.tier for a in self.quality.values()]
        counts = ' '.join(f'{t}={tiers.count(t)}' for t in ('exemplary', 'complete', 'basic', 'stub', 'retired'))
        self.log.info(f"[THEME] QUALITY docs={len(tiers)} {counts}")

    def build_page_quality_guide(self):
        """The system page every Quality tab item links to: tiers, every check with an example, the skeletons."""
        if not self.quality_on():
            return
        prof = profile(self.srvbes.get_dict('theme'))
        dims = []
        for key in DIMENSIONS:
            title, what = GUIDE_DIMS[key]
            checks = [dict(entry, key=check_key) for check_key, entry in GUIDE_CHECKS.items() if entry['dim'] == key]
            dims.append({'key': key, 'title': title, 'what': what, 'max': MAXIMA[key], 'checks': checks})
        folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates', 'skeletons')
        skeletons = []
        for name, skeleton in sorted(load_skeletons(folder).items()):
            with open(os.path.join(folder, f'{name}-SKELETON.md'), encoding='utf-8') as fh:
                text = fh.read().strip()
            skeletons.append({'key': name.lower(), 'title': name.capitalize(),
                              'headings': [h.capitalize() for h in skeleton.headings], 'text': text})
        page = self.template('PAGE_QUALITY_GUIDE').render(var={
            'tiers': prof['tiers'], 'retired': prof['retired_status'], 'dims': dims, 'skeletons': skeletons})
        self.distribute_md('quality-guide', page, as_html=False)
        self.srvdtb.add_document('quality-guide.md')
        self.srvdtb.add_document_key('quality-guide.md', 'Title', 'Quality guide')
        self.srvdtb.add_document_key('quality-guide.md', 'SystemPage', 'Yes')

    def _quality_best(self, per_type=3):
        """Top documents per DocType for the Quality page Best documents section."""
        if not getattr(self, 'quality', None):
            return []
        from kb4it.core.util import html_id_for
        # get diataxis types
        diataxis = [
            {'name': 'Tutorial'},
            {'name': 'How-to guide'},
            {'name': 'Reference'},
            {'name': 'Explanation'},
        ]
        from techdoc_quality import profile
        floor = profile(self.srvbes.get_dict('theme'))['tiers']['complete']
        shelf = []
        for item in diataxis:
            docs = sorted((d for d, a in self.quality.items() if a.peer == item['name'] and a.tier != 'retired' and a.score >= floor),
                          key=lambda d: (-self.quality[d].score, d))[:per_type]
            for doc in docs:
                a = self.quality[doc]
                year = (self.srvdtb.get_values(doc, 'Date') or [''])[0][:4]
                shelf.append({'title': (self.srvdtb.get_values(doc, 'Title') or [doc])[0], 'href': html_id_for(doc),
                              'score': a.score, 'tier': a.tier, 'type': item['name'], 'year': year})
        return shelf


    def build_page_quality(self):
        """The Quality page: tier mix, Exemplary documents, quick wins, broken links, missing images, no Summary, duplicates."""
        if not self.quality:
            return

        def title(doc):
            return (self.srvdtb.get_values(doc, 'Title') or [doc])[0]

        def ref(doc, **extra):
            return dict({'title': title(doc), 'href': html_id_for(doc)}, **extra)

        live = {d: a for d, a in self.quality.items() if a.tier != 'retired'}
        broken, images = [], []
        for doc, a in sorted(live.items()):
            for c in a.checks:
                if c.key == 'check-broken-link' and not c.passed:
                    broken.append(ref(doc, target=c.todo.rsplit(' to ', 1)[-1]))
                elif c.key == 'check-missing-image' and not c.passed:
                    images.append(ref(doc, target=c.todo.rsplit(' image ', 1)[-1]))
        best = sorted((d for d, a in live.items() if a.tier == 'exemplary'), key=lambda d: (-live[d].score, d))
        pairs = duplicates({d: title(d) for d in live})
        q = {
            'mix': tier_mix(self.quality),
            'best': self._quality_best(),
            'exemplary': [ref(d, score=live[d].score, peer=live[d].peer) for d in best],
            'wins': [dict(ref(w['doc']), **w) for w in quick_wins(live, profile(self.srvbes.get_dict('theme')))],
            'broken': broken,
            'images': images,
            'no_summary': [ref(d) for d in sorted(live) if not any(c.key == 'check-summary' and c.passed for c in live[d].checks)],
            'duplicates': [(ref(a, score=live[a].score), ref(b, score=live[b].score), s) for a, b, s in pairs],
        }
        self.distribute_md('quality', self.template('PAGE_QUALITY').render(var={'q': q}))
        self.srvdtb.add_document('quality.md')
        self.srvdtb.add_document_key('quality.md', 'Title', 'Quality')
        self.srvdtb.add_document_key('quality.md', 'SystemPage', 'Yes')

    def build(self):
        """Create standard pages for default theme"""
        self.ensure_quality()
        self.build_page_quality_guide()
        self.build_page_quality()
        var = self.get_theme_var()
        self.build_page_events()
        self.build_page_properties()
        self.build_page_stats()
        self.build_page_bookmarks()
        self.build_page_404()
        self.create_page_add()
        self.build_page_index(var)
        self.build_page_index_all()
        self.create_page_about_kb4it()
        self.create_page_about_app()
        self.create_page_help()
        self.create_page_search()

    def build_page(self, path_md):
        """Build the final HTML Page.

        At this point, the Markdown compilation has finished successfully and
        the html page can be built. The Builder receives the source filepath;
        another file with extension .html should also exist.

        The html page is built by inserting the html header at the beginning,
        appending the footer at the end, and applying the necessary
        transformations in the body.

        Finally, the html page produced by the compiler is overwritten.
        """
        path_hdoc = html_id_for(path_md)
        basename_md = os.path.basename(path_md)
        basename_hdoc = os.path.basename(path_hdoc)
        exists_hdoc = os.path.exists(path_hdoc)  # it should be true

        if not exists_hdoc:
            self.log.error(f"[THEME] HTML_MISSING doc={basename_md}")
        else:
            HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
            HTML_BODY = self.template('HTML_BODY')
            HTML_FOOTER = self.template('HTML_FOOTER')
            var = self.get_theme_var()
            now = datetime.now()
            timestamp = get_human_datetime(now)
            keys = self.srvdtb.get_doc_properties(basename_md)

            with open(path_md, 'r', encoding='utf-8') as fpa:
                source_md = fpa.read()

            with open(path_hdoc, 'r', encoding='utf-8') as fph:
                source_html = fph.read()

            var['toc'] = self.extract_toc(source_html)
            var['has_toc'] = True
            var['toc_sidebar'] = False

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
                theme_conf = self.srvbes.get_dict('theme') or {}
                var['toc_sidebar'] = self.toc_sidebar(source_html)
                doc_summary = summary(self.srvdtb, basename_md)
                q = self.quality_view(basename_md)
                var['has_quality'] = q is not None
                var['page']['exemplary'] = bool(q) and q['tier'] == 'exemplary'
                var['doc_header'] = self.template('DOC_HEADER').render(var={
                    'quality': q,
                    'strip': header_strip(self.srvdtb, basename_md, theme_conf.get('header_keys', {})),
                    'summary': doc_summary,
                    'banners': banners(self.srvdtb, basename_md),
                })
                info_tabs = theme_conf.get('info_tabs', {})
                repo = var['repo']
                edit_url = ''
                if var.get('git_ok'):
                    edit_url = (f"{repo['git_server']}/{repo['git_user']}/{repo['git_repo']}/edit/"
                                f"{repo['git_branch']}/{repo['git_path']}/{basename_md}")
                var['info_card'] = self.template('INFO_CARD').render(var={'card': {
                    'open': not doc_summary,
                    'groups': info_groups(self.srvdtb, basename_md, theme_conf.get('info_groups', []), source_md),
                    'history': {
                        'date': (self.srvdtb.get_values(basename_md, 'Date') or [''])[0],
                        'source': basename_md,
                        'built': timestamp,
                        'edit_url': edit_url,
                    },
                    'print': {name: info_tabs.get(name, {}).get('print', name == 'details')
                              for name in ('details', 'quality', 'related', 'history')},
                    'related': self.related_view(basename_md),
                    'quality_html': self.template('QUALITY_PANEL').render(var={'q': q}) if q else '',
                }})

            var['menu_contents'] = HTML_TOC
            var['keys'] = keys
            var['page']['title'] = 'No title found...'
            var['page']['title-tooltip'] = 'No title found...'
            try:
                var['page']['title'] = keys['Title']  # the top bar cuts it with CSS
                var['page']['title-tooltip'] = keys['Title']
            except Exception:
                pass
            var['basename_md'] = basename_md
            var['basename_hdoc'] = basename_hdoc
            var['source_md'] = source_md
            var['fmt'] = source_ext(basename_md) or "md"
            var['source_html'] = self.apply_transformations(source_html)
            if not var['SystemPage']:
                var['source_html'], missing = enhance_images(var['source_html'], self.srvbes.get_path('source'))
                for src in missing:
                    self.log.warning(f"[THEME] IMAGE_MISSING doc={basename_md} src={src}")
            var['source_html'] = enhance_blocks(var['source_html'])
            actions = self.get_page_actions(var)
            var['actions'] = actions
            var['timestamp'] = timestamp

            HEADER = HTML_HEADER_COMMON.render(var=var)
            BODY = HTML_BODY.render(var=var)
            FOOTER = HTML_FOOTER.render(var=var)

            HTML = ""
            HTML += HEADER
            HTML += BODY
            HTML += FOOTER

            with open(path_hdoc, 'w', encoding='utf-8') as fhtml:
                tree = etree.fromstring(HTML, parser)
                pretty_html = etree.tostring(tree, pretty_print=True, method="html").decode()
                fhtml.write(f"<!DOCTYPE html>\n{pretty_html}")

            # ~ self.log.debug(f"KEY[{key}] VALUE[{value}] targets to RESOURCE[{var['pagename']}]")

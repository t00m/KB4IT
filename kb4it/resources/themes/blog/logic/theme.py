#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
# Author: Tomás Vírseda
# License: GPL v3
# Description: Theme Blog for KB4IT
"""

import threading
from html import escape

from kb4it.core.structured import DEFAULT_MAP
from kb4it.core.util import extract_sections_from_md, get_font_size, guess_datetime, valid_filename
from kb4it.theme import BaseTheme, page_name, q


class Theme(BaseTheme):
    # events: one archive page per day, month and year of the posts (every dated post is an event).
    features = ("documents", "events", "stats", "bookmarks", "search", "about", "editor")
    properties_title = 'Metadata'
    reuse_unchanged_pages = True
    datatable_link_template = 'LINK'

    def setup(self):
        self._undated = set()
        self._undated_lock = threading.Lock()

    def _post_author(self, post, metadata):
        """The first Author of a post, with the link to its page and the tooltip of its profile, for the post header."""
        author = next((v for v in metadata.get('Author') or [] if v), '')
        if author:
            post['Author_0_Url'] = metadata.get(f'Author_{author}_Url') or page_name('Author', author)
            people = self.site.people
            post['Author_0_Tip'] = people.tip(author) if 'Author' in people.keys else ''

    def structured_defaults(self):
        """A post is a BlogPosting and its Category is the section of the blog."""
        return {'type': 'BlogPosting', 'map': {**DEFAULT_MAP, 'Category': 'articleSection'}}

    def note_undated(self, doc_id, dates):
        """Log once a post without a usable Date: it is listed after the dated ones, without a calendar line."""
        stamp = (dates or [None])[0]
        if stamp and guess_datetime(stamp) is not None:
            return
        with self._undated_lock:
            if doc_id in self._undated:
                return
            self._undated.add(doc_id)
        self.log.warning(f"[THEME] DOC_UNDATED doc={q(doc_id)}")

    def datatable_date_cell(self, doc):
        """Blog's date cell: a link to the day's page, no alignment class."""
        if doc.date is None:
            return '<td class=""></td>'
        ts_title = escape(doc.date[:16])
        url = self.site.features.events.day_url(doc)
        if url is None:
            return f'<td class="">{ts_title}</td>'
        return f"""<td class=""><a class="uk-link-heading" href="{escape(url)}">{ts_title}</a></td>"""

    # ---------------------------------------------------------------- pages
    def build(self, site):
        """The home page with the newest posts, and the archive (events.html)."""
        self.build_page_index(site)
        self.build_page_events(site)

    def build_page_index(self, site):
        """The home page: the excerpt of the newest posts (repo.json index_posts, default 10).

        At this point the posts are not compiled yet, so the excerpt is read from the Markdown
        source and wrapped in paragraphs.
        """
        if site.keep('index'):
            return
        var = self.base_var()
        tpl_post = self.template('POST_MD_INDEX')
        nip = site.repo.get('index_posts', 10)  # number of posts on the home page
        var['page']['title'] = "Index"

        html_parts = [self.template('PAGE_INDEX').render(var=var)]
        for doc in list(site.documents)[:nip]:
            metadata = doc.template_keys()
            var['post'] = {'filename': doc.id, **metadata}
            self._post_author(var['post'], metadata)
            md_content = doc.source()
            md_filepath = f"{site.paths.source}/{doc.id}"
            sections = extract_sections_from_md(md_filepath)
            if 'Excerpt' in sections:
                start, end = sections['Excerpt']['start'], sections['Excerpt']['end']
                text = '\n'.join(md_content.splitlines()[start:end])
                var['post']['Excerpt'] = "\n".join(
                    [f"<p>{line}</p>" if line.strip() else line for line in text.strip().splitlines()])
            else:
                var['post']['Excerpt'] = "<p>Excerpt missing</p>"
            self.note_undated(doc.id, var['post'].get('Date'))
            var['basename_md'] = doc.id
            var['metadata'] = site.features.metadata.section(doc)
            var['source_md'] = md_content
            try:
                html_parts.append(tpl_post.render(var=var))
                self.log.debug(f"[THEME] INDEX_ADD doc={q(doc.id)}")
            except Exception as error:
                self.log.warning(f"[THEME] INDEX_SKIP doc={q(doc.id)} error={q(error)}")
        site.page('index', 'Index', ''.join(html_parts))

    def build_year_pagination(self, events):
        """The archive: one entry per year with its number of posts."""
        item_tpl = self.template('EVENTCAL_YEAR_PAGINATION_ITEM')
        items = []
        for year in events.years():
            total = sum(len(docs) for days in events.index[year].values() for docs in days.values())
            items.append(item_tpl.render(var={'year': year, 'year_count': total}))
        return self.template('EVENTCAL_YEAR_PAGINATION').render(var={'items': ''.join(items)})

    def build_page_events(self, site):
        """events.html, the archive of the years."""
        html = self.build_year_pagination(site.features.events)
        if site.keep('events'):
            return
        site.page('events', 'Archive', self.template('PAGE_EVENTS').render(var={'content': html}))

    def after_build(self, site):
        self.log.debug("[THEME] POST_START")
        self.log.debug("[THEME] POST_END")

    # ------------------------------------------------------------ post pages
    def page_context(self, doc, var):
        """The post, the property counts, topics and tags, the header menu and the metadata."""
        site = self.site
        var['count_docs'] = len(site.documents)
        keys = site.properties.all_keys()
        var['count_keys'] = len(keys)
        var['leader_items'] = [{'key': key, 'vfkey': valid_filename(key),
                                'count_values': len(site.properties.values(key))}
                               for key in keys if key != 'Date']
        var['post'] = dict(var['keys'])
        self._post_author(var['post'], var['keys'])
        if not var['SystemPage']:
            self.note_undated(doc.id, var['post'].get('Date'))
        var['topics'] = list(site.properties.values('Topic'))
        var['tags'] = list(site.properties.values('Tag'))
        var['menu_contents'] = site.features.toc.menu_contents(var)
        var['metadata'] = site.features.metadata.section(doc)
        return var

    def page_template(self, doc, var):
        """A document is a post; with repo.json strict only a document whose Category is Post."""
        if var['SystemPage']:
            return 'HTML_BODY'
        if self.site.repo.get('strict', False):
            return 'POST_HTML_SINGLE' if 'Post' in var['post']['Category'] else 'HTML_BODY'
        return 'POST_HTML_SINGLE'

    def render_page(self, doc, var):
        """A body template that fails (a document without Date or Category) falls back to HTML_BODY."""
        header = self.template('HTML_HEADER_COMMON').render(var=var)
        name = 'POST_HTML_SINGLE'  # the only choice that can fail
        try:
            name = self.page_template(doc, var)
            body = self.template(name).render(var=var)
        except Exception as error:
            self.log.warning(f"[THEME] POST_TEMPLATE_FALLBACK doc={q(doc.id)} template={q(name)} "
                             f"error={q(' '.join(str(error).split()) or type(error).__name__)}")
            body = self.template('HTML_BODY').render(var=var)
        return header + body + self.template('HTML_FOOTER').render(var=var)

    # ------------------------------------------------------- property pages
    def cloud_measure(self, frequency, max_frequency):
        """Blog sizes property buttons and tag cloud words by font size."""
        return {'size': get_font_size(frequency, max_frequency)}

    def frequency_keys(self):
        """Blog sizes the property buttons against every property that is not blocked."""
        blocked = self.site.properties.blocked
        return [key for key in self.site.properties.all_keys() if key not in blocked]

    def stats_keys(self):
        """Blog lists every property on the stats page."""
        return list(self.site.properties.all_keys())

    def generate_sources(self, site):
        """This theme doesn't generate sources, yet."""
        self.log.debug("[THEME] NO_SOURCES_GENERATED")

    def base_var(self):
        var = super().base_var()
        # The footer prints the tagline; an empty line when repo.json has none.
        var['repo'].setdefault('tagline', '')
        return var

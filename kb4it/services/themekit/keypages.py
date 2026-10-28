"""System pages built from the metadata: properties, property and value pages,
bookmarks and the list of every document. The stats page lives in `stats.py`."""

from __future__ import annotations

import math
import os
from typing import Any

from kb4it.core.documents import is_yes
from kb4it.core.util import set_max_frequency, valid_filename
from kb4it.services.themekit.host import ThemeHost


class KeyPagesMixin(ThemeHost):
    """Pages about properties and values; needs `Builder` and `build_datatable`."""

    #: Title of the properties page.
    properties_title = 'Properties'
    #: The properties page shows a cloud of property buttons, each opening its values; with False the page
    #: template gets only the list of properties (var['keys']) and shows it another way.
    properties_cloud = True
    #: Reuse the cached properties, stats, bookmarks and all-documents pages when no
    #: property (properties, stats) or no document (bookmarks, all) changed.
    reuse_unchanged_pages = False
    #: Scale a tag cloud without the empty value, which stands for "property not set".
    tagcloud_scale_skips_empty = False

    def cloud_measure(self, frequency: int, max_frequency: int) -> dict[str, Any]:
        """Return the size fields of a property button or a tag cloud word."""
        log_max = math.log(1 + max_frequency) if max_frequency > 0 else 1
        weight = math.log(1 + frequency) / log_max if log_max else 0.0
        return {'count': frequency, 'weight': round(weight, 3)}

    def frequency_keys(self) -> list[str]:
        """Return the properties whose value count sizes the property buttons."""
        return list(self.srvdtb.get_theme_keys())

    def stats_keys(self) -> list[str]:
        """Return the properties listed on the stats page."""
        return list(self.srvdtb.get_theme_keys())

    def _reuse_cached_page(self, name: str, counter: str, reason: str, func: str) -> bool:
        """Keep the cached `name`.html when nothing it shows changed; True if kept."""
        if not self.reuse_unchanged_pages or self.srvbes.get_value('runtime', counter) != 0:
            return False
        if not os.path.exists(os.path.join(self.srvbes.get_path('cache'), f'{name}.html')):
            return False
        self.log.debug(f"[THEME] SKIP reason={reason} func={func}")
        self.srvbes.add_target(f'{name}.md', f'{name}.html')
        return True

    def _add_system_page(self, name: str, title: str) -> None:
        self.srvdtb.add_document(f'{name}.md')
        self.srvdtb.add_document_key(f'{name}.md', 'Title', title)
        self.srvdtb.add_document_key(f'{name}.md', 'SystemPage', 'Yes')

    def get_maxkv_freq(self) -> int:
        """Return the highest number of values of a property."""
        maxkvfreq = 0
        for key in self.frequency_keys():
            maxkvfreq = max(maxkvfreq, len(self.srvdtb.get_all_values_for_key(key)))
        return maxkvfreq

    def build_tagcloud_from_key(self, key: str) -> str:
        """Return a tag cloud of the values of a property, or '' when it has none."""
        dkeyurl: dict[str, set[str]] = {}
        for docId in self.srvdtb.get_documents():
            url = os.path.basename(docId)[:-5]
            for tag in self.srvdtb.get_values(docId, key):
                if tag or not self.tagcloud_scale_skips_empty:
                    dkeyurl.setdefault(tag, set()).add(url)
        lwords = sorted((word for word in dkeyurl if len(word) > 0), key=lambda y: y.lower())
        if not lwords:
            return ''
        max_frequency = set_max_frequency(dkeyurl)
        var = self.get_theme_var()
        var['items'] = []
        for word in lwords:
            frequency = len(dkeyurl[word])
            item = {
                'url': f"{valid_filename(key)}_{valid_filename(word)}.html",
                'tooltip': f"{frequency} documents",
                'word': word,
            }
            item.update(self.cloud_measure(frequency, max_frequency))
            var['items'].append(item)
        return self.template('WORDCLOUD').render(var=var)

    def build_page_properties(self) -> None:
        """Create the properties page: every property with its numbers of values and documents, and with
        properties_cloud, one button per property opening its tag cloud."""
        if self._reuse_cached_page('properties', 'nck', 'no_key_changes', 'build_page_properties'):
            return
        tpl_button = self.template('KEY_MODAL_BUTTON') if self.properties_cloud else None
        max_frequency = self.get_maxkv_freq() if self.properties_cloud else 0
        var = self.get_theme_var()
        var['buttons'] = []
        var['keys'] = []
        ignored_keys = self.srvdtb.get_ignored_keys()
        for key in self.srvdtb.get_all_keys():
            if key in ignored_keys:
                continue
            values = self.srvdtb.get_all_values_for_key(key)
            docs = {doc for value in values for doc in self.srvdtb.get_docs_by_key_value(key, value)}
            var['keys'].append({'key': key, 'vfkey': valid_filename(key), 'values': len(values), 'docs': len(docs)})
            if tpl_button is None:  # properties_cloud is off
                continue
            content = self.build_tagcloud_from_key(key)
            frequency = len(values)
            self.log.debug(f"[THEME] KEY key={key} frequency={frequency}")
            vbtn = {'content': content, 'key': key, 'vfkey': valid_filename(key)}
            vbtn.update(self.cloud_measure(frequency, max_frequency))
            vbtn['tooltip'] = f"{frequency} values"
            var['buttons'].append(tpl_button.render(var=vbtn))
        self.distribute_md('properties', self.template('PAGE_PROPERTIES').render(var=var))
        self._add_system_page('properties', self.properties_title)

    def build_page_key(self, key: str, values: list[str]) -> None:
        """Create the page of a property: its tag cloud and the count of each value."""
        var = self.get_theme_var()
        var['title'] = key
        var['cloud'] = self.build_tagcloud_from_key(key)
        var['leader'] = []
        var['key_values'] = {}
        for value in values:
            docs = self.srvdtb.get_docs_by_key_value(key, value)
            var['leader'].append({
                'count': len(docs),
                'vfkey': valid_filename(key),
                'vfvalue': valid_filename(value),
                'name': value,
            })
        content = self.template('PAGE_KEY').render(var=var)
        var['pagename'] = valid_filename(key)
        self.distribute_md(var['pagename'], content)
        self._add_system_page(var['pagename'], key)
        self.log.debug(f"[THEME] KEY_TARGET key={key} resource={var['pagename']}")

    def build_page_key_value(self, kvpath: tuple[str, str, bool]) -> None:
        """Create the page of a property value: the documents that have it."""
        key, value, compile_value = kvpath
        docs = self.srvbes.get_kbdict_value(key, value, new=True)
        sorted_docs = self.srvdtb.sort_by_date(docs)
        var = self.get_theme_var()
        var['key'] = key
        var['value'] = value
        var['vfkey'] = valid_filename(key)
        var['title'] = f'{key}: {value}'
        var['pagename'] = f"{valid_filename(key)}_{valid_filename(value)}"
        var['doclist'] = sorted_docs
        var['compile'] = compile_value
        var['has_toc'] = False
        var['page']['dt_documents'] = self.build_datatable([], sorted_docs)
        if var['compile']:
            self.distribute_md(var['pagename'], self.template('PAGE_KEY_VALUE').render(var=var))
            self._add_system_page(var['pagename'], var['title'])
            self.log.debug(f"[THEME] KV_TARGET key={key} value={value} resource={var['pagename']}")

    def build_page_bookmarks(self) -> str | None:
        """Create the bookmarks page: documents with Bookmark set to Yes, True or On, in any case."""
        if self._reuse_cached_page('bookmarks', 'ncd', 'no_doc_changes', 'build_page_bookmarks'):
            return None
        var = self.get_theme_var()
        doclist = []
        for docId in self.srvdtb.get_documents():
            bookmark = (self.srvdtb.get_values(docId, 'Bookmark') or [''])[0]
            doc_bookmarked = is_yes(bookmark)
            self.log.debug(f"[THEME] BOOKMARK_CHECK doc={docId} bookmark={bookmark} is_bookmarked={doc_bookmarked}")
            if doc_bookmarked:
                doclist.append(docId)
        self.log.debug(f"[THEME] BOOKMARKS_FOUND n={len(doclist)}")
        datatable = self.build_datatable([], doclist)
        self._add_system_page('bookmarks', 'Bookmarks')
        var['page']['title'] = 'Bookmarks'
        var['page']['dt_bookmarks'] = datatable
        page = self.template('PAGE_BOOKMARKS').render(var=var)
        self.distribute_md('bookmarks', page)
        self.log.debug("[THEME] BOOKMARKS_PAGE_CREATED")
        return page

    def build_page_index_all(self) -> str | None:
        """Create the page that lists every document."""
        if self._reuse_cached_page('all', 'ncd', 'no_doc_changes', 'build_page_index_all'):
            return None
        var = self.get_theme_var()
        var['content'] = self.build_datatable([], list(self.srvdtb.get_documents()))
        page = self.template('PAGE_ALL').render(var=var)
        self.distribute_md('all', page)
        self._add_system_page('all', 'All documents')
        return page

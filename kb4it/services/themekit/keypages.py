"""System pages built from the metadata: properties, property and value pages, stats,
bookmarks and the list of every document."""

import math
import os

from kb4it.core.util import set_max_frequency, valid_filename


class KeyPagesMixin:
    """Pages about properties and values; needs `Builder` and `build_datatable`."""

    #: Title of the properties page.
    properties_title = 'Properties'
    #: Reuse the cached properties, stats, bookmarks and all-documents pages when no
    #: property (properties, stats) or no document (bookmarks, all) changed.
    reuse_unchanged_pages = False
    #: Scale a tag cloud without the empty value, which stands for "property not set".
    tagcloud_scale_skips_empty = False

    def cloud_measure(self, frequency, max_frequency):
        """Return the size fields of a property button or a tag cloud word."""
        log_max = math.log(1 + max_frequency) if max_frequency > 0 else 1
        weight = math.log(1 + frequency) / log_max if log_max else 0.0
        return {'count': frequency, 'weight': round(weight, 3)}

    def frequency_keys(self):
        """Return the properties whose value count sizes the property buttons."""
        return self.srvdtb.get_theme_keys()

    def stats_keys(self):
        """Return the properties listed on the stats page."""
        return self.srvdtb.get_theme_keys()

    def _reuse_cached_page(self, name, counter, reason, func):
        """Keep the cached `name`.html when nothing it shows changed; True if kept."""
        if not self.reuse_unchanged_pages or self.srvbes.get_value('runtime', counter) != 0:
            return False
        if not os.path.exists(os.path.join(self.srvbes.get_path('cache'), f'{name}.html')):
            return False
        self.log.debug(f"[THEME] SKIP reason={reason} func={func}")
        self.srvbes.add_target(f'{name}.md', f'{name}.html')
        return True

    def _add_system_page(self, name, title):
        self.srvdtb.add_document(f'{name}.md')
        self.srvdtb.add_document_key(f'{name}.md', 'Title', title)
        self.srvdtb.add_document_key(f'{name}.md', 'SystemPage', 'Yes')

    def get_maxkv_freq(self):
        """Return the highest number of values of a property."""
        maxkvfreq = 0
        for key in self.frequency_keys():
            maxkvfreq = max(maxkvfreq, len(self.srvdtb.get_all_values_for_key(key)))
        return maxkvfreq

    def build_tagcloud_from_key(self, key):
        """Return a tag cloud of the values of a property, or '' when it has none."""
        dkeyurl = {}
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

    def build_page_properties(self):
        """Create the properties page: one button per property, with its tag cloud."""
        if self._reuse_cached_page('properties', 'nck', 'no_key_changes', 'build_page_properties'):
            return
        tpl_button = self.template('KEY_MODAL_BUTTON')
        max_frequency = self.get_maxkv_freq()
        var = self.get_theme_var()
        var['buttons'] = []
        ignored_keys = self.srvdtb.get_ignored_keys()
        for key in self.srvdtb.get_all_keys():
            if key in ignored_keys:
                continue
            content = self.build_tagcloud_from_key(key)
            frequency = len(self.srvdtb.get_all_values_for_key(key))
            self.log.debug(f"[THEME] KEY key={key} frequency={frequency}")
            vbtn = {'content': content, 'key': key, 'vfkey': valid_filename(key)}
            vbtn.update(self.cloud_measure(frequency, max_frequency))
            vbtn['tooltip'] = f"{frequency} values"
            var['buttons'].append(tpl_button.render(var=vbtn))
        self.distribute_md('properties', self.template('PAGE_PROPERTIES').render(var=var))
        self._add_system_page('properties', self.properties_title)

    def build_page_key(self, key, values):
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

    def build_page_key_value(self, kvpath):
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

    def build_page_stats(self):
        """Create the stats page: documents, properties and values of each."""
        if self._reuse_cached_page('stats', 'nck', 'no_key_changes', 'build_page_stats'):
            return
        var = self.get_theme_var()
        var['count_docs'] = self.srvdtb.get_documents_count()
        keys = self.stats_keys()
        var['count_keys'] = len(keys)
        var['leader_items'] = []
        for key in keys:
            var['leader_items'].append({
                'key': key,
                'vfkey': valid_filename(key),
                'count_values': len(self.srvdtb.get_all_values_for_key(key)),
            })
        self.distribute_md('stats', self.template('PAGE_STATS').render(var=var))
        self._add_system_page('stats', 'Stats')

    def build_page_bookmarks(self):
        """Create the bookmarks page: documents with Bookmark set to Yes or True."""
        if self._reuse_cached_page('bookmarks', 'ncd', 'no_doc_changes', 'build_page_bookmarks'):
            return None
        var = self.get_theme_var()
        doclist = []
        for docId in self.srvdtb.get_documents():
            bookmark = (self.srvdtb.get_values(docId, 'Bookmark') or [''])[0]
            doc_bookmarked = bookmark in ('Yes', 'True')
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

    def build_page_index_all(self):
        """Create the page that lists every document."""
        if self._reuse_cached_page('all', 'ncd', 'no_doc_changes', 'build_page_index_all'):
            return None
        var = self.get_theme_var()
        var['content'] = self.build_datatable([], list(self.srvdtb.get_documents()))
        page = self.template('PAGE_ALL').render(var=var)
        self.distribute_md('all', page)
        self._add_system_page('all', 'All documents')
        return page

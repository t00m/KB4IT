"""Feature property_pages: properties.html, one page per property and one per value."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from kb4it.core.log import q
from kb4it.core.util import set_max_frequency, valid_filename
from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Doc, Site


class PropertyPages(Feature):
    """The pages built from the properties of the documents."""

    name = "property_pages"
    requires = ("table",)
    options = {
        "properties_title": "Properties",       # title of the properties page
        "properties_cloud": True,               # a cloud of property buttons; False: only var['keys']
        "reuse_unchanged_pages": False,         # keep the cached properties page when no property changed
        "tagcloud_scale_skips_empty": False,    # scale a tag cloud without the empty value
    }
    hooks = ("cloud_measure", "frequency_keys", "value_page")
    # Always rendered; with properties_cloud the properties page also needs KEY_MODAL_BUTTON.
    templates = ("PAGE_PROPERTIES", "PAGE_KEY", "PAGE_KEY_VALUE", "WORDCLOUD")

    # ------------------------------------------------------------ hook defaults
    def cloud_measure(self, frequency: int, max_frequency: int) -> dict[str, Any]:
        """The size fields of a property button or a tag cloud word."""
        log_max = math.log(1 + max_frequency) if max_frequency > 0 else 1
        weight = math.log(1 + frequency) / log_max if log_max else 0.0
        return {'count': frequency, 'weight': round(weight, 3)}

    def frequency_keys(self) -> list[str]:
        """The properties whose value count sizes the property buttons."""
        return list(self.engine.srvdtb.get_theme_keys())

    def value_page(self, key: str, value: str, docs: list[Doc]) -> None:
        """Write the page of a property value (Key_Value.html): the table of its documents."""
        self.write_value_page((key, value, True))

    # ------------------------------------------------------------------ helpers
    def reuse(self, name: str, counter: str, reason: str, func: str) -> bool:
        """Keep the cached page when reuse_unchanged_pages is on and nothing it shows changed."""
        if not self.option("reuse_unchanged_pages"):
            return False
        return bool(self.engine.reuse_cached_page(name, counter, reason, func))

    def max_values(self) -> int:
        """The highest number of values of a property."""
        db = self.engine.srvdtb
        return max([len(db.get_all_values_for_key(key)) for key in self.hook("frequency_keys")()] + [0])

    def tagcloud(self, key: str) -> str:
        """A tag cloud of the values of a property, or '' when it has none."""
        engine, db = self.engine, self.engine.srvdtb
        skip_empty = self.option("tagcloud_scale_skips_empty")
        dkeyurl: dict[str, set[str]] = {}
        for doc_id in db.get_documents():
            for tag in db.get_values(doc_id, key):
                if tag or not skip_empty:
                    dkeyurl.setdefault(tag, set()).add(doc_id)
        lwords = sorted((word for word in dkeyurl if len(word) > 0), key=lambda y: y.lower())
        if not lwords:
            return ''
        max_frequency = set_max_frequency(dkeyurl)
        measure = self.hook("cloud_measure")
        var = engine.get_theme_var()
        var['items'] = []
        for word in lwords:
            frequency = len(dkeyurl[word])
            item = {
                'url': f"{valid_filename(key)}_{valid_filename(word)}.html",
                'tooltip': f"{frequency} documents",
                'word': word,
            }
            item.update(measure(frequency, max_frequency))
            var['items'].append(item)
        html: str = engine.template('WORDCLOUD').render(var=var)
        return html

    # -------------------------------------------------------------------- pages
    def write_properties_page(self) -> None:
        """properties.html: every property with its numbers of values and documents, and with
        properties_cloud, one button per property opening its tag cloud."""
        if self.reuse('properties', 'nck', 'no_key_changes', 'build_page_properties'):
            return
        engine, db = self.engine, self.engine.srvdtb
        cloud = self.option("properties_cloud")
        tpl_button = engine.template('KEY_MODAL_BUTTON') if cloud else None
        max_frequency = self.max_values() if cloud else 0
        measure = self.hook("cloud_measure")
        var = engine.get_theme_var()
        var['buttons'] = []
        var['keys'] = []
        # ignored_keys get no pages at all; hidden_properties keep their pages but are not listed here.
        skipped = set(db.get_ignored_keys()) | set(db.get_hidden_keys())
        for key in db.get_all_keys():
            if key in skipped:
                continue
            values = db.get_all_values_for_key(key)
            docs = {doc for value in values for doc in db.get_docs_by_key_value(key, value)}
            var['keys'].append({'key': key, 'vfkey': valid_filename(key), 'values': len(values), 'docs': len(docs)})
            if tpl_button is None:  # properties_cloud is off
                continue
            content = self.tagcloud(key)
            frequency = len(values)
            engine.log.debug(f"[THEME] KEY key={q(key)} frequency={q(frequency)}")
            vbtn = {'content': content, 'key': key, 'vfkey': valid_filename(key)}
            vbtn.update(measure(frequency, max_frequency))
            vbtn['tooltip'] = f"{frequency} values"
            var['buttons'].append(tpl_button.render(var=vbtn))
        engine.distribute_md('properties', engine.template('PAGE_PROPERTIES').render(var=var), listing=True)
        engine.add_system_page('properties', self.option("properties_title"))

    def write_key_page(self, key: str, values: list[str]) -> None:
        """Key.html: the tag cloud of a property and the count of each value."""
        engine, db = self.engine, self.engine.srvdtb
        var = engine.get_theme_var()
        var['title'] = key
        var['cloud'] = self.tagcloud(key)
        var['leader'] = []
        var['key_values'] = {}
        for value in values:
            docs = db.get_docs_by_key_value(key, value)
            var['leader'].append({
                'count': len(docs),
                'vfkey': valid_filename(key),
                'vfvalue': valid_filename(value),
                'name': value,
            })
        content = engine.template('PAGE_KEY').render(var=var)
        var['pagename'] = valid_filename(key)
        engine.distribute_md(var['pagename'], content, listing=True)
        engine.add_system_page(var['pagename'], key)
        engine.log.debug(f"[THEME] KEY_TARGET key={q(key)} resource={q(var['pagename'])}")

    def write_value_page(self, kvpath: tuple[str, str, bool]) -> None:
        """Key_Value.html: the documents that have a value (written only when compile is True)."""
        engine = self.engine
        key, value, compile_value = kvpath
        docs = engine.srvbes.get_kbdict_value(key, value, new=True)
        sorted_docs = engine.srvdtb.sort_by_date(docs)
        var = engine.get_theme_var()
        var['key'] = key
        var['value'] = value
        var['vfkey'] = valid_filename(key)
        var['title'] = f'{key}: {value}'
        var['pagename'] = f"{valid_filename(key)}_{valid_filename(value)}"
        var['doclist'] = sorted_docs
        var['compile'] = compile_value
        var['has_toc'] = False
        var['page']['dt_documents'] = self.table_html(sorted_docs, filterable=True)
        var['profile_card'] = engine.profile_card(key, value) if compile_value else ''
        if var['compile']:
            engine.distribute_md(var['pagename'], engine.template('PAGE_KEY_VALUE').render(var=var), listing=True)
            engine.add_system_page(var['pagename'], var['title'])
            engine.log.debug(f"[THEME] KV_TARGET key={q(key)} value={q(value)} resource={q(var['pagename'])}")

    def value_page_of(self, kvpath: tuple[str, str, bool]) -> None:
        """The pipeline's call for one value: the theme's value_page() hook when the page is rebuilt."""
        key, value, compile_value = kvpath
        if not compile_value:
            return
        docs = [self.doc(d) for d in self.engine.srvdtb.sort_by_date(
            self.engine.srvbes.get_kbdict_value(key, value, new=True))]
        self.hook("value_page")(key, value, docs)

    def pages(self, site: Site) -> None:
        self.write_properties_page()

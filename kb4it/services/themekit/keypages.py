"""System pages built from the metadata: properties, property and value pages,
bookmarks and the list of every document. The stats page lives in `stats.py`.

Legacy API: the code lives in the features property_pages, bookmarks and
all_documents (kb4it/theme/features/); these methods keep their old names.
"""

from __future__ import annotations

from typing import Any

from kb4it.services.themekit.host import ThemeHost, feature_of
from kb4it.theme.features.alldocuments import AllDocuments
from kb4it.theme.features.bookmarks import Bookmarks
from kb4it.theme.features.propertypages import PropertyPages


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

    def _pages(self) -> PropertyPages:
        return feature_of(self, PropertyPages)

    def cloud_measure(self, frequency: int, max_frequency: int) -> dict[str, Any]:
        """Return the size fields of a property button or a tag cloud word."""
        return self._pages().cloud_measure(frequency, max_frequency)

    def frequency_keys(self) -> list[str]:
        """Return the properties whose value count sizes the property buttons."""
        return self._pages().frequency_keys()

    def stats_keys(self) -> list[str]:
        """Return the properties listed on the stats page."""
        return list(self.srvdtb.get_theme_keys())

    def _reuse_cached_page(self, name: str, counter: str, reason: str, func: str) -> bool:
        """Keep the cached `name`.html when nothing it shows changed; True if kept."""
        return self._pages().reuse(name, counter, reason, func)

    def _add_system_page(self, name: str, title: str) -> None:
        """Deprecated alias of Builder.add_system_page(name, title), kept for custom themes."""
        self.add_system_page(name, title)

    def get_maxkv_freq(self) -> int:
        """Return the highest number of values of a property."""
        return self._pages().max_values()

    def build_tagcloud_from_key(self, key: str) -> str:
        """Return a tag cloud of the values of a property, or '' when it has none."""
        return self._pages().tagcloud(key)

    def build_page_properties(self) -> None:
        """Create the properties page: every property with its numbers of values and documents, and with
        properties_cloud, one button per property opening its tag cloud."""
        self._pages().write_properties_page()

    def build_page_key(self, key: str, values: list[str]) -> None:
        """Create the page of a property: its tag cloud and the count of each value."""
        self._pages().write_key_page(key, values)

    def build_page_key_value(self, kvpath: tuple[str, str, bool]) -> None:
        """Create the page of a property value: the documents that have it."""
        self._pages().write_value_page(kvpath)

    def build_page_bookmarks(self) -> str | None:
        """Create the bookmarks page: documents with Bookmark set to Yes, True or On, in any case."""
        return feature_of(self, Bookmarks).write()

    def build_page_index_all(self) -> str | None:
        """Create the page that lists every document."""
        return feature_of(self, AllDocuments).write()

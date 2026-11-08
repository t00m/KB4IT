"""The built-in features. A feature here imports kb4it.theme, kb4it.core and its own helpers,
never another feature module; it reaches other features through requires, uses and site.features."""

from __future__ import annotations

from kb4it.theme.feature import Feature
from kb4it.theme.features.about import About
from kb4it.theme.features.alldocuments import AllDocuments
from kb4it.theme.features.bookmarks import Bookmarks
from kb4it.theme.features.editor import Editor
from kb4it.theme.features.events import Events
from kb4it.theme.features.metadata import Metadata
from kb4it.theme.features.notfound import NotFound
from kb4it.theme.features.propertypages import PropertyPages
from kb4it.theme.features.search import Search
from kb4it.theme.features.stats import Stats
from kb4it.theme.features.table import Table
from kb4it.theme.features.tablefilter import TableFilter
from kb4it.theme.features.toc import Toc

#: Built-in features by name.
REGISTRY: dict[str, type[Feature]] = {cls.name: cls for cls in (
    About, AllDocuments, Bookmarks, Editor, Events, Metadata, NotFound, PropertyPages, Search, Stats, Table,
    TableFilter, Toc)}

#: Names that stand for several features.
BUNDLES: dict[str, tuple[str, ...]] = {
    # What DocumentTheme gave: the pages built from the properties of the documents.
    "documents": ("toc", "metadata", "property_pages", "all_documents", "not_found"),
}

#: The names a theme can list in `features`.
FEATURES: tuple[str, ...] = tuple(sorted((*REGISTRY, *BUNDLES)))

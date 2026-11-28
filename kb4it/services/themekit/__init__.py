"""Code shared by the document themes: techdoc, blog and bookshelf (AR-01).

`DocumentTheme` combines the mixins of this package on top of `Builder`. A document
theme subclasses it and keeps only what it does differently; such an override says
why in a docstring that starts with "Override:". Other themes keep subclassing
`Builder`.
"""

from kb4it.services.builder import Builder
from kb4it.services.themekit.events import EventsMixin
from kb4it.services.themekit.keypages import KeyPagesMixin
from kb4it.services.themekit.metadata import MetadataMixin
from kb4it.services.themekit.notfound import NotFoundMixin
from kb4it.services.themekit.page import DocumentPageMixin
from kb4it.services.themekit.stats import StatsMixin
from kb4it.services.themekit.tables import TableMixin
from kb4it.services.themekit.toc import TocMixin

# Layer 1 kits: module -> mixin class. A theme adds the mixin to its class line; no kit imports another
# kit or DocumentTheme (tests/core/test_kit_independence.py). The hook reference has a section per kit.
KITS = {
    "kb4it.services.themekit.diagrams": "DiagramsMixin",
    "kb4it.services.themekit.filters": "FilterMixin",
    "kb4it.services.themekit.gallery": "GalleryMixin",
    "kb4it.services.themekit.navigation": "NavigationMixin",
    "kb4it.services.themekit.related": "RelatedMixin",
    "kb4it.services.themekit.tocsidebar": "TocSidebarMixin",
}

__all__ = ["KITS", "DocumentPageMixin", "DocumentTheme", "EventsMixin", "KeyPagesMixin", "MetadataMixin", "NotFoundMixin", "StatsMixin", "TableMixin", "TocMixin"]


class DocumentTheme(DocumentPageMixin, MetadataMixin, NotFoundMixin, StatsMixin, KeyPagesMixin, TableMixin, EventsMixin,
                    TocMixin, Builder):
    """Base class of the document themes."""

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
from kb4it.services.themekit.tables import TableMixin

__all__ = ["DocumentTheme", "EventsMixin", "KeyPagesMixin", "MetadataMixin", "TableMixin"]


class DocumentTheme(MetadataMixin, KeyPagesMixin, TableMixin, EventsMixin, Builder):
    """Base class of the document themes."""

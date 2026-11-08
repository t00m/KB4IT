"""Gallery kit (Layer 1): thumbnails of the images of every document, shown by the properties chosen in a filter panel.

Legacy API: the code lives in the gallery feature (kb4it/theme/features/gallery.py). A theme on
DocumentTheme calls build_page_gallery() in build() and deploy_gallery_thumbs() after deployment.
"""

from __future__ import annotations

from typing import Any

from kb4it.services.themekit.host import ThemeHost, feature_of
from kb4it.theme.features.gallery import (CODE_SPAN, FENCED, FRONTMATTER, HTML_ATTR, HTML_IMG, MD_IMAGE, MD_IMAGE_REF,
                                          MD_REF_DEF, Gallery, document_images)
from kb4it.theme.media import MediaData

__all__ = ["CODE_SPAN", "FENCED", "FRONTMATTER", "HTML_ATTR", "HTML_IMG", "MD_IMAGE", "MD_IMAGE_REF", "MD_REF_DEF",
           "GalleryMixin", "document_images"]


class GalleryMixin(ThemeHost):
    """The Gallery page: property buttons, a value chooser, a masonry grid of thumbnails, a lightbox."""

    def _gallery(self) -> Gallery:
        return feature_of(self, Gallery)

    @property
    def _gallery_thumbs(self) -> set[str] | None:
        return self._gallery().thumbs

    def gallery_thumb_dir(self) -> str:
        """Thumbnails made by earlier builds: <repo>/var/thumbs."""
        return self._gallery().thumb_dir()

    def gallery_image(self, src: str, local: str | None) -> dict[str, Any]:
        """The entry of one image: what the grid shows (a thumbnail or the original) and its size."""
        return self._gallery().image(src, local)

    def gallery_items(self, doc_id: str) -> list[dict[str, Any]]:
        """The images one document shows, each with its thumbnail, size and caption."""
        return self._gallery().items(doc_id)

    def gallery_data(self) -> MediaData:
        """Return the documents with images, newest first, their images and the filters they can be narrowed by."""
        return self._gallery().data()

    def build_page_gallery(self) -> None:
        """The Gallery page: no image at first; the property buttons on the right choose which ones to show."""
        self._gallery().write()

    def deploy_gallery_thumbs(self) -> None:
        """Copy the thumbnails the Gallery uses into the site and drop the others, there and in var/thumbs."""
        self._gallery().deploy_thumbs()

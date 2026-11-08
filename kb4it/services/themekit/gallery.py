"""Gallery kit (Layer 1): thumbnails of the images of every document, shown by the properties chosen in a filter panel."""

import os
import re
from html import unescape
from typing import Any

from kb4it.core import trace
from kb4it.core.html import image_size, is_filename_alt, resolve_src
from kb4it.core.files import prune_tree, sync_file
from kb4it.core.thumbs import SITE_FOLDER, make_thumbnail
from kb4it.services.themekit.media import MediaData, media_data, render_media_page
from kb4it.services.themekit.host import ThemeHost
from kb4it.core.log import q

FRONTMATTER = re.compile(r'\A---\n.*?\n---[ \t]*\n?', re.DOTALL)
FENCED = re.compile(r'^ {0,3}(```|~~~).*?^ {0,3}\1[^\n]*$', re.MULTILINE | re.DOTALL)
CODE_SPAN = re.compile(r'(`+).+?\1', re.DOTALL)
# ![alt](src "title") and ![alt](<src with spaces>)
MD_IMAGE = re.compile(r'!\[([^\]]*)\]\(\s*(?:<([^>]+)>|([^)\s]+))(?:\s+["\'(][^)]*)?\)')
# ![alt][ref], ![alt][] and the [ref]: src definitions they point to
MD_IMAGE_REF = re.compile(r'!\[([^\]]*)\]\[([^\]]*)\]')
MD_REF_DEF = re.compile(r'^ {0,3}\[([^\]]+)\]:\s*<?([^\s>]+)>?', re.MULTILINE)
HTML_IMG = re.compile(r'<img\b[^>]*>', re.IGNORECASE)
HTML_ATTR = re.compile(r'\b(src|alt)\s*=\s*(?:"([^"]*)"|\'([^\']*)\')', re.IGNORECASE)

def document_images(text: str) -> list[tuple[str, str]]:
    """Return [(src, alt), ...] of the images a Markdown document shows, in order, each src once.

    Images inside fenced code blocks and code spans are examples, not images, and are left out.
    """
    body = FRONTMATTER.sub('', text.replace('\r\n', '\n'), count=1)
    body = CODE_SPAN.sub('', FENCED.sub('', body))
    refs = {name.strip().lower(): src for name, src in MD_REF_DEF.findall(body)}
    found = []
    for match in MD_IMAGE.finditer(body):
        found.append((match.start(), match.group(2) or match.group(3), match.group(1)))
    for match in MD_IMAGE_REF.finditer(body):
        alt, name = match.group(1), match.group(2) or match.group(1)
        src = refs.get(name.strip().lower())
        if src:
            found.append((match.start(), src, alt))
    for match in HTML_IMG.finditer(body):
        attrs = {m.group(1).lower(): unescape(m.group(2) if m.group(2) is not None else m.group(3))
                 for m in HTML_ATTR.finditer(match.group(0))}
        if attrs.get('src'):
            found.append((match.start(), attrs['src'], attrs.get('alt', '')))
    images, seen = [], set()
    for _pos, src, alt in sorted(found, key=lambda item: item[0]):
        src = src.strip()
        if src and src not in seen:
            seen.add(src)
            images.append((src, alt.strip()))
    return images


class GalleryMixin(ThemeHost):
    """The Gallery page: property buttons, a value chooser, a masonry grid of thumbnails, a lightbox."""

    def gallery_thumb_dir(self) -> str:
        """Thumbnails made by earlier builds: <repo>/var/thumbs."""
        return os.path.join(os.path.dirname(self.srvbes.get_path('db')), 'thumbs')

    def gallery_image(self, src: str, local: str | None) -> dict[str, Any]:
        """The entry of one image: what the grid shows (a thumbnail or the original) and its size."""
        entry = {'src': src, 'thumb': src, 'w': 0, 'h': 0}
        if local is None:
            return entry  # a remote image: shown as it is, sized by the browser
        made = make_thumbnail(local, self.gallery_thumb_dir())
        if made:
            name, width, height = made
            self._gallery_thumbs.add(name)
            entry.update(thumb=f'{SITE_FOLDER}/{name}'.replace(os.sep, '/'), w=width, h=height)
        else:
            size = image_size(local)
            if size:
                entry.update(w=size[0], h=size[1])
        return entry

    def gallery_items(self, doc_id: str) -> list[dict[str, Any]]:
        """The images one document shows, each with its thumbnail, size and caption."""
        source_dir = self.srvbes.get_path('source')
        try:
            with open(os.path.join(source_dir, doc_id), encoding='utf-8') as fh:
                text = fh.read()
        except OSError:
            return []
        images = []
        for src, alt in document_images(text):
            local = resolve_src(src, source_dir)
            if local is not None and not os.path.isfile(local):
                continue  # the document page shows the placeholder and logs IMAGE_MISSING
            images.append(dict(self.gallery_image(src, local), caption='' if is_filename_alt(alt, src) else alt))
        return images

    def gallery_data(self) -> MediaData:
        """Return the documents with images, newest first, their images and the filters they can be narrowed by."""
        self._gallery_thumbs: set[str] = set()
        return media_data(self, self.gallery_items)

    def build_page_gallery(self) -> None:
        """The Gallery page: no image at first; the property buttons on the right choose which ones to show."""
        with trace.span('gallery'):
            data = self.gallery_data()
        render_media_page(self, 'gallery', 'Gallery', 'image', data)
        docs, items, _filters = data
        self.log.info(f"[THEME] GALLERY images={len(items)} docs={len(docs)} thumbs={len(self._gallery_thumbs)}")

    def deploy_gallery_thumbs(self) -> None:
        """Copy the thumbnails the Gallery uses into the site and drop the others, there and in var/thumbs."""
        used = getattr(self, '_gallery_thumbs', None)
        if used is None:
            return
        cache = self.gallery_thumb_dir()
        dest = os.path.join(self.srvbes.get_path('target'), SITE_FOLDER)
        with trace.span('gallery_thumbs'):
            copied = 0
            for name in sorted(used):
                os.makedirs(dest, exist_ok=True)
                copied += sync_file(os.path.join(cache, name), os.path.join(dest, name))
            deleted = prune_tree(dest, {os.path.join(dest, name) for name in used})
            prune_tree(cache, {os.path.join(cache, name) for name in used})
        self.log.info(f"[THEME] GALLERY_THUMBS used={len(used)} copied={q(copied)} deleted={q(deleted)}")

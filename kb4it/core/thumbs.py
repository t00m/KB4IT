"""techdoc thumbnails: small WebP copies of the document images for the Gallery page, kept between builds."""

import os

from PIL import Image, ImageOps, UnidentifiedImageError

from kb4it.core.util import get_hash_from_content

# Width of a thumbnail in pixels: twice the width of a gallery column, for sharp screens.
THUMB_WIDTH = 480
THUMB_QUALITY = 80

# Formats Pillow cannot make a smaller picture of; the original is used.
KEEP_ORIGINAL = ('.svg', '.svgz')

# Thumbnails live in this folder of the site, next to the pages.
SITE_FOLDER = os.path.join('resources', 'kb4it-thumbs')


def thumb_name(path, width=THUMB_WIDTH):
    """The cache name of the thumbnail of path: changes with the file's size, time and the thumbnail width."""
    stat = os.stat(path)
    key = f'{os.path.abspath(path)}|{stat.st_size}|{stat.st_mtime_ns}|{width}|{THUMB_QUALITY}'
    return get_hash_from_content(key)[:24] + '.webp'


def make_thumbnail(path, cache_dir, width=THUMB_WIDTH):
    """Return (file name, width, height) of the thumbnail of path in cache_dir, making it when missing.

    Return None when the original should be shown instead: a vector image, an image no wider than
    the thumbnail, or a file Pillow cannot read. A thumbnail made by an earlier build is reused.
    """
    if path.lower().endswith(KEEP_ORIGINAL):
        return None
    name = thumb_name(path, width)
    dest = os.path.join(cache_dir, name)
    if os.path.isfile(dest):
        try:
            with Image.open(dest) as done:
                return name, done.width, done.height
        except (OSError, UnidentifiedImageError):
            os.unlink(dest)  # a broken file from an interrupted build: make it again
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            if img.width <= width:
                return None
            height = max(1, round(img.height * width / img.width))
            img = img.convert('RGBA' if img.mode in ('RGBA', 'LA', 'PA') or 'transparency' in img.info else 'RGB')
            thumb = img.resize((width, height), Image.LANCZOS)
            os.makedirs(cache_dir, exist_ok=True)
            tmp = dest + '.tmp'
            thumb.save(tmp, 'WEBP', quality=THUMB_QUALITY, method=4)
            os.replace(tmp, dest)
            return name, width, height
    except (OSError, UnidentifiedImageError, ValueError, Image.DecompressionBombError):
        return None

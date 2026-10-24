"""techdoc media: image sizes and the rewrite of the images of a document body."""

import os
import re
import struct
from urllib.parse import unquote

# Bytes read from an image file to find its size.
HEADER_BYTES = 65536

# JPEG start-of-frame markers; C4, C8 and CC are other segments.
JPEG_SOF = {m for m in range(0xC0, 0xD0) if m not in (0xC4, 0xC8, 0xCC)}

SVG_TAG = re.compile(rb"<svg\b[^>]*>", re.IGNORECASE)
SVG_LENGTH = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:px)?\s*$")


def _svg_attr(tag, name):
    # The value of one attribute of the root <svg> tag, or None.
    match = re.search(rb'\s' + name.encode() + rb'\s*=\s*["\']([^"\']*)["\']', tag)
    return match.group(1).decode('utf-8', 'replace') if match else None


def _svg_size(data):
    tag = SVG_TAG.search(data)
    if not tag:
        return None
    tag = tag.group(0)
    width, height = _svg_attr(tag, 'width'), _svg_attr(tag, 'height')
    if width and height:
        w, h = SVG_LENGTH.match(width), SVG_LENGTH.match(height)
        if w and h:
            return round(float(w.group(1))), round(float(h.group(1)))
    box = _svg_attr(tag, 'viewBox')
    if box:
        parts = box.replace(',', ' ').split()
        if len(parts) == 4:
            try:
                return round(float(parts[2])), round(float(parts[3]))
            except ValueError:
                return None
    return None


def _jpeg_size(data):
    pos = 2
    while pos + 9 <= len(data):
        if data[pos] != 0xFF:
            return None
        marker = data[pos + 1]
        if marker == 0xFF:
            pos += 1
            continue
        length = struct.unpack('>H', data[pos + 2:pos + 4])[0]
        if marker in JPEG_SOF:
            height, width = struct.unpack('>HH', data[pos + 5:pos + 9])
            return width, height
        pos += 2 + length
    return None


def image_size(path):
    """Return (width, height) of a PNG, JPEG, GIF or SVG file, or None."""
    try:
        with open(path, 'rb') as fh:
            data = fh.read(HEADER_BYTES)
    except OSError:
        return None
    try:
        if data.startswith(b'\x89PNG\r\n\x1a\n') and data[12:16] == b'IHDR':
            return struct.unpack('>II', data[16:24])
        if data.startswith((b'GIF87a', b'GIF89a')):
            return struct.unpack('<HH', data[6:10])
        if data.startswith(b'\xff\xd8'):
            return _jpeg_size(data)
        if SVG_TAG.search(data):
            return _svg_size(data)
    except struct.error:
        return None
    return None


def is_filename_alt(alt, src):
    """Return True when an alt text looks like a file name rather than a caption."""
    alt = (alt or '').strip()
    if not alt:
        return True
    stem = os.path.splitext(os.path.basename(unquote(src or '')))[0]
    if alt.lower() == stem.lower():
        return True
    return ' ' not in alt and bool(re.search(r'[\d_-]', alt))


def resolve_src(src, source_dir):
    """Return the local file a relative image src points to, or None for remote and absolute ones."""
    src = (src or '').strip()
    if not src or src.startswith(('/', 'data:')) or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', src):
        return None
    return os.path.join(source_dir, unquote(src.split('#')[0].split('?')[0]))

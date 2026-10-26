"""techdoc media: image sizes and the rewrite of the images of a document body."""

import os
import re
import struct
from html import escape
from urllib.parse import unquote

from lxml import etree
from lxml import html as lhtml

# Bytes read from an image file to find its size.
HEADER_BYTES = 65536

# Images narrower than this stay inline, without figure or frame.
MIN_FIGURE_WIDTH = 64

# Figures in a row from which a gallery is built.
GALLERY_MIN = 3

GALLERY_CLASS = 'kb-gallery uk-child-width-1-2 uk-child-width-1-3@m'

# Alt texts that name the kind of picture, not what it shows; they give no caption.
GENERIC_ALTS = {'image', 'img', 'picture', 'pic', 'photo', 'screenshot', 'screen capture', 'screen shot', 'capture', 'untitled'}

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
    if not alt or alt.lower() in GENERIC_ALTS:
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
    return os.path.normpath(os.path.join(source_dir, unquote(src.split('#')[0].split('?')[0])))


def _blank(text):
    return not (text or '').strip()


def _inside_link(img):
    return any(el.tag == 'a' for el in img.iterancestors())


def _images_only(p):
    # True when a paragraph holds images (and line breaks) and no text.
    return (p.tag == 'p' and _blank(p.text)
            and all(child.tag in ('img', 'br') and _blank(child.tail) for child in p))


def _placeholder(tag, src):
    node = etree.Element(tag)
    node.set('class', 'kb-figure kb-img-missing' if tag == 'figure' else 'kb-img-missing')
    node.text = 'Image missing: '
    etree.SubElement(node, 'code').text = src
    return node


def _figure(img, src, caption, number):
    figure = etree.Element('figure')
    figure.set('class', 'kb-figure')
    link = etree.SubElement(figure, 'a')
    link.set('class', 'kb-zoom')
    link.set('href', src)
    link.set('data-caption', caption)
    img.tail = None
    img.set('class', ' '.join(filter(None, [img.get('class'), 'kb-shot'])))
    link.append(img)
    if number:
        etree.SubElement(figure, 'figcaption').text = f'Figure {number}. {caption}'
    return figure


def _replace(old, new_nodes):
    # Put new_nodes where old was, keeping the text that followed it.
    parent = old.getparent()
    index = parent.index(old)
    tail = old.tail
    old.tail = None
    parent.remove(old)
    for offset, node in enumerate(new_nodes):
        parent.insert(index + offset, node)
    new_nodes[-1].tail = tail


def _make_galleries(root):
    # Runs of three or more figures with only whitespace between them become one gallery.
    children = list(root)
    run = []
    for child in children + [None]:
        is_figure = (child is not None and child.tag == 'figure' and child.get('class') == 'kb-figure'
                     and (not run or _blank(run[-1].tail)))
        if is_figure:
            run.append(child)
            continue
        if len(run) >= GALLERY_MIN:
            gallery = etree.Element('div')
            gallery.set('class', GALLERY_CLASS)
            gallery.set('data-uk-grid', 'masonry: false')
            tail = run[-1].tail
            root.insert(root.index(run[0]), gallery)
            for figure in run:
                cell = etree.SubElement(gallery, 'div')
                figure.tail = None
                cell.append(figure)
            gallery.tail = tail
        run = [child] if child is not None and child.tag == 'figure' and child.get('class') == 'kb-figure' else []


def enhance_images(html, source_dir):
    """Rewrite the images of a body: size, lazy loading, figures, lightbox links, galleries, missing files.

    Returns the new HTML and the src of every missing local image, in document order.
    """
    if '<img' not in html.lower():
        return html, []
    root = lhtml.fragment_fromstring(html, create_parent='div')
    missing = []
    number = 0
    done = []  # paragraphs already turned into figures; kept alive so their identity is stable
    for position, img in enumerate(list(root.iter('img'))):
        src = img.get('src', '')
        local = resolve_src(src, source_dir)
        exists = local is None or os.path.isfile(local)
        size = image_size(local) if local and exists else None
        if size and not (img.get('width') and img.get('height')):
            img.set('width', str(size[0]))
            img.set('height', str(size[1]))
        if position > 0:
            img.set('loading', 'lazy')
            img.set('decoding', 'async')
        parent = img.getparent()
        block = parent if parent is root else (parent if _images_only(parent) else None)
        if block is not None and block is not root and any(block is d for d in done):
            continue
        small = [i for i in ([img] if block is root else block.iter('img') if block is not None else [])
                 if _narrow(i, source_dir)]
        if _inside_link(img) or block is None or small:
            if not exists:
                missing.append(src)
                _replace(img, [_placeholder('span', src)])
            continue
        images = [img] if block is root else list(block.iter('img'))
        # A bare image is replaced by itself; a paragraph of images by the paragraph.
        target = img if block is root else block
        anchor = etree.Element('span')
        target.addprevious(anchor)
        anchor.tail, target.tail = target.tail, None
        nodes = []
        for item in images:
            item_src = item.get('src', '')
            item_local = resolve_src(item_src, source_dir)
            if item_local is not None and not os.path.isfile(item_local):
                missing.append(item_src)
                nodes.append(_placeholder('figure', item_src))
                continue
            alt = (item.get('alt') or '').strip()
            captioned = not is_filename_alt(alt, item_src)
            if captioned:
                number += 1
            nodes.append(_figure(item, item_src, alt, number if captioned else 0))
        if block is not root:
            # The images moved into their figures; the emptied paragraph goes.
            block.getparent().remove(block)
            done.append(block)
        elif img.getparent() is root:
            # A missing bare image was not moved into a figure.
            root.remove(img)
        _replace(anchor, nodes)
    _make_galleries(root)
    out = escape(root.text, quote=False) if root.text else ''
    return out + ''.join(lhtml.tostring(child, encoding='unicode') for child in root), missing


def _narrow(img, source_dir):
    # True when the image is known to be narrower than MIN_FIGURE_WIDTH.
    width = img.get('width')
    if not width:
        local = resolve_src(img.get('src', ''), source_dir)
        size = image_size(local) if local else None
        width = size[0] if size else None
    try:
        return width is not None and int(width) < MIN_FIGURE_WIDTH
    except ValueError:
        return False

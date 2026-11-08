"""Rewrites of a compiled document body, for BaseTheme.body_transforms().

Each takes the HTML of the body and returns it changed:

- enhance_images(html, source_dir): size, lazy loading and captions of images.
- enhance_blocks(html, table_filter=True): code blocks with copy buttons, wide tables, notes.
- lazy_images(root) and wrap_code(pre, wrapper_class, copy_class): the lxml helpers of the two above.
"""

from kb4it.core.html import enhance_blocks, enhance_images, lazy_images, wrap_code

__all__ = ["enhance_blocks", "enhance_images", "lazy_images", "wrap_code"]

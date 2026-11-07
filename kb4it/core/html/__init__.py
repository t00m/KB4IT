"""Rewrites of a compiled document body that any theme can use."""

from kb4it.core.html.blocks import FOLDED_CODE_LINES, LONG_CODE_LINES, STICKY_TABLE_ROWS, enhance_blocks, lazy_images, wrap_code
from kb4it.core.html.images import enhance_images, image_size, is_filename_alt, resolve_src

__all__ = ["FOLDED_CODE_LINES", "LONG_CODE_LINES", "STICKY_TABLE_ROWS", "enhance_blocks", "enhance_images", "image_size",
           "is_filename_alt", "lazy_images", "resolve_src", "wrap_code"]

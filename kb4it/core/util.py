#!/usr/bin/python

"""
Utils functions used along the project.

Dates, documents and files have their own modules (kb4it.core.dates, documents and
files); their names are imported here too, since themes, hooks and templates import
them from kb4it.core.util.

# File: util.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: Generic functions module
"""

import math
import multiprocessing
import operator
import os
import re
import unicodedata
from functools import wraps
from typing import Any

from kb4it.core import trace
from kb4it.core.dates import (
    DateCache,
    get_day,
    get_human_datetime,
    get_human_datetime_day,
    get_human_datetime_month,
    get_human_datetime_year,
    get_month,
    get_timestamp_yyyymmdd,
    get_year,
    guess_datetime,
    kb4it_timestamp,
    log_timestamp,
    now,
    string_timestamp,
)
from kb4it.core.documents import (
    extract_sections_from_md,
    fences_in_blocks,
    first_heading,
    get_document_attributes,
    get_hash_from_body,
    get_markdown_attributes,
    raw_script_lines,
    strip_first_heading,
)
from kb4it.core.files import (
    SOURCE_ENCODING,
    copy_docs,
    copydir,
    delete_files,
    delete_target_contents,
    get_hash_from_content,
    get_hash_from_dict,
    get_hash_from_file,
    get_hash_from_list,
    get_source_docs,
    json_load,
    json_save,
    quarantine,
    tree_hash,
    valid_filename,
)
from kb4it.core.log import get_logger

log = get_logger("Util")

# Every public name of this module before the split; the moved ones are imported above.
__all__ = [
    "SOURCE_ENCODING",
    "SOURCE_EXT_RE",
    "WINDOWS_RESERVED_NAMES",
    "DateCache",
    "copy_docs",
    "copydir",
    "delete_files",
    "delete_target_contents",
    "ellipsize_text",
    "extract_sections_from_md",
    "fences_in_blocks",
    "first_heading",
    "get_day",
    "get_default_workers",
    "get_document_attributes",
    "get_font_size",
    "get_hash_from_body",
    "get_hash_from_content",
    "get_hash_from_dict",
    "get_hash_from_file",
    "get_hash_from_list",
    "get_human_datetime",
    "get_human_datetime_day",
    "get_human_datetime_month",
    "get_human_datetime_year",
    "get_markdown_attributes",
    "get_month",
    "get_source_docs",
    "get_timestamp_yyyymmdd",
    "get_year",
    "guess_datetime",
    "html_id_for",
    "human_size",
    "is_windows_reserved",
    "json_load",
    "json_save",
    "kb4it_timestamp",
    "log_timestamp",
    "now",
    "page_name_clashes",
    "quarantine",
    "raw_script_lines",
    "set_max_frequency",
    "slugify",
    "sort_dictionary",
    "source_ext",
    "string_timestamp",
    "strip_first_heading",
    "timeit",
    "tree_hash",
    "valid_filename",
]


SOURCE_EXT_RE = re.compile(r"\.(md|markdown)$", re.IGNORECASE)


def html_id_for(doc_id: str) -> str:
    """Return the HTML filename corresponding to a source docId."""
    return SOURCE_EXT_RE.sub(".html", doc_id)


WINDOWS_RESERVED_NAMES = frozenset(
    ["CON", "PRN", "AUX", "NUL"] + [f"COM{n}" for n in range(1, 10)] + [f"LPT{n}" for n in range(1, 10)])


def is_windows_reserved(filename: str) -> bool:
    """True when Windows cannot create a file with this name (CON, NUL, COM1, ... with any extension)."""
    return os.path.basename(filename).split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES


def page_name_clashes(doc_ids) -> list[tuple[str, str]]:
    """Pairs of documents whose pages differ only by letter case or extension (Foo.md, foo.markdown).

    Their pages overwrite each other on macOS and Windows, whose file systems ignore case.
    """
    seen, clashes = {}, []
    for doc_id in sorted(doc_ids):
        page = html_id_for(doc_id).lower()
        if page in seen:
            clashes.append((seen[page], doc_id))
        else:
            seen[page] = doc_id
    return clashes


def source_ext(doc_id: str) -> str:
    """Return the source extension ('md' or 'markdown') from a docId, or '' if none."""
    m = SOURCE_EXT_RE.search(doc_id)
    return m.group(1).lower() if m else ""


def timeit(func):
    """Record the time a method takes in the performance trace (kb4it build --trace)."""

    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        with trace.span(func.__name__):
            return func(*args, **kwargs)

    return timeit_wrapper


def get_default_workers():
    """Calculate default number or workers.

    Workers = Number of CPU / 2
    Minimum workers = 1
    """
    ncpu = multiprocessing.cpu_count()
    workers = ncpu / 2
    return math.ceil(workers)


def set_max_frequency(dkeyurl: dict[str, Any]) -> int:
    """Calculate and set max frequency."""
    max_frequency = 1
    for keyword in dkeyurl:
        cur_frequency = len(dkeyurl[keyword])
        max_frequency = max(max_frequency, cur_frequency)

    return max_frequency


def get_font_size(frequency, max_frequency):
    """Get font size for a word based in its frequency."""
    proportion = int(math.log((frequency * 100) / max_frequency))

    if max_frequency == 1:
        size = 10
    else:
        if proportion < 1:
            size = 8
        elif proportion in range(1, 2):
            size = 10
        elif proportion in range(2, 3):
            size = 18
        elif proportion in range(3, 4):
            size = 36
        elif proportion in range(4, 5):
            size = 72
        else:
            size = 72

    return size


def slugify(text: str) -> str:
    """Return a lowercase, dash separated version of *text*.

    Accents are stripped, any run of non alphanumeric characters becomes a
    single dash and leading/trailing dashes are removed.
    >>> slugify("SAP Notes Knowledge Base")
    'sap-notes-knowledge-base'
    """
    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def human_size(nbytes: float) -> str:
    """Return a human readable representation of a size in bytes."""
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024:
            return f"{nbytes:.0f} {unit}" if unit == "B" else f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def sort_dictionary(adict, reverse=True):
    """Return a reversed sorted list from a dictionary."""
    return sorted(adict.items(), key=operator.itemgetter(1), reverse=reverse)


def ellipsize_text(text: str, max_length: int = 70):
    """Elipsize a given text given a max length."""
    if len(text) <= max_length:
        return text

    # Number of characters to show on each side of the ellipsis
    split_length = (max_length - 3) // 2

    # Handle odd max_length cases
    start = text[:split_length]
    end = text[-split_length:] if max_length % 2 == 0 else text[-split_length - 1:]

    return f"{start}...{end}"

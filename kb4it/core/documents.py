"""
Document helpers: frontmatter, title and body of a Markdown document.

# Author: Tomás Vírseda
# License: GPL v3
"""

import hashlib
import os
import re

import yaml

from kb4it.core.files import SOURCE_ENCODING, valid_filename
from kb4it.core.log import get_logger

log = get_logger("Util")

def extract_sections_from_md(file_path: str) -> dict:
    """Extract H2 sections from a Markdown file.

    Returns a dict mapping section name -> {start, end} (1-indexed line numbers).
    """
    sections = []

    with open(file_path, "r", encoding=SOURCE_ENCODING) as fh:
        lines = fh.readlines()

    current_section = None
    start = None

    for i, line in enumerate(lines, 1):
        line = line.rstrip("\n")
        if line.startswith("## ") and not line.startswith("###"):
            if current_section:
                sections.append(
                    {"name": current_section, "start": start, "end": i - 1})
            current_section = line[3:].strip()
            start = i

    if current_section:
        sections.append(
            {"name": current_section, "start": start, "end": len(lines)})

    return {
        s["name"]: {"start": s["start"], "end": s["end"]}
        for s in sections
    }


_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


_H1_RE = re.compile(r"^#[ \t]+(\S.*?)[ \t]*$")


def first_heading(body: str):
    """Return (title, line index) of the first level-1 heading of body, or (None, None).

    Lines inside fenced code blocks (three or more backticks or tildes, indented up
    to three spaces) and indented code blocks are skipped, so a "# comment" in a
    shell or Python block is never taken for the title.
    """
    fence = None  # the opening run of the fenced block we are in
    prev_blank = True
    in_indented = False
    for index, line in enumerate(body.splitlines()):
        if fence is not None:
            stripped = line.strip()
            if stripped.startswith(fence) and set(stripped) == {fence[0]}:
                fence = None
            continue
        match = _FENCE_RE.match(line)
        if match:
            fence = match.group(1)
            prev_blank = in_indented = False
            continue
        blank = not line.strip()
        if not blank and line.startswith(("    ", "\t")) and (prev_blank or in_indented):
            in_indented = True
            prev_blank = False
            continue
        if not blank:
            in_indented = False
        prev_blank = blank
        heading = _H1_RE.match(line)
        if heading:
            return heading.group(1), index
    return None, None


def fences_in_blocks(body: str) -> list:
    """Line numbers (1-based) of code fences indented four spaces or a tab, outside top-level fences.

    python-markdown's fenced_code only sees fences at the start of a line, so such a
    fence (inside an admonition or a list item) renders as inline code unless
    pymdownx.superfences is enabled.
    """
    found = []
    fence = None
    for number, line in enumerate(body.splitlines(), start=1):
        if fence is not None:
            stripped = line.strip()
            if stripped.startswith(fence) and set(stripped) == {fence[0]}:
                fence = None
            continue
        match = _FENCE_RE.match(line)
        if match:
            fence = match.group(1)
        elif re.match(r"^(?: {4,}|\t)\s*(?:`{3,}|~{3,})", line):
            found.append(number)
    return found


_RAW_SCRIPT_RE = re.compile(r"<script\b|<[a-zA-Z][^>]*\son[a-zA-Z]+\s*=", re.IGNORECASE)


def raw_script_lines(body: str) -> list:
    """Line numbers (1-based) with a <script> element or an on*= handler outside code.

    Fenced and indented code blocks and `inline code` are skipped: there the text
    is shown, not run.
    """
    found = []
    fence = None
    prev_blank = True
    in_indented = False
    for number, line in enumerate(body.splitlines(), start=1):
        if fence is not None:
            stripped = line.strip()
            if stripped.startswith(fence) and set(stripped) == {fence[0]}:
                fence = None
            continue
        match = _FENCE_RE.match(line)
        if match:
            fence = match.group(1)
            prev_blank = in_indented = False
            continue
        blank = not line.strip()
        if not blank and line.startswith(("    ", "\t")) and (prev_blank or in_indented):
            in_indented = True
            prev_blank = False
            continue
        in_indented = False if not blank else in_indented
        prev_blank = blank
        if _RAW_SCRIPT_RE.search(re.sub(r"(`+).*?\1", "", line)):
            found.append(number)
    return found


def strip_first_heading(body: str) -> str:
    """Return body without the line of its first level-1 heading (see first_heading)."""
    _title, index = first_heading(body)
    if index is None:
        return body
    lines = body.splitlines(keepends=True)
    del lines[index]
    return "".join(lines)


def get_hash_from_body(path):
    """Get blake2b hash for the document body.

    Body is the content after the closing YAML frontmatter delimiter, with the
    leading H1 heading stripped so title renames don't invalidate the cache.
    """
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding=SOURCE_ENCODING) as fin:
        content = fin.read()
    end = content.find("\n---", 3)
    if end >= 0:
        body = strip_first_heading(content[end + 4:].lstrip("\n"))
    else:
        body = content
    return hashlib.blake2b(body.encode("utf-8")).hexdigest()


def get_markdown_attributes(docpath: str):
    """Get metadata from a Markdown document's YAML frontmatter."""
    basename = os.path.basename(docpath)
    keys = {}

    try:
        with open(docpath, "r", encoding=SOURCE_ENCODING) as fh:
            content = fh.read()

        if not content.startswith("---"):
            log.error(f"[UTIL] DOC_INVALID doc={basename} reason=missing_frontmatter")
            return {}, False, "missing_frontmatter"

        end = content.find("\n---", 3)
        if end < 0:
            log.error(f"[UTIL] DOC_INVALID doc={basename} reason=missing_frontmatter_close")
            return {}, False, "missing_frontmatter_close"

        fm_text = content[3:end].strip()
        body = content[end + 4:].lstrip("\n")

        fm = yaml.safe_load(fm_text) if fm_text else {}
        if not isinstance(fm, dict):
            log.error(f"[UTIL] DOC_INVALID doc={basename} reason=invalid_frontmatter")
            return {}, False, "invalid_frontmatter"

        # Title comes from the first # heading in the body
        title, _index = first_heading(body)
        if title is None:
            log.error(f"[UTIL] DOC_INVALID doc={basename} reason=missing_h1_title")
            return {}, False, "missing_h1_title"

        keys["Title"] = [title.strip()]

        if "title" in fm or "Title" in fm:
            log.warning(f"[UTIL] DOC_WARN doc={basename} reason=title_in_frontmatter_ignored")
            fm.pop("title", None)
            fm.pop("Title", None)

        for k, v in fm.items():
            if v is None:
                keys[k] = []
            elif isinstance(v, list):
                keys[k] = [str(i).strip() for i in v if i is not None]
            elif isinstance(v, str) and "," in v:
                keys[k] = [i.strip() for i in v.split(",")]
            else:
                keys[k] = [str(v).strip()]

        # Every property name and value becomes part of a page name; one that cleans to nothing
        # (such as "..." or "???") cannot, so the document is reported instead of breaking the site.
        for k, values in keys.items():
            if k == "Title":
                continue
            if not valid_filename(k):
                reason = f"bad_property_name key={k}"
            elif any(value and not valid_filename(value) for value in values):
                reason = f"bad_property_value key={k}"
            else:
                continue
            log.error(f"[UTIL] DOC_INVALID doc={basename} reason={reason}")
            return {}, False, reason

    except yaml.YAMLError as err:
        reason = "yaml_error"
        mark = getattr(err, "problem_mark", None)
        if mark is not None:
            # The mark counts from the stripped frontmatter; add the lines before it.
            raw = content[3:end]
            offset = content[:3 + len(raw) - len(raw.lstrip())].count("\n")
            reason += f" line={offset + mark.line + 1} col={mark.column + 1}"
        problem = getattr(err, "problem", None)
        if problem:
            reason += f" {problem}"
        log.error(f"[UTIL] DOC_INVALID doc={basename} reason={reason}")
        return {}, False, reason
    except Exception as err:
        log.error(f"[UTIL] DOC_INVALID doc={basename} reason=error error={err}")
        return {}, False, str(err)

    return keys, True, "Success"


def get_document_attributes(docpath: str):
    """Extract metadata from a Markdown document."""
    if docpath.endswith((".md", ".markdown")):
        return get_markdown_attributes(docpath)
    return {}, False, "unsupported_format"

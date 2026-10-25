"""
Document helpers: frontmatter, title and body of a Markdown document.

# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

import hashlib
import os
import re
from typing import Any

import yaml

from kb4it.core.files import SOURCE_ENCODING, valid_filename
from kb4it.core.log import get_logger

log = get_logger("Util")


class _FrontmatterLoader(yaml.SafeLoader):
    """SafeLoader that reads every plain value as written; only an empty value, null or ~ means none.

    YAML 1.1 reads yes and no as booleans, 0.10 as 0.1, 010 as 8, 12:30 as 750 and dates as dates,
    and str() then wrote something else than the author did ("Bookmark: Yes" made Bookmark_True.html).
    A header value is text, so the author's text is kept.
    """


_TYPED = {"tag:yaml.org,2002:bool", "tag:yaml.org,2002:int", "tag:yaml.org,2002:float",
          "tag:yaml.org,2002:timestamp"}
_FrontmatterLoader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in resolvers if tag not in _TYPED]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}

YES_VALUES = ("yes", "true", "on")


def load_frontmatter(text: str) -> Any:
    """Read a frontmatter block as the build does: safe YAML, every plain value kept as text."""
    return yaml.load(text, Loader=_FrontmatterLoader)  # a SafeLoader subclass: safe


def joined_value(values: list[str] | None) -> str:
    """Join the values of a free-text key, such as Summary, that the frontmatter parser split on commas."""
    return ", ".join(v for v in values or [] if v)


def is_yes(value: Any) -> bool:
    """True for a header value that means yes (Yes, true, On, in any case), as Bookmark uses it."""
    return str(value).strip().lower() in YES_VALUES


def extract_sections_from_md(file_path: str) -> dict[str, dict[str, int]]:
    """Extract H2 sections from a Markdown file.

    Returns a dict mapping section name -> {start, end} (1-indexed line numbers).
    """
    sections: list[dict[str, Any]] = []

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


def first_heading(body: str) -> tuple[str | None, int | None]:
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


def fences_in_blocks(body: str) -> list[int]:
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


def raw_script_lines(body: str) -> list[int]:
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


def get_hash_from_body(path: str, content: str | None = None) -> str | None:
    """Get blake2b hash for the document body.

    Body is the content after the closing YAML frontmatter delimiter, with the
    leading H1 heading stripped so title renames don't invalidate the cache.
    Pass the already-read text as content to avoid opening the file again.
    """
    if content is None:
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


def parse_markdown_attributes(content: str, basename: str) -> tuple[dict[str, list[str]], bool, str, bool]:
    """Parse a Markdown header from text that is already in memory.

    Returns keys, valid, reason and warned. warned is true when the frontmatter
    carried a Title key that was ignored, so a caller that caches the result can
    parse the document again and log the warning on every build.
    """
    keys: dict[str, list[str]] = {}
    warned = False

    try:
        if not content.startswith("---"):
            log.error(f"[UTIL] DOC_INVALID doc={basename} reason=missing_frontmatter")
            return {}, False, "missing_frontmatter", False

        end = content.find("\n---", 3)
        if end < 0:
            log.error(f"[UTIL] DOC_INVALID doc={basename} reason=missing_frontmatter_close")
            return {}, False, "missing_frontmatter_close", False

        fm_text = content[3:end].strip()
        body = content[end + 4:].lstrip("\n")

        fm = load_frontmatter(fm_text) if fm_text else {}
        if not isinstance(fm, dict):
            log.error(f"[UTIL] DOC_INVALID doc={basename} reason=invalid_frontmatter")
            return {}, False, "invalid_frontmatter", False

        # Title comes from the first # heading in the body
        title, _index = first_heading(body)
        if title is None:
            log.error(f"[UTIL] DOC_INVALID doc={basename} reason=missing_h1_title")
            return {}, False, "missing_h1_title", False

        keys["Title"] = [title.strip()]

        if "title" in fm or "Title" in fm:
            log.warning(f"[UTIL] DOC_WARN doc={basename} reason=title_in_frontmatter_ignored")
            warned = True
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
            # A value repeated in one key is kept once, in its first place.
            keys[k] = list(dict.fromkeys(keys[k]))

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
            return {}, False, reason, False

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
        return {}, False, reason, False
    except Exception as err:
        log.error(f"[UTIL] DOC_INVALID doc={basename} reason=error error={err}")
        return {}, False, str(err), False

    return keys, True, "Success", warned


def get_markdown_attributes(docpath: str) -> tuple[dict[str, list[str]], bool, str]:
    """Get metadata from a Markdown document's YAML frontmatter."""
    basename = os.path.basename(docpath)
    try:
        with open(docpath, "r", encoding=SOURCE_ENCODING) as fh:
            content = fh.read()
    except Exception as err:
        log.error(f"[UTIL] DOC_INVALID doc={basename} reason=error error={err}")
        return {}, False, str(err)
    keys, valid, reason, _warned = parse_markdown_attributes(content, basename)
    return keys, valid, reason


def get_document_attributes(docpath: str) -> tuple[dict[str, list[str]], bool, str]:
    """Extract metadata from a Markdown document."""
    if docpath.endswith((".md", ".markdown")):
        return get_markdown_attributes(docpath)
    return {}, False, "unsupported_format"

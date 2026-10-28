"""Nested lists indented by two or three spaces, as most editors and GitHub write them.

python-markdown nests a list item only when it is indented by four spaces; with two,
the item silently joins its parent's list. `ListIndentExtension` rewrites, before the
block parser runs, every list that nests an item by fewer than four spaces so that
each level sits four spaces deeper than its parent, and moves the text, code and
notes of each item with it. A list nested by four spaces is never touched, so a
document written for python-markdown renders exactly as before.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from markdown import Markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

# A list item: indentation, marker, the spaces after it. "- [ ] task" is an item too.
ITEM_RE = re.compile(r"^( *)([*+-]|\d+[.)])( +|$)")
# A thematic break ("- - -", "***") is not an item.
HR_RE = re.compile(r"^ {0,3}([-*_])( *\1){2,} *$")
FENCE_RE = re.compile(r"^ *(`{3,}|~{3,})")
# python-markdown's indent: one nesting level, and the start of an indented code block.
TAB = 4


@dataclass
class _Item:
    """An open list item: where it starts and where its text starts, in the source and once moved."""

    src: int
    content: int
    dst: int


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _item(line: str) -> tuple[int, int] | None:
    """(indent, content column) of a list item line, or None."""
    match = ITEM_RE.match(line)
    if not match or HR_RE.match(line):
        return None
    spaces = len(match.group(3))
    # Five or more spaces after the marker start indented code; the text then starts after one.
    return len(match.group(1)), match.end(2) + (spaces if 0 < spaces <= TAB else 1)


def _closes(match: re.Match[str] | None, fence: str) -> bool:
    """True when `match` (a fence line) closes `fence`: same character, at least as long."""
    if match is None:
        return False
    mark = match.group(1)
    return mark[0] == fence[0] and len(mark) >= len(fence)


def _list_end(lines: list[str], start: int) -> int:
    """Index after the list that starts at `start`: it ends at an unindented line after a blank one."""
    fence = ''
    for index in range(start + 1, len(lines)):
        line = lines[index]
        match = FENCE_RE.match(line)
        if fence:
            fence = '' if _closes(match, fence) else fence
        elif match:
            fence = match.group(1)
        elif line.strip() and _indent(line) == 0 and _item(line) is None and not lines[index - 1].strip():
            return index
    return len(lines)


def _place(stack: list[int], indent: int) -> str:
    """Close the items an item at `indent` is not nested in; say whether it is a sibling, a child or a root."""
    while stack and indent < stack[-1]:
        stack.pop()
    if stack and indent < stack[-1] + 2:  # the same indent, or one space more
        return 'sibling'
    return 'child' if stack else 'root'


def _nests_short(block: list[str]) -> bool:
    """True when an item of the list is nested by fewer than four spaces."""
    parents: list[int] = []
    fence = ''
    for line in block:
        match = FENCE_RE.match(line)
        if fence:
            fence = '' if _closes(match, fence) else fence
            continue
        if match:
            fence = match.group(1)
            continue
        item = _item(line)
        if item is None:
            continue
        indent = item[0]
        place = _place(parents, indent)
        if place == 'child' and indent - parents[-1] < TAB:
            return True
        if place == 'sibling':
            parents.pop()
        parents.append(indent)
    return False


def _shift(line: str, delta: int) -> str:
    indent = _indent(line)
    return " " * max(0, indent + delta) + line[indent:]


def _rewrite(block: list[str]) -> list[str]:
    """Move every item of the list to python-markdown's four-space grid, with its content."""
    out: list[str] = []
    stack: list[_Item] = []
    fence, fence_delta = '', 0
    for line in block:
        match = FENCE_RE.match(line)
        if fence:
            out.append(_shift(line, fence_delta) if line.strip() else line)
            fence = '' if _closes(match, fence) else fence
            continue
        item = None if match else _item(line)
        if not line.strip():
            out.append(line)
        elif item is not None:
            indent, content = item
            sources = [entry.src for entry in stack]
            place = _place(sources, indent)
            del stack[len(sources):]
            if place == 'sibling':
                dst = stack.pop().dst
            elif place == 'child':
                dst = stack[-1].dst + TAB
            else:
                dst = indent
            stack.append(_Item(indent, content, dst))
            out.append(_shift(line, dst - indent))
        else:
            indent = _indent(line)
            owners = [entry for entry in stack if entry.content <= indent]
            if not owners:  # a lazy continuation line, as python-markdown reads it
                out.append(line)
                continue
            owner = owners[-1]
            del stack[stack.index(owner) + 1:]
            delta = owner.dst + TAB - owner.content
            out.append(_shift(line, delta))
            if match:
                fence, fence_delta = match.group(1), delta
    return out


def normalize_lists(lines: list[str]) -> list[str]:
    """Return `lines` with every list nested by two or three spaces moved to four."""
    out: list[str] = []
    index = 0
    fence = ''
    while index < len(lines):
        # Fenced code outside a list stays as it is; python-markdown stashes it first, but never rely on that.
        match = FENCE_RE.match(lines[index])
        if fence:
            fence = '' if _closes(match, fence) else fence
        elif match is not None:
            fence = match.group(1)
        if fence or match:
            out.append(lines[index])
            index += 1
            continue
        item = _item(lines[index])
        if item is None or item[0] >= TAB:
            out.append(lines[index])
            index += 1
            continue
        end = _list_end(lines, index)
        block = lines[index:end]
        out.extend(_rewrite(block) if _nests_short(block) else block)
        index = end
    return out


class _ListIndentPreprocessor(Preprocessor):
    def run(self, lines: list[str]) -> list[str]:
        return normalize_lists(lines)


class ListIndentExtension(Extension):
    """python-markdown extension: nested lists may be indented by two, three or four spaces."""

    def extendMarkdown(self, md: Markdown) -> None:
        # 15: after the tabs are expanded (30), the fences (25) and the raw HTML blocks (20) are stashed.
        md.preprocessors.register(_ListIndentPreprocessor(md), "kb4it_list_indent", 15)

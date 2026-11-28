"""
Widgets that let the user select text with the mouse.

Textual already selects text in Static, Label, Markdown and Log. RichLog and
DataTable draw their lines by hand, so they get no selection; the subclasses
here add it. Drag with the mouse to select, Ctrl+A to select all, Ctrl+C to copy.
"""

from __future__ import annotations

from rich.segment import Segment
from rich.style import Style
from textual.coordinate import Coordinate
from textual.selection import Selection
from textual.strip import Strip
from textual.widgets import DataTable, RichLog

# A cursor and hover location outside the table, so plain text has no highlight.
_NOWHERE = Coordinate(-1, -1)


def _highlight(strip: Strip, start: int, end: int, style: Style) -> Strip:
    """Paint cells [start, end) of a strip with the selection style; end -1 means to the end."""
    length = strip.cell_length
    end = length if end == -1 else min(end, length)
    start = max(0, min(start, length))
    if start >= end:
        return strip
    before, middle, after = strip.divide([start, end, length])
    middle = Strip(
        [Segment(text, (seg_style or Style()) + style, control) for text, seg_style, control in middle],
        middle.cell_length,
    )
    return Strip.join([before, middle, after])


def _selected(widget, strip: Strip, line: int, scroll_x: int) -> Strip:
    """Strip with the part of the selection on this content line painted."""
    selection = widget.text_selection
    if selection is None or (span := selection.get_span(line)) is None:
        return strip
    start, end = span
    style = widget.screen.get_component_rich_style("screen--selection")
    return _highlight(strip, start - scroll_x, -1 if end == -1 else end - scroll_x, style)


class SelectableRichLog(RichLog):
    """RichLog whose lines can be selected and copied."""

    def render_line(self, y: int) -> Strip:
        scroll_x, scroll_y = self.scroll_offset
        line = scroll_y + y
        strip = self._render_line(line, scroll_x, self.scrollable_content_region.width)
        strip = _selected(self, strip, line, scroll_x)
        # The offsets tell Textual which content cell sits under the mouse.
        return strip.apply_style(self.rich_style).apply_offsets(scroll_x, line)

    def get_selection(self, selection: Selection) -> tuple[str, str] | None:
        text = "\n".join(strip.text.rstrip() for strip in self.lines)
        return selection.extract(text), "\n"

    def selection_updated(self, selection: Selection | None) -> None:
        self._line_cache.clear()
        self.refresh()


class SelectableDataTable(DataTable):
    """DataTable whose cells can be selected and copied, header included.

    A click still moves the cursor; a drag selects text. Fixed columns are not supported.
    """

    ALLOW_SELECT = True

    def render_line(self, y: int) -> Strip:
        scroll_x, scroll_y = self.scroll_offset
        fixed_height = sum(self.get_row_height(self._row_locations.get_key(index))
                           for index in range(self.fixed_rows))
        if self.show_header:
            fixed_height += self.header_height
        line = y + scroll_y if y >= fixed_height else y
        strip = self._render_line(line, scroll_x, scroll_x + self.size.width, self.rich_style)
        strip = _selected(self, strip, line, scroll_x)
        return strip.apply_offsets(scroll_x, line)

    def _line_text(self, line: int) -> str:
        """Plain text of one table line at full width, without cursor or hover."""
        try:
            row_key, offset = self._get_offsets(line)
        except LookupError:
            return ""
        _fixed, scrollable = self._render_line_in_row(
            row_key, offset, Style(), cursor_location=_NOWHERE, hover_location=_NOWHERE)
        return "".join(segment.text for cell in scrollable for segment in cell).rstrip()

    def get_selection(self, selection: Selection) -> tuple[str, str] | None:
        total = self.virtual_size.height
        text = "\n".join(self._line_text(line) for line in range(total))
        return selection.extract(text), "\n"

    def selection_updated(self, selection: Selection | None) -> None:
        self._line_cache.clear()
        self.refresh()

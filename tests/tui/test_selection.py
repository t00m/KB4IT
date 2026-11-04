"""TUI text selection: the build log, the log viewer and the tables can be selected and copied."""

import asyncio

from textual.app import App
from textual.geometry import Offset
from textual.selection import SELECT_ALL, Selection

from kb4it.tui import app as tui
from kb4it.tui.widgets import SelectableDataTable, SelectableRichLog


class _Host(App):
    def __init__(self, widget):
        super().__init__()
        self._widget = widget

    def compose(self):
        yield self._widget


def _run(widget, scenario):
    async def main():
        app = _Host(widget)
        async with app.run_test(size=(80, 20)) as pilot:
            await pilot.pause()
            await scenario(app, pilot)
    asyncio.run(main())


def test_rich_log_select_all_returns_every_line():
    log = SelectableRichLog()

    async def scenario(app, pilot):
        log.write("first line")
        log.write("second línea")
        await pilot.pause()
        app.screen.text_select_all()
        await pilot.pause()
        assert app.screen.get_selected_text() == "first line\nsecond línea"

    _run(log, scenario)


def test_rich_log_partial_selection():
    log = SelectableRichLog()

    async def scenario(app, pilot):
        log.write("alpha beta")
        log.write("gamma delta")
        await pilot.pause()
        text, _end = log.get_selection(Selection(Offset(6, 0), Offset(5, 1)))
        assert text == "beta\ngamma"

    _run(log, scenario)


def test_rich_log_lines_carry_offsets():
    """Without offsets the mouse cannot start a selection."""
    log = SelectableRichLog()

    async def scenario(app, pilot):
        log.write("abc")
        await pilot.pause()
        strip = log.render_line(0)
        offsets = [seg.style.meta.get("offset") for seg in strip if seg.style and seg.text.strip()]
        assert offsets and offsets[0] == (0, 0)

    _run(log, scenario)


def test_data_table_select_all_has_header_and_rows():
    table = SelectableDataTable()

    async def scenario(app, pilot):
        table.add_columns("Key", "Value")
        table.add_row("Author", "Tomás Vírseda")
        table.add_row("Title", "Notes")
        await pilot.pause()
        app.screen.text_select_all()
        await pilot.pause()
        lines = [line.split() for line in app.screen.get_selected_text().splitlines()]
        assert lines == [["Key", "Value"], ["Author", "Tomás", "Vírseda"], ["Title", "Notes"]]

    _run(table, scenario)


def test_data_table_selection_is_highlighted():
    table = SelectableDataTable(show_cursor=False)

    async def scenario(app, pilot):
        table.add_columns("Key")
        table.add_row("Author")
        await pilot.pause()
        before = table.render_line(1)
        app.screen.text_select_all()
        await pilot.pause()
        assert table.text_selection == SELECT_ALL
        assert table.render_line(1) != before

    _run(table, scenario)


def test_ctrl_c_uses_the_system_clipboard_tool(monkeypatch):
    sent = []
    monkeypatch.setattr(tui, "_copy_with_tools", lambda text: sent.append(text) or "wl-copy")

    async def main():
        app = tui.KB4ITTUI()
        async with app.run_test(size=(140, 60)) as pilot:
            await pilot.pause()
            app.copy_to_clipboard("hello")
            assert sent == ["hello"]
            assert app.clipboard == "hello"
    asyncio.run(main())


def test_ctrl_a_selects_the_focused_log(monkeypatch):
    async def main():
        app = tui.KB4ITTUI()
        async with app.run_test(size=(140, 60)) as pilot:
            await pilot.pause()
            log = SelectableRichLog()
            await app.screen.mount(log)
            log.write("only this")
            log.focus()
            await pilot.pause()
            await pilot.press("ctrl+a")
            await pilot.pause()
            assert app.screen.get_selected_text() == "only this"
    asyncio.run(main())

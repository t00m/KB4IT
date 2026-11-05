"""
Settings of a project: every repo.json key its theme reads, and a small editor for repo.json.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Static, TextArea

from kb4it.core.files import text_save
from kb4it.core.repocheck import check_repo
from kb4it.core.util import json_load
from kb4it.tui.repo_options import RepoOption, current_value, theme_options
from kb4it.tui.screens.confirm import ConfirmScreen
from kb4it.tui.widgets import SelectableDataTable


class SettingsReferenceScreen(Screen):
    """Every repo.json key the project's theme reads, its default, meaning and the project's value."""

    CSS = """
    SettingsReferenceScreen { layout: vertical; }
    #summary { height: auto; padding: 0 1; }
    #filter { margin: 0 1; }
    #tbl { height: 1fr; margin: 0 1; }
    #detail-box { height: 9; margin: 0 1; border: solid $primary; padding: 0 1; }
    #footer-bar { height: 3; align: center middle; }
    """

    BINDINGS = [Binding("escape", "back", "Back", show=True)]

    def __init__(self, config: str, **kw: Any):
        super().__init__(**kw)
        self._config = config
        self._options: list[RepoOption] = []
        self._shown: list[RepoOption] = []
        self._repo: dict = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="summary")
        yield Input(placeholder="Filter by key or meaning", id="filter")
        yield SelectableDataTable(id="tbl", cursor_type="row")
        with VerticalScroll(id="detail-box"):
            yield Static("", id="detail")
        with Horizontal(id="footer-bar"):
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Settings Reference"
        try:
            self._repo = json_load(self._config)
        except Exception as error:  # noqa: BLE001 - shown to the user
            self._repo = {}
            self.query_one("#summary", Static).update(
                f"[red]Cannot read {self._config}: {error}[/red]. Showing the common settings.")
        theme = self._repo.get("theme", "") if isinstance(self._repo.get("theme"), str) else ""
        self._options, has_page = theme_options(theme)
        table = self.query_one("#tbl", DataTable)
        table.add_columns("Key", "Set in this project", "Default", "From")
        set_count = sum(current_value(self._repo, option.key) is not None for option in self._options)
        if self._repo:
            note = "" if has_page else f" Theme '{theme}' has no reference page: common settings only."
            self.query_one("#summary", Static).update(
                f"Theme [b]{theme}[/b]: {len(self._options)} settings, {set_count} set in this project "
                f"(in bold).{note}")
        self._fill("")
        table.focus()

    def _fill(self, words: str) -> None:
        words = words.lower().strip()
        table = self.query_one("#tbl", DataTable)
        table.clear()
        self._shown = [option for option in self._options
                       if not words or words in option.key.lower() or words in option.meaning.lower()]
        for option in self._shown:
            value = current_value(self._repo, option.key)
            style = "bold" if value is not None else ""
            table.add_row(Text(option.key, style=style), Text(value or "", style=style),
                          option.default, option.group)
        self._show_detail(0)

    def _show_detail(self, row: int) -> None:
        detail = self.query_one("#detail", Static)
        if not self._shown or not 0 <= row < len(self._shown):
            detail.update("No setting matches the filter.")
            return
        option = self._shown[row]
        value = current_value(self._repo, option.key)
        lines = [Text(option.key, style="bold"), Text(option.meaning)]
        if option.values:
            lines.append(Text(f"Values: {option.values}", style="dim"))
        lines.append(Text(f"Default: {option.default or 'none'}", style="dim"))
        lines.append(Text(f"This project: {value if value is not None else 'not set'}", style="dim"))
        detail.update(Text("\n").join(lines))

    @on(Input.Changed, "#filter")
    def _filter(self, event: Input.Changed) -> None:
        self._fill(event.value)

    @on(DataTable.RowHighlighted, "#tbl")
    def _highlighted(self, event: DataTable.RowHighlighted) -> None:
        self._show_detail(event.cursor_row)

    def action_back(self) -> None:
        self.app.pop_screen()

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()


class RepoEditorScreen(Screen):
    """Edit repo.json as text; Save writes it only after a check that finds no problem."""

    CSS = """
    RepoEditorScreen { layout: vertical; }
    #path { height: 1; padding: 0 1; }
    #editor { height: 1fr; margin: 0 1; }
    #result-box { height: 7; margin: 0 1; border: solid $primary; padding: 0 1; }
    #footer-bar { height: 3; align: center middle; }
    #footer-bar Button { margin: 0 1; }
    """

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("f5", "check", "Check", show=True),
        Binding("ctrl+s", "save", "Save", show=True),
    ]

    def __init__(self, config: str, **kw: Any):
        super().__init__(**kw)
        self._config = config
        self._saved = ""
        self._checked: str | None = None  # the text the last passing check saw

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="path")
        editor = TextArea("", id="editor", show_line_numbers=True, tab_behavior="indent")
        if "json" in editor.available_languages:
            editor.language = "json"
        yield editor
        with VerticalScroll(id="result-box"):
            yield Static("", id="result")
        with Horizontal(id="footer-bar"):
            yield Button("Check", id="check", variant="primary")
            yield Button("Save", id="save", variant="success", disabled=True)
            yield Button("Revert", id="revert", variant="warning")
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Edit repo.json"
        self.query_one("#path", Static).update(Text(self._config, style="dim"))
        try:
            self._saved = Path(self._config).read_text(encoding="utf-8-sig")
        except OSError as error:
            self._result(f"Cannot read the file: {error}", "red")
            self.query_one("#editor", TextArea).read_only = True
            self.query_one("#check", Button).disabled = True
            return
        self._load(self._saved)

    def _load(self, text: str) -> None:
        editor = self.query_one("#editor", TextArea)
        editor.load_text(text)
        editor.focus()
        self._checked = None
        self._update_save()
        self._result("Edit the settings, then Check (F5). Save (Ctrl+S) is possible after a check passes.")

    @property
    def _text(self) -> str:
        return self.query_one("#editor", TextArea).text

    def _result(self, message: str, colour: str = "") -> None:
        self.query_one("#result", Static).update(Text(message, style=colour))

    def _update_save(self) -> None:
        passed = self._checked is not None and self._checked == self._text
        self.query_one("#save", Button).disabled = not passed or self._text == self._saved

    @on(TextArea.Changed, "#editor")
    def _changed(self) -> None:
        if self._checked is not None and self._checked != self._text:
            self._checked = None
            self._result("Changed since the last check. Check again before saving.", "yellow")
        self._update_save()

    def _run_check(self) -> list[str]:
        return check_repo(self._text, self._config)

    def action_check(self) -> None:
        problems = self._run_check()
        if problems:
            self._checked = None
            self._result("Check failed; the file cannot be saved:\n" + "\n".join(f"- {p}" for p in problems), "red")
        else:
            self._checked = self._text
            unchanged = " Nothing to save: the text is the same as the file." if self._text == self._saved else ""
            self._result(f"Check passed.{unchanged}", "green")
        self._update_save()

    def action_save(self) -> None:
        if self.query_one("#save", Button).disabled:
            self.app.notify("Run a check that passes first (F5).", severity="warning")
            return
        problems = self._run_check()  # the folders or themes may have changed since the check
        if problems:
            self.action_check()
            return
        text = self._text
        try:
            text_save(self._config, text)
        except OSError as error:
            self._result(f"Cannot save: {error}", "red")
            return
        self._saved = text
        self._update_save()
        self._result("Saved. The next build uses these settings.", "green")
        self.app.notify("repo.json saved.")

    @on(Button.Pressed, "#check")
    def _check(self) -> None:
        self.action_check()

    @on(Button.Pressed, "#save")
    def _save(self) -> None:
        self.action_save()

    @on(Button.Pressed, "#revert")
    def _revert(self) -> None:
        self._load(self._saved)

    def action_back(self) -> None:
        if self._text == self._saved:
            self.dismiss(False)
            return

        def answer(discard: bool | None) -> None:
            if discard:
                self.dismiss(False)

        self.app.push_screen(ConfirmScreen("Leave without saving? Your changes will be lost."), callback=answer)

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.action_back()

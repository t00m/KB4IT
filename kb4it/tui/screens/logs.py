"""
Build log viewer.
"""

from __future__ import annotations

from typing import Any

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import (
    Button,
    Footer,
    Header,
    RichLog,
)

from kb4it.tui import clipboard
from kb4it.tui.projects import _log_path

_LOG_STYLE: dict[str, str] = {
    "CRITICAL": "bold red",
    "ERROR": "red",
    "WARNING": "yellow",
    "INFO": "white",
    "DEBUG": "dim white",
}


def _parse_level(line: str) -> str:
    prefix = line[:15].upper()
    for lvl in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"):
        if lvl in prefix:
            return lvl
    return "INFO"


class LogViewerScreen(Screen):
    CSS = """
    LogViewerScreen { layout: vertical; }
    #filter-bar { height: 3; align: center middle; padding: 0 1; }
    #filter-bar Button { margin: 0 1; }
    #log { height: 1fr; margin: 0 1; border: solid $primary; }
    #footer-bar { height: 3; align: center middle; }
    """

    def __init__(self, config: str, **kw: Any):
        super().__init__(**kw)
        self._config = config
        self._lines: list[tuple[str, str]] = []
        self._filter = "all"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="filter-bar"):
            yield Button("All", id="f-all", variant="primary")
            yield Button("Info only", id="f-info", variant="default")
            yield Button("Warnings+", id="f-warn", variant="warning")
            yield Button("Errors only", id="f-err", variant="error")
        yield RichLog(highlight=False, markup=False, id="log")
        with Horizontal(id="footer-bar"):
            yield Button("Copy Log", id="copy", variant="default")
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Build Log"
        self._load()

    def _load(self) -> None:
        p = _log_path(self._config)
        log = self.query_one(RichLog)
        if p is None:
            log.write("No build log found,  build the project first.")
            return
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            log.write(f"Cannot read log: {exc}")
            return
        self._lines = [(line, _parse_level(line)) for line in text.splitlines()]
        self._apply_filter()

    def _apply_filter(self) -> None:
        rank = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
        log = self.query_one(RichLog)
        log.clear()
        for line, level in self._lines:
            r = rank.get(level, 1)
            if self._filter == "all":
                show = True
            elif self._filter == "info":
                show = r == 1
            elif self._filter == "warn":
                show = r >= 2
            elif self._filter == "err":
                show = r >= 3
            else:
                show = True
            if show:
                log.write(Text(line, style=_LOG_STYLE.get(level, "white")))

    @on(Button.Pressed, "#f-all")
    def _f_all(self) -> None:
        self._filter = "all"
        self._apply_filter()

    @on(Button.Pressed, "#f-info")
    def _f_info(self) -> None:
        self._filter = "info"
        self._apply_filter()

    @on(Button.Pressed, "#f-warn")
    def _f_warn(self) -> None:
        self._filter = "warn"
        self._apply_filter()

    @on(Button.Pressed, "#f-err")
    def _f_err(self) -> None:
        self._filter = "err"
        self._apply_filter()

    @on(Button.Pressed, "#copy")
    def _copy(self) -> None:
        rank = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
        keep = []
        for line, level in self._lines:
            r = rank.get(level, 1)
            if (self._filter == "all"
                or (self._filter == "info" and r == 1)
                or (self._filter == "warn" and r >= 2)
                or (self._filter == "err" and r >= 3)):
                keep.append(line)
        text = "\n".join(keep)
        if not text:
            self.app.notify("Nothing to copy.", severity="warning")
            return
        ok, info = clipboard._copy_to_clipboard(self.app, text)
        if ok:
            self.app.notify(f"Copied {len(text)} chars to clipboard via {info}.", severity="information")
        else:
            self.app.notify(f"Could not copy: {info}", severity="error")

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()

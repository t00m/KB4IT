"""
Build screen: runs a build and shows its progress and log.
"""

from __future__ import annotations

import argparse
import logging
import threading
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
    Label,
    ProgressBar,
    RichLog,
)

from kb4it.core.log import reset_logging
from kb4it.tui import clipboard
from kb4it.tui.screens.logs import _LOG_STYLE

_reset_logging = reset_logging


class _TUILogHandler(logging.Handler):
    """Forward log records to a callback for real-time display in the TUI."""

    def __init__(self, callback):
        super().__init__()
        self._cb = callback

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._cb(record.levelname, self.format(record))
        except Exception:
            pass


class BuildScreen(Screen):
    CSS = """
    BuildScreen { layout: vertical; }
    #status { height: 1; margin: 1 1 0 1; color: $text-muted; }
    #prog { margin: 0 1 1 1; }
    #log { height: 1fr; margin: 0 1; border: solid $primary; }
    #footer-bar { height: 3; align: center middle; }
    """

    def __init__(self, proj_name: str, config: str, force: bool, **kw: Any):
        super().__init__(**kw)
        self._proj_name = proj_name
        self._config = config
        self._force = force
        self._total = 0
        self._completed = 0
        self._lock = threading.Lock()
        self._log_buffer: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("Preparing build…", id="status")
        yield ProgressBar(total=None, id="prog")
        yield RichLog(highlight=True, markup=False, id="log")
        with Horizontal(id="footer-bar"):
            yield Button("Copy Log", id="copy", variant="default")
            yield Button("Close", id="close", variant="primary", disabled=True)
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"Build,  {self._proj_name}"
        self._launch_build()

    def _launch_build(self) -> None:
        handler = _TUILogHandler(self._on_log)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))
        t = threading.Thread(target=self._build_thread, args=(handler,), daemon=True)
        t.start()

    def _build_thread(self, handler: _TUILogHandler) -> None:
        from kb4it.core.main import KB4IT
        error = ""
        try:
            _reset_logging()
            params = argparse.Namespace(
                action="build",
                config=self._config,
                log_level="DEBUG",
                force=self._force,
                progress_callback=self._on_compiled,
                compile_start_callback=self._on_start,
            )
            inst = KB4IT(params)
            # KB4IT's __init__ has already called setup_logging() and registered
            # its file handler; now we add our real-time display handler.
            logging.getLogger().addHandler(handler)
            if not inst.run():
                error = "Build failed,  see log for details."
        except SystemExit as exc:
            if exc.code and exc.code != 0:
                error = "Build failed,  see log for details."
        except Exception as exc:
            error = str(exc)
        finally:
            logging.getLogger().removeHandler(handler)
            self.app.call_from_thread(self._on_done, error)

    # ── callbacks invoked from the build thread ───────────────────────────────

    def _on_start(self, total: int) -> None:
        self.app.call_from_thread(self._set_total, total)

    def _set_total(self, total: int) -> None:
        self._total = total
        self.query_one(ProgressBar).update(total=max(total, 1), progress=0)
        self.query_one("#status", Label).update(f"Compiling 0 / {total} documents…")

    def _on_compiled(self, basename: str, rc: bool) -> None:
        self.app.call_from_thread(self._advance, basename, rc)

    def _advance(self, basename: str, rc: bool) -> None:
        with self._lock:
            self._completed += 1
            n = self._completed
        self.query_one(ProgressBar).advance(1)
        total_str = str(self._total) if self._total else "?"
        self.query_one("#status", Label).update(f"Compiling {n} / {total_str} documents…")
        colour = "green" if rc else "red"
        #self.query_one(RichLog).write(Text(f"compiled: {basename}", style=colour))

    def _on_log(self, level: str, msg: str) -> None:
        self.app.call_from_thread(self._write_log, level, msg)

    def _write_log(self, level: str, msg: str) -> None:
        if level == "DEBUG":
            return
        self._log_buffer.append(msg)
        self.query_one(RichLog).write(Text(msg, style=_LOG_STYLE.get(level, "white")))

    def _on_done(self, error: str) -> None:
        n = self._completed
        total = max(self._total, n, 1)
        bar = self.query_one(ProgressBar)
        if error:
            self.query_one("#status", Label).update(f"FAILED,  {error}")
            self.query_one(RichLog).write(Text(f"Build failed: {error}", style="bold red"))
        else:
            bar.update(total=total, progress=total)
            self.query_one("#status", Label).update(f"Done,  {n} document(s) compiled.")
            self.query_one(RichLog).write(
                Text(f"Build complete. {n} document(s) compiled.", style="bold green")
            )
        self.query_one("#close", Button).disabled = False

    @on(Button.Pressed, "#copy")
    def _copy(self) -> None:
        text = "\n".join(self._log_buffer)
        if not text:
            self.app.notify("Nothing to copy yet.", severity="warning")
            return
        ok, info = clipboard._copy_to_clipboard(self.app, text)
        if ok:
            self.app.notify(f"Copied {len(text)} chars to clipboard via {info}.", severity="information")
        else:
            self.app.notify(f"Could not copy: {info}", severity="error")

    @on(Button.Pressed, "#close")
    def _close(self) -> None:
        self.dismiss(None)

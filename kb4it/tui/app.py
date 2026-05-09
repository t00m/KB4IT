#!/usr/bin/env python
"""
KB4IT Terminal User Interface — Textual edition.

Launched automatically when kb4it is run with no arguments in a terminal.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import threading
from pathlib import Path
from typing import Any

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import (Container, Horizontal, ScrollableContainer,
                                Vertical)
from textual.screen import ModalScreen, Screen
from textual.widgets import (Button, DataTable, Footer, Header, Input, Label,
                             ListItem, ListView, Markdown, ProgressBar,
                             RichLog, Static)

from kb4it.core.env import ENV
from kb4it.core.util import json_load, json_save

# ─── constants ────────────────────────────────────────────────────────────────

PROJECTS_FILE = Path(ENV["LPATH"]["ROOT"]) / "projects.json"
VERSION = ENV["APP"]["version"]

_LOG_STYLE: dict[str, str] = {
    "CRITICAL": "bold red",
    "ERROR": "red",
    "WARNING": "yellow",
    "INFO": "white",
    "DEBUG": "dim white",
}


# ─── project registry ─────────────────────────────────────────────────────────

def load_projects() -> list[dict]:
    if not PROJECTS_FILE.exists():
        return []
    try:
        data = json_load(str(PROJECTS_FILE))
        return data.get("projects", [])
    except Exception:
        return []


def save_projects(projects: list[dict]) -> None:
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    json_save(str(PROJECTS_FILE), {"projects": projects})


# ─── theme / apps helpers ─────────────────────────────────────────────────────

def get_themes() -> list[dict]:
    themes: list[dict] = []
    seen_ids: set[str] = set()
    for scope, base in [
        ("global", ENV["GPATH"]["THEMES"]),
        ("local", ENV["LPATH"]["THEMES"]),
    ]:
        base_path = Path(base)
        if not base_path.exists():
            continue
        for entry in sorted(base_path.iterdir()):
            if not entry.is_dir():
                continue
            tfile = entry / "theme.json"
            if not tfile.exists():
                continue
            try:
                data = json_load(str(tfile))
                tid = data.get("id", entry.name)
                if tid in seen_ids:
                    continue
                seen_ids.add(tid)
                data["_scope"] = scope
                data["_path"] = str(entry)
                themes.append(data)
            except Exception:
                pass
    return themes


def get_apps(theme_name: str) -> list[str]:
    apps: list[str] = []
    seen: set[str] = set()
    for base in [ENV["GPATH"]["THEMES"], ENV["LPATH"]["THEMES"]]:
        apps_path = Path(base) / theme_name / "apps"
        if not apps_path.exists():
            continue
        for entry in sorted(apps_path.iterdir()):
            if entry.is_dir() and entry.name not in seen:
                seen.add(entry.name)
                apps.append(entry.name)
    return apps


# ─── path helpers ─────────────────────────────────────────────────────────────

def _log_path(config_path: str) -> Path | None:
    try:
        repo = json_load(config_path)
        source = Path(repo.get("source", ""))
        p = source.parent / "var" / "log" / "kb4it.log"
        return p if p.exists() else None
    except Exception:
        return None


def _kbdict_path(config_path: str) -> Path | None:
    try:
        repo = json_load(config_path)
        source_path = Path(repo.get("source", ""))
        p = source_path.parent / "var" / "db" / "kbdict.json"
        return p if p.exists() else None
    except Exception:
        return None


def _parse_level(line: str) -> str:
    prefix = line[:15].upper()
    for lvl in ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"):
        if lvl in prefix:
            return lvl
    return "INFO"


# ─── logging helpers ──────────────────────────────────────────────────────────

def _reset_logging() -> None:
    """
    Clear every handler from the root logger so the next KB4IT instance
    can call setup_logging() from scratch.

    KB4IT's setup_logging() has an early-return guard ('if root.handlers:
    return') that prevents re-initialisation when handlers already exist.
    Without this reset a second KB4IT instance in the same process never
    creates its temp log file, causing the build to silently fail.
    """
    root = logging.getLogger()
    for h in list(root.handlers):
        try:
            h.flush()
            h.close()
        except Exception:
            pass
        root.removeHandler(h)


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


# ─── modal: confirm dialog ────────────────────────────────────────────────────

class ConfirmScreen(ModalScreen):
    CSS = """
    ConfirmScreen { align: center middle; }
    #dialog {
        width: 64; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #dialog Label { text-align: center; margin-bottom: 1; width: 100%; }
    #btns { align: center middle; height: 3; }
    #btns Button { margin: 0 2; }
    """

    def __init__(self, message: str, **kw: Any):
        super().__init__(**kw)
        self._msg = message

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label(self._msg)
            with Horizontal(id="btns"):
                yield Button("Yes", id="yes", variant="error")
                yield Button("No", id="no", variant="primary")

    @on(Button.Pressed, "#yes")
    def _yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def _no(self) -> None:
        self.dismiss(False)


# ─── screen: build ────────────────────────────────────────────────────────────

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

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("Preparing build…", id="status")
        yield ProgressBar(total=None, id="prog")
        yield RichLog(highlight=True, markup=False, id="log")
        with Horizontal(id="footer-bar"):
            yield Button("Close", id="close", variant="primary", disabled=True)
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"Build — {self._proj_name}"
        self._launch_build()

    def _launch_build(self) -> None:
        from kb4it.services import compiler as cmod
        cmod.set_progress_callback(self._on_compiled)
        cmod.set_compile_start_callback(self._on_start)
        handler = _TUILogHandler(self._on_log)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s"))
        t = threading.Thread(target=self._build_thread, args=(handler,), daemon=True)
        t.start()

    def _build_thread(self, handler: _TUILogHandler) -> None:
        from kb4it.core.main import KB4IT
        from kb4it.services import compiler as cmod
        error = ""
        try:
            _reset_logging()
            params = argparse.Namespace(
                action="build",
                config=self._config,
                log_level="DEBUG",
                force=self._force,
            )
            inst = KB4IT(params)
            # KB4IT's __init__ has already called setup_logging() and registered
            # its file handler; now we add our real-time display handler.
            logging.getLogger().addHandler(handler)
            inst.run()
        except SystemExit as exc:
            if exc.code and exc.code != 0:
                error = "Build failed — see log for details."
        except Exception as exc:
            error = str(exc)
        finally:
            logging.getLogger().removeHandler(handler)
            cmod.clear_progress_callback()
            cmod.clear_compile_start_callback()
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
        self.query_one(RichLog).write(Text(msg, style=_LOG_STYLE.get(level, "white")))

    def _on_done(self, error: str) -> None:
        n = self._completed
        total = max(self._total, n, 1)
        bar = self.query_one(ProgressBar)
        if error:
            self.query_one("#status", Label).update(f"FAILED — {error}")
            self.query_one(RichLog).write(Text(f"Build failed: {error}", style="bold red"))
        else:
            bar.update(total=total, progress=total)
            self.query_one("#status", Label).update(f"Done — {n} document(s) compiled.")
            self.query_one(RichLog).write(
                Text(f"Build complete. {n} document(s) compiled.", style="bold green")
            )
        self.query_one("#close", Button).disabled = False

    @on(Button.Pressed, "#close")
    def _close(self) -> None:
        self.app.pop_screen()


# ─── screen: log viewer ───────────────────────────────────────────────────────

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
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Build Log"
        self._load()

    def _load(self) -> None:
        p = _log_path(self._config)
        log = self.query_one(RichLog)
        if p is None:
            log.write("No build log found — build the project first.")
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

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()


# ─── screen: document viewer ──────────────────────────────────────────────────

class DocumentViewerScreen(Screen):
    CSS = """
    DocumentViewerScreen { layout: vertical; }
    #meta { height: auto; max-height: 12; margin: 1 1 0 1; border: solid $primary; }
    #content { height: 1fr; margin: 0 1; border: solid $secondary; padding: 0 1; }
    #footer-bar { height: 3; align: center middle; }
    """

    def __init__(self, doc_id: str, kbdict: dict, **kw: Any):
        super().__init__(**kw)
        self._doc_id = doc_id
        self._kbdict = kbdict

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable(id="meta", show_cursor=False)
        with ScrollableContainer(id="content"):
            yield Markdown("", id="md")
        with Horizontal(id="footer-bar"):
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = self._doc_id
        doc_info = self._kbdict.get("document", {}).get(self._doc_id, {})
        doc_keys = doc_info.get("keys", {})
        content_path = doc_info.get("content", "")

        table = self.query_one("#meta", DataTable)
        table.add_columns("Key", "Values")
        for k, v in sorted(doc_keys.items()):
            display = ", ".join(str(x) for x in v) if isinstance(v, list) else str(v)
            table.add_row(k, display)

        if content_path and Path(content_path).exists():
            try:
                raw = Path(content_path).read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                raw = f"Error reading file: {exc}"
        else:
            raw = f"Source not found: {content_path}"

        self.query_one("#md", Markdown).update(raw)

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()


# ─── screen: explorer ─────────────────────────────────────────────────────────

class ExplorerScreen(Screen):
    CSS = """
    ExplorerScreen { layout: vertical; }
    #col-labels { height: 1; margin: 0 1; }
    .col-label { width: 1fr; text-align: center; color: $text-muted; }
    #panels { height: 1fr; margin: 0 1; }
    #keys-pane, #vals-pane, #docs-pane {
        width: 1fr; border: solid $primary; margin: 0 1;
    }
    #footer-bar { height: 3; align: center middle; }
    #footer-bar Button { margin: 0 2; }
    """

    def __init__(self, config: str, **kw: Any):
        super().__init__(**kw)
        self._config = config
        self._kbdict: dict = {}
        self._metadata: dict = {}
        self._selected_key = ""
        self._selected_value = ""
        self._selected_doc = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="col-labels"):
            yield Label("Keys", classes="col-label")
            yield Label("Values", classes="col-label")
            yield Label("Documents", classes="col-label")
        with Horizontal(id="panels"):
            yield ListView(id="keys-pane")
            yield ListView(id="vals-pane")
            yield ListView(id="docs-pane")
        with Horizontal(id="footer-bar"):
            yield Button("View Document", id="btn-view", variant="success", disabled=True)
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Explorer — Metadata Keys & Values"
        p = _kbdict_path(self._config)
        if p is None:
            self.app.notify(
                "Build the project first to generate the metadata database.",
                severity="warning",
            )
            self.app.pop_screen()
            return
        try:
            self._kbdict = json_load(str(p)) or {}
            self._metadata = self._kbdict.get("metadata", {})
        except Exception as exc:
            self.app.notify(f"Cannot read database: {exc}", severity="error")
            self.app.pop_screen()
            return
        keys_lv = self.query_one("#keys-pane", ListView)
        for k in sorted(self._metadata.keys()):
            n = len(self._metadata[k])
            keys_lv.append(ListItem(Label(f"{k}  ({n})")))

    @on(ListView.Highlighted, "#keys-pane")
    def _key_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None:
            return
        keys = sorted(self._metadata.keys())
        idx = event.list_view.index
        if idx is None or idx >= len(keys):
            return
        self._selected_key = keys[idx]
        self._selected_value = ""
        self._selected_doc = ""
        self.query_one("#btn-view", Button).disabled = True
        vals_lv = self.query_one("#vals-pane", ListView)
        vals_lv.clear()
        self.query_one("#docs-pane", ListView).clear()
        values = self._metadata.get(self._selected_key, {})
        for v in sorted(values.keys()):
            n = len(values[v])
            vals_lv.append(ListItem(Label(f"{v}  ({n})")))

    @on(ListView.Highlighted, "#vals-pane")
    def _val_highlighted(self, event: ListView.Highlighted) -> None:
        if not self._selected_key or event.item is None:
            return
        values = self._metadata.get(self._selected_key, {})
        val_keys = sorted(values.keys())
        idx = event.list_view.index
        if idx is None or idx >= len(val_keys):
            return
        self._selected_value = val_keys[idx]
        self._selected_doc = ""
        self.query_one("#btn-view", Button).disabled = True
        docs_lv = self.query_one("#docs-pane", ListView)
        docs_lv.clear()
        for d in sorted(values.get(self._selected_value, [])):
            docs_lv.append(ListItem(Label(d)))

    @on(ListView.Highlighted, "#docs-pane")
    def _doc_highlighted(self, event: ListView.Highlighted) -> None:
        if not self._selected_value or event.item is None:
            return
        values = self._metadata.get(self._selected_key, {})
        doc_ids = sorted(values.get(self._selected_value, []))
        idx = event.list_view.index
        if idx is None or idx >= len(doc_ids):
            return
        self._selected_doc = doc_ids[idx]
        self.query_one("#btn-view", Button).disabled = False

    @on(ListView.Selected, "#docs-pane")
    def _doc_selected(self, _event: ListView.Selected) -> None:
        self._open_doc()

    @on(Button.Pressed, "#btn-view")
    def _view(self) -> None:
        self._open_doc()

    def _open_doc(self) -> None:
        if self._selected_doc:
            self.app.push_screen(DocumentViewerScreen(self._selected_doc, self._kbdict))

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()


# ─── screen: project info ─────────────────────────────────────────────────────

class ProjectInfoScreen(Screen):
    CSS = """
    ProjectInfoScreen { layout: vertical; }
    #tbl { height: 1fr; margin: 1; }
    #footer-bar { height: 3; align: center middle; }
    """

    def __init__(self, project: dict, config: str, **kw: Any):
        super().__init__(**kw)
        self._project = project
        self._config = config

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable(id="tbl", show_cursor=False)
        with Horizontal(id="footer-bar"):
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"Info — {self._project['name']}"
        table = self.query_one(DataTable)
        table.add_columns("Key", "Value")
        try:
            repo = json_load(self._config)
            for k in sorted(repo.keys()):
                v = repo[k]
                if isinstance(v, list):
                    v = ", ".join(str(x) for x in v)
                elif isinstance(v, dict):
                    v = str(v)
                table.add_row(str(k), str(v))
            table.add_row("config_file", self._config)
        except Exception as exc:
            table.add_row("error", str(exc))

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()


# ─── screen: file list ────────────────────────────────────────────────────────

class FileListScreen(Screen):
    CSS = """
    FileListScreen { layout: vertical; }
    #tbl { height: 1fr; margin: 1; }
    #footer-bar { height: 3; align: center middle; }
    """

    def __init__(self, config: str, **kw: Any):
        super().__init__(**kw)
        self._config = config

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable(id="tbl", show_cursor=True)
        with Horizontal(id="footer-bar"):
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Source Files"
        table = self.query_one(DataTable)
        table.add_columns("#", "Filename", "Size")
        try:
            repo = json_load(self._config)
            source = Path(repo.get("source", ""))
            files = sorted([f for ext in ("*.md", "*.markdown") for f in source.glob(ext)])
            for i, f in enumerate(files, 1):
                sz = f.stat().st_size
                sz_str = f"{sz:,} B" if sz < 1024 else f"{sz // 1024} KB"
                table.add_row(str(i), f.name, sz_str)
            self.title = f"Source Files ({len(files)})"
        except Exception as exc:
            table.add_row("", f"Error: {exc}", "")

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()


# ─── screen: themes ───────────────────────────────────────────────────────────

class ThemesScreen(Screen):
    CSS = """
    ThemesScreen { layout: vertical; }
    #tbl { height: 1fr; margin: 1; }
    #footer-bar { height: 3; align: center middle; }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable(id="tbl", show_cursor=True)
        with Horizontal(id="footer-bar"):
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Installed Themes"
        table = self.query_one(DataTable)
        table.add_columns("ID", "Name", "Version", "Description", "Scope")
        for t in get_themes():
            table.add_row(
                t.get("id", "?"),
                t.get("name", "?"),
                t.get("version", "?"),
                t.get("description", ""),
                t.get("_scope", "?"),
            )

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()


# ─── screen: apps ─────────────────────────────────────────────────────────────

class AppsScreen(Screen):
    CSS = """
    AppsScreen { layout: vertical; }
    #theme-label { margin: 1 1 0 1; color: $text-muted; }
    #themes-list { height: 8; margin: 0 1; border: solid $primary; }
    #apps-label { margin: 1 1 0 1; color: $text-muted; }
    #apps-tbl { height: 1fr; margin: 0 1; border: solid $secondary; }
    #footer-bar { height: 3; align: center middle; }
    """

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self._themes = get_themes()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("Select a theme:", id="theme-label")
        yield ListView(id="themes-list")
        yield Label("Apps:", id="apps-label")
        yield DataTable(id="apps-tbl", show_cursor=True)
        with Horizontal(id="footer-bar"):
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Theme Apps"
        lv = self.query_one("#themes-list", ListView)
        for t in self._themes:
            lv.append(ListItem(Label(f"{t.get('id', '?')} — {t.get('description', '')}")))
        self.query_one("#apps-tbl", DataTable).add_columns("#", "App Name")

    @on(ListView.Highlighted, "#themes-list")
    def _theme_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None:
            return
        idx = event.list_view.index
        if idx is None or idx >= len(self._themes):
            return
        theme_id = self._themes[idx].get("id", "")
        apps = get_apps(theme_id)
        table = self.query_one("#apps-tbl", DataTable)
        table.clear()
        for i, app_name in enumerate(apps, 1):
            table.add_row(str(i), app_name)

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()


# ─── screen: create project ───────────────────────────────────────────────────

class CreateProjectScreen(Screen):
    CSS = """
    CreateProjectScreen { layout: vertical; }
    .field-label { margin: 1 1 0 1; color: $text-muted; }
    #themes-list { height: 6; margin: 0 1; border: solid $primary; }
    #apps-list   { height: 4; margin: 0 1; border: solid $secondary; }
    Input { margin: 0 1 1 1; }
    #help-banner {
        margin: 1 1 0 1;
        padding: 0 1;
        color: $text-muted;
        background: $boost;
        border: solid $primary;
    }
    #error-banner {
        margin: 0 1;
        padding: 0 1;
        color: $error;
    }
    #footer-bar { height: 3; align: center middle; }
    #footer-bar Button { margin: 0 2; }
    """

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self._themes = get_themes()
        self._theme_idx = 0
        self._apps: list[str] = []
        self._app_idx = 0

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label(
            "Create a new repository from a theme app template.\n"
            "  Theme   — visual style for your website\n"
            "  App     — template to initialise the repository from\n"
            "  Name    — label shown in the project list (any text)\n"
            "  Path    — full path where the repository will be created;\n"
            "            its parent directory must already exist",
            id="help-banner",
        )
        yield Label("Select theme:", classes="field-label")
        yield ListView(id="themes-list")
        yield Label("Select app:", classes="field-label")
        yield ListView(id="apps-list")
        yield Label("Project display name:", classes="field-label")
        yield Input(placeholder="My Project", id="inp-name")
        yield Label("Repository path:", classes="field-label")
        yield Input(
            placeholder=str(Path.home() / "Documents" / "my_project"),
            id="inp-path",
        )
        yield Label("", id="error-banner", classes="")
        with Horizontal(id="footer-bar"):
            yield Button("Create", id="create", variant="success")
            yield Button("Cancel", id="cancel", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Create New Project"
        self.query_one("#error-banner", Label).display = False
        if not self._themes:
            self.app.notify("No themes installed.", severity="warning")
        lv = self.query_one("#themes-list", ListView)
        for t in self._themes:
            lv.append(ListItem(Label(f"{t.get('id', '?')} — {t.get('description', '')}")))
        self._refresh_apps()

    def _refresh_apps(self) -> None:
        """Repopulate the apps list for the currently selected theme."""
        lv = self.query_one("#apps-list", ListView)
        lv.clear()
        self._app_idx = 0
        if self._themes:
            theme_id = self._themes[self._theme_idx].get("id", "")
            self._apps = get_apps(theme_id)
        else:
            self._apps = []
        for app_name in self._apps:
            lv.append(ListItem(Label(app_name)))

    def _show_error(self, msg: str) -> None:
        banner = self.query_one("#error-banner", Label)
        banner.update(f"Error: {msg}")
        banner.display = True

    def _clear_error(self) -> None:
        banner = self.query_one("#error-banner", Label)
        banner.update("")
        banner.display = False

    @on(ListView.Highlighted, "#themes-list")
    def _theme_hi(self, event: ListView.Highlighted) -> None:
        idx = event.list_view.index
        if idx is not None:
            self._theme_idx = idx
            self._refresh_apps()

    @on(ListView.Highlighted, "#apps-list")
    def _app_hi(self, event: ListView.Highlighted) -> None:
        idx = event.list_view.index
        if idx is not None:
            self._app_idx = idx

    @on(Button.Pressed, "#cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#create")
    def _create(self) -> None:
        self._clear_error()
        if not self._themes:
            self._show_error("No themes available. Install at least one theme first.")
            return
        theme_id = self._themes[self._theme_idx].get("id", "")
        app_name = self._apps[self._app_idx] if self._apps else "default"
        name = self.query_one("#inp-name", Input).value.strip()
        path = os.path.expanduser(self.query_one("#inp-path", Input).value.strip())
        if not name:
            self._show_error("Project display name cannot be empty.")
            return
        if not path:
            self._show_error("Repository path cannot be empty.")
            return
        parent = Path(path).parent
        if not parent.exists():
            self._show_error(
                f"Parent directory '{parent}' does not exist. "
                "Create it first or choose a different path."
            )
            return
        try:
            from kb4it.core.main import KB4IT
            _reset_logging()
            params = argparse.Namespace(
                action="create",
                theme=theme_id,
                app=app_name,
                repo_path=path,
                log_level="WARNING",
            )
            inst = KB4IT(params)
            try:
                inst.run()
            except SystemExit:
                pass
        except PermissionError:
            self._show_error(
                f"Permission denied. Check that you have write access to: {path}"
            )
            return
        except OSError as exc:
            self._show_error(
                f"Cannot access '{path}': {exc.strerror}. Verify the path is valid."
            )
            return
        except KeyError as exc:
            self._show_error(
                f"Configuration error: missing key {exc}. "
                "The selected theme may be incompatible with this action."
            )
            return
        except Exception as exc:
            self._show_error(f"{type(exc).__name__}: {exc}")
            return
        config = str(Path(path) / "config" / "repo.json")
        if not Path(config).exists():
            self._show_error(
                f"Repo created but config not found at: {config}. "
                f"Theme '{theme_id}' may be missing its example repository skeleton."
            )
            return
        self.app.notify(f"Project '{name}' created at: {path}", severity="information")
        self.dismiss({"name": name, "config": config})


# ─── screen: import project ───────────────────────────────────────────────────

class ImportProjectScreen(Screen):
    CSS = """
    ImportProjectScreen { layout: vertical; }
    .field-label { margin: 1 1 0 1; color: $text-muted; }
    Input { margin: 0 1 1 1; }
    #preview { height: auto; max-height: 10; margin: 0 1 1 1; border: solid $primary; }
    #footer-bar { height: 3; align: center middle; }
    #footer-bar Button { margin: 0 2; }
    """

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self._repo: dict = {}
        self._config_path = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("Path to repo.json:", classes="field-label")
        yield Input(placeholder="/path/to/config/repo.json", id="inp-path")
        yield Label("Display name:", classes="field-label")
        yield Input(placeholder="My Project", id="inp-name")
        yield DataTable(id="preview", show_cursor=False)
        with Horizontal(id="footer-bar"):
            yield Button("Import", id="import", variant="success")
            yield Button("Cancel", id="cancel", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Import Existing Project"
        self.query_one("#preview", DataTable).add_columns("Key", "Value")

    @on(Input.Submitted, "#inp-path")
    def _path_submitted(self, event: Input.Submitted) -> None:
        path = os.path.expanduser(event.value.strip())
        if not path or not Path(path).exists():
            self.app.notify("File not found.", severity="error")
            return
        try:
            self._repo = json_load(path) or {}
            self._config_path = path
        except Exception as exc:
            self.app.notify(f"Cannot parse: {exc}", severity="error")
            return
        default_name = self._repo.get("title") or Path(path).parent.parent.name
        self.query_one("#inp-name", Input).value = str(default_name)
        table = self.query_one("#preview", DataTable)
        table.clear()
        for k in ("title", "tagline", "theme", "source", "target"):
            if k in self._repo:
                table.add_row(k, str(self._repo[k]))
        table.add_row("config", path)

    @on(Button.Pressed, "#cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#import")
    def _import(self) -> None:
        path = self._config_path or os.path.expanduser(
            self.query_one("#inp-path", Input).value.strip()
        )
        name = self.query_one("#inp-name", Input).value.strip()
        if not name:
            self.app.notify("Display name cannot be empty.", severity="error")
            return
        if not Path(path).exists():
            self.app.notify("File not found — submit the path field first.", severity="error")
            return
        for field in ("source", "target", "theme"):
            if field not in self._repo:
                self.app.notify(f"Config missing required field: '{field}'", severity="error")
                return
        self.dismiss({"name": name, "config": path})


# ─── screen: project submenu ──────────────────────────────────────────────────

class ProjectScreen(Screen):
    CSS = """
    ProjectScreen { layout: vertical; }
    #info-panel {
        height: auto; margin: 1; border: solid $primary;
        padding: 1 2; background: $panel;
    }
    #actions { height: 1fr; align: center top; padding: 1 0; }
    #actions Button { width: 40; margin: 0 0 1 0; }
    """

    def __init__(self, project: dict, **kw: Any):
        super().__init__(**kw)
        self._project = project

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="info-panel")
        with Vertical(id="actions"):
            yield Button("Compile", id="compile", variant="success")
            yield Button("Force Compile  (recompile everything)", id="force-compile", variant="warning")
            yield Button("Project Info", id="info", variant="default")
            yield Button("List Source Files", id="files", variant="default")
            yield Button("Explore Keys & Values", id="explore", variant="default")
            yield Button("View Build Log", id="log", variant="default")
            yield Button("Back", id="back", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.title = self._project["name"]
        self._refresh()

    def _refresh(self) -> None:
        config = self._project["config"]
        try:
            repo = json_load(config)
            title = repo.get("title", self._project["name"])
            theme = repo.get("theme", "?")
            source = repo.get("source", "?")
            target = repo.get("target", "?")
        except Exception:
            title = self._project["name"]
            theme = source = target = "?"
        db_ok = _kbdict_path(config) is not None
        log_ok = _log_path(config) is not None
        built = "[green]yes[/green]" if db_ok else "[dim]not yet[/dim]"
        log_lbl = "[green]yes[/green]" if log_ok else "[dim]none[/dim]"
        self.query_one("#info-panel", Static).update(
            f"[bold]{title}[/bold]\n"
            f"Theme: {theme}   Built: {built}   Log: {log_lbl}\n"
            f"Source: [dim]{source}[/dim]\n"
            f"Target: [dim]{target}[/dim]"
        )
        self.query_one("#explore", Button).disabled = not db_ok
        self.query_one("#log", Button).disabled = not log_ok

    @on(Button.Pressed, "#compile")
    def _compile(self) -> None:
        self.app.push_screen(
            BuildScreen(self._project["name"], self._project["config"], False),
            callback=lambda _: self._refresh(),
        )

    @on(Button.Pressed, "#force-compile")
    def _force_compile(self) -> None:
        self.app.push_screen(
            BuildScreen(self._project["name"], self._project["config"], True),
            callback=lambda _: self._refresh(),
        )

    @on(Button.Pressed, "#info")
    def _info(self) -> None:
        self.app.push_screen(ProjectInfoScreen(self._project, self._project["config"]))

    @on(Button.Pressed, "#files")
    def _files(self) -> None:
        self.app.push_screen(FileListScreen(self._project["config"]))

    @on(Button.Pressed, "#explore")
    def _explore(self) -> None:
        self.app.push_screen(ExplorerScreen(self._project["config"]))

    @on(Button.Pressed, "#log")
    def _log(self) -> None:
        self.app.push_screen(LogViewerScreen(self._project["config"]))

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()


# ─── screen: main ─────────────────────────────────────────────────────────────

class MainScreen(Screen):
    CSS = """
    MainScreen { layout: vertical; }
    #list-label { margin: 1 1 0 1; color: $text-muted; }
    #proj-list { height: 1fr; margin: 0 1; border: solid $primary; }
    #row1, #row2 { height: 3; align: center middle; padding: 0 1; }
    #row1 Button, #row2 Button { margin: 0 1; }
    """

    BINDINGS = [
        Binding("enter", "open_project", "Open", show=True),
        Binding("q", "request_quit", "Quit", show=True),
    ]

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self._projects: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("Projects:", id="list-label")
        yield ListView(id="proj-list")
        with Horizontal(id="row1"):
            yield Button("New Project", id="new", variant="success")
            yield Button("Import Project", id="import", variant="primary")
            yield Button("Delete Project", id="delete", variant="error")
        with Horizontal(id="row2"):
            yield Button("Themes", id="themes", variant="default")
            yield Button("Apps", id="apps", variant="default")
            yield Button("Quit", id="quit", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = f"KB4IT v{VERSION}"
        self.sub_title = "Static Website Generator"
        self._reload()

    def _reload(self) -> None:
        self._projects = load_projects()
        lv = self.query_one("#proj-list", ListView)
        lv.clear()
        if self._projects:
            for p in self._projects:
                lv.append(
                    ListItem(Label(f"[bold]{p['name']}[/bold]  [dim]{p.get('config', '')}[/dim]"))
                )
        else:
            lv.append(ListItem(Label("[dim]No projects. Use New or Import to add one.[/dim]")))
        n = len(self._projects)
        self.query_one("#list-label", Label).update(
            f"Projects: [dim]({n} configured)[/dim]" if n else "Projects: [dim](none)[/dim]"
        )

    def _open_at(self, idx: int) -> None:
        if idx >= len(self._projects):
            return
        project = self._projects[idx]
        self.app.push_screen(ProjectScreen(project), callback=lambda _: self._reload())

    @on(ListView.Selected, "#proj-list")
    def _proj_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None:
            self._open_at(idx)

    def action_open_project(self) -> None:
        idx = self.query_one("#proj-list", ListView).index
        if idx is not None:
            self._open_at(idx)

    def action_request_quit(self) -> None:
        self.app.exit()

    @on(Button.Pressed, "#new")
    def _new(self) -> None:
        def _after(result: dict | None) -> None:
            if result:
                self._projects.append(result)
                save_projects(self._projects)
                self._reload()
        self.app.push_screen(CreateProjectScreen(), callback=_after)

    @on(Button.Pressed, "#import")
    def _import(self) -> None:
        def _after(result: dict | None) -> None:
            if result:
                self._projects.append(result)
                save_projects(self._projects)
                self._reload()
        self.app.push_screen(ImportProjectScreen(), callback=_after)

    @on(Button.Pressed, "#delete")
    def _delete(self) -> None:
        lv = self.query_one("#proj-list", ListView)
        idx = lv.index
        if idx is None or idx >= len(self._projects):
            self.app.notify("Select a project to delete.", severity="warning")
            return
        project = self._projects[idx]

        def _after(confirmed: bool | None) -> None:
            if confirmed:
                del self._projects[idx]
                save_projects(self._projects)
                self._reload()
                self.app.notify(f"Removed '{project['name']}' from registry.")

        self.app.push_screen(
            ConfirmScreen(
                f"Remove '{project['name']}' from the registry?\n"
                "(Files on disk are NOT deleted)"
            ),
            callback=_after,
        )

    @on(Button.Pressed, "#themes")
    def _themes(self) -> None:
        self.app.push_screen(ThemesScreen())

    @on(Button.Pressed, "#apps")
    def _apps(self) -> None:
        self.app.push_screen(AppsScreen())

    @on(Button.Pressed, "#quit")
    def _quit(self) -> None:
        self.app.exit()


# ─── app root ─────────────────────────────────────────────────────────────────

class KB4ITTUI(App):
    CSS = """
    Screen { background: $surface; }
    """
    TITLE = f"KB4IT v{VERSION}"

    def on_mount(self) -> None:
        self.push_screen(MainScreen())


def run() -> None:
    """Launch the KB4IT Textual TUI."""
    KB4ITTUI().run()

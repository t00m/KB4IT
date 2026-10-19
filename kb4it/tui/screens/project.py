"""
A project: its actions, information and files.
"""

from __future__ import annotations

import webbrowser
from pathlib import Path
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Static,
)

from kb4it.core.util import json_load
from kb4it.tui.projects import _kbdict_path, _log_path, _resolve_repo_path
from kb4it.tui.screens.build import BuildScreen
from kb4it.tui.screens.documents import ExplorerScreen
from kb4it.tui.screens.logs import LogViewerScreen
from kb4it.tui.servers import _WEB_SERVERS, _start_live_server


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
        self.title = f"Info,  {self._project['name']}"
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
            source = _resolve_repo_path(self._config, repo.get("source", ""))
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


class ProjectScreen(Screen):
    CSS = """
    ProjectScreen { layout: vertical; }
    #info-panel {
        height: auto; margin: 1; border: solid $primary;
        padding: 1 2; background: $panel;
    }
    #actions {
        height: 1fr; padding: 1 2;
        layout: grid; grid-size: 2; grid-columns: 1fr 1fr;
        grid-rows: 3; grid-gutter: 1 2;
    }
    #actions Button { width: 1fr; }
    #footer-bar { height: 3; align: center middle; }
    """

    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
    ]

    def __init__(self, project: dict, **kw: Any):
        super().__init__(**kw)
        self._project = project

    def action_back(self) -> None:
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="info-panel")
        with ScrollableContainer(id="actions"):
            yield Button("Compile", id="compile", variant="success")
            yield Button("Force Compile  (recompile everything)", id="force-compile", variant="warning")
            yield Button("Project Info", id="info", variant="default")
            yield Button("List Source Files", id="files", variant="default")
            yield Button("Explore Keys & Values", id="explore", variant="default")
            yield Button("View Build Log", id="log", variant="default")
            yield Button("Browse Local (file://)", id="browse-local", variant="default")
            yield Button("Browse via Web Server (http)", id="browse-server", variant="default")
        with Horizontal(id="footer-bar"):
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
        if target not in ("", "?"):
            target_dir = _resolve_repo_path(config, target)
            target_ok = (target_dir / "index.html").exists()
        else:
            target_ok = False
        self.query_one("#browse-local", Button).disabled = not target_ok
        self.query_one("#browse-server", Button).disabled = not target_ok

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

    def _target_index(self) -> Path | None:
        try:
            repo = json_load(self._project["config"])
        except Exception:
            return None
        target = repo.get("target")
        if not target:
            return None
        index = _resolve_repo_path(self._project["config"], target) / "index.html"
        return index if index.exists() else None

    @on(Button.Pressed, "#browse-local")
    def _browse_local(self) -> None:
        index = self._target_index()
        if index is None:
            self.app.notify("No built index.html found,  compile the project first.",
                            severity="warning")
            return
        webbrowser.open(index.as_uri())
        self.app.notify(f"Opened {index.as_uri()}", severity="information")

    @on(Button.Pressed, "#browse-server")
    def _browse_server(self) -> None:
        index = self._target_index()
        if index is None:
            self.app.notify("No built index.html found,  compile the project first.",
                            severity="warning")
            return
        key = self._project["config"]
        entry = _WEB_SERVERS.get(key)
        if entry is None:
            httpd, port, err = _start_live_server(self.app, key, str(index.parent))
            if err or httpd is None or port is None:
                self.app.notify(f"Could not start web server: {err}", severity="error")
                return
            _WEB_SERVERS[key] = (httpd, port)
        else:
            port = entry[1]
        url = f"http://127.0.0.1:{port}/"
        webbrowser.open(url)
        self.app.notify(f"Serving at {url}", severity="information")

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.dismiss(None)

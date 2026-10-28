"""
Create a project from a theme app, or import an existing one.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    RadioButton,
    RadioSet,
)

from kb4it.core.util import json_load
from kb4it.tui.projects import get_apps, get_themes
from kb4it.tui.screens.build import _reset_logging


class CreateProjectScreen(Screen):
    CSS = """
    CreateProjectScreen { layout: vertical; }
    .field-label { margin: 1 1 0 1; color: $text-muted; }
    #themes-list { height: 6; margin: 0 1; border: solid $primary; }
    #apps-list   { height: 4; margin: 0 1; border: solid $secondary; }
    Input { margin: 0 1 1 1; }
    #index-choice { margin: 0 1; height: auto; layout: horizontal; }
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
            "  Theme  ,  visual style for your website\n"
            "  App    ,  template to initialise the repository from\n"
            "  Name   ,  label shown in the project list (any text)\n"
            "  Path   ,  full path where the repository will be created;\n"
            "            its parent directory must already exist\n"
            "  Search ,  whether search engines may index the published site",
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
        yield Label("Allow search engines:", classes="field-label")
        with RadioSet(id="index-choice"):
            yield RadioButton("Yes", id="index-yes")
            yield RadioButton("No", id="index-no")
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
            lv.append(ListItem(Label(f"{t.get('id', '?')},  {t.get('description', '')}")))
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

    def _index_choice(self) -> str | None:
        """'yes' or 'no' for kb4it create --index, or None while nothing is chosen."""
        pressed = self.query_one("#index-choice", RadioSet).pressed_button
        if pressed is None:
            return None
        return "yes" if pressed.id == "index-yes" else "no"

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
        index = self._index_choice()
        if index is None:
            self._show_error("Choose whether search engines may index the site (Yes or No).")
            return
        try:
            from kb4it.core.main import KB4IT
            _reset_logging()
            params = argparse.Namespace(
                action="create",
                theme=theme_id,
                app=app_name,
                repo_path=path,
                index=index,
                log_level="WARNING",
            )
            inst = KB4IT(params)
            try:
                inst.run()
            except SystemExit:
                pass
            next_steps = inst.next_steps
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
        self.app.notify("\n".join(next_steps), severity="information", timeout=20)
        self.dismiss({"name": name, "config": config})


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
            self.app.notify("File not found,  submit the path field first.", severity="error")
            return
        for field in ("source", "target", "theme"):
            if field not in self._repo:
                self.app.notify(f"Config missing required field: '{field}'", severity="error")
                return
        self.dismiss({"name": name, "config": path})

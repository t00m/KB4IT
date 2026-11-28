"""
Themes and apps that KB4IT ships.
"""

from __future__ import annotations

import os
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
    Label,
    ListItem,
    ListView,
)

from kb4it.core import themeinstall
from kb4it.core.exceptions import LockBusyError
from kb4it.core.themecli import install_lines, project_warning
from kb4it.core.themeinstall import ThemeInstallError
from kb4it.tui.projects import active_themes, get_apps, get_themes
from kb4it.tui.screens.confirm import ConfirmScreen
from kb4it.tui.screens.theme_install import InstallThemeScreen
from kb4it.tui.widgets import SelectableDataTable


class ThemesScreen(Screen):
    CSS = """
    ThemesScreen { layout: vertical; }
    #tbl { height: 1fr; margin: 1; }
    #footer-bar { height: 3; align: center middle; }
    #footer-bar Button { margin: 0 1; }
    """

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self._themes: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield SelectableDataTable(id="tbl", show_cursor=True, cursor_type="row")
        with Horizontal(id="footer-bar"):
            yield Button("Install", id="install", variant="success")
            yield Button("Uninstall", id="uninstall", variant="error", disabled=True)
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Installed Themes"
        table = self.query_one(DataTable)
        table.add_columns("ID", "Name", "Version", "Active", "Scope", "Fingerprint", "Description", "Path")
        self._reload()

    def _reload(self) -> None:
        self._themes = get_themes()
        table = self.query_one(DataTable)
        table.clear()
        for t in self._themes:
            table.add_row(
                t.get("id", "?"),
                t.get("name", "?"),
                t.get("version", "?"),
                "yes" if t.get("_active") else "no",
                t.get("_scope", "?"),
                t.get("fingerprint", "?"),
                t.get("description", ""),
                t.get("_path", ""),
            )
        self._update_buttons()

    def _selected(self) -> dict | None:
        row = self.query_one(DataTable).cursor_row
        return self._themes[row] if 0 <= row < len(self._themes) else None

    def _update_buttons(self) -> None:
        theme = self._selected()
        self.query_one("#uninstall", Button).disabled = not (theme and theme.get("_scope") == "local")

    @on(DataTable.RowHighlighted, "#tbl")
    def _row_highlighted(self) -> None:
        self._update_buttons()

    @on(Button.Pressed, "#install")
    def _install(self) -> None:
        def _after(source: str | None) -> None:
            if source:
                self.app.notify(f"Installing {source}...")
                self.run_worker(lambda: self._install_worker(source), thread=True, exclusive=True)
        self.app.push_screen(InstallThemeScreen(), callback=_after)

    def _install_worker(self, source: str) -> None:
        if not source.lower().startswith(("http://", "https://")):
            source = os.path.expanduser(source)
        try:
            result = themeinstall.install(source)
        except Exception as error:  # an error in a worker would close the whole interface
            self.app.call_from_thread(self.app.notify, str(error), severity="error", timeout=10)
            return
        self.app.call_from_thread(self.app.notify, "\n".join(install_lines(result)), timeout=8)
        self.app.call_from_thread(self._reload)

    @on(Button.Pressed, "#uninstall")
    def _uninstall(self) -> None:
        theme = self._selected()
        if not theme or theme.get("_scope") != "local":
            return
        theme_id = os.path.basename(theme["_path"])
        warning = project_warning(theme_id, themeinstall.projects_using(theme_id))
        message = f"Uninstall the theme {theme_id} {theme.get('version', '')}?\n{theme['_path']} is deleted."
        if warning:
            message += f"\n\n{warning}"

        def _after(confirmed: bool | None) -> None:
            if not confirmed:
                return
            try:
                version = themeinstall.uninstall(theme_id)
            except (ThemeInstallError, LockBusyError) as error:
                self.app.notify(str(error), severity="error", timeout=10)
                return
            self.app.notify(f"Uninstalled {theme_id} {version}.")
            self._reload()

        self.app.push_screen(ConfirmScreen(message), callback=_after)

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()


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
        self._themes = active_themes()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("Select a theme:", id="theme-label")
        yield ListView(id="themes-list")
        yield Label("Apps:", id="apps-label")
        yield SelectableDataTable(id="apps-tbl", show_cursor=True)
        with Horizontal(id="footer-bar"):
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Theme Apps"
        lv = self.query_one("#themes-list", ListView)
        for t in self._themes:
            lv.append(ListItem(Label(f"{t.get('id', '?')},  {t.get('description', '')}")))
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

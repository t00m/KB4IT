"""
Themes and apps that KB4IT ships.
"""

from __future__ import annotations

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

from kb4it.tui.projects import get_apps, get_themes


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

"""
Main screen: the list of projects.
"""

from __future__ import annotations

from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    Static,
)

from kb4it.core.notice import (HELP_ONLINE_URL, dismiss_help_notice, help_notice_lines,
                               help_notice_visible, offline_index)
from kb4it.core import projects
from kb4it.tui.projects import BUILD_VERSION
from kb4it.tui.screens.catalog import AppsScreen, ThemesScreen
from kb4it.tui.screens.confirm import ConfirmScreen
from kb4it.tui.screens.create import CreateProjectScreen, ImportProjectScreen
from kb4it.tui.screens.project import ProjectScreen


class MainScreen(Screen):
    CSS = """
    MainScreen { layout: vertical; }
    #help-banner { margin: 1 1 0 1; color: $text-muted; }
    #list-label { margin: 1 1 0 1; color: $text-muted; }
    #proj-list { height: 1fr; margin: 0 1; border: solid $primary; }
    #row1, #row2 { height: 3; align: center middle; padding: 0 1; }
    #row1 Button, #row2 Button { margin: 0 1; }
    """

    BINDINGS = [
        Binding("enter", "open_project", "Open", show=True),
        Binding("q", "request_quit", "Quit", show=True),
        Binding("d", "dismiss_help", "Dismiss help notice", show=True),
    ]

    def __init__(self, **kw: Any):
        super().__init__(**kw)
        self._projects: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        line = help_notice_lines(offline_index(), HELP_ONLINE_URL)[0]
        banner = Static(f"{line} Press d to hide this notice.", id="help-banner")
        banner.display = help_notice_visible()
        yield banner
        yield Label("Projects:", id="list-label")
        yield DataTable(id="proj-list", cursor_type="row", zebra_stripes=True)
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
        self.title = f"KB4IT {BUILD_VERSION}"
        self.sub_title = "Static Website Generator"
        self.query_one("#proj-list", DataTable).add_columns("ID", "Name", "Config")
        self._reload()

    def _reload(self) -> None:
        self._projects = projects.load()
        table = self.query_one("#proj-list", DataTable)
        table.clear()
        for p in self._projects:
            table.add_row(p.get("id") or "-", p.get("name", ""), p.get("config", ""))
        n = len(self._projects)
        self.query_one("#list-label", Label).update(
            f"Projects: [dim]({n} configured)[/dim]" if n
            else "Projects: [dim](none)  Use New or Import to add one.[/dim]"
        )

    def _open_at(self, idx: int) -> None:
        if idx >= len(self._projects):
            return
        project = self._projects[idx]
        self.app.push_screen(ProjectScreen(project), callback=lambda _: self._reload())

    @on(DataTable.RowSelected, "#proj-list")
    def _proj_selected(self, event: DataTable.RowSelected) -> None:
        self._open_at(event.cursor_row)

    def action_open_project(self) -> None:
        self._open_at(self.query_one("#proj-list", DataTable).cursor_row)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        # Offer "d" only while the banner shows; afterwards it leaves the footer.
        if action == "dismiss_help":
            banner = self.query("#help-banner")
            return bool(banner) and bool(banner.first().display)
        return True

    def action_dismiss_help(self) -> None:
        banner = self.query_one("#help-banner", Static)
        if not banner.display:
            return
        try:
            dismiss_help_notice()
        except OSError as error:
            self.app.notify(f"Cannot dismiss the help notice: {error}", severity="warning")
            return
        banner.display = False
        self.refresh_bindings()

    def action_request_quit(self) -> None:
        self.app.exit()

    def _register(self, result: dict) -> None:
        try:
            projects.register(result["config"], name=result["name"], pid=result.get("id") or None)
        except projects.ProjectError as error:
            self.app.notify(str(error), severity="error")

    @on(Button.Pressed, "#new")
    def _new(self) -> None:
        def _after(result: dict | None) -> None:
            if result:
                self._register(result)
                self._reload()
        self.app.push_screen(CreateProjectScreen(), callback=_after)

    @on(Button.Pressed, "#import")
    def _import(self) -> None:
        def _after(result: dict | None) -> None:
            if result:
                self._register(result)
                self._reload()
        self.app.push_screen(ImportProjectScreen(), callback=_after)

    @on(Button.Pressed, "#delete")
    def _delete(self) -> None:
        idx = self.query_one("#proj-list", DataTable).cursor_row
        if idx < 0 or idx >= len(self._projects):
            self.app.notify("Select a project to delete.", severity="warning")
            return
        project = self._projects[idx]

        def _after(confirmed: bool | None) -> None:
            if confirmed:
                projects.remove(project["config"])
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

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
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
)

from kb4it.tui.projects import VERSION, load_projects, save_projects
from kb4it.tui.screens.catalog import AppsScreen, ThemesScreen
from kb4it.tui.screens.confirm import ConfirmScreen
from kb4it.tui.screens.create import CreateProjectScreen, ImportProjectScreen
from kb4it.tui.screens.project import ProjectScreen


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

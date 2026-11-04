#!/usr/bin/env python
"""
KB4IT Terminal User Interface,  Textual edition.

Launched automatically when kb4it is run with no arguments in a terminal.
"""

from __future__ import annotations

from textual.app import App
from textual.binding import Binding

from kb4it.tui.clipboard import (
    _CLIPBOARD_TOOLS,
    _copy_to_clipboard,
    _copy_with_tools,
    clipboard_commands,
)
from kb4it.tui.projects import (
    BUILD_VERSION,
    PROJECTS_FILE,
    VERSION,
    _kbdict_path,
    _log_path,
    _project_root,
    _resolve_repo_path,
    get_apps,
    get_themes,
    load_projects,
    save_projects,
)
from kb4it.tui.screens.build import (
    BuildScreen,
    _reset_logging,
    _TUILogHandler,
)
from kb4it.tui.screens.catalog import (
    AppsScreen,
    ThemesScreen,
)
from kb4it.tui.screens.confirm import (
    ConfirmScreen,
)
from kb4it.tui.screens.create import (
    CreateProjectScreen,
    ImportProjectScreen,
)
from kb4it.tui.screens.documents import (
    DocumentViewerScreen,
    ExplorerScreen,
)
from kb4it.tui.screens.logs import (
    _LOG_STYLE,
    LogViewerScreen,
    _parse_level,
)
from kb4it.tui.screens.main import (
    MainScreen,
)
from kb4it.tui.screens.project import (
    FileListScreen,
    ProjectInfoScreen,
    ProjectScreen,
)
from kb4it.tui.servers import (
    _WEB_SERVERS,
    KB4IT_DEFAULT_PORT,
    KB4IT_PORT_SCAN_LIMIT,
    _start_live_server,
    _start_project_server,
)

# Every name this module had before the split into projects, servers, clipboard and screens;
# tests, applications and the kb4it command import them from here.
__all__ = [
    "KB4ITTUI",
    "KB4IT_DEFAULT_PORT",
    "KB4IT_PORT_SCAN_LIMIT",
    "PROJECTS_FILE",
    "VERSION",
    "_CLIPBOARD_TOOLS",
    "_LOG_STYLE",
    "_WEB_SERVERS",
    "AppsScreen",
    "BuildScreen",
    "ConfirmScreen",
    "CreateProjectScreen",
    "DocumentViewerScreen",
    "ExplorerScreen",
    "FileListScreen",
    "ImportProjectScreen",
    "LogViewerScreen",
    "MainScreen",
    "ProjectInfoScreen",
    "ProjectScreen",
    "ThemesScreen",
    "_TUILogHandler",
    "_copy_to_clipboard",
    "_kbdict_path",
    "_log_path",
    "_parse_level",
    "_project_root",
    "_reset_logging",
    "_resolve_repo_path",
    "_start_live_server",
    "_start_project_server",
    "clipboard_commands",
    "get_apps",
    "get_themes",
    "load_projects",
    "run",
    "save_projects",
]


# ─── app root ─────────────────────────────────────────────────────────────────

class KB4ITTUI(App):
    CSS = """
    Screen { background: $surface; }
    """
    TITLE = f"KB4IT {BUILD_VERSION}"

    BINDINGS = [
        Binding("ctrl+a", "select_all", "Select All", show=True),
        Binding("ctrl+c", "screen.copy_text", "Copy", show=True),
    ]

    def action_select_all(self) -> None:
        """Select the text of the focused widget, or of the whole screen when nothing selectable has focus."""
        focused = self.screen.focused
        target = focused if focused is not None and focused.allow_select else self.screen
        target.text_select_all()

    def copy_to_clipboard(self, text: str) -> None:
        """Copy with the system clipboard tool when there is one; OSC 52 only works in some terminals.

        Textual calls this for Ctrl+C on selected text and for copies inside an Input.
        """
        if tool := _copy_with_tools(text):
            self._clipboard = text
            self.notify(f"Copied {len(text)} chars to clipboard via {tool}.")
            return
        super().copy_to_clipboard(text)
        self.notify(f"Copied {len(text)} chars to clipboard via OSC52.")

    def on_mount(self) -> None:
        self.push_screen(MainScreen())


def run() -> None:
    """Launch the KB4IT Textual TUI."""
    KB4ITTUI().run()

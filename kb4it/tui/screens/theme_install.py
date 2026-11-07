"""
Dialog to install a theme from a zip file or an https URL.
"""

from __future__ import annotations

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class InstallThemeScreen(ModalScreen):
    """Dismisses with the source typed (a zip path or an https:// URL), or None when cancelled."""

    CSS = """
    InstallThemeScreen { align: center middle; }
    #dialog {
        width: 80; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #source-error { color: $error; width: 100%; }
    #btns { align: center middle; height: 3; }
    #btns Button { margin: 0 2; }
    """

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Theme zip: a file path or an https:// URL.\n"
                        "Its top folder must be named as the id in its theme.json.")
            yield Input(placeholder="~/Downloads/mytheme.zip", id="inp-source")
            yield Label("", id="source-error")
            with Horizontal(id="btns"):
                yield Button("Install", id="do-install", variant="success")
                yield Button("Cancel", id="cancel", variant="default")

    @on(Input.Submitted, "#inp-source")
    @on(Button.Pressed, "#do-install")
    def _install(self) -> None:
        source = self.query_one("#inp-source", Input).value.strip()
        if not source:
            self.query_one("#source-error", Label).update("Type a zip path or an https:// URL.")
            return
        self.dismiss(source)

    @on(Button.Pressed, "#cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

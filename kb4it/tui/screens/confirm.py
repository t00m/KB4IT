"""
Confirmation dialog.
"""

from __future__ import annotations

from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Label,
)


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

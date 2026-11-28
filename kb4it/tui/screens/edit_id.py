"""
Dialog to set, change or remove the id of a project.
"""

from __future__ import annotations

from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

from kb4it.core import projects


def id_error(pid: str, config: str | None) -> str:
    """The problem with pid as the id of config, or '' when it is fine or empty (no id)."""
    if not pid:
        return ""
    return projects.id_problem(pid, projects.load(), config) or ""


class EditIdScreen(ModalScreen):
    """Dismisses with the new id ('' removes it) or None when cancelled."""

    CSS = """
    EditIdScreen { align: center middle; }
    #dialog {
        width: 64; height: auto; padding: 1 2;
        border: thick $primary; background: $surface;
    }
    #id-error { color: $error; width: 100%; }
    #btns { align: center middle; height: 3; }
    #btns Button { margin: 0 2; }
    """

    def __init__(self, current: str, config: str, **kw: Any):
        super().__init__(**kw)
        self._current = current
        self._config = config

    def compose(self) -> ComposeResult:
        with Container(id="dialog"):
            yield Label("Project id (letters, digits and dashes; empty removes it):")
            yield Input(value=self._current, placeholder="sapblog", id="inp-id")
            yield Label("", id="id-error")
            with Horizontal(id="btns"):
                yield Button("Save", id="save", variant="success")
                yield Button("Cancel", id="cancel", variant="default")

    @on(Input.Changed, "#inp-id")
    def _check(self, event: Input.Changed) -> None:
        self.query_one("#id-error", Label).update(id_error(event.value.strip(), self._config))

    @on(Button.Pressed, "#save")
    def _save(self) -> None:
        pid = self.query_one("#inp-id", Input).value.strip()
        problem = id_error(pid, self._config)
        if problem:
            self.query_one("#id-error", Label).update(problem)
            return
        self.dismiss(pid)

    @on(Button.Pressed, "#cancel")
    def _cancel(self) -> None:
        self.dismiss(None)

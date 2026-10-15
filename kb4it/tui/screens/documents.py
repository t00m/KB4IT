"""
Metadata explorer and document viewer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, ScrollableContainer
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    Markdown,
)

from kb4it.core.util import json_load
from kb4it.tui import clipboard
from kb4it.tui.projects import _kbdict_path


class DocumentViewerScreen(Screen):
    CSS = """
    DocumentViewerScreen { layout: vertical; }
    #meta { height: auto; max-height: 12; margin: 1 1 0 1; border: solid $primary; }
    #content { height: 1fr; margin: 0 1; border: solid $secondary; padding: 0 1; }
    #footer-bar { height: 3; align: center middle; }
    """

    def __init__(self, doc_id: str, kbdict: dict, **kw: Any):
        super().__init__(**kw)
        self._doc_id = doc_id
        self._kbdict = kbdict
        self._raw = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable(id="meta", show_cursor=False)
        with ScrollableContainer(id="content"):
            yield Markdown("", id="md")
        with Horizontal(id="footer-bar"):
            yield Button("Copy Document", id="copy", variant="default")
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = self._doc_id
        doc_info = self._kbdict.get("document", {}).get(self._doc_id, {})
        doc_keys = doc_info.get("keys", {})
        content_path = doc_info.get("content", "")

        table = self.query_one("#meta", DataTable)
        table.add_columns("Key", "Values")
        for k, v in sorted(doc_keys.items()):
            display = ", ".join(str(x) for x in v) if isinstance(v, list) else str(v)
            table.add_row(k, display)

        if content_path and Path(content_path).exists():
            try:
                raw = Path(content_path).read_text(encoding="utf-8", errors="replace")
            except Exception as exc:
                raw = f"Error reading file: {exc}"
        else:
            raw = f"Source not found: {content_path}"

        self._raw = raw
        self.query_one("#md", Markdown).update(raw)

    @on(Button.Pressed, "#copy")
    def _copy(self) -> None:
        if not self._raw:
            self.app.notify("Nothing to copy.", severity="warning")
            return
        ok, info = clipboard._copy_to_clipboard(self.app, self._raw)
        if ok:
            self.app.notify(f"Copied {len(self._raw)} chars to clipboard via {info}.", severity="information")
        else:
            self.app.notify(f"Could not copy: {info}", severity="error")

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()


class ExplorerScreen(Screen):
    CSS = """
    ExplorerScreen { layout: vertical; }
    #col-labels { height: 1; margin: 0 1; }
    .col-label { width: 1fr; text-align: center; color: $text-muted; }
    #panels { height: 1fr; margin: 0 1; }
    #keys-pane, #vals-pane, #docs-pane {
        width: 1fr; border: solid $primary; margin: 0 1;
    }
    #footer-bar { height: 3; align: center middle; }
    #footer-bar Button { margin: 0 2; }
    """

    def __init__(self, config: str, **kw: Any):
        super().__init__(**kw)
        self._config = config
        self._kbdict: dict = {}
        self._metadata: dict = {}
        self._selected_key = ""
        self._selected_value = ""
        self._selected_doc = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="col-labels"):
            yield Label("Keys", classes="col-label")
            yield Label("Values", classes="col-label")
            yield Label("Documents", classes="col-label")
        with Horizontal(id="panels"):
            yield ListView(id="keys-pane")
            yield ListView(id="vals-pane")
            yield ListView(id="docs-pane")
        with Horizontal(id="footer-bar"):
            yield Button("View Document", id="btn-view", variant="success", disabled=True)
            yield Button("Back", id="back", variant="default")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Explorer,  Metadata Keys & Values"
        p = _kbdict_path(self._config)
        if p is None:
            self.app.notify(
                "Build the project first to generate the metadata database.",
                severity="warning",
            )
            self.app.pop_screen()
            return
        try:
            self._kbdict = json_load(str(p)) or {}
            self._metadata = self._kbdict.get("metadata", {})
        except Exception as exc:
            self.app.notify(f"Cannot read database: {exc}", severity="error")
            self.app.pop_screen()
            return
        keys_lv = self.query_one("#keys-pane", ListView)
        for k in sorted(self._metadata.keys()):
            n = len(self._metadata[k])
            keys_lv.append(ListItem(Label(f"{k}  ({n})")))

    @on(ListView.Highlighted, "#keys-pane")
    def _key_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is None:
            return
        keys = sorted(self._metadata.keys())
        idx = event.list_view.index
        if idx is None or idx >= len(keys):
            return
        self._selected_key = keys[idx]
        self._selected_value = ""
        self._selected_doc = ""
        self.query_one("#btn-view", Button).disabled = True
        vals_lv = self.query_one("#vals-pane", ListView)
        vals_lv.clear()
        self.query_one("#docs-pane", ListView).clear()
        values = self._metadata.get(self._selected_key, {})
        for v in sorted(values.keys()):
            n = len(values[v])
            vals_lv.append(ListItem(Label(f"{v}  ({n})")))

    @on(ListView.Highlighted, "#vals-pane")
    def _val_highlighted(self, event: ListView.Highlighted) -> None:
        if not self._selected_key or event.item is None:
            return
        values = self._metadata.get(self._selected_key, {})
        val_keys = sorted(values.keys())
        idx = event.list_view.index
        if idx is None or idx >= len(val_keys):
            return
        self._selected_value = val_keys[idx]
        self._selected_doc = ""
        self.query_one("#btn-view", Button).disabled = True
        docs_lv = self.query_one("#docs-pane", ListView)
        docs_lv.clear()
        for d in sorted(values.get(self._selected_value, [])):
            docs_lv.append(ListItem(Label(d)))

    @on(ListView.Highlighted, "#docs-pane")
    def _doc_highlighted(self, event: ListView.Highlighted) -> None:
        if not self._selected_value or event.item is None:
            return
        values = self._metadata.get(self._selected_key, {})
        doc_ids = sorted(values.get(self._selected_value, []))
        idx = event.list_view.index
        if idx is None or idx >= len(doc_ids):
            return
        self._selected_doc = doc_ids[idx]
        self.query_one("#btn-view", Button).disabled = False

    @on(ListView.Selected, "#docs-pane")
    def _doc_selected(self, _event: ListView.Selected) -> None:
        self._open_doc()

    @on(Button.Pressed, "#btn-view")
    def _view(self) -> None:
        self._open_doc()

    def _open_doc(self) -> None:
        if self._selected_doc:
            self.app.push_screen(DocumentViewerScreen(self._selected_doc, self._kbdict))

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        self.app.pop_screen()

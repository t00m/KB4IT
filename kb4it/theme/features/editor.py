"""Feature editor: the Add page (add.html), an editor for new documents in the browser."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from kb4it.theme.feature import Feature

if TYPE_CHECKING:
    from kb4it.theme.site import Site


class Editor(Feature):
    """add.html when the editor setting is on (repo.json "editor", default theme.json "editor")."""

    name = "editor"
    hooks = ("editor_keys", "register_add_page")
    options = {"profile_skeleton": True}
    templates = ("PAGE_ADD", "EDITOR_DIALOGS")

    def pages(self, site: Site) -> None:
        self.engine.create_page_add()

    def editor_keys(self) -> dict[str, Any]:
        """Completion data {Key: [{"v": value, "c": count}]} for the properties pane."""
        from kb4it.services.addpage import AddPageMixin
        keys: dict[str, Any] = AddPageMixin.editor_keys(self.engine)
        return keys

    def register_add_page(self, html: str) -> None:
        """Write the Add page and register it as a system page."""
        self.engine.add_system_page("add", "Add document", html)

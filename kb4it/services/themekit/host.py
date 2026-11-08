"""What the themekit mixins use from Builder, declared for the type checker (AR-06)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol


class Renderable(Protocol):
    """A compiled template."""

    def render(self, **kwargs: Any) -> str: ...


class ThemeHost:
    """Base of the themekit mixins. At run time it is empty: Builder provides all of this."""

    if TYPE_CHECKING:
        srvdtb: Any
        srvbes: Any
        log: Any  # a logging.Logger once the service starts

        def _initialize(self) -> None: ...

        def template(self, template: str) -> Renderable: ...

        def get_theme_var(self) -> dict[str, Any]: ...

        def distribute_md(self, name: str, content: str, as_html: bool = True, listing: bool = False) -> None: ...

        def distribute_html(self, mdId: str, htmlId: str) -> None: ...

        def extract_toc(self, source: str) -> str: ...

        def get_page_actions(self, var: dict[str, Any]) -> str: ...

        def add_system_page(self, name: str, title: str, html: str | None = None, as_html: bool = True,
                            listing: bool = False) -> None: ...

        def build_datatable(self, headers: list[str] | None = None, doclist: list[str] | None = None,
                            table_id: str = 'kb4it-datatable') -> str: ...

        # Page builders of DocumentTheme that kits such as FilterMixin wrap with super().
        def build_page_index_all(self) -> Any: ...

        def build_page_bookmarks(self) -> Any: ...

        def build_page_key_value(self, kvpath: Any) -> Any: ...

        def build_events(self, doclist: Any) -> Any: ...

        def datatable_title_cell(self, docId: str, properties: Any) -> str: ...

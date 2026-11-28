"""What the themekit mixins use from Builder, declared for the type checker (AR-06)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar

if TYPE_CHECKING:
    from kb4it.theme.feature import Feature


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

        def profile_card(self, key: str, value: str) -> str: ...

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

        def has_event_page(self, doc_id: str) -> bool: ...


_F = TypeVar("_F", bound="Feature")


def feature_of(host: Any, cls: type[_F]) -> _F:
    """The feature object a legacy mixin hands its work to, one per theme instance and build.

    The theme is both the hook owner and the engine: the feature calls the theme's methods
    with their old arguments, and the theme's services (srvdtb, srvbes, template()).
    """
    cache: dict[str, Any] = host.__dict__.setdefault("_kb4it_features", {})
    feature = cache.get(cls.name)
    if feature is None:
        feature = cache[cls.name] = cls(host, host)
    return feature

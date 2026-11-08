#!/usr/bin/env python

"""
BaseTheme: the base class of every theme.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

A theme is `class Theme(BaseTheme)` in logic/theme.py. It switches on features
by name, sets options as class attributes and overrides the hooks it needs.
Every hook is optional. KB4IT sets self.site, self.config and self.log before
the first hook runs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, ClassVar

if TYPE_CHECKING:
    from kb4it.core.checks import Problem
    from kb4it.theme.site import Doc, Site


class Internals:
    """KB4IT internals, for what the public API does not cover yet. Unstable: any release may change them."""

    def __init__(self, engine: Any) -> None:
        self.builder = engine
        self.db = engine.srvdtb
        self.backend = engine.srvbes


class BaseTheme:
    """Base class of a theme."""

    #: Features to switch on: names of built-in features or bundles, or Feature subclasses.
    features: ClassVar[tuple[Any, ...]] = ()
    #: Dataclass of the theme's settings (theme.json and the repo.json block named after the theme).
    config_class: ClassVar[type | None] = None
    #: Source file names the build refuses because the theme writes a page with that name.
    reserved_pages: ClassVar[tuple[str, ...]] = ()
    #: Title of a page whose document has no Title.
    untitled_label: ClassVar[str] = ""
    #: Cut long titles (True) or leave them whole (False, when the CSS cuts them).
    ellipsize_titles: ClassVar[bool] = True
    #: Area of the theme's log lines, such as [THEME] HTML_MISSING.
    log_area: ClassVar[str] = "THEME"
    #: The site has a page per person (Author_<name>.html) that the structured data links to;
    #: False describes each person in the home page instead.
    person_pages: ClassVar[bool] = True

    # Set by KB4IT before the first hook runs.
    site: Site
    config: Any
    log: Any
    internals: Internals
    _engine: Any

    # ------------------------------------------------------------ rendering
    def render(self, name: str, **values: Any) -> str:
        """Render template `name` with the base variables plus values, all under `var`."""
        var = self.base_var()
        var.update(values)
        html: str = self._engine.render_template(name, var)
        return html

    def template(self, name: str) -> Any:
        """The compiled template `name`; call .render(var=...) on it."""
        return self._engine.template(name)

    def has_template(self, name: str) -> bool:
        """True when a template named `name` exists (site override, theme, base or common)."""
        return bool(self._engine.has_template(name))

    def base_var(self) -> dict[str, Any]:
        """A new dict of the variables every template gets: repo, theme, page, lang, search_box..."""
        var: dict[str, Any] = self._engine.default_theme_var()
        return var

    # ------------------------------------------------------------ lifecycle
    def setup(self) -> None:
        """Once per build, before anything else: reset the theme's own per-build state."""

    def generate_sources(self, site: Site) -> None:
        """Write documents into the source folder before KB4IT reads it."""

    def prepare(self, site: Site) -> None:
        """After the documents are read, before any page is built: compute what the pages need."""

    def build(self, site: Site) -> None:
        """Write the theme's own pages with site.page(). The features' pages are already written."""

    def after_build(self, site: Site) -> None:
        """After every document page is compiled, before the site is deployed."""

    def after_deploy(self, site: Site) -> None:
        """After the site is in target (site.paths.target): copy or package files there."""

    def checks(self, site: Site) -> list[Problem]:
        """Problems of the built site; default: links to missing pages and anchors."""
        problems: list[Problem] = self._engine.default_checks()
        return problems

    def after_checks(self, site: Site) -> None:
        """After the checks passed: publish, copy, notify."""

    # ------------------------------------------------------------ document pages
    def page_var(self) -> dict[str, Any]:
        """The starting var of a document page; default: base_var()."""
        return self.base_var()

    def page_context(self, doc: Doc, var: dict[str, Any]) -> dict[str, Any]:
        """Add the theme's data to var before the body is rewritten and the page rendered."""
        return var

    def body_transforms(self, doc: Doc, var: dict[str, Any]) -> list[Callable[[str], str]]:
        """Functions from HTML to HTML applied in order to the compiled body."""
        transforms: list[Callable[[str], str]] = self._engine.default_body_transforms(doc.id, var)
        return transforms

    def page_template(self, doc: Doc, var: dict[str, Any]) -> str:
        """Name of the template that renders the body of the page."""
        return "HTML_BODY"

    def render_page(self, doc: Doc, var: dict[str, Any]) -> str:
        """The whole page: page_template() between HTML_HEADER_COMMON and HTML_FOOTER when they exist."""
        html: str = self._engine.default_render_page(doc.id, var)
        return html

    def finalize_html(self, html: str) -> str:
        """Last change to the whole page before it is written."""
        return html

    # ------------------------------------------------------------ site-wide
    def site_signature(self) -> str:
        """A value that changes when every page must be rebuilt (site-wide navigation...); '' for none."""
        return ""

    def target_subdir(self) -> str | None:
        """Folder inside target to build into, or None."""
        return None

    def page_lang(self) -> str:
        """Language of the pages (<html lang>); default: repo.json seo.lang."""
        lang: str = self._engine.default_page_lang()
        return lang

    def structured_defaults(self) -> dict[str, Any]:
        """Schema.org defaults of the theme's documents: {'type': ..., 'map': {property: schema field}}."""
        defaults: dict[str, Any] = self._engine.default_structured_defaults()
        return defaults

    def search_page(self) -> str:
        """The search page of the site, for the structured data of the home page."""
        page: str = self._engine.default_search_page()
        return page

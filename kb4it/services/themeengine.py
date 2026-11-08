#!/usr/bin/env python

"""
ThemeEngine: runs a BaseTheme theme for the build pipeline.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

The pipeline calls the theme service through the Builder interface (build(),
build_page(), the search, SEO and check methods). A theme on the public API
(kb4it.theme.BaseTheme) does not inherit from Builder: this adapter owns the
theme instance and its features, implements that interface, and calls the
theme's hooks with Site and Doc objects. Internal: themes never see it, except
through theme.internals.
"""

from __future__ import annotations

from typing import Any, Callable

from kb4it.core.exceptions import ThemeError
from kb4it.core.log import q
from kb4it.services.builder import Builder
from kb4it.services.headmeta import HeadMetaMixin
from kb4it.services.pagepipeline import PagePipelineMixin
from kb4it.theme.base import BaseTheme, Internals
from kb4it.theme.feature import Feature, resolve, theme_json_keys
from kb4it.theme.features import BUNDLES, REGISTRY
from kb4it.theme.site import Doc, Site

# Theme class attributes the engine takes over as its own Builder settings.
ENGINE_OPTIONS = ("untitled_label", "ellipsize_titles", "log_area", "config_class")


def features_of(theme_class: type[BaseTheme]) -> list[type[Feature]]:
    """The feature classes a theme class switches on, in stage order."""
    return resolve(theme_class.features, REGISTRY, BUNDLES)


def theme_json_of(theme_class: type[BaseTheme]) -> dict[str, Any]:
    """The theme.json keys the features of a theme class set."""
    classes = features_of(theme_class)
    return theme_json_keys(classes, any(c.name == "property_pages" for c in classes))


def unused_hooks(theme_class: type[BaseTheme]) -> list[tuple[str, str]]:
    """(method, feature) of theme methods named like a hook of a built-in feature that is off."""
    enabled = {cls.name for cls in features_of(theme_class)}
    found = []
    for name, cls in sorted(REGISTRY.items()):
        if name in enabled:
            continue
        for hook in cls.hooks:
            if callable(getattr(theme_class, hook, None)) and not hasattr(BaseTheme, hook):
                found.append((hook, name))
    return found


class ThemeEngine(Builder):
    """The theme service of a BaseTheme theme."""

    page_pipeline = True

    def __init__(self, theme_class: type[BaseTheme], app: Any = None) -> None:
        super().__init__(app)
        self.theme_class = theme_class
        self.modname = "Theme"
        for name in ENGINE_OPTIONS:
            setattr(self, name, getattr(theme_class, name))
        self.feature_classes = features_of(theme_class)
        names = {cls.name for cls in self.feature_classes}
        for cls in self.feature_classes:
            for option, default in cls.options.items():
                setattr(self, option, getattr(theme_class, option, default))
        self.add_page = "editor" in names
        reserved = list(theme_class.reserved_pages)
        for cls in self.feature_classes:
            reserved += [name for name in cls.reserves if name not in reserved]
        self.reserved_pages = tuple(reserved)
        self.theme = theme_class()
        self.theme._engine = self
        self.features: dict[str, Feature] = {cls.name: cls(self.theme, self) for cls in self.feature_classes}
        self._hook_owner: dict[str, Feature] = {}
        for feature in self.features.values():
            for hook in feature.hooks:
                self._hook_owner.setdefault(hook, feature)

    # The settings object belongs to the theme: Frontend sets it on the service.
    @property
    def config(self) -> Any:
        return getattr(self.theme, "config", None)

    @config.setter
    def config(self, value: Any) -> None:
        self.theme.config = value

    @property
    def required_templates(self) -> list[str]:
        names: list[str] = []
        for feature in self.features.values():
            names += [t for t in feature.templates if t not in names]
        return names

    def _initialize(self) -> None:
        super()._initialize()
        self.site = Site(self.srvdtb, self.srvbes, host=self, features=self.features)
        self.theme.site = self.site
        self.theme.log = self.log
        self.theme.internals = Internals(self)
        for hook, feature in unused_hooks(self.theme_class):
            self.log.warning(f"[FRONTEND] THEME_HOOK_UNUSED theme={q(self.theme_class.__module__)} "
                             f"hook={q(hook)} feature={q(feature)}")
        self.theme.setup()

    def doc(self, doc_id: str) -> Doc:
        return Doc(self.site, doc_id)

    def hook(self, name: str) -> Callable[..., Any]:
        """The theme's method `name`, else the default of the feature that owns the hook."""
        feature = self._hook_owner.get(name)
        if feature is None:
            raise ThemeError(f"no enabled feature has the hook {name!r}")
        return feature.hook(name)

    # ------------------------------------------------------------------ stages
    def generate_sources(self) -> None:
        self.theme.generate_sources(self.site)

    def prepare(self) -> None:
        for feature in self.features.values():
            feature.prepare(self.site)
        self.theme.prepare(self.site)

    def build(self) -> None:
        for feature in self.features.values():
            feature.pages(self.site)
        self.theme.build(self.site)

    def post_activities(self) -> None:
        for feature in self.features.values():
            feature.after_build(self.site)
        self.theme.after_build(self.site)

    def post_deploy_activities(self) -> None:
        for feature in self.features.values():
            feature.after_deploy(self.site)
        self.theme.after_deploy(self.site)

    def checks(self, target: str) -> list[Any]:
        return self.theme.checks(self.site)

    def default_checks(self) -> list[Any]:
        return list(Builder.checks(self, self.srvbes.get_path("target")))

    def after_checks(self) -> None:
        self.theme.after_checks(self.site)

    # ------------------------------------------------------------ page pipeline
    def page_var(self) -> dict[str, Any]:
        return self.theme.page_var()

    def page_context(self, doc_id: str, var: dict[str, Any]) -> dict[str, Any]:
        doc = self.doc(doc_id)
        for feature in self.features.values():
            var = feature.page_context(doc, var)
        return self.theme.page_context(doc, var)

    def body_transforms(self, doc_id: str, var: dict[str, Any]) -> list[Callable[[str], str]]:
        return self.theme.body_transforms(self.doc(doc_id), var)

    def default_body_transforms(self, doc_id: str, var: dict[str, Any]) -> list[Callable[[str], str]]:
        return list(PagePipelineMixin.body_transforms(self, doc_id, var))

    def page_body_template(self, doc_id: str, var: dict[str, Any]) -> str:
        return self.theme.page_template(self.doc(doc_id), var)

    def render_page(self, doc_id: str, var: dict[str, Any]) -> str:
        return self.theme.render_page(self.doc(doc_id), var)

    def default_render_page(self, doc_id: str, var: dict[str, Any]) -> str:
        return PagePipelineMixin.render_page(self, doc_id, var)

    def finalize_html(self, html: str) -> str:
        return self.theme.finalize_html(html)

    # --------------------------------------------------------------- site-wide
    def site_signature(self) -> str:
        return self.theme.site_signature()

    def target_subdir(self) -> str | None:
        return self.theme.target_subdir()

    def page_lang(self) -> str:
        return self.theme.page_lang()

    def default_page_lang(self) -> str:
        return HeadMetaMixin.page_lang(self)

    def structured_defaults(self) -> dict[str, Any]:
        return self.theme.structured_defaults()

    def default_structured_defaults(self) -> dict[str, Any]:
        return dict(HeadMetaMixin.structured_defaults(self))

    def search_page(self) -> str:
        return self.theme.search_page()

    def default_search_page(self) -> str:
        return HeadMetaMixin.search_page(self)

    # ------------------------------------------------------- feature services
    def page_toc(self, source_html: str) -> str:
        toc = self.features.get("toc")
        return toc.extract(source_html) if toc is not None else ""

    def page_actions(self, var: dict[str, Any]) -> str:
        metadata = self.features.get("metadata")
        return metadata.actions(var) if metadata is not None else ""

    def build_datatable(self, headers: list[str] | None = None, doclist: list[str] | None = None,
                        table_id: str = "kb4it-datatable") -> str:
        table = self.features.get("table")
        if table is None:
            raise ThemeError("site.table() needs the table feature")
        html: str = table.render(headers, doclist, table_id)
        return html

    def editor_keys(self) -> dict[str, Any]:
        if "editor" not in self.features:
            return dict(Builder.editor_keys(self))
        keys: dict[str, Any] = self.hook("editor_keys")()
        return keys

    def register_add_page(self, html: str) -> None:
        self.hook("register_add_page")(html)

    # ------------------------------------------------------------------ search
    def search_documents(self) -> list[str]:
        if "search" not in self.features:
            return list(Builder.search_documents(self))
        return [d.id if isinstance(d, Doc) else d for d in self.hook("search_documents")()]

    def search_record(self, doc_id: str) -> dict[str, Any]:
        if "search" not in self.features:
            return Builder.search_record(self, doc_id)
        record: dict[str, Any] = self.hook("search_record")(self.doc(doc_id))
        return record

    def search_sections(self, doc_id: str) -> list[Any]:
        if "search" not in self.features:
            return list(Builder.search_sections(self, doc_id))
        return list(self.hook("search_sections")(self.doc(doc_id)))

#!/usr/bin/env python

"""
Features: the parts a theme switches on by name.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

A feature is a class that declares what it needs and brings, and does its work
at fixed stages of the build. A theme lists the features it wants:

    class Theme(BaseTheme):
        features = ("documents", "search")

KB4IT expands bundles and requirements, orders the features so a feature runs
after the ones it requires or uses, and calls each one at its stage. A theme
customises a feature with class attributes (the feature's `options`) and with
methods named like the feature's `hooks`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, ClassVar, Iterable, Mapping

from kb4it.core.exceptions import ThemeError

if TYPE_CHECKING:
    from kb4it.theme.site import Doc, Site


class Feature:
    """Base class of a feature. Subclass it for a theme-local feature and list the class in features."""

    #: Unique name, used in `features` and in site.features.
    name: ClassVar[str] = ""
    #: Features switched on with this one; they run before it.
    requires: ClassVar[tuple[str, ...]] = ()
    #: Features read when they are on, never switched on by this one; they run before it.
    uses: ClassVar[tuple[str, ...]] = ()
    #: Theme class attributes this feature reads, with their defaults.
    options: ClassVar[Mapping[str, Any]] = {}
    #: Theme methods this feature calls when the theme defines them; the default is the feature's own method.
    hooks: ClassVar[tuple[str, ...]] = ()
    #: Templates the theme must have (in its folder, its base or the common templates).
    templates: ClassVar[tuple[str, ...]] = ()
    #: Vendor libraries (resources/vendor/<name>) added to theme.json "assets".
    assets: ClassVar[tuple[str, ...]] = ()
    #: Source file names the build refuses, because the feature writes a page with that name.
    reserves: ClassVar[tuple[str, ...]] = ()
    #: theme.json keys this feature sets; a different value in theme.json is an error.
    theme_json: ClassVar[Mapping[str, Any]] = {}

    def __init__(self, theme: Any, engine: Any) -> None:
        self.theme = theme
        self.engine = engine

    def __repr__(self) -> str:
        return f"<feature {self.name}>"

    @property
    def site(self) -> Site:
        site: Site = self.engine.site
        return site

    def option(self, name: str) -> Any:
        """The theme's value of one of this feature's options, else its default."""
        return getattr(self.theme, name, self.options[name])

    def hook(self, name: str) -> Callable[..., Any]:
        """The theme's method `name` when the theme defines it, else this feature's own."""
        own = getattr(self, name)
        method = getattr(type(self.theme), name, None)
        if method is None:
            return own  # type: ignore[no-any-return]
        return getattr(self.theme, name)  # type: ignore[no-any-return]

    # Stages, all optional.
    def prepare(self, site: Site) -> None:
        """After the documents are read, before any page is built: compute what the feature needs."""

    def pages(self, site: Site) -> None:
        """Before the theme's build(): write the feature's pages."""

    def page_context(self, doc: Doc, var: dict[str, Any]) -> dict[str, Any]:
        """Add the feature's data to the var of every document page."""
        return var

    def after_build(self, site: Site) -> None:
        """After the documents are compiled."""

    def after_deploy(self, site: Site) -> None:
        """After the site is in target."""


FeatureSpec = "str | type[Feature]"


def _named(registry: Mapping[str, type[Feature]], spec: Any) -> type[Feature]:
    if isinstance(spec, type) and issubclass(spec, Feature):
        if not spec.name:
            raise ThemeError(f"feature class {spec.__name__} has no name")
        return spec
    if isinstance(spec, str) and spec in registry:
        return registry[spec]
    known = ", ".join(sorted(registry))
    raise ThemeError(f"unknown feature {spec!r}; built-in features: {known}")


def resolve(declared: Iterable[Any], registry: Mapping[str, type[Feature]],
            bundles: Mapping[str, tuple[str, ...]]) -> list[type[Feature]]:
    """The feature classes to switch on, in the order their stages run.

    declared holds names (built-in features or bundles) and Feature subclasses. Bundles
    expand in place, requirements come before the feature that requires them, and a
    feature runs after every enabled feature it requires or uses; ties keep the order
    of declaration.
    """
    order: list[type[Feature]] = []
    seen: dict[str, type[Feature]] = {}

    def add(spec: Any, chain: tuple[str, ...]) -> None:
        if isinstance(spec, str) and spec in bundles:
            for member in bundles[spec]:
                add(member, chain)
            return
        cls = _named(registry, spec)
        if cls.name in seen:
            if seen[cls.name] is not cls:
                raise ThemeError(f"two features are named {cls.name!r}")
            return
        if cls.name in chain:
            raise ThemeError(f"features require each other: {' -> '.join(chain + (cls.name,))}")
        for required in cls.requires:
            add(required, chain + (cls.name,))
        seen[cls.name] = cls
        order.append(cls)

    for spec in declared:
        add(spec, ())

    # Stable topological order on requires and uses (uses only when that feature is on).
    position = {cls.name: i for i, cls in enumerate(order)}
    result: list[type[Feature]] = []
    done: set[str] = set()

    def place(cls: type[Feature], chain: tuple[str, ...]) -> None:
        if cls.name in done:
            return
        if cls.name in chain:
            raise ThemeError(f"features use each other: {' -> '.join(chain + (cls.name,))}")
        before = sorted((n for n in (*cls.requires, *cls.uses) if n in seen), key=position.__getitem__)
        for name in before:
            place(seen[name], chain + (cls.name,))
        done.add(cls.name)
        result.append(cls)

    for cls in order:
        place(cls, ())
    return result


def theme_json_keys(features: Iterable[type[Feature]], document_pages: bool) -> dict[str, Any]:
    """The theme.json keys the features set, assets merged."""
    keys: dict[str, Any] = {"metadata_pages": document_pages}
    assets: list[str] = []
    for cls in features:
        for key, value in cls.theme_json.items():
            if key in keys and keys[key] != value:
                raise ThemeError(f"features disagree on theme.json {key!r}")
            keys[key] = value
        for asset in cls.assets:
            if asset not in assets:
                assets.append(asset)
    keys["assets"] = assets
    return keys


def apply_theme_json(theme: dict[str, Any], keys: Mapping[str, Any], theme_id: str) -> None:
    """Fill theme.json (the runtime copy) with the keys the features set.

    A key theme.json sets to another value is a ThemeError naming both; assets are merged.
    """
    for key, value in keys.items():
        if key == "assets":
            current = list(theme.get("assets") or [])
            theme["assets"] = current + [a for a in value if a not in current]
            continue
        if key in theme and theme[key] != value:
            raise ThemeError(f"theme {theme_id}: theme.json {key!r} is {theme[key]!r}, but its features "
                             f"need {value!r}; remove the key from theme.json")
        theme[key] = value

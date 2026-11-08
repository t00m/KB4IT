"""The built-in features. A feature here imports kb4it.theme, kb4it.core and its own helpers,
never another feature module; it reaches other features through requires, uses and site.features."""

from __future__ import annotations

from kb4it.theme.feature import Feature
from kb4it.theme.features.search import Search

#: Built-in features by name.
REGISTRY: dict[str, type[Feature]] = {cls.name: cls for cls in (Search,)}

#: Names that stand for several features.
BUNDLES: dict[str, tuple[str, ...]] = {}

#: The names a theme can list in `features`.
FEATURES: tuple[str, ...] = tuple(sorted((*REGISTRY, *BUNDLES)))

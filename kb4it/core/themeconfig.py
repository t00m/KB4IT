"""Theme settings (P5).

A theme may set the class attribute `config_class` to a dataclass. Its settings are,
in this order: the field defaults, the theme.json keys named like a field, and the
repo.json block named after the theme id (`"techdoc": {...}`). Frontend builds the
object when the theme loads and stores it as `theme.config`. A theme without a
config_class gets a ThemeSettings that wraps its theme.json dict.
"""

import dataclasses
import typing

from kb4it.core.exceptions import ThemeError

# Field types checked by build_config; any other annotation is not checked.
CHECKED_TYPES = {bool: "true or false", int: "a whole number", float: "a number", str: "a text",
                 list: "a list", dict: "an object"}


class ThemeSettings:
    """Read-only view of a theme.json dict, for themes without a config_class."""

    def __init__(self, data):
        self._data = dict(data or {})

    def get(self, name, default=None):
        return self._data.get(name, default)

    def __getitem__(self, name):
        return self._data[name]

    def __contains__(self, name):
        return name in self._data


def _field_types(config_class) -> dict:
    hints = typing.get_type_hints(config_class)
    return {f.name: hints.get(f.name) for f in dataclasses.fields(config_class)}


def _defaults(config_class) -> dict:
    values = {}
    for f in dataclasses.fields(config_class):
        if f.default is not dataclasses.MISSING:
            values[f.name] = f.default
        elif f.default_factory is not dataclasses.MISSING:
            values[f.name] = f.default_factory()
    return values


def _type_ok(value, expected) -> bool:
    origin = typing.get_origin(expected) or expected
    if origin not in CHECKED_TYPES:
        return True
    if origin is bool:
        return isinstance(value, bool)
    if origin in (int, float):
        return isinstance(value, (int, float) if origin is float else int) and not isinstance(value, bool)
    return isinstance(value, origin)


def repo_block(repo: dict, theme_id: str) -> dict:
    """The repo.json block named after the theme; ThemeError when it is not an object."""
    block = (repo or {}).get(theme_id)
    if block is None:
        return {}
    if not isinstance(block, dict):
        raise ThemeError(f"repo.json '{theme_id}' must be an object of theme settings")
    return block


def known_keys(config_class) -> set:
    """Keys a repo.json block may hold: SETTINGS_KEYS when the class defines it, else its field names."""
    keys = getattr(config_class, "SETTINGS_KEYS", None)
    return set(keys) if keys is not None else {f.name for f in dataclasses.fields(config_class)}


def build_config(config_class, theme_json: dict, repo: dict, theme_id: str) -> tuple[object, list[str]]:
    """Return (settings object, unknown keys of the repo.json block, sorted)."""
    types = _field_types(config_class)
    block = repo_block(repo, theme_id)
    merged = _defaults(config_class)
    merged.update({k: v for k, v in (theme_json or {}).items() if k in types})
    merged.update({k: v for k, v in block.items() if k in types})
    unknown = sorted(k for k in block if k not in known_keys(config_class))
    from_settings = getattr(config_class, "from_settings", None)
    if from_settings is not None:
        return from_settings(merged, repo or {}), unknown
    for key, value in merged.items():
        expected = types.get(key)
        if not _type_ok(value, expected):
            kind = CHECKED_TYPES[typing.get_origin(expected) or expected]
            raise ThemeError(f"theme setting '{key}' of {theme_id} must be {kind}")
    return config_class(**merged), unknown


def unknown_theme_settings(config_class, repo: dict, theme_id: str) -> list[str]:
    """Unknown keys of the repo.json block of a theme, for kb4it verify; [] without a config_class."""
    if config_class is None:
        return []
    return sorted(k for k in repo_block(repo, theme_id) if k not in known_keys(config_class))

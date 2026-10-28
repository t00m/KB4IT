"""
People: the repo.json "people" block and the author profiles of a knowledge base.

# File: people.py
# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from kb4it.core.exceptions import ConfigError
from kb4it.core.structured import CORE_KEYS

# A source with a Person key is a profile; Alias names the other spellings documents use.
RESERVED_KEYS = ("Person", "Alias")
PEOPLE_KEYS = ("keys", "contact_keys", "private")


@dataclass(frozen=True)
class PeopleSettings:
    """The repo.json "people" block, checked."""

    # Frontmatter keys whose values are people.
    keys: tuple[str, ...] = ("Author",)
    # Profile keys that tell readers how to reach the person.
    contact_keys: tuple[str, ...] = ("Email", "Phone", "Chat", "Url")
    # Profile keys kept out of the pages and the structured data.
    private: tuple[str, ...] = ()


def _key_list(block: Mapping[str, Any], name: str, default: tuple[str, ...], core_ok: bool) -> tuple[str, ...]:
    value = block.get(name, list(default))
    if not isinstance(value, list):
        raise ConfigError(f"repo.json 'people.{name}' must be a list such as [\"Author\"]")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise ConfigError(f"repo.json 'people.{name}' must be a list of key names")
    for item in value:
        if item in RESERVED_KEYS:
            raise ConfigError(f"repo.json 'people.{name}': {item} is reserved for profiles")
        if not core_ok and item in CORE_KEYS:
            raise ConfigError(f"repo.json 'people.{name}': {item} is a KB4IT key")
    return tuple(value)


def load_people(repo: Mapping[str, Any]) -> PeopleSettings:
    """PeopleSettings from repo.json; ConfigError names the first bad entry."""
    block = repo.get("people")
    if block is None:
        return PeopleSettings()
    if not isinstance(block, dict):
        raise ConfigError("repo.json 'people' must be an object such as {\"keys\": [\"Author\"]}")
    unknown = sorted(set(block) - set(PEOPLE_KEYS))
    if unknown:
        raise ConfigError(f"repo.json 'people' has unknown key {unknown[0]!r}; known keys: {', '.join(PEOPLE_KEYS)}")
    defaults = PeopleSettings()
    keys = _key_list(block, "keys", defaults.keys, core_ok=False)
    if not keys:
        raise ConfigError("repo.json 'people.keys' must name at least one key")
    return PeopleSettings(keys=keys,
                          contact_keys=_key_list(block, "contact_keys", defaults.contact_keys, core_ok=True),
                          private=_key_list(block, "private", defaults.private, core_ok=True))

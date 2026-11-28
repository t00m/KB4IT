"""
Profiles settings: the repo.json "profiles" block, and the old "people" block read in its place (spec D6).

# File: profiles.py
# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from kb4it.core.dateclass import date_key_names
from kb4it.core.exceptions import ConfigError
from kb4it.core.people import RESERVED_KEYS, PeopleSettings, load_people
from kb4it.core.structured import CORE_KEYS, check_person_target

ENTRY_KEYS = ("type", "contact_keys", "missing", "tip", "map")
MISSING = ("penalty", "notice", "none")
# "property" or "property:Type", schema.org style.
TARGET_RE = re.compile(r"^[a-z][A-Za-z]*(:[A-Z][A-Za-z]*)?$")
PERSON_TIP = ("Role", "Team")


@dataclass(frozen=True)
class KeyProfile:
    """What profiles of one key do: schema.org type, contact keys, cost of a missing profile, tooltip, map."""

    type: str = "Thing"
    contact_keys: tuple[str, ...] = ()
    missing: str = "none"
    tip: tuple[str, ...] = ()
    map: dict[str, str | None] = field(default_factory=dict)


@dataclass(frozen=True)
class ProfilesSettings:
    """The profiled keys and the profile keys kept private everywhere."""

    keys: dict[str, KeyProfile]
    private: tuple[str, ...] = ()

    def people_keys(self) -> tuple[str, ...]:
        return tuple(key for key, entry in self.keys.items() if entry.type == "Person")

    def entry(self, key: str) -> KeyProfile:
        return self.keys.get(key) or KeyProfile()


def _person(people: PeopleSettings) -> KeyProfile:
    return KeyProfile("Person", tuple(people.contact_keys), "penalty", PERSON_TIP, dict(people.map))


def _names(value: Any, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ConfigError(f"repo.json '{where}' must be a list of key names")
    return tuple(value)


def _entry(key: str, spec: Any) -> KeyProfile:
    where = f"profiles.{key}"
    if not isinstance(spec, dict):
        raise ConfigError(f"repo.json '{where}' must be an object such as {{\"type\": \"Organization\"}}")
    unknown = sorted(set(spec) - set(ENTRY_KEYS))
    if unknown:
        raise ConfigError(f"repo.json '{where}' has unknown key {unknown[0]!r}; known keys: {', '.join(ENTRY_KEYS)}")
    kind = spec.get("type", "Thing")
    if not isinstance(kind, str) or not re.fullmatch(r"[A-Z][A-Za-z]*", kind):
        raise ConfigError(f"repo.json '{where}.type' must be a schema.org type such as \"Organization\"")
    missing = spec.get("missing", "none")
    if missing not in MISSING:
        raise ConfigError(f"repo.json '{where}.missing' must be one of {', '.join(MISSING)}")
    mapping = spec.get("map", {})
    if not isinstance(mapping, dict):
        raise ConfigError(f"repo.json '{where}.map' must be an object of profile key -> schema.org property")
    for name, target in mapping.items():
        if target is None:
            continue
        if kind == "Person":
            check_person_target(f"{where}.map.{name}", target)
        elif not isinstance(target, str) or not TARGET_RE.fullmatch(target):
            raise ConfigError(f"repo.json '{where}.map.{name}' must be \"property\" or \"property:Type\"")
    return KeyProfile(kind, _names(spec.get("contact_keys", []), f"{where}.contact_keys"), missing,
                      _names(spec.get("tip", []), f"{where}.tip"), dict(mapping))


def load_profiles(repo: Mapping[str, Any]) -> tuple[ProfilesSettings, list[str]]:
    """The profiles settings of repo.json and its notice lines; ConfigError names the first bad entry."""
    block = repo.get("profiles")
    # With both blocks, profiles decides and people is not read at all.
    notices = ["PEOPLE_BLOCK_IGNORED" if block is not None else "PEOPLE_BLOCK_DEPRECATED"] if "people" in repo else []
    if block is None:
        people = load_people(repo)
        return ProfilesSettings({key: _person(people) for key in people.keys}, tuple(people.private)), notices
    if not isinstance(block, dict):
        raise ConfigError("repo.json 'profiles' must be an object of key -> settings, such as {\"Team\": {}}")
    dates = date_key_names(repo)
    keys: dict[str, KeyProfile] = {}
    for key, spec in block.items():
        if key in dates:
            raise ConfigError(f"repo.json 'profiles.{key}': {key} is a date key")
        if key in CORE_KEYS or key in RESERVED_KEYS:
            raise ConfigError(f"repo.json 'profiles.{key}': {key} is a KB4IT key")
        keys[key] = _entry(key, spec)
    private = _names(repo.get("profiles_private", []), "profiles_private")
    return ProfilesSettings(keys, private), notices


def people_settings(settings: ProfilesSettings) -> PeopleSettings:
    """The PeopleSettings the author features take: the Person keys, else Author."""
    keys = settings.people_keys()
    first = settings.entry(keys[0]) if keys else KeyProfile()
    contact = first.contact_keys if keys else PeopleSettings().contact_keys
    return PeopleSettings(keys=keys or ("Author",), contact_keys=contact, private=settings.private, map=dict(first.map))


def key_notices(people, documents: Iterable[Mapping[str, list[str]]], settings: ProfilesSettings) -> list[str]:
    """Information about profiles of keys other than the people keys.

    PROFILE_UNUSED for a profile whose value no document uses under its keys, and VALUE_NO_PROFILE
    for each value of a key with missing "notice" that has no profile (the people keys have their own).
    """
    person_keys = set(people.people_keys)
    used: dict[str, set[str]] = {}
    for keys in documents:
        for key, values in keys.items():
            used.setdefault(key, set()).update(str(v).strip() for v in values or [] if str(v).strip())
    lines = []
    for profile in people.all_profiles():
        if set(profile.keys) & person_keys:
            continue
        if not any(name in used.get(key, ()) for key in profile.keys for name in people.names(profile)):
            lines.append(f"PROFILE_UNUSED person={profile.person} doc={profile.doc_id}")
    for key, entry in settings.keys.items():
        if entry.missing != "notice" or key in person_keys:
            continue
        counts: dict[str, int] = {}
        for keys in documents:
            for value in {str(v).strip() for v in keys.get(key) or [] if str(v).strip()}:
                if people.lookup(value, key) is None:
                    counts[value] = counts.get(value, 0) + 1
        lines += [f"VALUE_NO_PROFILE key={key} value={value} docs={n}" for value, n in sorted(counts.items())]
    return sorted(lines)

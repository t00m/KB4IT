"""
People: the repo.json "people" block and the author profiles of a knowledge base.

# File: people.py
# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from kb4it.core.exceptions import ConfigError
from kb4it.core.files import get_hash_from_dict, valid_filename
from kb4it.core.mdlinks import document_body
from kb4it.core.structured import CORE_KEYS

# A source with a Person key is a profile; Alias names the other spellings documents use.
RESERVED_KEYS = ("Person", "Alias")
PEOPLE_KEYS = ("keys", "contact_keys", "private")
# Profile keys whose values make the tooltip of a person's name on document pages.
TIP_KEYS = ("Role", "Team")
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
PHONE_RE = re.compile(r"\+?[\d\s().-]{7,}")


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


@dataclass(frozen=True)
class Profile:
    """One profile document: the person it describes, the other spellings, its keys and its body."""

    doc_id: str
    person: str
    aliases: tuple[str, ...]
    values: dict[str, list[str]]
    body: str


@dataclass(frozen=True)
class ProfileProblem:
    """A profile left out of the build: PROFILE_INVALID, PROFILE_DUPLICATE or PROFILE_ALIAS_IS_PERSON."""

    code: str
    doc_id: str
    detail: str


class People:
    """The profiles of a knowledge base, found by Person or by Alias."""

    def __init__(self, profiles: Iterable[Profile] = ()):
        self.profiles: dict[str, Profile] = {}
        self._names: dict[str, Profile] = {}
        for profile in profiles:
            self.profiles[profile.person] = profile
            for name in self.names(profile):
                self._names[name] = profile

    def lookup(self, name: str) -> Profile | None:
        """The profile of a Person or Alias name; names match exactly."""
        return self._names.get(name)

    @staticmethod
    def names(profile: Profile) -> list[str]:
        return [profile.person, *profile.aliases]

    def alias_count(self) -> int:
        return sum(len(profile.aliases) for profile in self.profiles.values())

    def __len__(self) -> int:
        return len(self.profiles)


def is_profile(keys: Mapping[str, list[str]]) -> bool:
    """True for the keys of a profile document: it has a Person key, even an empty one."""
    return "Person" in keys


def _clean(values) -> list[str]:
    return [str(value).strip() for value in values or [] if str(value).strip()]


def build_people(entries: Iterable[tuple[str, dict[str, list[str]], str]],
                 settings: PeopleSettings) -> tuple[People, list[ProfileProblem]]:
    """The profiles of (doc_id, keys, Markdown text) entries, and the ones left out with the reason.

    A profile whose alias is another profile's Person is left out, wherever it comes; then a name
    already taken leaves out the later profile in doc_id order.
    """
    problems: list[ProfileProblem] = []
    candidates: list[Profile] = []
    for doc_id, keys, text in sorted(entries, key=lambda item: item[0]):
        persons = _clean(keys.get("Person"))
        if len(persons) != 1:
            problems.append(ProfileProblem("PROFILE_INVALID", doc_id, f"Person must hold one name, found {len(persons)}"))
            continue
        values = {key: _clean(vals) for key, vals in keys.items() if key not in (*RESERVED_KEYS, "Title")}
        aliases = tuple(dict.fromkeys(a for a in _clean(keys.get("Alias")) if a != persons[0]))
        candidates.append(Profile(doc_id, persons[0], aliases, values, document_body(text)))
    owners = {profile.person: profile.doc_id for profile in candidates}
    kept: list[Profile] = []
    for profile in candidates:
        clash = next((a for a in profile.aliases if owners.get(a, profile.doc_id) != profile.doc_id), None)
        if clash:
            problems.append(ProfileProblem("PROFILE_ALIAS_IS_PERSON", profile.doc_id,
                                           f"alias={clash} person_of={owners[clash]}"))
        else:
            kept.append(profile)
    taken: dict[str, str] = {}
    accepted: list[Profile] = []
    for profile in kept:
        clash = next((name for name in People.names(profile) if name in taken), None)
        if clash:
            problems.append(ProfileProblem("PROFILE_DUPLICATE", profile.doc_id, f"name={clash} kept={taken[clash]}"))
            continue
        taken.update({name: profile.doc_id for name in People.names(profile)})
        accepted.append(profile)
    return People(accepted), problems


def person_status(profile: Profile | None, settings: PeopleSettings) -> str:
    """'missing' (no profile), 'no_contact' (no visible contact key) or 'ok'."""
    if profile is None:
        return "missing"
    visible = [key for key in settings.contact_keys if key not in settings.private]
    return "ok" if any(profile.values.get(key) for key in visible) else "no_contact"


def person_tip(profile: Profile | None, settings: PeopleSettings) -> str:
    """Role and team of a person, for the tooltip of their name; empty without a profile or with both private."""
    if profile is None:
        return ""
    return ", ".join(value for key in TIP_KEYS if key not in settings.private for value in profile.values.get(key) or [])


def person_page(name: str, settings: PeopleSettings) -> str:
    """The value page of a person: the first people key and the name, such as Author_Jane_Doe.html."""
    return f"{valid_filename(settings.keys[0])}_{valid_filename(name)}.html"


def named_people(values_by_key: Mapping[str, list[str]], people: People, settings: PeopleSettings) -> list[str]:
    """The people a document names in the people keys: Person names where a profile exists, else the value."""
    found: list[str] = []
    for key in settings.keys:
        for value in _clean(values_by_key.get(key)):
            profile = people.lookup(value)
            name = profile.person if profile else value
            if name not in found:
                found.append(name)
    return found


def profile_hash(profile: Profile) -> str:
    return get_hash_from_dict(asdict(profile))


def notices(people: People, named: Mapping[str, int], settings: PeopleSettings,
            indexed: bool) -> dict[str, list[str]]:
    """Warnings and information about profiles; named is person name -> number of documents naming them."""
    warning, information = [], []
    for person, profile in people.profiles.items():
        if person_status(profile, settings) == "no_contact":
            warning.append(f"PROFILE_NO_CONTACT person={person} doc={profile.doc_id}")
        if person not in named:
            information.append(f"PROFILE_UNUSED person={person} doc={profile.doc_id}")
        if indexed:
            for key, values in profile.values.items():
                if key not in settings.private and any(EMAIL_RE.fullmatch(v) or PHONE_RE.fullmatch(v) for v in values):
                    information.append(f"PROFILE_CONTACT_PUBLIC person={person} key={key}")
    if people:
        information += [f"AUTHOR_NO_PROFILE person={name} docs={count}"
                        for name, count in named.items() if people.lookup(name) is None]
    return {"warning": sorted(warning), "information": sorted(information)}

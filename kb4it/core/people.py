"""
People: the repo.json "people" block and the author profiles of a knowledge base.

# File: people.py
# Author: Tomás Vírseda
# License: GPL v3
"""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from kb4it.core.dateclass import date_key_names
from kb4it.core.exceptions import ConfigError
from kb4it.core.files import get_hash_from_dict, valid_filename
from kb4it.core.mdlinks import document_body
from kb4it.core.structured import CORE_KEYS, check_person_target

# A source whose file name starts with PROFILE- (any case) is a profile. Its title is the value it
# describes, ProfileOf the key of that value, Alias the other spellings documents use. PERSON- is the
# old prefix, read as a profile of the first people key for one release.
PROFILE_PREFIX = "PROFILE-"
LEGACY_PREFIX = "PERSON-"
RESERVED_KEYS = ("Alias", "ProfileOf")
PEOPLE_GROUP = "\x00people"  # the group of every people key: they share person profiles
PEOPLE_KEYS = ("keys", "contact_keys", "private", "map")
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
    # Profile key -> schema.org property of the person ("property" or "property:Type"); None leaves the key out.
    map: dict[str, str | None] = field(default_factory=dict)


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
    dated = next((key for key in keys if key in date_key_names(repo)), None)
    if dated:
        raise ConfigError(f"repo.json 'people.keys': {dated} is a date key")
    return PeopleSettings(keys=keys,
                          contact_keys=_key_list(block, "contact_keys", defaults.contact_keys, core_ok=True),
                          private=_key_list(block, "private", defaults.private, core_ok=True),
                          map=_person_map(block.get("map", {})))


def _person_map(raw: Any) -> dict[str, str | None]:
    if not isinstance(raw, dict):
        raise ConfigError("repo.json 'people.map' must be an object of profile key -> schema.org property")
    mapping: dict[str, str | None] = {}
    for key, spec in raw.items():
        if key in RESERVED_KEYS:
            raise ConfigError(f"repo.json 'people.map.{key}': {key} is mapped by KB4IT and cannot be changed")
        if spec is not None:
            check_person_target(f"people.map.{key}", spec)
        mapping[str(key)] = spec
    return mapping


@dataclass(frozen=True)
class Profile:
    """One profile document: the value it describes (person), the other spellings, its keys and its body."""

    doc_id: str
    person: str
    aliases: tuple[str, ...]
    values: dict[str, list[str]]
    body: str
    keys: tuple[str, ...] = ("Author",)  # ProfileOf


@dataclass(frozen=True)
class ProfileProblem:
    """A profile left out of the build: PROFILE_INVALID, PROFILE_DUPLICATE or PROFILE_ALIAS_IS_NAME."""

    code: str
    doc_id: str
    detail: str


class People:
    """The profiles of a knowledge base, found by key and name (the profile title) or Alias.

    The people keys form one group, so Author and Owner share a person's profile. profiles,
    len() and lookup(value) without a key mean the person profiles, as before profiles of
    other keys existed.
    """

    def __init__(self, profiles: Iterable[Profile] = (), people_keys: Iterable[str] = ("Author",)):
        self.people_keys = tuple(people_keys)
        self._all: list[Profile] = []
        self.profiles: dict[str, Profile] = {}
        self._names: dict[tuple[str, str], Profile] = {}
        for profile in profiles:
            self._all.append(profile)
            groups = self.groups(profile)
            if PEOPLE_GROUP in groups:
                self.profiles[profile.person] = profile
            for group in groups:
                for name in self.names(profile):
                    self._names[(group, name)] = profile

    def group(self, key: str | None) -> str:
        return PEOPLE_GROUP if key is None or key in self.people_keys else key

    def groups(self, profile: Profile) -> list[str]:
        return list(dict.fromkeys(self.group(key) for key in profile.keys))

    def lookup(self, name: str, key: str | None = None) -> Profile | None:
        """The profile of a name or an alias under a key (None: the people keys); names match exactly."""
        return self._names.get((self.group(key), name))

    def all_profiles(self) -> list[Profile]:
        return list(self._all)

    @staticmethod
    def names(profile: Profile) -> list[str]:
        return [profile.person, *profile.aliases]

    def alias_count(self) -> int:
        return sum(len(profile.aliases) for profile in self._all)

    def __len__(self) -> int:
        return len(self.profiles)


def is_profile(doc_id: str) -> bool:
    """True for a profile: its file name starts with PROFILE- or the old PERSON-, in any case."""
    return os.path.basename(doc_id).upper().startswith((PROFILE_PREFIX, LEGACY_PREFIX))


def is_legacy_profile(doc_id: str) -> bool:
    """True for a profile named with the old PERSON- prefix."""
    return os.path.basename(doc_id).upper().startswith(LEGACY_PREFIX)


def _clean(values) -> list[str]:
    return [str(value).strip() for value in values or [] if str(value).strip()]


def _profile_keys(doc_id: str, keys: dict[str, list[str]], settings: PeopleSettings,
                  refused: frozenset[str]) -> tuple[tuple[str, ...], str]:
    """(ProfileOf keys, reason it is invalid or '')."""
    targets = tuple(dict.fromkeys(_clean(keys.get("ProfileOf"))))
    if not targets:
        # Only a PROFILE- file must say its key; a PERSON- file is a person, as before.
        new = os.path.basename(doc_id).upper().startswith(PROFILE_PREFIX)
        return ((), "ProfileOf is missing") if new else ((settings.keys[0],), "")
    bad = next((key for key in targets if key in refused or key in RESERVED_KEYS), None)
    return (targets, f"ProfileOf names {bad}, which cannot have profiles") if bad else (targets, "")


def build_people(entries: Iterable[tuple[str, dict[str, list[str]], str]], settings: PeopleSettings,
                 refused: frozenset[str] = frozenset()) -> tuple[People, list[ProfileProblem]]:
    """The profiles of (doc_id, keys, Markdown text) entries, and the ones left out with the reason.

    The title of a profile is the value it describes. Under one key (all people keys count as one),
    a profile whose alias is another profile's name is left out, wherever it comes; then a name
    already taken leaves out the later profile in doc_id order.
    """
    problems: list[ProfileProblem] = []
    candidates: list[Profile] = []
    for doc_id, keys, text in sorted(entries, key=lambda item: item[0]):
        person = next(iter(_clean(keys.get("Title"))), "")
        # A comma splits values, so a name with one could never match.
        if "," in person or not valid_filename(person):
            problems.append(ProfileProblem("PROFILE_INVALID", doc_id, "the title must be one name, without a comma"))
            continue
        targets, reason = _profile_keys(doc_id, keys, settings, refused)
        if reason:
            problems.append(ProfileProblem("PROFILE_INVALID", doc_id, reason))
            continue
        values = {key: _clean(vals) for key, vals in keys.items() if key not in (*RESERVED_KEYS, "Title")}
        aliases = tuple(dict.fromkeys(a for a in _clean(keys.get("Alias")) if a != person))
        candidates.append(Profile(doc_id, person, aliases, values, document_body(text), targets))
    index = People((), settings.keys)
    owners = {(group, p.person): p.doc_id for p in candidates for group in index.groups(p)}
    kept: list[Profile] = []
    for profile in candidates:
        clash = next(((g, a) for g in index.groups(profile) for a in profile.aliases
                      if owners.get((g, a), profile.doc_id) != profile.doc_id), None)
        if clash:
            problems.append(ProfileProblem("PROFILE_ALIAS_IS_NAME", profile.doc_id,
                                           f"alias={clash[1]} name_of={owners[clash]}"))
        else:
            kept.append(profile)
    taken: dict[tuple[str, str], str] = {}
    accepted: list[Profile] = []
    for profile in kept:
        pairs = [(g, name) for g in index.groups(profile) for name in People.names(profile)]
        clash = next((pair for pair in pairs if pair in taken), None)
        if clash:
            problems.append(ProfileProblem("PROFILE_DUPLICATE", profile.doc_id, f"name={clash[1]} kept={taken[clash]}"))
            continue
        taken.update({pair: profile.doc_id for pair in pairs})
        accepted.append(profile)
    return People(accepted, settings.keys), problems


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


def first_paragraph(body: str) -> str:
    """The first paragraph of a profile text as plain text, for the description of the person."""
    for block in re.split(r"\n\s*\n", body):
        text = block.strip()
        if text and not text.startswith(("#", "```", "~~~", "|", "!!!", "<", "-", "*", ">")):
            text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
            return " ".join(re.sub(r"[*_`]+", "", text).split())
    return ""


def person_page(name: str, settings: PeopleSettings) -> str:
    """The value page of a person: the first people key and the name, such as Author_Jane_Doe.html."""
    return f"{valid_filename(settings.keys[0])}_{valid_filename(name)}.html"


def named_people(values_by_key: Mapping[str, list[str]], people: People, settings: PeopleSettings) -> list[str]:
    """The people a document names in the people keys: the profile name where a profile exists, else the value."""
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

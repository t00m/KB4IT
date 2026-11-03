#!/usr/bin/python
"""
People service: the author profiles of a build and the pages they rebuild (see core/people.py).

# File: people.py
# Author: Tomás Vírseda
# License: GPL v3
"""

from kb4it.core.dateclass import date_key_names
from kb4it.core.people import (RESERVED_KEYS, PeopleSettings, build_people, is_legacy_profile, person_page,
                               person_status, person_tip, profile_hash)
from kb4it.core.util import valid_filename
from kb4it.core.log import q


def profile_page(name: str, keys, settings: PeopleSettings) -> str:
    """The page a link to a profile leads to: the person's page, else the value page of its first key."""
    keys = list(keys or [settings.keys[0]])
    if any(key in settings.keys for key in keys):
        return person_page(name, settings)
    return f"{valid_filename(keys[0])}_{valid_filename(name)}.html"


def expand_keys(keys, settings: PeopleSettings) -> list[str]:
    """The keys whose value pages show a profile: a people key stands for every people key."""
    found: list[str] = []
    for key in keys or [settings.keys[0]]:
        for one in (settings.keys if key in settings.keys else (key,)):
            if one not in found:
                found.append(one)
    return found


def refused_keys(repo) -> frozenset[str]:
    """Keys ProfileOf may not name: date keys, blocked and ignored keys, and the reserved profile keys."""
    return date_key_names(repo) | {"Title", "SystemPage"} | set(repo.get("ignored_keys") or []) | set(RESERVED_KEYS)


class PeopleMixin:
    """Profile methods of Processor."""

    def load_people(self, profiles) -> None:
        """Profiles into srvdtb.people and kbdict["profiles"]; a bad one is left out like an invalid document."""
        settings = getattr(self.srvbes, "people", None) or PeopleSettings()
        for doc_id, _keys, _text in profiles:
            if is_legacy_profile(doc_id):
                self.log.warning(f"[PEOPLE] PROFILE_PERSON_PREFIX doc={q(doc_id)} hint=rename to PROFILE- and add ProfileOf")
        people, problems = build_people(profiles, settings, refused_keys(self.srvbes.get_dict("repo") or {}))
        for problem in problems:
            self.log.error(f"[PEOPLE] {problem.code} doc={q(problem.doc_id)} detail={q(problem.detail)}")
            self.plan.invalid_docs.append((problem.doc_id, problem.code))
        # A ProfileOf that names a key no document uses and repo.json does not profile is most likely a
        # value written where the key belongs (ProfileOf: Jane Doe instead of ProfileOf: Author).
        profiled = set(getattr(getattr(self.srvbes, "profiles", None), "keys", None) or ())
        known = set(self.kbdict_new.get("metadata") or {}) | set(settings.keys) | profiled
        for profile in people.all_profiles():
            for key in profile.keys:
                if key not in known:
                    self.log.warning(f"[PEOPLE] PROFILE_KEY_UNUSED doc={q(profile.doc_id)} key={q(key)} "
                                     f"hint=ProfileOf names the property, such as ProfileOf: {settings.keys[0]}")
        self.srvdtb.people = people
        self.plan.profile_count = len(people.all_profiles())
        self.plan.profile_pages = {p.doc_id: profile_page(p.person, p.keys, settings) for p in people.all_profiles()}
        persons = {p.doc_id for p in people.profiles.values()}
        self.kbdict_new["profiles"] = {
            p.doc_id: {"person": p.person, "aliases": list(p.aliases), "keys": list(p.keys), "hash": profile_hash(p),
                       "status": person_status(p, settings) if p.doc_id in persons else "",
                       "tip": person_tip(p, settings) if p.doc_id in persons else ""}
            for p in people.all_profiles()}
        self.log.info(f"[PEOPLE] LOADED profiles={len(people)} aliases={q(people.alias_count())}")

    def people_changes(self) -> tuple[set, set]:
        """(key, value) pages to force and documents to rebuild because a profile changed since the last build.

        A changed, new or removed profile forces the pages of all its names. A document is rebuilt when a
        person it names changed status (no profile, no contact, ok) or tooltip (role and team), when it links to a source whose person
        page changed, and every document that names anyone is rebuilt when the first profile appears or
        the last one goes.
        """
        settings = getattr(self.srvbes, "people", None) or PeopleSettings()
        old = self.kbdict_cur.get("profiles") or {}
        new = self.kbdict_new.get("profiles") or {}
        pairs = set()
        for doc_id in set(old) | set(new):
            before, after = old.get(doc_id), new.get(doc_id)
            if (before or {}).get("hash") == (after or {}).get("hash"):
                continue
            for entry in (before, after):
                if entry:
                    names = [entry["person"], *entry.get("aliases", [])]
                    pairs.update((key, name) for key in expand_keys(entry.get("keys"), settings) for name in names)

        def is_person(entry):
            return any(key in settings.keys for key in entry.get("keys") or [settings.keys[0]])

        def statuses(profiles):
            return {name: (entry.get("status", "missing"), entry.get("tip", ""))
                    for entry in profiles.values() if is_person(entry)
                    for name in [entry["person"], *entry.get("aliases", [])]}

        status_old, status_new = statuses(old), statuses(new)
        missing = ("missing", "")
        # The author checks turn on with the first person profile and off with the last one.
        flipped = any(map(is_person, old.values())) != any(map(is_person, new.values()))
        docs = set()
        for doc_id, entry in self.kbdict_new["document"].items():
            keys = entry.get("keys") or {}
            names = [v for key in settings.keys for v in keys.get(key) or [] if str(v).strip()]
            if names and (flipped or any(status_old.get(n, missing) != status_new.get(n, missing) for n in names)):
                docs.add(doc_id)
        # A link to a source leads to the person's page while the source is a profile: rebuild the documents
        # linking to a source that became a profile, stopped being one, or now names another person.
        page_old = {doc_id: profile_page(entry["person"], entry.get("keys"), settings) for doc_id, entry in old.items()}
        page_new = {doc_id: profile_page(entry["person"], entry.get("keys"), settings) for doc_id, entry in new.items()}
        moved = {doc_id for doc_id in set(page_old) | set(page_new) if page_old.get(doc_id) != page_new.get(doc_id)}
        if moved:
            for doc_id, targets in (self.kbdict_new.get("links") or {}).items():
                if doc_id in self.kbdict_new["document"] and any(path in moved for path, _frag in targets):
                    docs.add(doc_id)
            # A profile card may link to the moved profile too: rebuild every profiled value page.
            for entry in new.values():
                names = [entry["person"], *entry.get("aliases", [])]
                pairs.update((key, name) for key in expand_keys(entry.get("keys"), settings) for name in names)
        self.log.debug(f"[PEOPLE] REBUILD docs={len(docs)} pairs={len(pairs)}")
        return pairs, docs

    def profile_kv_paths(self, kv_values: set, forced: bool, force_kv_pairs: set) -> list:
        """(first people key, profile name, compile) for each profile no document names under that key yet.

        Its page is compiled when the build is forced, the profile changed (force_kv_pairs), or
        documents named the person in the previous build (the page held a list then).
        """
        settings = getattr(self.srvbes, "people", None) or PeopleSettings()
        key = settings.keys[0]
        paths = []
        for person in sorted(self.srvdtb.people.profiles):
            if (key, person) in kv_values:
                continue
            compile_value = forced or (key, person) in force_kv_pairs or bool(self.get_kbdict_value(key, person, new=False))
            paths.append((key, person, compile_value))
            self.log.debug(f"[PEOPLE] KV key={q(key)} value={q(person)} compile={q(compile_value)}")
        return paths

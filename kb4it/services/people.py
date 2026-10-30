#!/usr/bin/python
"""
People service: the author profiles of a build and the pages they rebuild (see core/people.py).

# File: people.py
# Author: Tomás Vírseda
# License: GPL v3
"""

from kb4it.core.people import PeopleSettings, build_people, person_page, person_status, person_tip, profile_hash


class PeopleMixin:
    """Profile methods of Processor."""

    def load_people(self, profiles) -> None:
        """Profiles into srvdtb.people and kbdict["profiles"]; a bad one is left out like an invalid document."""
        settings = getattr(self.srvbes, "people", None) or PeopleSettings()
        people, problems = build_people(profiles, settings)
        for problem in problems:
            self.log.error(f"[PEOPLE] {problem.code} doc={problem.doc_id} detail={problem.detail}")
            self.plan.invalid_docs.append((problem.doc_id, problem.code))
        self.srvdtb.people = people
        self.plan.profile_count = len(people)
        self.plan.profile_pages = {p.doc_id: person_page(p.person, settings) for p in people.profiles.values()}
        self.kbdict_new["profiles"] = {
            p.doc_id: {"person": p.person, "aliases": list(p.aliases), "hash": profile_hash(p),
                       "status": person_status(p, settings), "tip": person_tip(p, settings)}
            for p in people.profiles.values()}
        self.log.info(f"[PEOPLE] LOADED profiles={len(people)} aliases={people.alias_count()}")

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
                    pairs.update((key, name) for key in settings.keys for name in names)

        def statuses(profiles):
            return {name: (entry.get("status", "missing"), entry.get("tip", ""))
                    for entry in profiles.values() for name in [entry["person"], *entry.get("aliases", [])]}

        status_old, status_new = statuses(old), statuses(new)
        missing = ("missing", "")
        flipped = bool(old) != bool(new)
        docs = set()
        for doc_id, entry in self.kbdict_new["document"].items():
            keys = entry.get("keys") or {}
            names = [v for key in settings.keys for v in keys.get(key) or [] if str(v).strip()]
            if names and (flipped or any(status_old.get(n, missing) != status_new.get(n, missing) for n in names)):
                docs.add(doc_id)
        # A link to a source leads to the person's page while the source is a profile: rebuild the documents
        # linking to a source that became a profile, stopped being one, or now names another person.
        page_old = {doc_id: person_page(entry["person"], settings) for doc_id, entry in old.items()}
        page_new = {doc_id: person_page(entry["person"], settings) for doc_id, entry in new.items()}
        moved = {doc_id for doc_id in set(page_old) | set(page_new) if page_old.get(doc_id) != page_new.get(doc_id)}
        if moved:
            for doc_id, targets in (self.kbdict_new.get("links") or {}).items():
                if doc_id in self.kbdict_new["document"] and any(path in moved for path, _frag in targets):
                    docs.add(doc_id)
            # A profile card may link to the moved profile too: rebuild every person page.
            for entry in new.values():
                names = [entry["person"], *entry.get("aliases", [])]
                pairs.update((key, name) for key in settings.keys for name in names)
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
            self.log.debug(f"[PEOPLE] KV key={key} value={person} compile={compile_value}")
        return paths

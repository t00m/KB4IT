#!/usr/bin/env python
"""
Service Processor.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kb4it.core.types import KBDict

from kb4it.core.exceptions import CompilationError
from kb4it.core.log import get_logger
from kb4it.core.service import Service
from kb4it.services.addpage import ADD_DOC
from kb4it.core.documents import parse_markdown_attributes
from kb4it.core.files import read_document
from kb4it.core.mdlinks import scan_document
from kb4it.core.util import (get_hash_from_body,
                             get_hash_from_dict, html_id_for, is_windows_reserved,
                             page_name_clashes, string_timestamp, valid_filename,
                             SOURCE_ENCODING, timeit, tree_hash)

# repo.json keys that never reach a page: changing them must not rebuild the site.
NON_PAGE_KEYS = frozenset({"workers", "force", "fail_on_invalid", "source", "target"})


@dataclass
class AnalysisResult:
    """Carries the outputs of step_01_analysis so they are passed explicitly."""
    force_kv_pairs: set = field(default_factory=set)


@dataclass
class BuildPlan:
    """Full description of what a build will compile.

    Replaces the K_PATH/KV_PATH/ncd/nck side-channel keys previously written
    into runtime. Workflow, Compiler and Builder read this single source of
    truth instead of probing runtime.
    """
    docs_to_compile: set = field(default_factory=set)
    K_PATH: list = field(default_factory=list)   # [(key, values, compile_flag), ...]
    KV_PATH: list = field(default_factory=list)  # [(key, value, compile_flag), ...]
    force_kv_pairs: set = field(default_factory=set)
    force_all: bool = False
    invalid_docs: list = field(default_factory=list)  # [(docId, reason), ...]
    name_clashes: list = field(default_factory=list)  # [(docId, docId), ...] pages differing only by case
    backlinks: dict = field(default_factory=dict)  # {docId: [[title, source docId], ...]}

    @property
    def invalid_count(self) -> int:
        return len(self.invalid_docs)

    @property
    def doc_count(self) -> int:
        return len(self.docs_to_compile)

    @property
    def key_count(self) -> int:
        return sum(1 for _, _, flag in self.K_PATH if flag)

    @property
    def kv_count(self) -> int:
        return sum(1 for _, _, flag in self.KV_PATH if flag)


class Processor(Service):
    """KB4IT Processor Service."""

    def __init__(self, backend: Any, db: Any, theme: Any) -> None:
        """Processor of one build; the pipeline gives it the backend, the database and the theme."""
        super().__init__()
        self.log = get_logger(self.modname)
        self.started = True
        self.srvbes = backend
        self.srvdtb = db
        self.srvthm = theme
        self.kbdict_cur: KBDict = self.srvbes.load_kbdict()  # Previous run
        self.kbdict_new: KBDict = {"document": {}, "metadata": {}}
        self.plan = BuildPlan()

    def _forced(self) -> bool:
        """Every page is rebuilt: asked for (--force, repo.json "force") or decided by the backend."""
        return bool(self.srvbes.get_value("app", "force") or self.srvbes.get_value("runtime", "force_all"))

    @property
    def changed_docs(self) -> set:
        return self.plan.docs_to_compile

    def get_plan(self) -> BuildPlan:
        """Return the current BuildPlan."""
        return self.plan

    @timeit
    def step_00_extraction(self):
        """Extract metadata."""
        runtime = self.srvbes.get_dict("runtime")
        sources = self.srvbes.get_value("docs", "bag")
        for first, second in page_name_clashes(os.path.basename(f) for f in sources):
            self.log.warning(f"[PROCESSOR] DOC_NAME_CLASH a={first} b={second}")
            self.plan.name_clashes.append((first, second))
        for filepath in sources:
            # Get Id
            docId = os.path.basename(filepath)

            # A page Windows cannot create is left out everywhere, so a site builds the same on every system.
            if is_windows_reserved(docId) or docId in getattr(self.srvthm, "reserved_pages", ()) \
                    or (docId == ADD_DOC and getattr(self.srvthm, "editor_enabled", lambda: False)()):
                self.log.error(f"[PROCESSOR] DOC_NAME_RESERVED doc={docId}")
                self.plan.invalid_docs.append((docId, "reserved_name"))
                continue

            # Read the file once. The byte hash lets the next build reuse the parsed header.
            try:
                content, file_hash = read_document(filepath)
            except Exception as err:
                self.log.error(f"[UTIL] DOC_INVALID doc={docId} reason=error error={err}")
                self.plan.invalid_docs.append((docId, str(err)))
                continue

            current = (self.kbdict_cur.get("document") or {}).get(docId) or {}
            cached = bool(current.get("file_hash")) and current.get("file_hash") == file_hash \
                and not current.get("warned", False)
            if cached:
                keys = current.get("keys") or {}
                valid, reason, warned = True, "Success", False
                b_hash = current.get("body_hash")
                m_hash = current.get("metadata_hash")
                cache_action, cache_reason = "reuse", "unchanged"
            else:
                keys, valid, reason, warned = parse_markdown_attributes(content, docId)
                if current.get("warned"):
                    cache_reason = "warning"
                elif current.get("file_hash"):
                    cache_reason = "changed"
                else:
                    cache_reason = "missing"
                cache_action = "parse"
                if valid:
                    b_hash = get_hash_from_body(filepath, content=content)
                    m_hash = get_hash_from_dict(keys)
                else:
                    b_hash = m_hash = None
            self.log.debug(f"[PROCESSOR] HEADER_CACHE doc={docId} action={cache_action} reason={cache_reason}")
            self.log.debug(f"[PROCESSOR] DOC_VALID doc={docId} valid={valid} reason={reason}")

            if not valid:
                self.plan.invalid_docs.append((docId, reason))
                continue

            # Add to cache
            entry = {"content": filepath, "keys": keys, "file_hash": file_hash, "warned": warned}
            self.kbdict_new["document"][docId] = entry

            # Add to the in-memory database
            self.srvdtb.add_document(docId)
            for key in keys:
                alist = keys[key]
                for value in alist:
                    if len(value.strip()) == 0:
                        continue
                    if key == "Date":
                        value = string_timestamp(value)
                    self.srvdtb.add_document_key(docId, key, value)

                    # For each document and for each key/value linked to that document add an entry to kbdic['document']
                    try:
                        values = self.kbdict_new["document"][docId][key]
                        if value not in values:
                            values.append(value)
                    except KeyError:
                        self.kbdict_new["document"][docId][key] = [value]

                    # And viceversa, for each key/value add to kbdict['metadata'] all documents linked
                    try:
                        self.kbdict_new["metadata"][key][value].append(docId)
                    except KeyError:
                        if key not in self.kbdict_new["metadata"]:
                            self.kbdict_new["metadata"][key] = {}
                        if value not in self.kbdict_new["metadata"][key]:
                            self.kbdict_new["metadata"][key][value] = [docId]

            # Sorted once per document, not after each value.
            for key in keys:
                values = self.kbdict_new["document"][docId].get(key)
                if isinstance(values, list):
                    values.sort()

            # To track changes in a document, hashes for metadata and
            # content are created. Comparing them with those in the
            # cache, KB4IT determines if a document must be compiled
            # again. Very useful to reduce the compilation time.

            # Body and metadata hashes were computed while parsing, or taken from the cache.
            entry["body_hash"] = b_hash
            entry["metadata_hash"] = m_hash
            self.log.debug(f"[PROCESSOR] HASH doc={docId} body={b_hash} meta={m_hash}")

            # Add compiled page to the target list
            htmlId = html_id_for(docId)
            self.srvbes.add_target(docId, htmlId)

        # Sorted once, after every document: sorting after each append grew with the square of the documents.
        # The sort is stable, so documents read in the same order give the same list as before.
        for values in self.kbdict_new["metadata"].values():
            for documents in values.values():
                documents.sort(key=str.lower)

        # A repo can ask that any unreadable document fails the build instead of vanishing.
        problems = self.plan.invalid_docs + [(b, f"name_clash_with={a}") for a, b in self.plan.name_clashes]
        if problems and self.srvbes.get_value("repo", "fail_on_invalid") is True:
            names = ", ".join(f"{doc} ({reason})" for doc, reason in problems)
            raise CompilationError(f"{len(problems)} invalid document(s): {names}")

        # Rebuild every page when the theme says the site as a whole changed.
        signature = self.srvthm.site_signature()
        self.kbdict_new["site_signature"] = signature
        self.plan.force_all = bool(signature) and signature != self.kbdict_cur.get("site_signature", "")
        if self.plan.force_all:
            self.log.info("[PROCESSOR] SITE_SIGNATURE_CHANGED action=rebuild_all")

        # And when a core setting that shapes every page changed (Markdown settings, overrides, hooks).
        core = self.core_signature()
        self.kbdict_new["core_signature"] = core
        if self.kbdict_cur.get("document") and core != self.kbdict_cur.get("core_signature"):
            self.plan.force_all = True
            self.log.info("[PROCESSOR] CORE_SIGNATURE_CHANGED action=rebuild_all")

        # The new kbdict stays in memory; Backend.commit_kbdict() writes it once the build succeeded.


    def signature_parts(self) -> dict:
        """Core settings whose change must rebuild every page; each feature adds its own entry."""
        repo = self.srvbes.get_dict("repo")
        # site_url and og_image end up in every page head (canonical link, Open Graph tags).
        return {"markdown": repo.get("markdown") or {}, "search": repo.get("search", True),
                "site_url": repo.get("site_url"), "og_image": repo.get("og_image"), "feed": repo.get("feed"),
                "overrides": tree_hash(getattr(self.srvbes, "overrides_dir", None)),
                "hooks": self.srvbes.hooks.signature() if getattr(self.srvbes, "hooks", None) else "",
                "backlinks": repo.get("backlinks", True),
                # Theme templates, logic and assets, its template base and the common templates (TV-05).
                "theme": (self.srvbes.get_dict("runtime").get("theme") or {}).get("fingerprint", ""),
                # Any other setting may be printed by the theme (title, tagline, menus): rebuild on change.
                "repo": get_hash_from_dict({k: v for k, v in repo.items() if k not in NON_PAGE_KEYS})}

    def core_signature(self) -> str:
        """Hash of signature_parts(), stored in kbdict.json next to the theme's site signature."""
        return get_hash_from_dict(self.signature_parts())

    def document_links(self) -> dict:
        """Outgoing links to other sources: {docId: [[target docId, fragment], ...]}.

        Only documents whose body changed are parsed; the others keep the links stored in kbdict.json.
        """
        known = set(self.kbdict_new["document"])
        links_cur = self.kbdict_cur.get("links", {}) or {}
        links = {}
        for doc_id, entry in self.kbdict_new["document"].items():
            cur = self.kbdict_cur.get("document", {}).get(doc_id, {})
            if doc_id in links_cur and cur.get("body_hash") == entry.get("body_hash"):
                links[doc_id] = links_cur[doc_id]
                continue
            try:
                found, _anchors, _bare = scan_document(entry["content"])
            except Exception as err:
                self.log.warning(f"[LINKS] SCAN_FAIL doc={doc_id} error={err}")
                found = []
            pairs = sorted({(os.path.normpath(path).replace(os.sep, "/"), frag) for path, frag in found})
            links[doc_id] = [[path, frag] for path, frag in pairs]
        self.log.debug(f"[LINKS] SCANNED docs={len(known)}")
        return links

    def backlinks_from(self, links, titles) -> dict:
        """{target docId: [[source title, source docId], ...]} sorted by title, for existing targets only."""
        back = {}
        for source, targets in links.items():
            for path, _frag in targets:
                if path in titles and path != source:
                    back.setdefault(path, set()).add((titles.get(source, source), source))
        return {doc: [list(item) for item in sorted(items)] for doc, items in back.items()}

    @timeit
    def step_01_analysis(self):
        """Compilation strategy."""
        analysis = AnalysisResult()
        sources = self.srvbes.get_value("docs", "bag")
        ignored = set(self.srvdtb.get_ignored_keys())
        blocked = set(self.srvdtb.get_blocked_keys())

        # Links between documents: a page whose list of linking pages changed is rebuilt.
        links = self.document_links()
        self.kbdict_new["links"] = links
        titles_new = {d: (e.get("Title") or [d])[0] for d, e in self.kbdict_new["document"].items()}
        titles_cur = {d: (e.get("Title") or [d])[0] for d, e in (self.kbdict_cur.get("document") or {}).items()}
        self.plan.backlinks = self.backlinks_from(links, titles_new)
        backlinks_cur = self.backlinks_from(self.kbdict_cur.get("links", {}) or {}, titles_cur)
        backlinks_changed = {d for d in titles_new if self.plan.backlinks.get(d) != backlinks_cur.get(d)}
        for doc in sorted(backlinks_changed):
            self.log.debug(f"[LINKS] BACKLINKS_CHANGED doc={doc}")

        for filepath in sources:
            docId = os.path.basename(filepath)
            try:
                self.kbdict_new["document"][docId]
            except KeyError:
                continue

            result = self.step_01_00_analyze_document(docId)
            if docId in backlinks_changed and not result['compile']:
                result['compile'] = True
            if result['compile']:
                # Write new source file to temporary dir for the compiler
                self.plan.docs_to_compile.add(docId)
                source_path = os.path.join(self.srvbes.get_path("source"), docId)
                with open(source_path, "r", encoding=SOURCE_ENCODING) as fh:
                    content = fh.read()
                target = os.path.join(self.srvbes.get_path("tmp"), valid_filename(docId))
                with open(target, "w", encoding="utf-8") as fout:
                    fout.write(content)

            # On metadata change, force recompile of ALL (key, value) pairs
            # this document belongs to,  datatable rows reflect metadata
            # values, so any property change must refresh every page that
            # lists this document, even if its membership set is unchanged.
            if result['metadata_differs']:
                for key in self.srvdtb.get_doc_keys(docId):
                    if key in ignored or key in blocked:
                        continue
                    for value in self.srvdtb.get_values(docId, key):
                        analysis.force_kv_pairs.add((key, value))

            # Save compilation status
            self.kbdict_new["document"][docId]["compile"] = result['compile']

        self.plan.force_kv_pairs = analysis.force_kv_pairs

        # Decide keys compilation
        all_keys = set(self.srvdtb.get_all_keys())
        available_keys = list(all_keys - ignored)
        self.log.debug(f"[PROCESSOR] KEYS_ALL count={len(all_keys)}")
        self.log.debug(f"[PROCESSOR] KEYS_IGNORED count={len(ignored)}")
        self.log.debug(f"[PROCESSOR] KEYS_AVAILABLE count={len(available_keys)}")
        self.log.debug(f"[PROCESSOR] FORCE_KV_PAIRS count={len(analysis.force_kv_pairs)}")
        self.plan.K_PATH, self.plan.KV_PATH = self.step_01_01_decide_keys_compilation(
            available_keys, analysis.force_kv_pairs
        )

    def get_kb_dict(self):
        """Get new KB4IT Dictionary."""
        return self.kbdict_new

    def get_kbdict_key(self, key, new=True):
        """Return values for a given key from KB dictionary.

        If new is True, it will return the value from the kbdict just
        generated during the execution.
        If new is False, it will return the value from the kbdict saved
        in the previous execution.
        """
        if new:
            kbdict = self.kbdict_new
        else:
            kbdict = self.kbdict_cur

        try:
            alist = kbdict["metadata"][key]
        except KeyError:
            alist = []

        return alist

    def get_kbdict_value(self, key, value, new=True):
        """Get a value for a given key from KB dictionary.

        If new is True, it will return the value from the kbdict just
        generated during the execution.
        If new is False, it will return the value from the kbdict saved
        in the previous execution.
        """
        if new:
            kbdict = self.kbdict_new
        else:
            kbdict = self.kbdict_cur

        try:
            alist = kbdict["metadata"][key][value]
        except KeyError:
            alist = []

        return alist

    def step_01_00_analyze_document(self, docId: str) -> dict:
        """Decide whether a document must be recompiled.

        Body, metadata and title are compared independently:
          - body_differs:     body content changed
          - metadata_differs: extracted keys changed
          - titles_differ:    title changed

        A doc recompiles when its body, metadata or title changed, its
        HTML isn't cached yet, or compilation is forced. Metadata changes
        also trigger key/value index recompilation in
        step_01_01_decide_keys_compilation.
        """
        result = {}
        FORCE_COMPILATION = self._forced() or self.plan.force_all

        # Body hash
        try:
            body_new = self.kbdict_new["document"][docId]["body_hash"]
            body_cur = self.kbdict_cur["document"][docId]["body_hash"]
            BODY_DIFFERS = body_new != body_cur
        except (KeyError, TypeError):
            BODY_DIFFERS = True
        result['body_differs'] = BODY_DIFFERS

        # Metadata hash
        try:
            meta_new = self.kbdict_new["document"][docId]["metadata_hash"]
            meta_cur = self.kbdict_cur["document"][docId]["metadata_hash"]
            METADATA_DIFFERS = meta_new != meta_cur
        except (KeyError, TypeError):
            METADATA_DIFFERS = True
        result['metadata_differs'] = METADATA_DIFFERS

        # Title change
        try:
            title_cur = self.kbdict_cur["document"][docId]["Title"]
            title_new = self.kbdict_new["document"][docId]["Title"]
            TITLES_DIFFER = title_new != title_cur
        except KeyError:
            TITLES_DIFFER = True
        result['titles_differ'] = TITLES_DIFFER

        # HTML cache existence
        htmlId = html_id_for(docId)
        cached_document = os.path.join(self.srvbes.get_path("cache"), htmlId)
        NOT_CACHED = not os.path.exists(cached_document)
        result['not_cached'] = NOT_CACHED

        DOC_COMPILATION = BODY_DIFFERS or METADATA_DIFFERS or TITLES_DIFFER or NOT_CACHED or FORCE_COMPILATION
        result['compile'] = DOC_COMPILATION

        self.log.debug(f"[PROCESSOR] ANALYZE doc={docId} body={BODY_DIFFERS} meta={METADATA_DIFFERS} title={TITLES_DIFFER} not_cached={NOT_CACHED} compile={DOC_COMPILATION}")

        return result

    def step_01_01_decide_keys_compilation(self, available_keys, force_kv_pairs: set):
        """Decide which keys and values will be compiled.

        A key/value page recompiles when:
          - its doc set changed (rkvnew != rkvold), OR
          - it was forced via force_kv_pairs (doc metadata/title changed), OR
          - compilation is globally forced.
        A key index page recompiles when:
          - its value set changed (rknew != rkold), OR
          - any of its (key, value) pages recompiles, OR
          - compilation is globally forced.
        """
        K_PATH = []
        KV_PATH = []
        FORCE_COMPILATION = self._forced() or self.plan.force_all

        for key in sorted(available_keys):
            values = self.srvdtb.get_all_values_for_key(key)

            if FORCE_COMPILATION:
                K_PATH.append((key, values, True))
                for value in values:
                    KV_PATH.append((key, value, True))
                self.log.debug(f"[PROCESSOR] KEY key={key} compile=True forced=True")
                continue

            # Key value-set changed?
            rknew = sorted(self.get_kbdict_key(key, new=True))
            rkold = sorted(self.get_kbdict_key(key, new=False))
            COMPILE_KEY = rknew != rkold

            for value in values:
                rkvnew = self.get_kbdict_value(key, value, new=True)
                rkvold = self.get_kbdict_value(key, value, new=False)
                KV_FORCED = (key, value) in force_kv_pairs
                COMPILE_VALUE = rkvnew != rkvold or KV_FORCED
                KV_PATH.append((key, value, COMPILE_VALUE))
                if COMPILE_VALUE:
                    COMPILE_KEY = True
                self.log.debug(f"[PROCESSOR] KV key={key} value={value} compile={COMPILE_VALUE}")

            K_PATH.append((key, values, COMPILE_KEY))
            self.log.debug(f"[PROCESSOR] KEY key={key} compile={COMPILE_KEY}")

        return K_PATH, KV_PATH

    @timeit
    def step_02_transformation(self):
        """Process all keys/values got from documents.

        The algorithm detects which keys/values have changed and compile
        them again. This avoid recompile the whole database, saving time
        and CPU.
        """
        self.log.debug("[PROCESSOR] TRANSFORM_START")
        theme = self.srvbes.get_dict("theme")
        if theme.get("metadata_pages", True) is False:
            self.log.debug("[PROCESSOR] METADATA_PAGES_SKIP reason=theme")
            self.log.debug("[PROCESSOR] TRANSFORM_END")
            return

        # Keys
        keys_with_compile_true = 0
        for kpath in self.plan.K_PATH:
            key, values, COMPILE_KEY = kpath
            docId = f"{valid_filename(key)}.md"
            htmlId = html_id_for(docId)
            if COMPILE_KEY:
                self.srvthm.build_page_key(key, values)
                keys_with_compile_true += 1

            # Add compiled page to the target list
            self.srvbes.add_target(docId, htmlId)

        pairs_with_compile_true = 0
        for kvpath in self.plan.KV_PATH:
            key, value, COMPILE_VALUE = kvpath
            docId = f"{valid_filename(key)}_{valid_filename(value)}.md"
            htmlId = html_id_for(docId)
            if COMPILE_VALUE:
                self.srvthm.build_page_key_value(kvpath)
                pairs_with_compile_true += 1

            # Add compiled page to the target list
            self.srvbes.add_target(docId, htmlId)

        targets = self.srvbes.get_value("docs", "targets")
        self.log.debug(f"[PROCESSOR] KEYS_TO_COMPILE n={keys_with_compile_true}")
        self.log.debug(f"[PROCESSOR] KV_PAIRS_TO_COMPILE n={pairs_with_compile_true}")
        self.log.debug(f"[PROCESSOR] TARGET_DOCS n={len(targets)}")
        self.log.debug("[PROCESSOR] TRANSFORM_END")

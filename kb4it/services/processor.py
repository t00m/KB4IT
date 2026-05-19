#!/usr/bin/env python
"""
Service Processor.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kb4it.core.types import KBDict

from kb4it.core.service import Service
from kb4it.core.util import (get_document_attributes, get_hash_from_body,
                             get_hash_from_dict, html_id_for, string_timestamp,
                             valid_filename)


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

    def _initialize(self):
        """Initialize Processor service."""
        self.srvbes = self.app.get_service("Backend")
        self.srvdtb = self.app.get_service("DB")
        self.kbdict_cur: KBDict = self.srvbes.load_kbdict()  # Previous run
        self.kbdict_new: KBDict = {"document": {}, "metadata": {}}
        self.plan = BuildPlan()

    @property
    def changed_docs(self) -> set:
        return self.plan.docs_to_compile

    def get_plan(self) -> BuildPlan:
        """Return the current BuildPlan."""
        return self.plan

    def step_00_extraction(self):
        """Extract metadata."""
        runtime = self.srvbes.get_dict("runtime")
        sources = self.srvbes.get_value("docs", "bag")
        for filepath in sources:
            # Get Id
            docId = os.path.basename(filepath)

            # Get metadata
            keys, valid, reason = get_document_attributes(filepath)
            self.log.debug(f"[PROCESSOR] DOC_VALID doc={os.path.basename(filepath)} valid={valid} reason={reason}")

            if not valid:
                continue

            # Add to cache
            self.kbdict_new["document"][docId] = {}
            self.kbdict_new["document"][docId]["content"] = filepath
            self.kbdict_new["document"][docId]["keys"] = keys

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
                        self.kbdict_new["document"][docId][key] = sorted(
                            values)
                    except KeyError:
                        self.kbdict_new["document"][docId][key] = [value]

                    # And viceversa, for each key/value add to kbdict['metadata'] all documents linked
                    try:
                        documents = self.kbdict_new["metadata"][key][value]
                        documents.append(docId)
                        self.kbdict_new["metadata"][key][value] = sorted(
                            documents, key=lambda y: y.lower()
                        )
                    except KeyError:
                        if key not in self.kbdict_new["metadata"]:
                            self.kbdict_new["metadata"][key] = {}
                        if value not in self.kbdict_new["metadata"][key]:
                            self.kbdict_new["metadata"][key][value] = [docId]

            # To track changes in a document, hashes for metadata and
            # content are created. Comparing them with those in the
            # cache, KB4IT determines if a document must be compiled
            # again. Very useful to reduce the compilation time.

            # Get Document Body and Metadata Hashes
            b_hash = get_hash_from_body(filepath)
            m_hash = get_hash_from_dict(keys)
            self.kbdict_new["document"][docId]["body_hash"] = b_hash
            self.kbdict_new["document"][docId]["metadata_hash"] = m_hash
            self.log.debug(f"[PROCESSOR] HASH doc={docId} body={b_hash} meta={m_hash}")

            # Add compiled page to the target list
            htmlId = html_id_for(docId)
            self.srvbes.add_target(docId, htmlId)

        # Save new kbdict
        self.srvbes.save_kbdict(self.kbdict_new)


    def step_01_analysis(self):
        """Compilation strategy."""
        analysis = AnalysisResult()
        sources = self.srvbes.get_value("docs", "bag")
        ignored = set(self.srvdtb.get_ignored_keys())
        blocked = set(self.srvdtb.get_blocked_keys())
        for filepath in sources:
            docId = os.path.basename(filepath)
            try:
                self.kbdict_new["document"][docId]
            except KeyError:
                continue

            result = self.step_01_00_analyze_document(docId)
            if result['compile']:
                # Write new source file to temporary dir for the compiler
                self.plan.docs_to_compile.add(docId)
                source_path = os.path.join(self.srvbes.get_path("source"), docId)
                with open(source_path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                target = f"{self.srvbes.get_path('tmp')}/{valid_filename(docId)}"
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
        FORCE_COMPILATION = self.srvbes.get_value("repo", "force") or False

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
        FORCE_COMPILATION = self.srvbes.get_value("repo", "force") or False

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

    def step_02_transformation(self):
        """Process all keys/values got from documents.

        The algorithm detects which keys/values have changed and compile
        them again. This avoid recompile the whole database, saving time
        and CPU.
        """
        self.log.debug("[PROCESSOR] TRANSFORM_START")
        self.srvthm = self.get_service("Theme")

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

#!/usr/bin/env python
"""
Service Processor.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

import os

from kb4it.core.service import Service
from kb4it.core.util import (get_asciidoctor_attributes, get_hash_from_body,
                             get_hash_from_dict, string_timestamp,
                             valid_filename)


class Processor(Service):
    """KB4IT Processor Service."""

    def _initialize(self):
        """Initialize Processor service."""
        self.srvbes = self.app.get_service("Backend")
        self.srvdtb = self.app.get_service("DB")
        self.kbdict_cur = self.srvbes.load_kbdict()  # Previous run
        self.kbdict_new = {}  # New compilation cache
        self.kbdict_new["document"] = {}
        self.kbdict_new["metadata"] = {}
        self.force_kv_pairs = set()  # (key, value) pairs forced to recompile
        self.changed_docs = set()

    def get_force_kv_pairs(self):
        return self.force_kv_pairs

    def step_00_extraction(self):
        """Extract metadata."""
        runtime = self.srvbes.get_dict("runtime")
        sources = self.srvbes.get_value("docs", "bag")
        for filepath in sources:
            # Get Id
            adocId = os.path.basename(filepath)

            # Get metadata
            keys, valid, reason = get_asciidoctor_attributes(filepath)
            self.log.debug(f"[PROCESSOR] DOC_VALID doc={os.path.basename(filepath)} valid={valid} reason={reason}")

            if not valid:
                continue

            # Add to cache
            self.kbdict_new["document"][adocId] = {}
            self.kbdict_new["document"][adocId]["content"] = filepath
            self.kbdict_new["document"][adocId]["keys"] = keys

            # Add to the in-memory database
            self.srvdtb.add_document(adocId)
            for key in keys:
                alist = keys[key]
                for value in alist:
                    if len(value.strip()) == 0:
                        continue
                    if key == "Date":
                        value = string_timestamp(value)
                    self.srvdtb.add_document_key(adocId, key, value)

                    # For each document and for each key/value linked to that document add an entry to kbdic['document']
                    try:
                        values = self.kbdict_new["document"][adocId][key]
                        if value not in values:
                            values.append(value)
                        self.kbdict_new["document"][adocId][key] = sorted(
                            values)
                    except KeyError:
                        self.kbdict_new["document"][adocId][key] = [value]

                    # And viceversa, for each key/value add to kbdict['metadata'] all documents linked
                    try:
                        documents = self.kbdict_new["metadata"][key][value]
                        documents.append(adocId)
                        self.kbdict_new["metadata"][key][value] = sorted(
                            documents, key=lambda y: y.lower()
                        )
                    except KeyError:
                        if key not in self.kbdict_new["metadata"]:
                            self.kbdict_new["metadata"][key] = {}
                        if value not in self.kbdict_new["metadata"][key]:
                            self.kbdict_new["metadata"][key][value] = [adocId]

            # To track changes in a document, hashes for metadata and
            # content are created. Comparing them with those in the
            # cache, KB4IT determines if a document must be compiled
            # again. Very useful to reduce the compilation time.

            # Get Document Body and Metadata Hashes
            b_hash = get_hash_from_body(filepath)
            m_hash = get_hash_from_dict(keys)
            self.kbdict_new["document"][adocId]["body_hash"] = b_hash
            self.kbdict_new["document"][adocId]["metadata_hash"] = m_hash
            self.log.debug(f"[PROCESSOR] HASH doc={adocId} body={b_hash} meta={m_hash}")

            # Add compiled page to the target list
            htmlId = adocId.replace(".adoc", ".html")
            self.srvbes.add_target(adocId, htmlId)

        # Save new kbdict
        self.srvbes.save_kbdict(self.kbdict_new)

        # Build a list of documents sorted by timestamp
        # ~ self.srvdtb.sort_database()

    def step_01_analysis(self):
        """Compilation strategy."""
        sources = self.srvbes.get_value("docs", "bag")
        ignored = set(self.srvdtb.get_ignored_keys())
        blocked = set(self.srvdtb.get_blocked_keys())
        ncd = 0  # Number of documents to be compiled
        for filepath in sources:
            adocId = os.path.basename(filepath)
            try:
                self.kbdict_new["document"][adocId]
            except KeyError:
                continue

            result = self.step_01_00_analyze_document(adocId)
            if result['compile']:
                ncd += 1
                # Write new adoc to temporary dir for asciidoctor
                self.changed_docs.add(adocId)
                source_path = os.path.join(self.srvbes.get_path("source"), adocId)
                content = open(source_path, "r", encoding="utf-8").read()
                target = f"{self.srvbes.get_path('tmp')}/{valid_filename(adocId)}"
                with open(target, "w", encoding="utf-8") as target_adoc:
                    target_adoc.write(content)

            # On metadata change, force recompile of ALL (key, value) pairs
            # this document belongs to — datatable rows reflect metadata
            # values, so any property change must refresh every page that
            # lists this document, even if its membership set is unchanged.
            if result['metadata_differs']:
                for key in self.srvdtb.get_doc_keys(adocId):
                    if key in ignored or key in blocked:
                        continue
                    for value in self.srvdtb.get_values(adocId, key):
                        self.force_kv_pairs.add((key, value))

            # Save compilation status
            self.kbdict_new["document"][adocId]["compile"] = result['compile']

        self.srvbes.set_value("runtime", "ncd", ncd)

        # Decide keys compilation
        all_keys = set(self.srvdtb.get_all_keys())
        available_keys = list(all_keys - ignored)
        self.log.debug(f"[PROCESSOR] KEYS_ALL count={len(all_keys)}")
        self.log.debug(f"[PROCESSOR] KEYS_IGNORED count={len(ignored)}")
        self.log.debug(f"[PROCESSOR] KEYS_AVAILABLE count={len(available_keys)}")
        self.log.debug(f"[PROCESSOR] FORCE_KV_PAIRS count={len(self.force_kv_pairs)}")
        K_PATH, KV_PATH = self.step_01_01_decide_keys_compilation(available_keys)
        self.srvbes.set_value("runtime", "K_PATH", K_PATH)
        self.srvbes.set_value("runtime", "KV_PATH", KV_PATH)

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

    def step_01_00_analyze_document(self, adocId: str) -> dict:
        """Decide whether a document must be recompiled.

        Body, metadata and title are compared independently:
          - body_differs:     body content changed (after the EOH mark)
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
            body_new = self.kbdict_new["document"][adocId]["body_hash"]
            body_cur = self.kbdict_cur["document"][adocId]["body_hash"]
            BODY_DIFFERS = body_new != body_cur
        except (KeyError, TypeError):
            BODY_DIFFERS = True
        result['body_differs'] = BODY_DIFFERS

        # Metadata hash
        try:
            meta_new = self.kbdict_new["document"][adocId]["metadata_hash"]
            meta_cur = self.kbdict_cur["document"][adocId]["metadata_hash"]
            METADATA_DIFFERS = meta_new != meta_cur
        except (KeyError, TypeError):
            METADATA_DIFFERS = True
        result['metadata_differs'] = METADATA_DIFFERS

        # Title change
        try:
            title_cur = self.kbdict_cur["document"][adocId]["Title"]
            title_new = self.kbdict_new["document"][adocId]["Title"]
            TITLES_DIFFER = title_new != title_cur
        except KeyError:
            TITLES_DIFFER = True
        result['titles_differ'] = TITLES_DIFFER

        # HTML cache existence
        htmlId = adocId.replace(".adoc", ".html")
        cached_document = os.path.join(self.srvbes.get_path("cache"), htmlId)
        NOT_CACHED = not os.path.exists(cached_document)
        result['not_cached'] = NOT_CACHED

        DOC_COMPILATION = BODY_DIFFERS or METADATA_DIFFERS or TITLES_DIFFER or NOT_CACHED or FORCE_COMPILATION
        result['compile'] = DOC_COMPILATION

        self.log.debug(f"[PROCESSOR] ANALYZE doc={adocId} body={BODY_DIFFERS} meta={METADATA_DIFFERS} title={TITLES_DIFFER} not_cached={NOT_CACHED} compile={DOC_COMPILATION}")

        return result

    def step_01_01_decide_keys_compilation(self, available_keys):
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

        nck = 0  # Number of keys to be compiled
        for key in sorted(available_keys):
            values = self.srvdtb.get_all_values_for_key(key)

            if FORCE_COMPILATION:
                K_PATH.append((key, values, True))
                for value in values:
                    KV_PATH.append((key, value, True))
                self.log.debug(f"[PROCESSOR] KEY key={key} compile=True forced=True")
                nck += 1
                continue

            # Key value-set changed?
            rknew = sorted(self.get_kbdict_key(key, new=True))
            rkold = sorted(self.get_kbdict_key(key, new=False))
            COMPILE_KEY = rknew != rkold

            for value in values:
                rkvnew = self.get_kbdict_value(key, value, new=True)
                rkvold = self.get_kbdict_value(key, value, new=False)
                KV_FORCED = (key, value) in self.force_kv_pairs
                COMPILE_VALUE = rkvnew != rkvold or KV_FORCED
                KV_PATH.append((key, value, COMPILE_VALUE))
                if COMPILE_VALUE:
                    COMPILE_KEY = True
                self.log.debug(f"[PROCESSOR] KV key={key} value={value} compile={COMPILE_VALUE}")

            K_PATH.append((key, values, COMPILE_KEY))
            self.log.debug(f"[PROCESSOR] KEY key={key} compile={COMPILE_KEY}")
            if COMPILE_KEY:
                nck += 1

        self.srvbes.set_value("runtime", "nck", nck)
        return K_PATH, KV_PATH

    def step_02_transformation(self):
        """Process all keys/values got from documents.

        The algorithm detects which keys/values have changed and compile
        them again. This avoid recompile the whole database, saving time
        and CPU.
        """
        self.log.debug("[PROCESSOR] TRANSFORM_START")
        self.srvthm = self.get_service("Theme")
        runtime = self.srvbes.get_dict("runtime")

        # Keys
        keys_with_compile_true = 0
        for kpath in runtime["K_PATH"]:
            key, values, COMPILE_KEY = kpath
            adocId = f"{valid_filename(key)}.adoc"
            htmlId = adocId.replace(".adoc", ".html")
            if COMPILE_KEY:
                self.srvthm.build_page_key(key, values)
                keys_with_compile_true += 1

            # Add compiled page to the target list
            self.srvbes.add_target(adocId, htmlId)

        # # Keys/Values
        pairs_with_compile_true = 0
        for kvpath in runtime["KV_PATH"]:
            key, value, COMPILE_VALUE = kvpath
            adocId = f"{valid_filename(key)}_{valid_filename(value)}.adoc"
            htmlId = adocId.replace(".adoc", ".html")
            if COMPILE_VALUE:
                self.srvthm.build_page_key_value(kvpath)
                pairs_with_compile_true += 1

            # Add compiled page to the target list
            self.srvbes.add_target(adocId, htmlId)

        self.log.debug(f"[PROCESSOR] KEYS_TO_COMPILE n={keys_with_compile_true}")
        self.log.debug(f"[PROCESSOR] KV_PAIRS_TO_COMPILE n={pairs_with_compile_true}")
        self.log.debug(f"[PROCESSOR] TARGET_DOCS n={len(runtime['docs']['targets'])}")
        self.log.debug("[PROCESSOR] TRANSFORM_END")

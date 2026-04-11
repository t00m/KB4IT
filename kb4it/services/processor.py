#!/usr/bin/env python
"""
Service Processor.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

import os

from kb4it.core.service import Service
from kb4it.core.util import (get_asciidoctor_attributes, get_hash_from_dict,
                             get_hash_from_file, string_timestamp,
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
        self.force_keys = set()  # List of keys which must be compiled (forced)
        self.changed_docs = set()

    def get_force_keys(self):
        return self.force_keys

    def step_00_extraction(self):
        """Extract metadata."""
        runtime = self.srvbes.get_dict("runtime")
        sources = self.srvbes.get_value("docs", "bag")
        for filepath in sources:
            # Get Id
            adocId = os.path.basename(filepath)

            # Get metadata
            keys, valid, reason = get_asciidoctor_attributes(filepath)
            self.log.debug(f"DOC[{os.path.basename(filepath)}] valid? {valid}. Why? {reason}")

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
                    if key == runtime["sort_attribute"]:
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

            # Get Document Content and Metadata Hashes
            c_hash = get_hash_from_file(filepath)
            m_hash = get_hash_from_dict(keys)
            self.kbdict_new["document"][adocId]["content_hash"] = c_hash
            self.kbdict_new["document"][adocId]["metadata_hash"] = m_hash
            self.log.debug(f"DOC[{adocId}] HASH[{c_hash}{m_hash}]")

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

            # Write adoc to tmp directory for further compilation
            if result['compile']:
                # Write new adoc to temporary dir
                self.changed_docs.add(adocId)
                source_path = os.path.join(self.srvbes.get_path("source"), adocId)
                content = open(source_path, "r", encoding="utf-8").read()
                target = f"{self.srvbes.get_path('tmp')}/{valid_filename(adocId)}"
                with open(target, "w", encoding="utf-8") as target_adoc:
                    target_adoc.write(content)

            if result['titles_differ']:
                for key in self.srvdtb.get_doc_keys(adocId):
                    self.force_keys.add(key)

            # Save compilation status
            self.kbdict_new["document"][adocId]["compile"] = result['compile']

        self.srvbes.set_value("runtime", "ncd", ncd)

        # Decide keys compilation
        all_keys = set(self.srvdtb.get_all_keys())
        ignored_keys = self.srvdtb.get_ignored_keys()
        available_keys = list(all_keys - set(ignored_keys))
        self.log.debug(f"ALL Keys: {all_keys}")
        self.log.debug(f"IGN Keys: {ignored_keys}")
        self.log.debug(f"AVL Keys: {available_keys}")
        self.log.debug(f"FCD Keys: {self.force_keys}")
        K_PATH, KV_PATH = self.step_01_01_decide_keys_compilation(available_keys)
        self.srvbes.set_value("runtime", "K_PATH", K_PATH)
        self.srvbes.set_value("runtime", "KV_PATH", KV_PATH)

    def step_01_analysis_orig(self):
        """Compilation strategy."""
        # Decide documents compilation one by one
        sources = self.srvbes.get_value("docs", "bag")
        ncd = 0  # Number of documents to be compiled
        for filepath in sources:
            adocId = os.path.basename(filepath)
            keys = self.kbdict_new["document"][adocId]["keys"]
            need_compile = self.step_01_00_decide_document_compilation(adocId, keys)
            if need_compile:
                ncd += 1
        self.srvbes.set_value("runtime", "ncd", ncd)

        # Decide keys compilation
        all_keys = set(self.srvdtb.get_all_keys())
        ignored_keys = self.srvdtb.get_ignored_keys()
        available_keys = list(all_keys - set(ignored_keys))
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
        """Decide which documents will be compiled.

        Note: there is room for improvement here.
        What if only content changes but not keys or title?
        """
        result = {}
        FORCE_COMPILATION = self.srvbes.get_value("repo", "force") or False

        # Check hashes
        try:
            hash_new = (
                self.kbdict_new["document"][adocId]["content_hash"]
                + self.kbdict_new["document"][adocId]["metadata_hash"]
            )
            hash_cur = (
                self.kbdict_cur["document"][adocId]["content_hash"]
                + self.kbdict_cur["document"][adocId]["metadata_hash"]
            )
            HASHES_DIFFER = hash_new != hash_cur
        except Exception as warning:
            HASHES_DIFFER = True
        result['hashes_differ'] = HASHES_DIFFER

        # Check title change
        try:
            title_cur = self.kbdict_cur["document"][adocId]["Title"]
            title_new = self.kbdict_new["document"][adocId]["Title"]
            TITLES_DIFFER = title_new != title_cur
        except KeyError:
            TITLES_DIFFER = True
        result['titles_differ'] = TITLES_DIFFER

        # Check existence
        htmlId = adocId.replace(".adoc", ".html")
        cached_document = os.path.join(self.srvbes.get_path("cache"), htmlId)
        NOT_CACHED = not os.path.exists(cached_document)
        result['not_cached'] = NOT_CACHED

        DOC_COMPILATION = HASHES_DIFFER or TITLES_DIFFER or NOT_CACHED or FORCE_COMPILATION
        result['compile'] = DOC_COMPILATION

        self.log.debug(f"DOC[{adocId}]: Hashes_differ[{HASHES_DIFFER}] or TITLES_DIFFER[{TITLES_DIFFER}] or NOT_CACHED[{NOT_CACHED}] => Compile? {DOC_COMPILATION}")

        return result

    def step_01_01_decide_keys_compilation(self, available_keys):
        """Decide which keys and values will be compiled."""
        K_PATH = []
        KV_PATH = []
        FORCE_COMPILATION = self.srvbes.get_value("repo", "force") or False

        nck = 0  # Number of keys to be compiled
        for key in sorted(available_keys):
            COMPILE_KEY = False
            FORCE_KEY = key in self.force_keys or FORCE_COMPILATION
            values = self.srvdtb.get_all_values_for_key(key)
            if FORCE_KEY:
                self.log.debug(f"KEY[{key}] COMPILE[{FORCE_KEY}]")
                K_PATH.append((key, values, FORCE_KEY))
                nck += 1
                for value in values:
                    KV_PATH.append((key, value, FORCE_KEY))
            else:
                # Compare keys values for the current run and the cache
                # Otherwise, the key is not recompiled when a value is deleted
                rknew = sorted(self.get_kbdict_key(key, new=True))
                rkold = sorted(self.get_kbdict_key(key, new=False))
                if rknew != rkold:
                    COMPILE_KEY = True
                # ~ self.log.debug(f"KEY[{key}] COMPILE[{COMPILE_KEY}] | ({rknew}-{rkold})")

                for value in values:
                    rkvnew = self.get_kbdict_value(key, value, new=True)
                    rkvold = self.get_kbdict_value(key, value, new=False)
                    COMPILE_VALUE = rkvnew != rkvold or FORCE_COMPILATION
                    COMPILE_KEY = COMPILE_KEY or COMPILE_VALUE or FORCE_COMPILATION
                    KV_PATH.append((key, value, COMPILE_VALUE))
                    self.log.debug(f"KEY[{key}] VALUE[{value}] COMPILE[{COMPILE_VALUE}]")

                self.log.debug(f"KEY[{key}] COMPILE[{COMPILE_KEY}]")
                K_PATH.append((key, values, COMPILE_KEY))

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
        self.log.debug("[PROCESSING] - START")
        self.srvthm = self.get_service("Theme")
        runtime = self.srvbes.get_dict("runtime")

        # Keys
        keys_with_compile_true = 0
        self.log.debug(f"K_PATH: {runtime['K_PATH']}")
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
        self.log.debug(f"KV_PATH: {runtime['KV_PATH']}")
        for kvpath in runtime["KV_PATH"]:
            key, value, COMPILE_VALUE = kvpath
            adocId = f"{valid_filename(key)}_{valid_filename(value)}.adoc"
            htmlId = adocId.replace(".adoc", ".html")
            if COMPILE_VALUE:
                self.srvthm.build_page_key_value(kvpath)
                pairs_with_compile_true += 1

            # Add compiled page to the target list
            self.srvbes.add_target(adocId, htmlId)

        self.log.debug(
            f"STATS - {keys_with_compile_true} keys will be compiled")
        self.log.debug(
            f"STATS - {pairs_with_compile_true} key/value pairs will be compiled"
        )
        self.log.debug("STATS - Finish processing keys")
        self.log.debug(
            f"STATS - Target docs: {len(runtime['docs']['targets'])}")
        self.log.debug("[PROCESSINNG] - END")

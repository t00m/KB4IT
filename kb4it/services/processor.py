#!/usr/bin/env python
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Cleaner service
"""

import os
from kb4it.core.service import Service
from kb4it.core.util import get_asciidoctor_attributes
from kb4it.core.util import get_hash_from_file
from kb4it.core.util import get_hash_from_dict
from kb4it.core.util import get_hash_from_list
from kb4it.core.util import string_timestamp
from kb4it.core.util import valid_filename

class Processor(Service):
    """KB4IT Processor Service"""

    def _initialize(self):
        """Initialize Processor service"""
        self.srvbes = self.app.get_service('Backend')
        self.srvdtb = self.app.get_service('DB')
        self.kbdict_cur = self.srvbes.load_kbdict() # Previous run
        self.kbdict_new = {}     # New compilation cache
        self.kbdict_new['document'] = {}
        self.kbdict_new['metadata'] = {}
        self.force_keys = set()  # List of keys which must be compiled (forced)

    def step_00_extraction(self):
        runtime = self.srvbes.get_dict('runtime')
        sources = self.srvbes.get_value('docs', 'bag')
        for filepath in sources:
            # Get Id
            adocId = os.path.basename(filepath)

            # Get metadata
            keys, valid, reason = get_asciidoctor_attributes(filepath)
            self.log.debug(f"{os.path.basename(filepath)}: {reason}")

            if not valid:
                return

            # Add to cache
            self.kbdict_new['document'][adocId] = {}
            self.kbdict_new['document'][adocId]['content'] = filepath
            self.kbdict_new['document'][adocId]['keys'] = keys

            # Add to the in-memory database
            self.srvdtb.add_document(adocId)
            for key in keys:
                alist = keys[key]
                for value in alist:
                    if len(value.strip()) == 0:
                        continue
                    if key == runtime['sort_attribute']:
                        value = string_timestamp(value)
                    self.srvdtb.add_document_key(adocId, key, value)

            # To track changes in a document, hashes for metadata and
            # content are created. Comparing them with those in the
            # cache, KB4IT determines if a document must be compiled
            # again. Very useful to reduce the compilation time.

            # Get Document Content and Metadata Hashes
            c_hash = get_hash_from_file(filepath)
            m_hash = get_hash_from_dict(keys)
            self.kbdict_new['document'][adocId]['content_hash'] = c_hash
            self.kbdict_new['document'][adocId]['metadata_hash'] = m_hash
            self.log.debug(f"DOC[{adocId}] HASH[{c_hash}{m_hash}]")

            # Add compiled page to the target list
            htmlId = adocId.replace('.adoc', '.html')
            self.srvbes.add_target(adocId, htmlId)

        # Save new kbdict
        self.srvbes.save_kbdict(self.kbdict_new)

        # Build a list of documents sorted by timestamp
        # ~ self.srvdtb.sort_database()

    def step_01_analysis(self):
        # Compilation strategy

        # Force compilation for all documents?
        keys_hash_cur = get_hash_from_list(sorted(list(self.kbdict_cur['metadata'].keys())))
        keys_hash_new = get_hash_from_list(sorted(list(self.kbdict_new['metadata'].keys())))
        keys_hash_differ = keys_hash_cur != keys_hash_new
        if keys_hash_differ:
            # Force compilation!
            self.log.debug(f"CONF[APP] PARAM[force] VALUE[True]: Keys hashes mismatch. Force compilation!")
            self.srvbes.set_value('app', 'force', True)
        else:
            # Decide documents compilation one by one
            sources = self.srvbes.get_value('docs', 'bag')
            for filepath in sources:
                adocId = os.path.basename(filepath)
                keys = self.kbdict_new['document'][adocId]['keys']
                self.step_01_00_decide_document_compilation(adocId, keys)

            # Decide keys compilation
            all_keys = set(self.srvdtb.get_all_keys())
            ignored_keys = self.srvdtb.get_ignored_keys()
            available_keys = list(all_keys - set(ignored_keys))
            K_PATH, KV_PATH = self.step_01_01_decide_keys_compilation(available_keys)
            self.srvbes.set_value('runtime', 'K_PATH', K_PATH)
            self.srvbes.set_value('runtime', 'KV_PATH', KV_PATH)

    def display_stats(self):
        # Documents preprocessing stats
        self.log.debug(f"STATS - Documents analyzed: {len(sources)}")
        keep_docs = compile_docs = 0
        for adocId in self.kbdict_new['document']:
            if self.kbdict_new['document'][adocId]['compile']:
                compile_docs += 1
            else:
                keep_docs += 1
        self.log.debug(f"STATS - Keep: {keep_docs} - Compile: {compile_docs}")
        if compile_docs == 0:
            self.log.debug(f"[PREPROCESSING] - No changes in the repository")
        else:
            if compile_docs < keep_docs:
                self.log.debug(f"[PREPROCESSING] - There are changes in the repository. {compile_docs} documents will be compiled again")
            else:
                self.log.debug(f"[PREPROCESSING] - All documents will be compiled again")
        self.log.debug(f"[PREPROCESSING] - END")

    def get_kb_dict(self):
        return self.kbdict_new


    def get_kbdict_key(self, key, new=True):
        """
        Return values for a given key from KB dictionary.
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
            alist = kbdict['metadata'][key]
        except KeyError:
            alist = []

        return alist


    def get_kbdict_value(self, key, value, new=True):
        """
        Get a value for a given key from KB dictionary.
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
            alist = kbdict['metadata'][key][value]
        except KeyError:
            alist = []

        return alist

    def step_01_00_decide_document_compilation(self, adocId: str, keys:list):
        # Force compilation (from command line)?
        DOC_COMPILATION = False
        FORCE_ALL = self.srvbes.get_value('app', 'force')
        if not FORCE_ALL:
            # Get cached document path and check if it exists
            htmlId = adocId.replace('.adoc', '.html')
            cached_document = os.path.join(self.srvbes.get_path('cache'), htmlId)
            cached_document_exists = os.path.exists(cached_document)

            # Compare the document with the one in the cache
            if not cached_document_exists:
                DOC_COMPILATION = True
                REASON = "Not cached"
            else:
                try:
                    hash_new = self.kbdict_new['document'][adocId]['content_hash'] + self.kbdict_new['document'][adocId]['metadata_hash']
                    hash_cur = self.kbdict_cur['document'][adocId]['content_hash'] + self.kbdict_cur['document'][adocId]['metadata_hash']
                    #self.log.debug(f"[BACKEND-CACHE] - Old hash for {adocId}: '{hash_cur}'")
                    #self.log.debug(f"[BACKEND-CACHE] - New hash for {adocId}: '{hash_new}'")
                    DOC_COMPILATION = hash_new != hash_cur
                    REASON = f"Hashes differ? {DOC_COMPILATION}"
                except Exception as warning:
                    DOC_COMPILATION = True
                    REASON = warning
        else:
            REASON = "Forced"

        COMPILE = DOC_COMPILATION or FORCE_ALL
        # Save compilation status
        try:
            self.kbdict_new['document'][adocId]['compile'] = COMPILE
        except KeyError as error:
            self.log.error(f"FIXME: check")
            self.log.error(f"DOC[{adocId}]: {error}")
            self.app.stop(error=True)

        if COMPILE:
            # Write new adoc to temporary dir
            source_path = os.path.join(self.srvbes.get_path('source'), adocId)
            content = open(source_path).read()
            target = f"{self.srvbes.get_path('tmp')}/{valid_filename(adocId)}"
            with open(target, 'w') as target_adoc:
                target_adoc.write(content)

            try:
                title_cur = self.kbdict_cur['document'][adocId]['Title']
                title_new = self.kbdict_new['document'][adocId]['Title']
                if title_new != title_cur:
                    for key in keys:
                        if key != 'Title':
                            self.force_keys.add(key)
            except KeyError:
                # Very likely there is no kbdict, so this step is skipped
                pass
        self.log.debug(f"DOC[{adocId}] COMPILE[{COMPILE}] REASON[{REASON}]")


    def step_01_01_decide_keys_compilation(self, available_keys):
        K_PATH = []
        KV_PATH = []

        for key in sorted(available_keys):
            COMPILE_KEY = False
            FORCE_KEY = key in self.force_keys
            FORCE_ALL = self.srvbes.get_value('app', 'force') or FORCE_KEY
            values = self.srvdtb.get_all_values_for_key(key)

            # Compare keys values for the current run and the cache
            # Otherwise, the key is not recompiled when a value is deleted
            rknew = sorted(self.get_kbdict_key(key, new=True))
            rkold = sorted(self.get_kbdict_key(key, new=False))
            if rknew != rkold:
                COMPILE_KEY = True
            self.log.debug(f"KEY[{key}] COMPILE[{COMPILE_KEY}]")

            for value in values:
                COMPILE_VALUE = False
                key_value_docs_new = self.get_kbdict_value(key, value, new=True)
                key_value_docs_cur = self.get_kbdict_value(key, value, new=False)
                VALUE_COMPARISON = key_value_docs_new != key_value_docs_cur

                if VALUE_COMPARISON:
                    self.log.debug(f"KEY[{key}] VALUE[{value}] CHANGE[{VALUE_COMPARISON}]")
                    COMPILE_VALUE = True
                COMPILE_VALUE = COMPILE_VALUE or FORCE_ALL
                COMPILE_KEY = COMPILE_KEY or COMPILE_VALUE
                KV_PATH.append((key, value, COMPILE_VALUE))
                self.log.debug(f"KEY[{key}] VALUE[{value}] COMPILE[{COMPILE_VALUE}]")
            COMPILE_KEY = COMPILE_KEY or FORCE_ALL
            K_PATH.append((key, values, COMPILE_KEY))
            if COMPILE_KEY:
                self.log.debug(f"KEY[{key}] COMPILE[{COMPILE_KEY}]")
        return K_PATH, KV_PATH



    def step_02_transformation(self):
        """Process all keys/values got from documents.
        The algorithm detects which keys/values have changed and compile
        them again. This avoid recompile the whole database, saving time
        and CPU.
        """
        self.log.debug(f"[PROCESSING] - START")
        self.srvthm = self.get_service('Theme')
        runtime = self.srvbes.get_dict('runtime')

        # Keys
        keys_with_compile_true = 0
        for kpath in runtime['K_PATH']:
            key, values, COMPILE_KEY = kpath
            adocId = f"{valid_filename(key)}.adoc"
            htmlId = adocId.replace('.adoc', '.html')
            if COMPILE_KEY:
                self.srvthm.build_page_key(key, values)
                keys_with_compile_true += 1

            # Add compiled page to the target list
            self.srvbes.add_target(adocId, htmlId)

        # # Keys/Values
        pairs_with_compile_true = 0
        for kvpath in runtime['KV_PATH']:
            key, value, COMPILE_VALUE = kvpath
            adocId = f"{valid_filename(key)}_{valid_filename(value)}.adoc"
            htmlId = adocId.replace('.adoc', '.html')
            if COMPILE_VALUE:
                self.srvthm.build_page_key_value(kvpath)
                pairs_with_compile_true += 1

            # Add compiled page to the target list
            self.srvbes.add_target(adocId, htmlId)

        self.log.debug(f"STATS - {keys_with_compile_true} keys will be compiled")
        self.log.debug(f"STATS - {pairs_with_compile_true} key/value pairs will be compiled")
        self.log.debug(f"STATS - Finish processing keys")
        self.log.debug(f"STATS - Target docs: {len(runtime['docs']['targets'])}")
        self.log.debug(f"[PROCESSINNG] - END")


    def _finalize(self):
        pass

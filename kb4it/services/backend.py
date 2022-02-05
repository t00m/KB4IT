#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module with the application logic.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: module holding the application logic
"""

import re
import os
from os.path import abspath
import sys
import glob
import json
import time
import random
import shutil
import tempfile
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor as Executor

from kb4it.core.env import LPATH, GPATH, APP, ADOCPROPS, MAX_WORKERS, EOHMARK
from kb4it.core.service import Service
from kb4it.core.util import valid_filename, load_kbdict
from kb4it.core.util import exec_cmd, delete_target_contents
from kb4it.core.util import get_source_docs, get_asciidoctor_attributes
from kb4it.core.util import get_hash_from_file, get_hash_from_dict
from kb4it.core.util import save_kbdict, copy_docs, copydir
from kb4it.core.util import file_timestamp
from kb4it.core.util import string_timestamp


class Backend(Service):
    """Backend class for managing the main logic workflow.
    """
    running = False
    parameters = None
    runtime = {}  # Dictionary of runtime properties
    kbdict_new = {}  # New compilation cache
    kbdict_cur = {}  # Cached data

    def initialize(self):
        """Initialize application structure."""
        # Status
        self.running = False

        # Get params from command line

        self.parameters = self.app.get_params()
        for param in self.parameters:
            self.log.debug("[SETUP] - KB4IT Param[%s] Value[%s]", param, self.parameters[param])

        # Initialize directories
        self.runtime['dir'] = {}
        self.runtime['dir']['tmp'] = tempfile.mkdtemp(prefix=LPATH['TMP'] + '/')
        self.runtime['dir']['target'] = self.parameters['target']
        self.runtime['dir']['source'] = os.path.realpath(self.parameters['source'])
        self.runtime['dir']['cache'] = os.path.join(LPATH['CACHE'], valid_filename(self.runtime['dir']['source']))
        if not os.path.exists(self.runtime['dir']['cache']):
            os.makedirs(self.runtime['dir']['cache'])

        # if SORT attribute is given, use it instead of the OS timestamp
        if self.parameters['sort'] is None:
            self.runtime['sort_attribute'] = 'Timestamp'
        else:
            self.runtime['sort_attribute'] = self.parameters['sort']
        self.log.debug("[SETUP] - Sort attribute[%s]", self.runtime['sort_attribute'])

        # Initialize docs structure
        self.runtime['docs'] = {}
        self.runtime['docs']['count'] = 0
        self.runtime['docs']['bag'] = []
        self.runtime['docs']['target'] = set()

        # Load cache dictionary and initialize the new one
        self.kbdict_cur = load_kbdict(self.runtime['dir']['source'])
        self.kbdict_new['document'] = {}
        self.kbdict_new['metadata'] = {}

        # Get services
        self.get_services()

    def get_targets(self):
        """Get list of documents converted to pages"""
        return self.runtime['docs']['target']

    def add_target(self, filename):
        """Every doc converted into a page must be added to the target list."""
        self.runtime['docs']['target'].add(filename)
        self.log.debug("[TARGET] - Added page: %s", filename)

    def get_runtime(self):
        """Get all properties."""
        return self.runtime

    def get_runtime_parameter(self, parameter):
        """Get value for a given parameter."""
        return self.runtime[parameter]

    def get_theme_properties(self):
        """Get all properties from loaded theme."""
        return self.runtime['theme']

    def get_theme_property(self, prop):
        """Get value for a given property from loaded theme."""
        return self.runtime['theme'][prop]

    def get_cache_path(self):
        """Get cache path."""
        return self.runtime['dir']['cache']

    def get_source_path(self):
        """Get asciidoctor sources path."""
        return self.runtime['dir']['source']

    def get_target_path(self):
        """Get target path."""
        return self.runtime['dir']['target']

    def get_temp_path(self):
        """Get temporary working path."""
        return self.runtime['dir']['tmp']

    def get_services(self):
        """Get services needed."""
        self.srvdtb = self.get_service('DB')
        self.srvbld = self.get_service('Builder')
        self.srvfes = self.get_service('Frontend')

    def get_numdocs(self):
        """Get current number of valid documents."""
        return self.runtime['docs']['count']

    def stage_01_check_environment(self):
        """Check environment."""
        self.log.info("[SETUP] - Start")
        self.log.debug("[SETUP] - Cache directory: %s", self.runtime['dir']['cache'])
        self.log.debug("[SETUP] - Working directory: %s", self.runtime['dir']['tmp'])

        # Check if source directory exists. If not, stop application
        if not os.path.exists(self.get_source_path()):
            self.log.error("[SETUP] - Source directory '%s' doesn't exist.", self.get_source_path())
            self.log.info("[SETUP] - End")
            self.app.stop()
        self.log.debug("[SETUP] - Source directory: %s", self.get_source_path())

        # check if target directory exists. If not, create it:
        if not os.path.exists(self.get_target_path()):
            os.makedirs(self.get_target_path())
        self.log.debug("[SETUP] - Target directory: %s", self.get_target_path())

        # if no theme defined by params, try to autodetect it.
        # ~ self.log.debug("[SETUP] - Paramters: %s", self.parameters)
        theme_name = self.parameters['theme']
        if theme_name is None:
            self.log.debug("[SETUP] - Theme not provided. Autodetect it.")
            theme_path = self.srvfes.theme_search()
            if theme_path is not None:
                self.srvfes.theme_load(os.path.basename(theme_path))
                self.log.debug("[SETUP] Theme found and loaded")
            else:
                self.log.error("[SETUP] - Theme not found")
                self.log.info("[SETUP] - End")
                self.app.stop()
        else:
            theme_path = self.srvfes.theme_search(theme_name)
            if theme_path is not None:
                self.srvfes.theme_load(os.path.basename(theme_path))
            else:
                self.log.error("[SETUP] - Theme not found")
                self.log.info("[SETUP] - End")
                self.app.stop()

        self.log.info("[SETUP] - End")

    def stage_02_get_source_documents(self):
        """Get Asciidoctor source documents."""
        self.log.info("[DOCS] - Start")
        self.runtime['docs']['bag'] = get_source_docs(self.get_source_path())
        self.runtime['docs']['count'] = len(self.runtime['docs']['bag'])
        self.log.info("[DOCS] - Found %d asciidoctor documents", self.runtime['docs']['count'])
        self.log.info("[DOCS] - End")

    def stage_03_preprocessing(self):
        """
        Extract metadata from source docs into a dict.

        Create metadata section for each adoc and insert it after the
        EOHMARK.

        In this way, after being compiled into HTML, final adocs are
        browsable throught its metadata.
        """
        self.log.info("[PREPROCESSING] - Start")

        # Clean cache
        missing = []
        try:
            for docname in self.kbdict_cur['document']:
                docpath = os.path.join(self.get_source_path(), docname)
                if not os.path.exists(docpath):
                    missing.append(docname)
        except KeyError:
            pass # skip

        if len(missing) == 0:
            self.log.debug("[PREPROCESSING] - Cache is empty")
        else:
            for docname in missing:
                docname = docname.replace('.adoc', '')
                self.delete_document(docname)
            self.log.debug("[PREPROCESSING] - Cache cleaned up")

        # Preprocessing
        for source in self.runtime['docs']['bag']:
            docname = os.path.basename(source)

            # Get metadata
            docpath = os.path.join(self.get_source_path(), docname)
            keys = get_asciidoctor_attributes(docpath)

            # If not document doesn't have a title, skip it.
            try:
                keys['Title']
            except KeyError:
                self.runtime['docs']['count'] -= 1
                self.log.warning("[DOCS] - DOC[%s] doesn't has a title. Skip it.", docname)
                continue

            self.kbdict_new['document'][docname] = {}
            self.log.debug("[PREPROCESSING] - DOC[%s] Preprocessing", docname)

            # Add a new document to the database
            self.srvdtb.add_document(docname)

            # Get datetime timestamp from filesystem and add it as attribute
            timestamp = file_timestamp(source)
            self.srvdtb.add_document_key(docname, 'Timestamp', timestamp)

            # Get content
            with open(source) as source_adoc:
                content = source_adoc.read()

            # To track changes in a document, hashes for metadata and content are created.
            # Comparing them with those in the cache, KB4IT determines if a document must be
            # compiled again. Very useful to reduce the compilation time.

            # Get Document Content and Metadata Hashes
            self.kbdict_new['document'][docname]['content_hash'] = get_hash_from_dict({'content': content})
            self.kbdict_new['document'][docname]['metadata_hash'] = get_hash_from_dict(keys)
            self.kbdict_new['document'][docname]['Timestamp'] = timestamp

            # Generate caches
            for key in keys:
                alist = keys[key]
                for value in alist:
                    if len(value.strip()) == 0:
                        continue

                    try:
                        if key in self.runtime['theme']['date_attributes']:
                            value = string_timestamp(value)
                    except KeyError:
                        pass

                    if key == 'Tag':
                        value = value.lower()
                    self.srvdtb.add_document_key(docname, key, value)

                    # For each document and for each key/value linked to that document add an entry to kbdic['document']
                    try:
                        values = self.kbdict_new['document'][docname][key]
                        if value not in values:
                            values.append(value)
                        self.kbdict_new['document'][docname][key] = sorted(values)
                    except KeyError:
                        self.kbdict_new['document'][docname][key] = [value]

                    # And viceversa, for each key/value add to kbdict['metadata'] all documents linked
                    try:
                        documents = self.kbdict_new['metadata'][key][value]
                        documents.append(docname)
                        self.kbdict_new[key][value] = sorted(documents, key=lambda y: y.lower())
                    except KeyError:
                        if key not in self.kbdict_new['metadata']:
                            self.kbdict_new['metadata'][key] = {}
                        if value not in self.kbdict_new['metadata'][key]:
                            self.kbdict_new['metadata'][key][value] = [docname]

            # Force compilation (from command line)?
            DOC_COMPILATION = False
            FORCE_ALL = self.parameters['force']
            if not FORCE_ALL:
                # Get cached document path and check if it exists
                cached_document = os.path.join(self.runtime['dir']['cache'], docname.replace('.adoc', '.html'))
                cached_document_exists = os.path.exists(cached_document)

                # Compare the document with the one in the cache
                if not cached_document_exists:
                    DOC_COMPILATION = True
                    REASON = "Not cached"
                else:
                    try:
                        hash_new = self.kbdict_new['document'][docname]['content_hash'] + self.kbdict_new['document'][docname]['metadata_hash']
                        hash_cur = self.kbdict_cur['document'][docname]['content_hash'] + self.kbdict_cur['document'][docname]['metadata_hash']
                        DOC_COMPILATION = hash_new != hash_cur
                        REASON = "Hashes differ? %s" % DOC_COMPILATION
                    except Exception as warning:
                        DOC_COMPILATION = True
                        REASON = warning
            else:
                REASON = "Forced"

            COMPILE = DOC_COMPILATION or FORCE_ALL
            # Save compilation status
            self.kbdict_new['document'][docname]['compile'] = COMPILE

            if COMPILE:
                newadoc = content.replace(EOHMARK, '', 1)
                # Write new adoc to temporary dir
                target = "%s/%s" % (self.runtime['dir']['tmp'], valid_filename(docname))
                with open(target, 'w') as target_adoc:
                    target_adoc.write(newadoc)
            self.log.debug("[PREPROCESSING] - DOC[%s] Compile? %s. Reason: %s", docname, COMPILE, REASON)
            self.add_target(docname.replace('.adoc', '.html'))

        # Save current status for the next run
        save_kbdict(self.kbdict_new, self.get_source_path())

        # Build a list of documents sorted by timestamp
        self.srvdtb.sort_database()

        # Documents preprocessing stats
        self.log.debug("[PREPROCESSING] - Stats - Documents analyzed: %d", len(self.runtime['docs']['bag']))
        keep_docs = compile_docs = 0
        for docname in self.kbdict_new['document']:
            if self.kbdict_new['document'][docname]['compile']:
                compile_docs += 1
            else:
                keep_docs += 1
        self.log.info("[PREPROCESSING] - Stats - Keep: %d - Compile: %d", keep_docs, compile_docs)
        self.log.info("[PREPROCESSING] - End")

    def get_kb_dict(self):
        return self.kbdict_new

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

    def stage_04_processing(self):
        """Process all documents."""
        self.log.info("[PROCESSING] - Start")
        all_keys = set(self.srvdtb.get_all_keys())
        ign_keys = set(self.srvdtb.get_ignored_keys())
        available_keys = list(all_keys - ign_keys)
        K_PATH = []
        KV_PATH = []

        for key in sorted(available_keys):
            COMPILE_KEY = False
            FORCE_ALL = self.parameters['force']
            values = self.srvdtb.get_all_values_for_key(key)
            for value in values:
                COMPILE_VALUE = False
                key_value_docs_new = self.get_kbdict_value(key, value, new=True)
                key_value_docs_cur = self.get_kbdict_value(key, value, new=False)
                if key_value_docs_new != key_value_docs_cur:
                    COMPILE_VALUE = True
                COMPILE_VALUE = COMPILE_VALUE or FORCE_ALL
                COMPILE_KEY = COMPILE_KEY or COMPILE_VALUE
                KV_PATH.append((key, value, COMPILE_VALUE))
                self.log.debug("[PROCESSING] - KEY[%s] VALUE[%s] Compile? %s", key, value, COMPILE_VALUE)
            COMPILE_KEY = COMPILE_KEY or FORCE_ALL
            K_PATH.append((key, values, COMPILE_KEY))
            self.log.debug("[PROCESSING] - KEY[%s] Compile? %s", key, COMPILE_KEY)
        self.runtime['K_PATH'] = K_PATH
        self.runtime['KV_PATH'] = KV_PATH

        # # Keys
        for kpath in K_PATH:
            key, values, COMPILE_KEY = kpath
            docname = "%s.adoc" % valid_filename(key)
            if COMPILE_KEY:
                fpath = os.path.join(self.runtime['dir']['tmp'], docname)
                html = self.srvthm.build_page_key(key, values)
                with open(fpath, 'w') as fkey:
                    fkey.write(html)
            self.add_target(docname.replace('.adoc', '.html'))

        # # Keys/Values
        for kvpath in KV_PATH:
            self.srvthm.build_page_key_value(kvpath)

        # ~ self.log.debug("[PROCESSING] - Finish processing keys")
        self.log.debug("[PROCESSING] - Start processing theme")
        self.srvthm.build()
        self.log.debug("[PROCESSING] - End processing theme")
        self.log.info("[PROCESSING] - Target docs: %d", len(self.runtime['docs']['target']))
        self.log.info("[PROCESSING] - End")



    def stage_05_compilation(self):
        """Compile documents to html with asciidoctor."""
        self.log.info("[COMPILATION] - Start")
        dcomps = datetime.datetime.now()

        # copy online resources to target path
        # ~ resources_dir_source = GPATH['THEMES']
        resources_dir_tmp = os.path.join(self.runtime['dir']['tmp'], 'resources')
        shutil.copytree(GPATH['RESOURCES'], resources_dir_tmp)
        self.log.debug("[COMPILATION] - Resources copied to '%s'", resources_dir_tmp)

        adocprops = ''
        self.log.debug("[COMPILATION] - Parameters passed to Asciidoctor:")
        for prop in ADOCPROPS:
            self.log.debug("[COMPILATION] - Key[%s] = Value[%s]", prop, ADOCPROPS[prop])
            if ADOCPROPS[prop] is not None:
                if '%s' in ADOCPROPS[prop]:
                    adocprops += '-a %s=%s ' % (prop, ADOCPROPS[prop] % self.get_target_path())
                else:
                    adocprops += '-a %s=%s ' % (prop, ADOCPROPS[prop])
            else:
                adocprops += '-a %s ' % prop
        # ~ self.log.debug("[COMPILATION] - Parameters passed to Asciidoctor: %s", adocprops)

        # ~ distributed = self.srvthm.get_distributed()
        distributed = self.get_targets()
        with Executor(max_workers=MAX_WORKERS) as exe:
            docs = get_source_docs(self.runtime['dir']['tmp'])
            jobs = []
            jobcount = 0
            num = 1
            self.log.debug("[COMPILATION] - Generating jobs. Please, wait")
            for doc in docs:
                COMPILE = True
                basename = os.path.basename(doc)
                if basename in distributed:
                    distributed_file = os.path.join(LPATH['DISTRIBUTED'], basename)
                    cached_file = os.path.join(self.runtime['dir']['cache'], basename.replace('.adoc', '.html'))
                    if os.path.exists(distributed_file) and os.path.exists(cached_file):
                        cached_hash = get_hash_from_file(distributed_file)
                        current_hash = get_hash_from_file(doc)
                        if cached_hash == current_hash:
                            COMPILE = False

                if COMPILE or self.parameters['force']:
                    cmd = "asciidoctor -q -s %s -b html5 -D %s %s" % (adocprops, self.runtime['dir']['tmp'], doc)
                    # ~ self.log.debug("[COMPILATION] - CMD[%s]", cmd)
                    data = (doc, cmd, num)
                    self.log.debug("[COMPILATION] - Job[%4d] Document[%s] will be compiled", num, basename)
                    job = exe.submit(self.compilation_started, data)
                    job.add_done_callback(self.compilation_finished)
                    jobs.append(job)
                    num = num + 1
                else:
                    self.log.debug("[COMPILATION] - Document[%s] cached. Avoid compiling", basename)

            if num-1 > 0:
                self.log.debug("[COMPILATION] - Created %d jobs. Starting compilation", num - 1)
                # ~ self.log.debug("[COMPILATION] - %3s%% done", "0")
                for job in jobs:
                    adoc, res, jobid = job.result()
                    self.log.info("[COMPILATION] - Job[%d/%d]: %s compiled successfully", jobid, num - 1, os.path.basename(adoc))
                    jobcount += 1
                    if jobcount % MAX_WORKERS == 0:
                        pct = int(jobcount * 100 / len(docs))
                        self.log.debug("[COMPILATION] - %3s%% done", str(pct))

                dcompe = datetime.datetime.now()
                comptime = dcompe - dcomps
                duration = comptime.seconds
                if duration == 0:
                    duration = 1
                avgspeed = int(((num - 1) / duration))
                self.log.debug("[COMPILATION] - 100% done")
                self.log.info("[COMPILATION] - Stats - Time: %d seconds", comptime.seconds)
                self.log.info("[COMPILATION] - Stats - Compiled docs: %d", num - 1)
                self.log.info("[COMPILATION] - Stats - Avg. Speed: %d docs/sec", avgspeed)
                self.log.info("[COMPILATION] - End")
            else:
                self.log.debug("[COMPILATION] - Nothing to do.")

    def compilation_started(self, data):
        (doc, cmd, num) = data
        basename = os.path.basename(doc)
        res = exec_cmd(data)
        return res

    def compilation_finished(self, future):
        time.sleep(random.random())
        cur_thread = threading.current_thread().name
        x = future.result()
        if cur_thread != x:
            path_hdoc, rc, num = x
            basename = os.path.basename(path_hdoc)
            # ~ self.log.debug("[COMPILATION] - Job[%s] for Doc[%s] has RC[%s]", num, basename, rc)
            html = self.srvthm.build_page(path_hdoc)
            # ~ with open(path_hdoc, 'w') as fhtml:
                # ~ fhtml.write(html)
            return x

    def stage_07_clean_target(self):
        """Clean up stage."""
        self.log.info("[CLEANUP] - Start")
        delete_target_contents(LPATH['DISTRIBUTED'])
        self.log.debug("[CLEANUP] - Distributed files deleted")
        # ~ distributed = self.srvthm.get_distributed()
        distributed = self.get_targets()
        for adoc in distributed:
            source = os.path.join(self.runtime['dir']['tmp'], adoc)
            target = LPATH['DISTRIBUTED']
            try:
                shutil.copy(source, target)
            except:
                self.log.warning("Missing source file: %s", source)
        self.log.debug("[CLEANUP] - Copy temporary files to distributed directory")

        delete_target_contents(self.get_target_path())
        self.log.debug("[CLEANUP] - Deleted target contents in: %s", self.get_target_path())
        self.log.info("[CLEANUP] - End")

    def stage_08_refresh_target(self):
        """Refresh target."""
        self.log.info("[INSTALL] - Start")

        # Copy asciidocs documents to target path
        pattern = os.path.join(self.get_source_path(), '*.adoc')
        files = glob.glob(pattern)
        docsdir = os.path.join(self.get_target_path(), 'sources')
        os.makedirs(docsdir)
        copy_docs(files, docsdir)
        self.log.debug("[INSTALL] - Copy %d asciidoctor sources to target path", len(files))

        # Copy compiled documents to cache path
        pattern = os.path.join(self.runtime['dir']['tmp'], '*.html')
        files = glob.glob(pattern)
        copy_docs(files, self.runtime['dir']['cache'])
        self.log.debug("[INSTALL] - Copy %d html files from temporary path to cache path", len(files))

        # Copy cached documents to target path
        n = 0
        for filename in self.runtime['docs']['target']:
            source = os.path.join(self.runtime['dir']['cache'], filename)
            target = os.path.join(self.get_target_path(), filename)
            try:
                shutil.copy(source, target)
            except FileNotFoundError as error:
                self.log.error(error)
                self.log.error("[INSTALL] - Consider to run the command again with the option -force")
            n += 1
        self.log.debug("[INSTALL] - Copied %d cached documents successfully to target path", n)

        # Copy global resources to target path
        resources_dir_target = os.path.join(self.get_target_path(), 'resources')
        theme_target_dir = os.path.join(resources_dir_target, 'themes')
        theme = self.get_theme_properties()
        DEFAULT_THEME = os.path.join(GPATH['THEMES'], 'default')
        CUSTOM_THEME_ID = theme['id']
        CUSTOM_THEME_PATH = theme['path']
        copydir(DEFAULT_THEME, os.path.join(theme_target_dir, 'default'))
        copydir(CUSTOM_THEME_PATH, os.path.join(theme_target_dir, CUSTOM_THEME_ID))
        copydir(GPATH['COMMON'], os.path.join(resources_dir_target, 'common'))
        self.log.debug("[INSTALL] - Copied global resources to target path")

        # Copy local resources to target path
        source_resources_dir = os.path.join(self.get_source_path(), 'resources')
        if os.path.exists(source_resources_dir):
            resources_dir_target = os.path.join(self.get_target_path(), 'resources')
            copydir(source_resources_dir, resources_dir_target)
            self.log.debug("[INSTALL] - Copied local resources to target path")

        # Copy back all HTML files from target to cache
        delete_target_contents(self.runtime['dir']['cache'])
        pattern = os.path.join(self.get_target_path(), '*.html')
        html_files = glob.glob(pattern)
        copy_docs(html_files, self.runtime['dir']['cache'])
        self.log.debug("[INSTALL] - Copying HTML files back to cache...")

        # Copy JSON database to target path so it can be queried from
        # others applications
        save_kbdict(self.kbdict_new, self.get_target_path(), 'kb4it')
        self.log.debug("[INSTALL] - Copied JSON database to target")
        self.log.info("[INSTALL] - End")

    def stage_09_remove_temporary_dir(self):
        """Remove temporary dir."""
        self.log.info("[POST-INSTALL] - Start")
        shutil.rmtree(self.runtime['dir']['tmp'])
        self.log.debug("[POST-INSTALL] - Temporary directory deleted successfully")
        self.log.info("[POST-INSTALL] - End")

    def cleanup(self):
        """Clean KB4IT temporary environment.
        """
        try:
            delete_target_contents(self.runtime['dir']['tmp'])
        except  Exception as KeyError:
            pass
        self.log.debug("[CLEANUP] - KB4IT Workspace clean")

    def reset(self):
        """WARNING.

        Reset environment given source and target directories.
        Delete:
        - Source directory
        - Target directory
        - Temporary directory
        - Cache directory
        - KB4IT database file for this environment
        WARNING!!!

        Please, note: if you pass the wrong directory...
        """
        self.kbdict_new = {}
        self.kbdict_cur = {}
        filename = valid_filename(self.get_source_path())
        kdbdict = 'kbdict-%s.json' % filename
        KB4IT_DB_FILE = os.path.join(LPATH['DB'], kdbdict)

        delete_target_contents(self.runtime['dir']['cache'])
        self.log.info("[RESET] - DIR[%s] deleted", self.runtime['dir']['cache'])

        delete_target_contents(self.runtime['dir']['tmp'])
        self.log.info("[RESET] - DIR[%s] deleted", self.runtime['dir']['tmp'])

        delete_target_contents(self.get_source_path())
        self.log.info("[RESET] - DIR[%s] deleted", self.get_source_path())

        delete_target_contents(self.get_target_path())
        self.log.info("[RESET] - DIR[%s] deleted", self.get_target_path())

        delete_target_contents(KB4IT_DB_FILE)
        self.log.info("[RESET] - FILE[%s] deleted", KB4IT_DB_FILE)

        self.log.info("[RESET] - KB4IT environment reset")

    def run(self):
        """Start script execution following this flow.

        1. Check environment
        2. Get source documents
        3. Preprocess documents (get metadata)
        4. Process documents in a temporary dir
        5. Compile documents to html with asciidoctor
        6. Delete contents of target directory (if any)
        7. Refresh target directory
        8. Remove temporary directory
        """
        self.running = True
        self.stage_01_check_environment()
        self.srvthm = self.get_service('Theme')
        self.srvthm.generate_sources()
        self.stage_02_get_source_documents()
        self.stage_03_preprocessing()
        self.stage_04_processing()
        self.stage_05_compilation()
        self.stage_07_clean_target()
        self.stage_08_refresh_target()
        self.stage_09_remove_temporary_dir()
        self.log.debug("[APP] - Browse your documentation repository:")
        homepage = os.path.join(abspath(self.get_target_path()), 'index.html')
        self.log.info("[APP] - KB4IT homepage: %s", homepage)
        self.log.info("[APP] - KB4IT - Execution finished")
        self.running = False

    def is_running(self):
        """Return current execution status."""
        return self.running

    def delete_document(self, adoc):
        """Remove a document from database and also from cache."""
        # Remove source document
        try:
            source_dir = self.get_source_path()
            source_path = os.path.join(source_dir, "%s.adoc" % adoc)
            os.unlink(source_path)
            self.log.debug("DOC[%s] deleted from source directory", adoc)
        except FileNotFoundError:
            self.log.debug("DOC[%s] not found in source directory", adoc)

        # Remove database document
        self.srvdtb.del_document(adoc)
        self.log.debug("DOC[%s] deleted from database", adoc)

        # Remove cache document
        cache_dir = self.get_cache_path()
        cached_path = os.path.join(cache_dir, "%s.html" % adoc)
        try:
            os.unlink(cached_path)
            self.log.debug("DOC[%s] deleted from cache directory", adoc)
        except FileNotFoundError:
            self.log.debug("DOC[%s] not found in cache directory", adoc)

    def end(self):
        self.cleanup()


    # ~ def distribute_html(self, name, content, var):
        # ~ """
        # ~ Distribute html file to the temporary directory.
        # ~ """
        # ~ var['menu_contents'] = ''
        # ~ HTML_HEADER_COMMON = self.template('HTML_HEADER_COMMON')
        # ~ HTML_HEADER_DOC = self.template('HTML_HEADER_DOC')
        # ~ HTML_HEADER_NODOC = self.template('HTML_HEADER_NODOC')
        # ~ HTML_FOOTER = self.template('HTML_FOOTER')

        # ~ HTML = ""
        # ~ HEADER = HTML_HEADER_COMMON.render(var=var)
        # ~ FOOTER = HTML_FOOTER.render(var=var)

        # ~ HTML += HEADER
        # ~ HTML += content
        # ~ HTML += FOOTER

        # ~ PAGE_NAME = "%s.html" % name
        # ~ PAGE_PATH = os.path.join(self.srvbes.get_temp_path(), PAGE_NAME)
        # ~ with open(PAGE_PATH, 'w') as fpag:
            # ~ try:
                # ~ fpag.write(HTML)
            # ~ except Exception as error:
                # ~ self.log.error("[DISTRIBUTE] - %s", error)
        # ~ self.distributed[PAGE_NAME] = get_hash_from_file(PAGE_PATH)
        # ~ self.srvbes.add_target(PAGE_NAME)
        # ~ self.log.debug("[DISTRIBUTE] - Page[%s] distributed to temporary path", os.path.basename(PAGE_PATH))

    # ~ def distribute_to_source(self, name, content):
        # ~ """
        # ~ Distribute source file to user source directory.
        # ~ Use this method when the source asciidoctor file has to
        # ~ be analyzed to extract its properties.
        # ~ File path reference will be saved and deleted at the end of the
        # ~ execution.
        # ~ """
        # ~ PAGE_NAME = "%s.adoc" % name
        # ~ PAGE_PATH = os.path.join(self.srvbes.get_source_path(), PAGE_NAME)
        # ~ self.temp_sources.append(PAGE_PATH)
        # ~ try:
            # ~ with open(PAGE_PATH, 'w') as fpag:
                # ~ fpag.write(content)
                # ~ self.log.debug("[BUILDER] - PAGE[%s] distributed to source path", name)
        # ~ except OSError as error:
            # ~ self.log.error(error)
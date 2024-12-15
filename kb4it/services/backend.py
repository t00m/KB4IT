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
import errno
import random
import shutil
import tempfile
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor as Executor

from memory_profiler import profile

from kb4it.core.env import ENV
from kb4it.core.service import Service
from kb4it.core.util import now
from kb4it.core.util import valid_filename
from kb4it.core.util import exec_cmd, delete_target_contents
from kb4it.core.util import get_source_docs, get_asciidoctor_attributes
from kb4it.core.util import get_hash_from_file, get_hash_from_dict
from kb4it.core.util import copy_docs, copydir
# ~ from kb4it.core.util import file_timestamp
# ~ from kb4it.core.util import string_timestamp
from kb4it.core.util import json_load, json_save
from kb4it.core.util import timeit

from pyinstrument import Profiler

fp=open('memory_profiler.log','w+')

class Backend(Service):
    """Backend class for managing the main logic workflow.
    """
    running = False     # Backend running?
    runtime = {}        # Dictionary of runtime properties
    kbdict_new = {}     # New compilation cache
    kbdict_cur = {}     # Cached data
    force_keys = set()  # List of keys which must be compiled (forced)

    def initialize(self):
        """Initialize application structure."""

        self.log.trace("[BACKEND] - Started at %s", now())

        # Get params from command line
        self.params = self.app.get_params()

        # Get repository config file (if any)
        try:
            repo_config_file = self.params.config
            self.repo = json_load(repo_config_file)
            self.log.trace(f"[BACKEND/SETUP] - Repository config file: '{repo_config_file}")
            self.log.trace(f"[BACKEND/SETUP] - Repository parameters:")
            for param in self.repo:
                self.log.trace(f"[BACKEND/SETUP] - \tParameter[{param}]: {self.repo[param]}")
            repo_config_exists = True
        except Exception as error:
            self.log.trace(f"[BACKEND/SETUP] - Repository config file not found in command line params")
            repo_config_exists = False

        # Initialize runtime dictionary
        self.runtime['dir'] = {}
        if repo_config_exists:
            self.runtime['dir']['source'] = os.path.realpath(self.repo['source'])
            self.runtime['dir']['target'] = os.path.realpath(self.repo['target'])

            PROJECT = valid_filename(self.runtime['dir']['source'])
            WORKDIR = os.path.join(ENV['LPATH']['WORK'], PROJECT)
            self.runtime['dir']['work'] = WORKDIR
            self.runtime['dir']['tmp'] = os.path.join(WORKDIR, 'tmp')
            self.runtime['dir']['www'] = os.path.join(WORKDIR, 'www')
            self.runtime['dir']['dist'] = os.path.join(WORKDIR, 'dist')
            self.runtime['dir']['cache'] = os.path.join(WORKDIR, 'cache')

            self.log.trace(f"[BACKEND/SETUP] - Checking directories:")
            for entry in self.runtime['dir']:
                create_directory = False
                dirname = self.runtime['dir'][entry]
                if entry not in ['source', 'target']:
                    dirname = self.runtime['dir'][entry]
                    if not os.path.exists(dirname):
                        os.makedirs(dirname)
                        create_directory = True
                self.log.trace(f"[BACKEND/SETUP] - \tCreate directory {dirname}? {create_directory}")

            # if SORT attribute is given, use it instead of the OS timestamp
            try:
                self.runtime['sort_attribute'] = self.repo['sort']
            except:
                # ~ self.runtime['sort_attribute'] = 'Timestamp'
                self.log.error("[BACKEND/SETUP] - No property defined for sorting")
                sys.exit(-1)

            self.log.trace("[BACKEND/SETUP] - Sort attribute: {self.runtime['sort_attribute']}")

            # Initialize docs structure
            self.runtime['docs'] = {}
            self.runtime['docs']['count'] = 0
            self.runtime['docs']['bag'] = []
            self.runtime['docs']['target'] = set()

            # Load cache dictionary and initialize the new one
            self.kbdict_cur = self.load_kbdict(self.runtime['dir']['source'])
            self.log.trace(f"[BACKEND/SETUP] - Loaded kbdict from last run with {len(self.kbdict_cur['document'])} documents")

            self.kbdict_new['document'] = {}
            self.kbdict_new['metadata'] = {}
            self.log.trace(f"[BACKEND/SETUP] - Created new kbdict for current execution")

            # Get services
            self.get_services()
        else:
            self.runtime['dir']['source'] = '/dev/null'

    def set_config(self, config: dict):
        self.repo = config['repo']
        self.runtime = config['runtime']

    def load_kbdict(self, source_path):
        """C0111: Missing function docstring (missing-docstring)."""
        source_path = valid_filename(source_path)
        KB4IT_DB_FILE = os.path.join(ENV['LPATH']['DB'], 'kbdict-%s.json' % source_path)
        try:
            kbdict = json_load(KB4IT_DB_FILE)
            self.log.trace(f"[BACKEND/CONF] - Loading KBDICT from {KB4IT_DB_FILE}")
        except FileNotFoundError:
            kbdict = {}
            kbdict['document'] = {}
            kbdict['metadata'] = {}
        except Exception as error:
            self.log.error(f"[BACKEND/CONF] - There was an error reading file {KB4IT_DB_FILE}")
            sys.exit()
        self.log.trace("[BACKEND/CONF] - Current kbdict entries: %d", len(kbdict))
        return kbdict

    def save_kbdict(self, kbdict, path, name=None):
        """C0111: Missing function docstring (missing-docstring)."""
        if name is None:
            target_path = valid_filename(path)
            KB4IT_DB_FILE = os.path.join(ENV['LPATH']['DB'], 'kbdict-%s.json' % target_path)
        else:
            KB4IT_DB_FILE = os.path.join(path, '%s.json' % name)

        json_save(KB4IT_DB_FILE, kbdict)
        self.log.trace("[BACKEND/CONF] - KBDICT %s saved", KB4IT_DB_FILE)

    def get_targets(self):
        """Get list of documents converted to pages"""
        return self.runtime['docs']['target']

    def add_target(self, kbfile):
        """All objects received by this method will be appended to the
        list of objects that will be copied to the target directory.
        """
        self.runtime['docs']['target'].add(kbfile)
        self.log.trace("[BACKEND/TARGET] - Added resource: %s", kbfile)

    def get_runtime_dict(self):
        """Get all properties."""
        return self.runtime

    def get_repo_dict(self):
        """Get all properties."""
        return self.repo

    def get_runtime_parameter(self, parameter):
        """Get value for a given parameter."""
        return self.runtime[parameter]

    def get_repo_parameters(self):
        """Get repository parameters."""
        return self.repo

    def get_theme_properties(self):
        """Get all properties from loaded theme."""
        return self.runtime['theme']

    def get_theme_property(self, prop):
        """Get value for a given property from loaded theme."""
        return self.runtime['theme'][prop]

    def get_www_path(self):
        """Get temporary target directory."""
        return self.runtime['dir']['www']

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

    def get_numdocs(self):
        """Get current number of valid documents."""
        return self.runtime['docs']['count']

    @timeit
    @profile(stream=fp)
    def stage_01_check_environment(self):
        """Check environment."""
        frontend = self.get_service('Frontend')
        self.log.trace("[BACKEND/STAGE 1 - CHECKS] - Start at %s", now())
        #self.log.trace("[BACKEND/SETUP] - Cache directory: %s", self.runtime['dir']['cache'])
        #self.log.trace("[BACKEND/SETUP] - Working directory: %s", self.runtime['dir']['tmp'])
        #self.log.trace("[BACKEND/SETUP] - Distribution directory: %s", self.runtime['dir']['dist'])
        #self.log.trace("[BACKEND/SETUP] - Temporary target directory: %s", self.runtime['dir']['www'])

        # Check if source directory exists. If not, stop application
        if not os.path.exists(self.get_source_path()):
            self.log.error("[BACKEND/SETUP] - Source directory '%s' doesn't exist.", self.get_source_path())
            self.log.trace("[BACKEND/SETUP] - End at %s", now())
            self.app.stop()
        self.log.trace("[BACKEND/SETUP] - Source directory: %s", self.get_source_path())

        # check if target directory exists. If not, create it:
        if not os.path.exists(self.get_target_path()):
            os.makedirs(self.get_target_path())
        self.log.trace("[BACKEND/SETUP] - Target directory: %s", self.get_target_path())

        if  self.get_source_path() == ENV['LPATH']['TMP_SOURCE'] and self.get_target_path() == ENV['LPATH']['TMP_TARGET']:
            self.log.error("[BACKEND/SETUP] - No config file especified")
            self.log.error("[BACKEND/SETUP] - End at %s", now())
            sys.exit()

        # if no theme defined by params, try to autodetect it.
        # ~ self.log.trace("[SETUP] - Paramters: %s", self.repo)
        try:
            theme_name = self.repo['theme']
        except KeyError:
            theme_name = 'techdoc'

        if theme_name is None:
            self.log.trace("[BACKEND/SETUP] - Theme not provided. Autodetect it.")
            theme_path = frontend.theme_search()
            if theme_path is not None:
                frontend.theme_load(os.path.basename(theme_path))
                self.log.trace("[BACKEND/SETUP] Theme found and loaded")
            else:
                self.log.error("[BACKEND/SETUP] - Theme not found")
                self.log.trace("[BACKEND/SETUP] - End at %s", now())
                self.app.stop()
        else:
            theme_path = frontend.theme_search(theme_name)
            if theme_path is not None:
                frontend.theme_load(os.path.basename(theme_path))
            else:
                self.log.error("[BACKEND/SETUP] - Theme not found")
                self.log.trace("[BACKEND/SETUP] - End at %s", now())
                self.app.stop()

        self.log.trace("[BACKEND/SETUP] - End at %s", now())

    @timeit
    @profile(stream=fp)
    def stage_02_get_source_documents(self):
        """Get Asciidoctor documents from source directory."""
        self.log.trace("[BACKEND/STAGE 2 - SOURCES] - Start at %s", now())
        sources_path = self.get_source_path()

        # Firstly, allow theme to generate documents
        self.srvthm = self.get_service('Theme')
        self.srvthm.generate_sources()

        # If 'about_app.adoc' doesn't exist, create one from template
        about_app_source = os.path.join(sources_path, 'about_app.adoc')
        if not os.path.exists(about_app_source):
            about_app_default = os.path.join(ENV['GPATH']['TEMPLATES'], 'PAGE_ABOUT_APP.tpl')
            shutil.copy(about_app_default, about_app_source)
            self.log.warning("Added default 'About App' to your sources")

        # Then, get them
        self.runtime['docs']['bag'] = get_source_docs(sources_path)
        basenames = []
        for filepath in self.runtime['docs']['bag']:
            basenames.append(os.path.basename(filepath))
        self.runtime['docs']['filenames'] = basenames
        self.runtime['docs']['count'] = len(self.runtime['docs']['bag'])




        self.log.info("[BACKEND/SOURCEDOCS] - Found %d asciidoctor documents", self.runtime['docs']['count'])
        self.log.trace("[BACKEND/SOURCEDOCS] - End at %s", now())

    @timeit
    def stage_03_00_preprocess_document(self, source: str):
        docname = os.path.basename(source)

        # Get metadata
        keys = self.stage_03_00_preprocess_document_metadata(docname)

        if keys is None:
            self.log.error(f"[BACKEND/PREPROCESSING] - Document '{docname}' not compliant: please, check errors")
            return

        # If document doesn't have a title, skip it.
        try:
            title = keys['Title'][0]
            self.log.trace(f"[BACKEND/PREPROCESSING] - Document '{docname}: {title}' will be processed")
        except KeyError:
            self.runtime['docs']['count'] -= 1
            self.log.warning("[BACKEND/PREPROCESSING] - DOC[%s] doesn't have a title. Skip it.", docname)

        self.kbdict_new['document'][docname] = {}
        self.log.trace("[BACKEND/PREPROCESSING] - DOC[%s] Preprocessing", docname)

        # Add a new document to the database
        self.srvdtb.add_document(docname)

        # Get datetime timestamp from filesystem and add it as attribute
        # ~ ts = file_timestamp(source)
        # ~ self.srvdtb.add_document_key(docname, 'Timestamp', ts)

        # Get content
        with open(source) as source_adoc:
            content = source_adoc.read()

        self.stage_03_00_preprocess_document_hashes(docname, content, keys)
        self.stage_03_00_preprocess_document_caches(docname, keys)
        self.stage_03_00_preprocess_document_compile(docname, content, keys)

        # self.log.trace("[BACKEND/PREPROCESSING] - DOC[%s] Compile? %s. Reason: %s", docname, COMPILE, REASON)

        # Add compiled page to the target list
        self.add_target(docname.replace('.adoc', '.html'))

    @timeit
    def stage_03_00_preprocess_document_metadata(self, docname: str):
        docpath = os.path.join(self.get_source_path(), docname)
        keys = get_asciidoctor_attributes(docpath)
        self.log.trace(f"[BACKEND/PREPROCESSING] Document '{docname} keys: {keys}")
        return keys

    @timeit
    def stage_03_00_preprocess_document_hashes(self, docname: str, content: str, keys: list):
        # To track changes in a document, hashes for metadata and content are created.
        # Comparing them with those in the cache, KB4IT determines if a document must be
        # compiled again. Very useful to reduce the compilation time.

        # Get Document Content and Metadata Hashes
        self.kbdict_new['document'][docname]['content_hash'] = get_hash_from_dict({'content': content})
        self.kbdict_new['document'][docname]['metadata_hash'] = get_hash_from_dict(keys)

    @timeit
    def stage_03_00_preprocess_document_caches(self, docname: str, keys: list):
        # Generate caches
        for key in keys:
            alist = keys[key]
            for value in alist:
                if len(value.strip()) == 0:
                    continue

                try:
                    if key in self.runtime['sort_attribute']:
                        # ~ value = string_timestamp(value)
                        value = value[:10].replace('-', '')
                except:
                    self.log.error(f"Key involved: {key}")
                    self.log.error(f"Key involved: {self.runtime['theme']}")

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

    @timeit
    def stage_03_00_preprocess_document_compile(self, docname: str, content:str, keys:list):
        # Force compilation (from command line)?
        DOC_COMPILATION = False
        FORCE_ALL = self.params.force
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
        try:
            self.kbdict_new['document'][docname]['compile'] = COMPILE
        except KeyError as keyerror:
            #FIXME: check
            self.log.error(keyerror)
            raise

        if COMPILE:
            # Write new adoc to temporary dir
            target = "%s/%s" % (self.runtime['dir']['tmp'], valid_filename(docname))
            with open(target, 'w') as target_adoc:
                target_adoc.write(content)

            try:
                title_cur = self.kbdict_cur['document'][docname]['Title']
                title_new = self.kbdict_new['document'][docname]['Title']
                if title_new != title_cur:
                    for key in keys:
                        if key != 'Title':
                            self.force_keys.add(key)
            except KeyError:
                # Very likely there is no kbdict, so this step is skipped
                pass
        self.log.trace("[BACKEND/PREPROCESSING] - DOC[%s] Compile? %s. Reason: %s", docname, COMPILE, REASON)

    @timeit
    @profile(stream=fp)
    def stage_03_preprocessing(self):
        """
        Extract metadata from source docs into a dict.
        Create metadata section for each adoc and insert it after the
        EOHMARK.
        In this way, after being compiled into HTML, final adocs are
        browsable throught its metadata.
        """
        self.log.trace("[BACKEND/PREPROCESSING] - Start at %s", now())

        # ~ def _clean_cache():
            # ~ # Clean cache
            # ~ missing = []
            # ~ try:
                # ~ for docname in self.kbdict_cur['document']:
                    # ~ docpath = os.path.join(self.get_source_path(), docname)
                    # ~ if not os.path.exists(docpath):
                        # ~ missing.append(docname)
            # ~ except KeyError:
                # ~ pass  # skip

            # ~ if len(missing) == 0:
                # ~ self.log.trace("[BACKEND/PREPROCESSING] - Cache is empty")
            # ~ else:
                # ~ for docname in missing:
                    # ~ docname = docname.replace('.adoc', '')
                    # ~ self.delete_document(docname)
                # ~ self.log.trace("[BACKEND/PREPROCESSING] - Cache cleaned up")

        #_clean_cache()

        # Preprocessing
        #profiler = Profiler()
        for source in self.runtime['docs']['bag']:
            self.log.workflow(f"Preprocessing {source}")
            #profiler.start()
            self.stage_03_00_preprocess_document(source)
            #profiler.stop()
            #profiler.print()


        # Save current status for the next run
        self.save_kbdict(self.kbdict_new, self.get_source_path())

        # Build a list of documents sorted by timestamp
        self.srvdtb.sort_database()

        # Documents preprocessing stats
        self.log.trace("[BACKEND/PREPROCESSING] - Stats - Documents analyzed: %d", len(self.runtime['docs']['bag']))
        keep_docs = compile_docs = 0
        for docname in self.kbdict_new['document']:
            if self.kbdict_new['document'][docname]['compile']:
                compile_docs += 1
            else:
                keep_docs += 1
        self.log.info("[BACKEND/PREPROCESSING] - Stats - Keep: %d - Compile: %d", keep_docs, compile_docs)
        self.log.trace("[BACKEND/PREPROCESSING] - End %s", now())

    def get_ignored_keys(self):
        return self.ignored_keys

    def get_kb_dict(self):
        return self.kbdict_new

    @timeit
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

    @timeit
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

    @timeit
    def stage_04_processing_00_analyze_keys(self, available_keys):
        K_PATH = []
        KV_PATH = []

        for key in sorted(available_keys):
            COMPILE_KEY = False
            FORCE_KEY = key in self.force_keys
            FORCE_ALL = self.params.force or FORCE_KEY
            values = self.srvdtb.get_all_values_for_key(key)

            # Compare keys values for the current run and the cache
            # Otherwise, the key is not recompiled when a value is deleted
            rknew = sorted(self.get_kbdict_key(key, new=True))
            rkold = sorted(self.get_kbdict_key(key, new=False))
            if rknew != rkold:
                COMPILE_KEY = True
            self.log.trace("[BACKEND/PROCESSING] - Key[%s] Compile? %s", key, COMPILE_KEY)

            for value in values:
                COMPILE_VALUE = False
                key_value_docs_new = self.get_kbdict_value(key, value, new=True)
                key_value_docs_cur = self.get_kbdict_value(key, value, new=False)
                VALUE_COMPARISON = key_value_docs_new != key_value_docs_cur

                if VALUE_COMPARISON:
                    self.log.trace("[BACKEND/PROCESSING] - Key[%s] Value[%s] new != old? %s", key, value, VALUE_COMPARISON)
                    COMPILE_VALUE = True
                COMPILE_VALUE = COMPILE_VALUE or FORCE_ALL
                COMPILE_KEY = COMPILE_KEY or COMPILE_VALUE
                KV_PATH.append((key, value, COMPILE_VALUE))
                self.log.trace("[BACKEND/PROCESSING] - Key[%s] Value[%s] Compile? %s", key, value, COMPILE_VALUE)
            COMPILE_KEY = COMPILE_KEY or FORCE_ALL
            K_PATH.append((key, values, COMPILE_KEY))
            if COMPILE_KEY:
                self.log.trace("[BACKEND/PROCESSING] - Key[%s] Compile? %s", key, COMPILE_KEY)
        return K_PATH, KV_PATH


    @timeit
    @profile(stream=fp)
    def stage_04_processing(self):
        """Process all keys/values got from documents.
        The algorithm detects which keys/values have changed and compile
        them again. This avoid recompile the whole database, saving time
        and CPU.
        """
        self.log.trace("[BACKEND/PROCESSING] - Start at %s", now())
        repo = self.get_repo_parameters()
        all_keys = set(self.srvdtb.get_all_keys())
        ign_default_keys = set(self.srvdtb.get_ignored_keys())
        ign_theme_keys = set(repo['ignored_keys'])
        self.ignored_keys = ign_default_keys.union(ign_theme_keys)
        available_keys = list(all_keys - self.ignored_keys)
        # ~ self.log.trace("All keys: %s", all_keys)
        # ~ self.log.trace("Ign keys: %s", ', '.join(list(self.ignored_keys)))
        # ~ self.log.trace("Avl keys: %s", available_keys)

        self.runtime['K_PATH'], self.runtime['KV_PATH'] = self.stage_04_processing_00_analyze_keys(available_keys)

        # # Keys
        for kpath in self.runtime['K_PATH']:
            key, values, COMPILE_KEY = kpath
            docname = "%s.adoc" % valid_filename(key)
            if COMPILE_KEY:
                fpath = os.path.join(self.runtime['dir']['tmp'], docname)
                self.srvthm.build_page_key(key, values)

            # Add compiled page to the target list
            self.add_target(docname.replace('.adoc', '.html'))

        # # Keys/Values
        for kvpath in self.runtime['KV_PATH']:
            self.srvthm.build_page_key_value(kvpath)
            key, value, COMPILE_VALUE = kvpath
            docname = "%s_%s.adoc" % (valid_filename(key), valid_filename(value))

            # Add compiled page to the target list
            self.add_target(docname.replace('.adoc', '.html'))

        self.log.trace("[BACKEND/PROCESSING] - Finish processing keys")
        self.log.trace("[BACKEND/PROCESSING] - Start processing theme at %s", now())
        self.srvthm.build()
        self.log.trace("[BACKEND/PROCESSING] - End processing theme at %s", now())
        self.log.trace("[BACKEND/PROCESSING] - Target docs: %d", len(self.runtime['docs']['target']))
        self.log.trace("[BACKEND/PROCESSING] - End at %s", now())

    @timeit
    @profile(stream=fp)
    def stage_05_compilation(self):
        """Compile documents to html with asciidoctor."""
        # ~ profiler = Profiler()

        self.log.info("[BACKEND/COMPILATION] - Start at %s", now())
        dcomps = datetime.datetime.now()

        # copy online resources to target path
        # ~ resources_dir_source = GPATH['THEMES']
        resources_dir_tmp = os.path.join(self.runtime['dir']['tmp'], 'resources')
        #if path already exists, remove it before copying with copytree()
        if os.path.exists(resources_dir_tmp):
            shutil.rmtree(resources_dir_tmp)
            shutil.copytree(ENV['GPATH']['RESOURCES'], resources_dir_tmp)
        self.log.trace("[BACKEND/COMPILATION] - Resources copied to '%s'", resources_dir_tmp)

        adocprops = ''
        self.log.trace("[BACKEND/COMPILATION] - Parameters passed to Asciidoctor:")
        for prop in ENV['CONF']['ADOCPROPS']:
            self.log.trace("[BACKEND/COMPILATION] - Key[%s] = Value[%s]", prop, ENV['CONF']['ADOCPROPS'][prop])
            if ENV['CONF']['ADOCPROPS'][prop] is not None:
                if '%s' in ENV['CONF']['ADOCPROPS'][prop]:
                    adocprops += '-a %s=%s ' % (prop, ENV['CONF']['ADOCPROPS'][prop] % self.get_target_path())
                else:
                    adocprops += '-a %s=%s ' % (prop, ENV['CONF']['ADOCPROPS'][prop])
            else:
                adocprops += '-a %s ' % prop
        # ~ self.log.trace("[COMPILATION] - Parameters passed to Asciidoctor: %s", adocprops)

        # ~ distributed = self.srvthm.get_distributed()
        distributed = self.get_targets()
        # ~ params = self.app.get_app_conf()
        with Executor(max_workers=self.params.workers) as exe:
            docs = get_source_docs(self.runtime['dir']['tmp'])
            jobs = []
            jobcount = 0
            num = 1
            self.log.trace("[BACKEND/COMPILATION] - Generating jobs. Please, wait")
            for doc in docs:
                COMPILE = True
                basename = os.path.basename(doc)
                if basename in distributed:
                    distributed_file = os.path.join(self.runtime['dir']['dist'], basename)
                    cached_file = os.path.join(self.runtime['dir']['cache'], basename.replace('.adoc', '.html'))
                    if os.path.exists(distributed_file) and os.path.exists(cached_file):
                        cached_hash = get_hash_from_file(distributed_file)
                        current_hash = get_hash_from_file(doc)
                        if cached_hash == current_hash:
                            COMPILE = False


                if COMPILE or self.params.force:
                    # ~ profiler.start()
                    cmd = "asciidoctor -q -s %s -b html5 -D %s %s" % (adocprops, self.runtime['dir']['tmp'], doc)
                    self.log.trace("[COMPILATION] - CMD[%s]", cmd)
                    data = (doc, cmd, num)
                    self.log.trace("[BACKEND/COMPILATION] - Job[%4d] Document[%s] will be compiled", num, basename)
                    job = exe.submit(self.compilation_started, data)
                    job.add_done_callback(self.compilation_finished)
                    jobs.append(job)
                    num = num + 1
                    # ~ profiler.stop()
                    # ~ profiler.print()
                else:
                    self.log.trace("[BACKEND/COMPILATION] - Document[%s] cached. Avoid compiling", basename)

            if num-1 > 0:
                self.log.info("[BACKEND/COMPILATION] - Created %d jobs. Starting compilation at %s", num - 1, now())
                # ~ self.log.trace("[COMPILATION] - %3s%% done", "0")
                for job in jobs:
                    adoc, res, jobid = job.result()
                    self.log.trace("[BACKEND/COMPILATION] - Job[%d/%d]: %s compiled successfully", jobid, num - 1, os.path.basename(adoc))
                    jobcount += 1
                    if jobcount % ENV['CONF']['MAX_WORKERS'] == 0:
                        pct = int(jobcount * 100 / len(docs))
                        self.log.info("[BACKEND/COMPILATION] - %3s%% done", str(pct))

                dcompe = datetime.datetime.now()
                comptime = dcompe - dcomps
                duration = comptime.seconds
                if duration == 0:
                    duration = 1
                avgspeed = int(((num - 1) / duration))
                #self.log.info("[BACKEND/COMPILATION] - 100% done")
                self.log.trace("[BACKEND/COMPILATION] - Stats - Time: %d seconds", comptime.seconds)
                self.log.trace("[BACKEND/COMPILATION] - Stats - Compiled docs: %d", num - 1)
                self.log.trace("[BACKEND/COMPILATION] - Stats - Avg. Speed: %d docs/sec", avgspeed)
                self.log.info("[BACKEND/COMPILATION] - End at %s", now())
            else:
                self.log.info("[COMPILATION] - Nothing to do.")

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
            # ~ self.log.trace("[COMPILATION] - Job[%s] for Doc[%s] has RC[%s]", num, basename, rc)
            try:
                html = self.srvthm.build_page(path_hdoc)
            except MemoryError:
                self.log.error("Memory exhausted!")
                self.log.error("Please, consider using less workers or add more memory to your system")
                self.log.error("The application will exit now...")
                sys.exit(errno.ENOMEM)
            return x

    @timeit
    @profile(stream=fp)
    def stage_07_clean_target(self):
        """Clean up stage."""
        self.log.trace("[BACKEND/CLEANUP] - Start at %s", now())
        pattern = os.path.join(self.get_source_path(), '*.*')
        extra = glob.glob(pattern)
        copy_docs(extra, self.get_cache_path())
        delete_target_contents(self.runtime['dir']['dist'])
        self.log.trace("[BACKEND/CLEANUP] - Distributed files deleted")
        distributed = self.get_targets()
        for adoc in distributed:
            source = os.path.join(self.runtime['dir']['tmp'], adoc)
            target = self.runtime['dir']['www']
            try:
                shutil.copy(source, target)
            except Exception as warning:
                # FIXME
                # ~ self.log.warning(warning)
                # ~ self.log.warning("[CLEANUP] - Missing source file: %s", source)
                pass
        self.log.trace("[BACKEND/CLEANUP] - Copy temporary files to distributed directory")

        delete_target_contents(self.get_target_path())
        self.log.trace("[BACKEND/CLEANUP] - Deleted target contents in: %s", self.get_target_path())
        self.log.trace("[BACKEND/CLEANUP] - End at %s", now())

    @timeit
    @profile(stream=fp)
    def stage_08_refresh_target(self):
        """Refresh target."""
        self.log.trace("[BACKEND/INSTALL] - Start at %s", now())

        # Copy asciidocs documents to target path
        pattern = os.path.join(self.get_source_path(), '*.adoc')
        files = glob.glob(pattern)
        docsdir = os.path.join(self.get_target_path(), 'sources')
        os.makedirs(docsdir)
        copy_docs(files, docsdir)
        self.log.trace("[BACKEND/INSTALL] - Copy %d asciidoctor sources to target path", len(files))

        # Copy compiled documents to cache path
        pattern = os.path.join(self.runtime['dir']['tmp'], '*.html')
        files = glob.glob(pattern)
        copy_docs(files, self.runtime['dir']['cache'])
        self.log.trace("[BACKEND/INSTALL] - Copy %d html files from temporary path to cache path", len(files))

        # Copy objects in temporary target to cache path
        pattern = os.path.join(self.runtime['dir']['www'], '*.*')
        files = glob.glob(pattern)
        copy_docs(files, self.runtime['dir']['cache'])
        self.log.trace("[BACKEND/INSTALL] - Copy %d html files from temporary target to cache path", len(files))

        # Copy cached documents to target path
        n = 0
        for filename in sorted(self.runtime['docs']['target']):
            source = os.path.join(self.runtime['dir']['cache'], filename)
            target = os.path.join(self.get_target_path(), filename)
            try:
                shutil.copy(source, target)
                self.log.trace("%s -> %s", source, target)
            except FileNotFoundError as error:
                self.log.error(error)
                self.log.error("[BACKEND/INSTALL] - Consider to run the command again with the option -force")
            n += 1
        self.log.trace(f"[BACKEND/INSTALL] - Copied {n} cached documents successfully to target path")

        # Copy global resources to target path
        resources_dir_target = os.path.join(self.get_target_path(), 'resources')
        theme_target_dir = os.path.join(resources_dir_target, 'themes')
        theme = self.get_theme_properties()
        DEFAULT_THEME = os.path.join(ENV['GPATH']['THEMES'], 'default')
        CUSTOM_THEME_ID = theme['id']
        CUSTOM_THEME_PATH = theme['path']
        copydir(DEFAULT_THEME, os.path.join(theme_target_dir, 'default'))
        copydir(CUSTOM_THEME_PATH, os.path.join(theme_target_dir, CUSTOM_THEME_ID))
        copydir(ENV['GPATH']['COMMON'], os.path.join(resources_dir_target, 'common'))
        self.log.trace("[BACKEND/INSTALL] - Copied global resources to target path")

        # Copy local resources to target path
        source_resources_dir = os.path.join(self.get_source_path(), 'resources')
        if os.path.exists(source_resources_dir):
            resources_dir_target = os.path.join(self.get_target_path(), 'resources')
            copydir(source_resources_dir, resources_dir_target)
            self.log.trace("[BACKEND/INSTALL] - Copied local resources to target path")

        # Copy back all HTML files from target to cache
        delete_target_contents(self.runtime['dir']['cache'])
        pattern = os.path.join(self.get_target_path(), '*.html')
        html_files = glob.glob(pattern)
        copy_docs(html_files, self.runtime['dir']['cache'])
        self.log.trace("[BACKEND/INSTALL] - Copying HTML files back to cache...")

        # Copy JSON database to target path so it can be queried from
        # others applications
        self.save_kbdict(self.kbdict_new, self.get_target_path(), 'kb4it')
        self.log.trace("[BACKEND/INSTALL] - Copied JSON database to target")
        self.log.trace("[BACKEND/INSTALL] - End at %s", now())

    @timeit
    @profile(stream=fp)
    def stage_09_remove_temporary_dir(self):
        """Remove temporary dir."""
        self.log.trace("[BACKEND/POST-INSTALL] - Start at %s", now())
        #shutil.rmtree(self.runtime['dir']['tmp'])
        self.log.trace("[BACKEND/POST-INSTALL] - Temporary directory deleted successfully")
        self.log.trace("[BACKEND/POST-INSTALL] - End at %s", now())

    def cleanup(self):
        """Clean KB4IT temporary environment.
        """
        try:
            delete_target_contents(self.runtime['dir']['tmp'])
            delete_target_contents(self.runtime['dir']['www'])
            delete_target_contents(self.runtime['dir']['dist'])
        except Exception as KeyError:
            pass
        self.log.trace("[BACKEND/CLEANUP] - KB4IT Workspace clean")

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
        KB4IT_DB_FILE = os.path.join(ENV['LPATH']['DB'], kdbdict)

        delete_target_contents(self.runtime['dir']['cache'])
        self.log.trace("[BACKEND/RESET] - DIR[%s] deleted", self.runtime['dir']['cache'])

        delete_target_contents(self.runtime['dir']['tmp'])
        self.log.trace("[BACKEND/RESET] - DIR[%s] deleted", self.runtime['dir']['tmp'])

        delete_target_contents(self.get_source_path())
        self.log.trace("[BACKEND/RESET] - DIR[%s] deleted", self.get_source_path())

        delete_target_contents(self.get_target_path())
        self.log.trace("[BACKEND/RESET] - DIR[%s] deleted", self.get_target_path())

        delete_target_contents(KB4IT_DB_FILE)
        self.log.trace("[BACKEND/RESET] - FILE[%s] deleted", KB4IT_DB_FILE)

        self.log.trace("[BACKEND/RESET] - KB4IT environment reset")

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
        #self.log.trace("[BACKEND/APP] - Browse your documentation repository:")
        #homepage = os.path.join(abspath(self.get_target_path()), 'index.html')
        #self.log.trace("[BACKEND/APP] - KB4IT homepage: %s", homepage)
        self.log.trace("[BACKEND/APP] - KB4IT - Execution finished at %s", now())
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
            self.log.trace("DOC[%s] deleted from source directory", adoc)
        except FileNotFoundError:
            self.log.trace("DOC[%s] not found in source directory", adoc)

        # Remove database document
        self.srvdtb.del_document(adoc)
        self.log.trace("DOC[%s] deleted from database", adoc)

        # Remove cache document
        cache_dir = self.get_cache_path()
        cached_path = os.path.join(cache_dir, "%s.html" % adoc)
        try:
            os.unlink(cached_path)
            self.log.trace("DOC[%s] deleted from cache directory", adoc)
        except FileNotFoundError:
            self.log.trace("DOC[%s] not found in cache directory", adoc)

    def busy(self):
        self.running = True

    def free(self):
        self.running = False

    def end(self):
        self.cleanup()

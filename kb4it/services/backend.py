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
import pprint
import random
import shutil
import tempfile
import datetime
import traceback
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor as Executor

from kb4it.core.env import ENV
from kb4it.core.service import Service
from kb4it.core.util import now
from kb4it.core.util import valid_filename
from kb4it.core.util import exec_cmd, delete_target_contents
from kb4it.core.util import get_source_docs, get_asciidoctor_attributes
from kb4it.core.util import get_hash_from_file, get_hash_from_dict, get_hash_from_list
from kb4it.core.util import copy_docs, copydir
from kb4it.core.util import string_timestamp
from kb4it.core.util import json_load, json_save
from kb4it.core.perf import timeit


class Backend(Service):
    """Backend class for managing the main logic workflow.
    """

    def initialize(self):
        """Initialize application structure."""

        self.running = False     # Backend running?
        self.runtime = {}        # Dictionary of runtime properties
        self.kbdict_new = {}     # New compilation cache
        self.kbdict_cur = {}     # Cached data
        self.force_keys = set()  # List of keys which must be compiled (forced)

        self.log.debug(f"[BACKEND] - Started at {now()}")

        # Get params from command line
        self.params = self.app.get_params()

        # Get repository config file (if any)
        try:
            repo_config_file = self.params.config
            self.repo = json_load(repo_config_file)
            self.log.debug(f"[BACKEND/SETUP] - Repository config file: '{repo_config_file}")
            self.log.debug(f"[BACKEND/SETUP] - Repository parameters:")
            for param in self.repo:
                self.log.debug(f"[BACKEND/SETUP] - \tParameter[{param}]: {self.repo[param]}")
            repo_config_exists = True
        except FileNotFoundError as error:
            self.log.error(f"[BACKEND/SETUP] - Repository config file not found")
            self.log.error(f"[BACKEND/SETUP] - {error}")
            sys.exit(-1)
        except AttributeError as error:
            self.log.error(f"[BACKEND/SETUP] - Repository config couldn't be read")
            self.log.error(f"[BACKEND/SETUP] - Repository config file: {self.params.config}")
            repo_config_exists = False
        except Exception as error:
            self.log.error(f"[BACKEND/SETUP] - Repository config file not found in command line params")
            raise
            repo_config_exists = False

        # Initialize runtime dictionary
        self.runtime['dir'] = {}
        if repo_config_exists:
            self.runtime['dir']['source'] = os.path.realpath(self.repo['source'])
            self.runtime['dir']['target'] = os.path.realpath(self.repo['target'])

            ENV['LPATH']['VAR'] = os.path.join(ENV['LPATH']['ROOT'], 'var')
            ENV['LPATH']['WORK'] = os.path.join(ENV['LPATH']['VAR'], 'work')
            ENV['LPATH']['DB'] = os.path.join(ENV['LPATH']['VAR'], 'db')
            ENV['LPATH']['PLUGINS'] = os.path.join(ENV['LPATH']['VAR'], 'plugins')
            ENV['LPATH']['LOG'] = os.path.join(ENV['LPATH']['VAR'], 'log')
            ENV['LPATH']['TMP'] = os.path.join(ENV['LPATH']['VAR'], 'log')

            PROJECT = valid_filename(self.runtime['dir']['source'])
            WORKDIR = os.path.join(ENV['LPATH']['WORK'], PROJECT)
            dir_src = Path(self.runtime['dir']['source'])
            dir_root = dir_src.parent.absolute()
            dir_var = Path.joinpath(dir_root, 'var')
            dir_work = Path.joinpath(dir_var, 'work')
            dir_project = Path.joinpath(dir_work, PROJECT)
            dir_tmp = Path.joinpath(dir_project, 'tmp')
            dir_cache = Path.joinpath(dir_project, 'cache')
            dir_www = Path.joinpath(dir_project, 'www')
            dir_dist = Path.joinpath(dir_project, 'dist')


            self.runtime['dir']['work'] = dir_project
            self.runtime['dir']['tmp'] = dir_tmp
            self.runtime['dir']['www'] = dir_www
            self.runtime['dir']['dist'] = dir_dist
            self.runtime['dir']['cache'] = dir_cache

            self.log.debug(f"[BACKEND/SETUP] - Checking directories:")
            for entry in self.runtime['dir']:
                create_directory = False
                dirname = self.runtime['dir'][entry]
                if entry not in ['source', 'target']:
                    dirname = self.runtime['dir'][entry]
                    if not os.path.exists(dirname):
                        os.makedirs(dirname, exist_ok=True)
                        create_directory = True
                self.log.debug(f"[BACKEND/SETUP] - \tCreate directory {dirname}? {create_directory}")

            # if SORT attribute is given, use it instead of the OS timestamp
            try:
                self.runtime['sort_attribute'] = self.repo['sort']
                self.runtime['sort_enabled'] = True
            except:
                self.runtime['sort_enabled'] = False
                self.log.error("[BACKEND/SETUP] - No property defined for sorting")
                self.log.error("[BACKEND/SETUP] - Property 'sort' not found in repo config dict")
                sys.exit(-1)

            self.log.debug(f"[BACKEND/SETUP] - Sort enabled: {self.runtime['sort_enabled']}")
            self.log.debug(f"[BACKEND/SETUP] - Sort attribute: {self.runtime['sort_attribute']}")

            # Initialize docs structure
            self.runtime['docs'] = {}
            self.runtime['docs']['count'] = 0
            self.runtime['docs']['bag'] = []
            self.runtime['docs']['target'] = set()

            # Load cache dictionary from last run
            self.kbdict_cur = self.load_kbdict(self.runtime['dir']['source'])
            self.log.debug(f"[BACKEND/SETUP] - Loaded kbdict from last run with {len(self.kbdict_cur['document'])} documents")

            # And initialize the new one
            self.kbdict_new['document'] = {}
            self.kbdict_new['metadata'] = {}
            self.log.debug(f"[BACKEND/SETUP] - Created new kbdict for current execution")

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
        KB4IT_DB_FILE = os.path.join(ENV['LPATH']['DB'], f"kbdict-{source_path}.json")
        try:
            kbdict = json_load(KB4IT_DB_FILE)
            self.log.debug(f"[BACKEND/CONF] - Loading KBDICT from {KB4IT_DB_FILE}")
        except FileNotFoundError:
            kbdict = {}
            kbdict['document'] = {}
            kbdict['metadata'] = {}
        except Exception as error:
            self.log.error(f"[BACKEND/CONF] - There was an error reading file {KB4IT_DB_FILE}")
            sys.exit()
        self.log.debug(f"[BACKEND/CONF] - Current kbdict entries: {len(kbdict)}")
        return kbdict

    def save_kbdict(self, kbdict, path, name=None):
        """C0111: Missing function docstring (missing-docstring)."""
        if name is None:
            target_path = valid_filename(path)
            KB4IT_DB_FILE = os.path.join(ENV['LPATH']['DB'], f"kbdict-{target_path}.json")
        else:
            KB4IT_DB_FILE = os.path.join(path, f"{name}.json")

        json_save(KB4IT_DB_FILE, kbdict)
        self.log.debug(f"[BACKEND/CONF] - KBDICT {KB4IT_DB_FILE} saved")

    def get_targets(self):
        """Get list of documents converted to pages"""
        return self.runtime['docs']['target']

    def add_target(self, kbfile):
        """All objects received by this method will be appended to the
        list of objects that will be copied to the target directory.
        """
        self.runtime['docs']['target'].add(kbfile)
        self.log.debug(f"[BACKEND/TARGET] - Added resource: {kbfile}")

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

    def get_documents(self):
        """Get current number of valid documents."""
        try:
            return self.runtime['docs']['bag']
        except:
            self.log.warning("Runtime dictionary not yet initialiased")
            return []

    @timeit
    def stage_01_check_environment(self):
        """Check environment."""
        frontend = self.get_service('Frontend')
        self.log.debug(f"[BACKEND/STAGE 1 - CHECKS] - Start at {now()}")
        self.log.debug(f"[BACKEND/SETUP] - Cache directory: {self.runtime['dir']['cache']}")
        self.log.debug(f"[BACKEND/SETUP] - Working directory:{self.runtime['dir']['tmp']}")
        self.log.debug(f"[BACKEND/SETUP] - Distribution directory: {self.runtime['dir']['dist']}")
        self.log.debug(f"[BACKEND/SETUP] - Temporary target directory: {self.runtime['dir']['www']}")

        # Check if source directory exists. If not, stop application
        if not os.path.exists(self.get_source_path()):
            self.log.error(f"[BACKEND/SETUP] - Source directory '{self.get_source_path()}' doesn't exist.")
            self.log.debug(f"[BACKEND/SETUP] - End at {now()}")
            self.app.stop()
        self.log.debug(f"[BACKEND/SETUP] - Source directory: {self.get_source_path()}")

        # check if target directory exists. If not, create it:
        if not os.path.exists(self.get_target_path()):
            os.makedirs(self.get_target_path(), exist_ok=True)
        self.log.debug(f"[BACKEND/SETUP] - Target directory: {self.get_target_path()}")

        if  self.get_source_path() == ENV['LPATH']['TMP_SOURCE'] and self.get_target_path() == ENV['LPATH']['TMP_TARGET']:
            self.log.error("[BACKEND/SETUP] - No config file especified")
            self.log.error(f"[BACKEND/SETUP] - End at {now()}")
            sys.exit()

        # if no theme defined by params, try to autodetect it.
        # ~ self.log.debug(f"[SETUP] - Paramters: {self.repo}")
        try:
            theme_name = self.repo['theme']
        except KeyError:
            theme_name = 'techdoc'

        if theme_name is None:
            self.log.debug(f"[BACKEND/SETUP] - Theme not provided. Autodetect it.")
            theme_path = frontend.theme_search()
            if theme_path is not None:
                frontend.theme_load(os.path.basename(theme_path))
                self.log.debug(f"[BACKEND/SETUP] Theme found and loaded")
            else:
                self.log.error("[BACKEND/SETUP] - Theme not found")
                self.log.debug(f"[BACKEND/SETUP] - End at {now()}")
                self.app.stop()
        else:
            theme_path = frontend.theme_search(theme_name)
            if theme_path is not None:
                frontend.theme_load(os.path.basename(theme_path))
            else:
                self.log.error("[BACKEND/SETUP] - Theme not found")
                self.log.debug(f"[BACKEND/SETUP] - End at {now()}")
                self.app.stop()

        self.log.info(f"[BACKEND/SETUP] - Using theme {theme_name}")
        self.log.debug(f"[BACKEND/SETUP] - End at {now()}")

    @timeit
    def stage_02_get_source_documents(self):
        """Get Asciidoctor documents from source directory."""
        self.log.debug(f"[BACKEND/STAGE 2 - SOURCES] - Start at {now()}")
        sources_path = self.get_source_path()

        # Firstly, allow theme to generate documents
        self.srvthm = self.get_service('Theme')

        # If 'about_app.adoc' doesn't exist, create one from template
        # FIXME: if no file exists, tell theme
        about_app_source = os.path.join(sources_path, 'about_app.adoc')
        if not os.path.exists(about_app_source):
            about_app_default = os.path.join(ENV['GPATH']['TEMPLATES'], 'PAGE_ABOUT_APP.tpl')
            shutil.copy(about_app_default, about_app_source)
            self.log.warning("[BACKEND/SOURCEDOCS] - Added default 'About App' to your sources")

        # Then, get them
        self.runtime['docs']['bag'] = get_source_docs(sources_path)
        basenames = []
        for filepath in self.runtime['docs']['bag']:
            basenames.append(os.path.basename(filepath))
        self.runtime['docs']['filenames'] = basenames
        self.runtime['docs']['count'] = len(self.runtime['docs']['bag'])
        self.log.info(f"[BACKEND/SOURCEDOCS] - Found {self.runtime['docs']['count']} asciidoctor documents")
        self.log.story(f"[BACKEND/SOURCEDOCS] - We found {self.runtime['docs']['count']} documents in the repository")
        self.log.debug(f"[BACKEND/SOURCEDOCS] - End at {now()}")

    @timeit
    def stage_03_00_preprocess_document(self, filepath: str):
        self.log.debug(f"[BACKEND/PREPROCESSING] - DOC[{filepath}] Preprocessing")

        # Get Id
        adocId = os.path.basename(filepath)

        # Get metadata
        keys = self.stage_03_00_preprocess_document_metadata(adocId, tolerant=True)
        if keys is None:
            self.log.error(f"[BACKEND/PREPROCESSING] - Document '{adocId}' not compliant: please, check errors")
            return

        # Get content
        with open(filepath) as source_adoc:
            content = source_adoc.read()

        # Add to cache
        # Old cache
        self.kbdict_new['document'][adocId] = {}
        self.kbdict_new['document'][adocId]['content'] = content
        self.kbdict_new['document'][adocId]['keys'] = keys

        # Add to the in-memory database
        self.srvdtb.add_document(adocId)

        self.stage_03_00_preprocess_document_hashes(adocId, content, keys)
        self.stage_03_00_preprocess_document_caches(adocId, keys)
        # ~ self.stage_03_00_preprocess_document_compile(adocId, content, keys)

        # Add compiled page to the target list
        htmlId = adocId.replace('.adoc', '.html')
        self.add_target(htmlId)

    @timeit
    def stage_03_00_preprocess_document_metadata(self, adocId: str, tolerant: bool):
        docpath = os.path.join(self.get_source_path(), adocId)
        keys = get_asciidoctor_attributes(docpath, tolerant)
        self.log.debug(f"[BACKEND/PREPROCESSING] Document '{adocId} keys: {keys}")

        # If document doesn't have a title, skip it.
        try:
            title = keys['Title'][0]
            self.log.debug(f"[BACKEND/PREPROCESSING] - Document '{adocId}: {title}' will be processed")
        except (KeyError, TypeError):
            self.runtime['docs']['count'] -= 1
            self.log.warning(f"[BACKEND/PREPROCESSING] - DOC[{adocId}] doesn't have a title. Skip it.")

        self.log.debug(f"Document {adocId}: {keys}")
        return keys

    def get_sort_attribute(self):
        runtime = self.get_runtime_dict()
        sort_attribute = runtime['sort_attribute']
        return sort_attribute

    @timeit
    def stage_03_00_preprocess_document_hashes(self, adocId: str, content: str, keys: list):
        # To track changes in a document, hashes for metadata and content are created.
        # Comparing them with those in the cache, KB4IT determines if a document must be
        # compiled again. Very useful to reduce the compilation time.

        # Get Document Content and Metadata Hashes
        content_hash = get_hash_from_dict({'content': content})
        metadata_hash = get_hash_from_dict(keys)
        self.kbdict_new['document'][adocId]['content_hash'] = content_hash
        self.kbdict_new['document'][adocId]['metadata_hash'] = metadata_hash


    @timeit
    def stage_03_00_preprocess_document_caches(self, adocId: str, keys: list):
        # Generate caches
        for key in keys:
            alist = keys[key]
            for value in alist:
                if len(value.strip()) == 0:
                    continue
                self.log.debug(f"Doc['{adocId}'] Key['{key}'] Value['{value}']")
                if key == self.runtime['sort_attribute']:
                    value = string_timestamp(value)

                if key == 'Tag':
                    value = value.lower()

                self.srvdtb.add_document_key(adocId, key, value)

                # For each document and for each key/value linked to that document add an entry to kbdic['document']
                try:
                    values = self.kbdict_new['document'][adocId][key]
                    if value not in values:
                        values.append(value)
                    self.kbdict_new['document'][adocId][key] = sorted(values)
                except KeyError:
                    self.kbdict_new['document'][adocId][key] = [value]

                # And viceversa, for each key/value add to kbdict['metadata'] all documents linked
                try:
                    documents = self.kbdict_new['metadata'][key][value]
                    documents.append(adocId)
                    self.kbdict_new[key][value] = sorted(documents, key=lambda y: y.lower())
                except KeyError:
                    if key not in self.kbdict_new['metadata']:
                        self.kbdict_new['metadata'][key] = {}
                    if value not in self.kbdict_new['metadata'][key]:
                        self.kbdict_new['metadata'][key][value] = [adocId]

    @timeit
    def stage_03_00_preprocess_document_compile(self, adocId: str, content:str, keys:list):
        # Force compilation (from command line)?
        DOC_COMPILATION = False
        FORCE_ALL = self.params.force
        if not FORCE_ALL:
            # Get cached document path and check if it exists
            htmlId = adocId.replace('.adoc', '.html')
            cached_document = os.path.join(self.runtime['dir']['cache'], htmlId)
            cached_document_exists = os.path.exists(cached_document)

            # Compare the document with the one in the cache
            if not cached_document_exists:
                DOC_COMPILATION = True
                REASON = "Not cached"
            else:
                try:
                    hash_new = self.kbdict_new['document'][adocId]['content_hash'] + self.kbdict_new['document'][adocId]['metadata_hash']
                    hash_cur = self.kbdict_cur['document'][adocId]['content_hash'] + self.kbdict_cur['document'][adocId]['metadata_hash']
                    self.log.debug(f"[BACKEND-CACHE] - Old hash for {adocId}: '{hash_cur}'")
                    self.log.debug(f"[BACKEND-CACHE] - New hash for {adocId}: '{hash_new}'")
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
        except KeyError as keyerror:
            #FIXME: check
            self.log.error(keyerror)
            raise

        if COMPILE:
            # Write new adoc to temporary dir
            target = f"{self.runtime['dir']['tmp']}/{valid_filename(adocId)}"
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
        self.log.debug(f"[BACKEND/PREPROCESSING] - DOC[{adocId}] Compile? {COMPILE}. Reason: {REASON}")

    @timeit
    def stage_03_preprocessing(self):
        """
        Extract metadata from source docs into a dict.
        Create metadata section for each adoc and insert it after the
        EOHMARK.
        In this way, after being compiled into HTML, final adocs are
        browsable throught its metadata.
        """
        self.log.debug(f"[BACKEND/PREPROCESSING] - Start at {now()}")

        # Preprocessing
        for filepath in self.runtime['docs']['bag']:
            self.log.workflow(f"[BACKEND/PREPROCESSING] - {os.path.basename(filepath)}")
            self.stage_03_00_preprocess_document(filepath)

        # Save current status for the next run
        self.save_kbdict(self.kbdict_new, self.get_source_path())

        # Force compilation for all documents?
        # ~ self.log.debug(f"BACKEND/PREPROCESSING - KB Old keys: {sorted(list(self.kbdict_cur['metadata'].keys()))}")
        # ~ self.log.debug(f"BACKEND/PREPROCESSING - KB New keys: {sorted(list(self.kbdict_new['metadata'].keys()))}")
        keys_hash_cur = get_hash_from_list(sorted(list(self.kbdict_cur['metadata'].keys())))
        keys_hash_new = get_hash_from_list(sorted(list(self.kbdict_new['metadata'].keys())))
        keys_hash_differ = keys_hash_cur != keys_hash_new
        if keys_hash_differ:
            self.log.info("[BACKEND/PREPROCESSING] - Hash for old keys differs from hash for new ones. Force compilation!")
            self.log.debug("[BACKEND/PREPROCESSING] - New keys differ with previous execution.")
            self.log.debug("[BACKEND/PREPROCESSING] - Force compilation for all documents.")
            self.log.debug("[BACKEND/PREPROCESSING] - This is expected to ensure integrity")
            self.params.force = True

        # Compiling strategy
        for filepath in self.runtime['docs']['bag']:
            adocId = os.path.basename(filepath)
            content = self.kbdict_new['document'][adocId]['content']
            keys = self.kbdict_new['document'][adocId]['keys']
            self.stage_03_00_preprocess_document_compile(adocId, content, keys)

        # Build a list of documents sorted by timestamp
        self.srvdtb.sort_database()

        # Documents preprocessing stats
        self.log.debug(f"[BACKEND/PREPROCESSING] - Stats - Documents analyzed: {len(self.runtime['docs']['bag'])}")
        keep_docs = compile_docs = 0
        for adocId in self.kbdict_new['document']:
            if self.kbdict_new['document'][adocId]['compile']:
                compile_docs += 1
            else:
                keep_docs += 1
        self.log.info(f"[BACKEND/PREPROCESSING] - Stats - Keep: {keep_docs} - Compile: {compile_docs}")
        if compile_docs == 0:
            self.log.story(f"[BACKEND/PREPROCESSING] - No changes in the repository")
        else:
            if compile_docs < keep_docs:
                self.log.story(f"[BACKEND/PREPROCESSING] - There are changes in the repository. {compile_docs} documents will be compiled again")
            else:
                self.log.story(f"[BACKEND/PREPROCESSING] - All documents will be compiled again")
        self.log.debug(f"[BACKEND/PREPROCESSING] - End {now()}")

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
            self.log.debug(f"[BACKEND/PROCESSING] - Key[{key}] Compile? {COMPILE_KEY}")

            for value in values:
                COMPILE_VALUE = False
                key_value_docs_new = self.get_kbdict_value(key, value, new=True)
                key_value_docs_cur = self.get_kbdict_value(key, value, new=False)
                VALUE_COMPARISON = key_value_docs_new != key_value_docs_cur

                if VALUE_COMPARISON:
                    self.log.debug(f"[BACKEND/PROCESSING] - Key[{key}] Value[{value}] new != old? {VALUE_COMPARISON}")
                    COMPILE_VALUE = True
                COMPILE_VALUE = COMPILE_VALUE or FORCE_ALL
                COMPILE_KEY = COMPILE_KEY or COMPILE_VALUE
                KV_PATH.append((key, value, COMPILE_VALUE))
                self.log.debug(f"[BACKEND/PROCESSING] - Key[{key}] Value[{value}] Compile? {COMPILE_VALUE}")
            COMPILE_KEY = COMPILE_KEY or FORCE_ALL
            K_PATH.append((key, values, COMPILE_KEY))
            if COMPILE_KEY:
                self.log.debug(f"[BACKEND/PROCESSING] - Key[{key}] Compile? {COMPILE_KEY}")
        return K_PATH, KV_PATH


    @timeit
    def stage_04_processing(self):
        """Process all keys/values got from documents.
        The algorithm detects which keys/values have changed and compile
        them again. This avoid recompile the whole database, saving time
        and CPU.
        """
        self.log.debug(f"[BACKEND/PROCESSING] - Start at {now()}")
        repo = self.get_repo_parameters()
        all_keys = set(self.srvdtb.get_all_keys())
        ign_default_keys = set(self.srvdtb.get_ignored_keys())
        ign_theme_keys = set(repo['ignored_keys'])
        self.ignored_keys = ign_default_keys.union(ign_theme_keys)
        available_keys = list(all_keys - self.ignored_keys)
        self.runtime['K_PATH'], self.runtime['KV_PATH'] = self.stage_04_processing_00_analyze_keys(available_keys)

        # Keys
        keys_with_compile_true = 0
        for kpath in self.runtime['K_PATH']:
            key, values, COMPILE_KEY = kpath
            adocId = f"{valid_filename(key)}.adoc"
            htmlId = adocId.replace('.adoc', '.html')
            if COMPILE_KEY:
                self.srvthm.build_page_key(key, values)
                keys_with_compile_true += 1

            # Add compiled page to the target list
            self.add_target(htmlId)

        # # Keys/Values
        pairs_with_compile_true = 0
        for kvpath in self.runtime['KV_PATH']:
            key, value, COMPILE_VALUE = kvpath
            adocId = f"{valid_filename(key)}_{valid_filename(value)}.adoc"
            htmlId = adocId.replace('.adoc', '.html')
            if COMPILE_VALUE:
                self.srvthm.build_page_key_value(kvpath)
                pairs_with_compile_true += 1

            # Add compiled page to the target list
            self.add_target(htmlId)

        self.log.debug(f"[BACKEND/PROCESSING] - {keys_with_compile_true} keys will be compiled")
        self.log.debug(f"[BACKEND/PROCESSING] - {pairs_with_compile_true} key/value pairs will be compiled")
        self.log.debug(f"[BACKEND/PROCESSING] - Finish processing keys")
        self.log.debug(f"[BACKEND/PROCESSING] - Target docs: {len(self.runtime['docs']['target'])}")
        self.log.debug(f"[BACKEND/PROCESSING] - End at {now()}")

    @timeit
    def stage_05_compilation(self):
        """Compile documents to html with asciidoctor."""
        self.log.info(f"[BACKEND/COMPILATION] - Start at {now()}")
        dcomps = datetime.datetime.now()

        # copy online resources to target path
        # ~ resources_dir_source = GPATH['THEMES']
        resources_dir_tmp = os.path.join(self.runtime['dir']['tmp'], 'resources')
        #if path already exists, remove it before copying with copytree()
        if os.path.exists(resources_dir_tmp):
            shutil.rmtree(resources_dir_tmp)
            shutil.copytree(ENV['GPATH']['RESOURCES'], resources_dir_tmp)
        self.log.debug(f"[BACKEND/COMPILATION] - Resources copied to '%s'", resources_dir_tmp)

        adocprops = ''
        self.log.debug(f"[BACKEND/COMPILATION] - Parameters passed to Asciidoctor:")
        for prop in ENV['CONF']['ADOCPROPS']:
            self.log.debug(f"[BACKEND/COMPILATION] - Key[%s] = Value[%s]", prop, ENV['CONF']['ADOCPROPS'][prop])
            if ENV['CONF']['ADOCPROPS'][prop] is not None:
                if '%s' in ENV['CONF']['ADOCPROPS'][prop]:
                    adocprops += '-a %s=%s ' % (prop, ENV['CONF']['ADOCPROPS'][prop] % self.get_target_path())
                else:
                    adocprops += '-a %s=%s ' % (prop, ENV['CONF']['ADOCPROPS'][prop])
            else:
                adocprops += '-a %s ' % prop
        self.runtime['adocprops'] = adocprops
        self.log.debug(f"[COMPILATION] - Parameters passed to Asciidoctor: %s", adocprops)

        # ~ distributed = self.srvthm.get_distributed()
        distributed = self.get_targets()
        # ~ params = self.app.get_app_conf()
        with Executor(max_workers=self.params.workers) as exe:
            docs = get_source_docs(self.runtime['dir']['tmp'])
            jobs = []
            jobcount = 0
            num = 1
            self.log.debug(f"[BACKEND/COMPILATION] - Generating jobs. Please, wait")
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
                    cmd = "asciidoctor -q -s %s -b html5 -D %s %s" % (adocprops, self.runtime['dir']['tmp'], doc)
                    self.log.debug(f"[COMPILATION] - CMD[%s]", cmd)
                    data = (doc, cmd, num)
                    self.log.debug(f"[BACKEND/COMPILATION] - Job[%4d] Document[%s] will be compiled", num, basename)
                    job = exe.submit(self.compilation_started, data)
                    job.add_done_callback(self.compilation_finished)
                    jobs.append(job)
                    num = num + 1
                else:
                    self.log.debug(f"[BACKEND/COMPILATION] - Document[{basename}] cached. Avoid compiling")

            if num-1 > 0:
                self.log.info("[BACKEND/COMPILATION] - Created %d jobs. Starting compilation at %s", num - 1, now())
                # ~ self.log.debug(f"[COMPILATION] - %3s%% done", "0")
                for job in jobs:
                    adoc, res, jobid = job.result()
                    self.log.debug(f"[BACKEND/COMPILATION] - {os.path.basename(adoc)} compiled successfully")
                    jobcount += 1
                    if jobcount % ENV['CONF']['MAX_WORKERS'] == 0:
                        pct = int(jobcount * 100 / len(docs))
                        # ~ self.log.info("[BACKEND/COMPILATION] - %3s%% done", str(pct))
                        self.log.info("[BACKEND/COMPILATION] - %3s%% done (job %d/%d)", str(pct), jobid, num - 1)

                dcompe = datetime.datetime.now()
                comptime = dcompe - dcomps
                duration = comptime.seconds
                if duration == 0:
                    duration = 1
                avgspeed = int(((num - 1) / duration))
                #self.log.info("[BACKEND/COMPILATION] - 100% done")
                self.log.debug(f"[BACKEND/COMPILATION] - Stats - Time: {comptime.seconds} seconds")
                self.log.debug(f"[BACKEND/COMPILATION] - Stats - Compiled docs: {num - 1}")
                self.log.debug(f"[BACKEND/COMPILATION] - Stats - Avg. Speed: {avgspeed} docs/sec")
                self.log.info(f"[BACKEND/COMPILATION] - End at {now()}")
            else:
                self.log.info("[COMPILATION] - Nothing to do.")

    def compilation_started(self, data):
        (doc, cmd, num) = data
        res = exec_cmd(data)
        return res

    def compilation_finished(self, future):
        time.sleep(random.random())
        cur_thread = threading.current_thread().name
        x = future.result()
        if cur_thread != x:
            path_hdoc, rc, num = x
            basename = os.path.basename(path_hdoc)
            # ~ self.log.debug(f"[COMPILATION] - Job[%s] for Doc[%s] has RC[%s]", num, basename, rc)
            try:
                html = self.srvthm.build_page(path_hdoc)
            except MemoryError:
                self.log.error("Memory exhausted!")
                self.log.error("Please, consider using less workers or add more memory to your system")
                self.log.error("The application will exit now...")
                sys.exit(errno.ENOMEM)
            except Exception as error:
                self.log.error(error)
                self.log.error(traceback.format_exc())
                raise
            return x

    @timeit
    def stage_06_theme(self):
        self.log.debug(f"[BACKEND/PROCESSING] - Start processing theme at {now()}")
        self.srvthm.build()
        self.log.debug(f"[BACKEND/PROCESSING] - End processing theme at {now()}")

    @timeit
    def stage_07_clean_target(self):
        """Clean up stage."""
        self.log.debug(f"[BACKEND/CLEANUP] - Start at {now()}")
        pattern = os.path.join(self.get_source_path(), '*.*')
        extra = glob.glob(pattern)
        copy_docs(extra, self.get_cache_path())
        delete_target_contents(self.runtime['dir']['dist'])
        self.log.debug(f"[BACKEND/CLEANUP] - Distributed files deleted")
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
        self.log.debug(f"[BACKEND/CLEANUP] - Copy temporary files to distributed directory")

        delete_target_contents(self.get_target_path())
        self.log.debug(f"[BACKEND/CLEANUP] - Deleted target contents in: %s", self.get_target_path())
        self.log.debug(f"[BACKEND/CLEANUP] - End at {now()}")

    @timeit
    def stage_08_refresh_target(self):
        """Refresh target."""
        self.log.info(f"[BACKEND/INSTALL] - Start at {now()}")
        self.log.debug(f"[BACKEND/INSTALL] - Temporary path: {self.runtime['dir']['tmp']}")
        self.log.debug(f"[BACKEND/INSTALL] - Cache path: {self.runtime['dir']['cache']}")
        self.log.debug(f"[BACKEND/INSTALL] - Target path: {self.runtime['dir']['target']}")
        # Copy asciidocs documents to target path
        pattern = os.path.join(self.get_source_path(), '*.adoc')
        files = glob.glob(pattern)
        docsdir = os.path.join(self.get_target_path(), 'sources')
        os.makedirs(docsdir, exist_ok=True)
        copy_docs(files, docsdir)
        self.log.info(f"[BACKEND/INSTALL] - Copy {len(files)} asciidoctor sources to target path")

        # Copy compiled documents to cache path
        pattern = os.path.join(self.runtime['dir']['tmp'], '*.html')
        files = glob.glob(pattern)
        copy_docs(files, self.runtime['dir']['cache'])
        # ~ for file in files:
            # ~ self.log.debug(f"[BACKEND/INSTALL] - \tCopied '{os.path.basename(file)}' from temporary path to cache path")
        self.log.info(f"[BACKEND/INSTALL] - Copied {len(files)} html files from temporary path to cache path")

        # Copy objects in temporary target to cache path
        pattern = os.path.join(self.runtime['dir']['tmp'], '*.*')
        files = glob.glob(pattern)
        copy_docs(files, self.runtime['dir']['cache'])
        for file in files:
            self.log.debug(f"[BACKEND/INSTALL] - \tCopied '{os.path.basename(file)}' from temporary target to cache path")
        self.log.info(f"[BACKEND/INSTALL] - Copy {len(files)} html files from temporary target to cache path")

        # Copy cached documents to target path
        n = 0
        for filename in sorted(self.runtime['docs']['target']):
            source = os.path.join(self.runtime['dir']['cache'], filename)
            target = os.path.join(self.get_target_path(), filename)
            try:
                shutil.copy(source, target)
                # ~ self.log.debug(f"%s -> %s", os.path.basename(source), os.path.basename(target))
            except FileNotFoundError as error:
                self.log.error(error)
                self.log.error("[BACKEND/INSTALL] - Consider to run the command again with the option -force")
            n += 1
        self.log.info(f"[BACKEND/INSTALL] - Copied {n} cached documents successfully to target path")

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
        self.log.info("[BACKEND/INSTALL] - Copied global resources to target path")

        # Copy local resources to target path
        source_resources_dir = os.path.join(self.get_source_path(), 'resources')
        if os.path.exists(source_resources_dir):
            resources_dir_target = os.path.join(self.get_target_path(), 'resources')
            copydir(source_resources_dir, resources_dir_target)
            self.log.debug(f"[BACKEND/INSTALL] - Copied local resources to target path")
        self.log.info("[BACKEND/INSTALL] - Copied local resources to target path")

        # Copy back all HTML files from target to cache
        delete_target_contents(self.runtime['dir']['cache'])
        pattern = os.path.join(self.get_target_path(), '*.html')
        html_files = glob.glob(pattern)
        copy_docs(html_files, self.runtime['dir']['cache'])
        self.log.info("[BACKEND/INSTALL] - Copying HTML files back to cache...")

        # Copy JSON database to target path so it can be queried from
        # others applications
        self.save_kbdict(self.kbdict_new, self.get_target_path(), 'kb4it')
        self.log.info("[BACKEND/INSTALL] - Copied JSON database to target")
        self.log.info(f"[BACKEND/INSTALL] - End at {now()}")

    def cleanup(self):
        """Clean KB4IT temporary environment.
        """
        try:
            delete_target_contents(self.runtime['dir']['tmp'])
            delete_target_contents(self.runtime['dir']['www'])
            delete_target_contents(self.runtime['dir']['dist'])
            pass
        except Exception as KeyError:
            pass
        self.log.debug(f"[BACKEND/CLEANUP] - KB4IT Workspace clean")

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
        self.log.debug(f"[BACKEND/RESET] - DIR[%s] deleted", self.runtime['dir']['cache'])

        delete_target_contents(self.runtime['dir']['tmp'])
        self.log.debug(f"[BACKEND/RESET] - DIR[%s] deleted", self.runtime['dir']['tmp'])

        delete_target_contents(self.get_source_path())
        self.log.debug(f"[BACKEND/RESET] - DIR[%s] deleted", self.get_source_path())

        delete_target_contents(self.get_target_path())
        self.log.debug(f"[BACKEND/RESET] - DIR[%s] deleted", self.get_target_path())

        delete_target_contents(KB4IT_DB_FILE)
        self.log.debug(f"[BACKEND/RESET] - FILE[%s] deleted", KB4IT_DB_FILE)

        self.log.debug(f"[BACKEND/RESET] - KB4IT environment reset")

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
            self.log.debug(f"DOC[%s] deleted from source directory", adoc)
        except FileNotFoundError:
            self.log.debug(f"DOC[%s] not found in source directory", adoc)

        # Remove database document
        self.srvdtb.del_document(adoc)
        self.log.debug(f"DOC[%s] deleted from database", adoc)

        # Remove cache document
        cache_dir = self.get_cache_path()
        cached_path = os.path.join(cache_dir, "%s.html" % adoc)
        try:
            os.unlink(cached_path)
            self.log.debug(f"DOC[%s] deleted from cache directory", adoc)
        except FileNotFoundError:
            self.log.debug(f"DOC[%s] not found in cache directory", adoc)

    def busy(self):
        self.running = True

    def free(self):
        # Cache Manager Stats
        # ~ self.cache.print_cache_report()
        # ~ pprint.pprint(self.cache.get_new())

        self.running = False

    def end(self):
        self.cleanup()
        pass

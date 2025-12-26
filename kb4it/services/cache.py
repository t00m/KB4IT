#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cache Manager.
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: helping module for caching KB4IT objects
"""

import os
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from kb4it.core.log import get_logger

from kb4it.core.env import ENV
from kb4it.core.util import json_load
from kb4it.core.util import valid_filename
from kb4it.core.util import string_timestamp
from kb4it.core.util import get_hash_from_file
from kb4it.core.util import get_hash_from_dict
from kb4it.core.service import Service


@dataclass
class KB4ITObject:
    """Represents a cached document with its metadata"""
    id: str
    content: str
    keys: list
    must_compile: bool
    content_hash: str = field(init=False)   # Computed, not passed to __init__
    metadata_hash: str = field(init=False)  # Computed, not passed to __init__
    combined_hash: str = field(init=False)  # Computed, not passed to __init__
    compliant: bool = field(init=False)     # Computed, not passed to __init__

    def __post_init__(self):
        print(f"KB4ITObject: {self.keys}")
        self.content_hash = get_hash_from_dict({'content': self.content})
        self.metadata_hash = get_hash_from_dict(self.keys)
        self.combined_hash = self.content_hash + self.metadata_hash
        self.compliant = self.keys is not None and len(self.keys) > 0
        self.content = '' # Reset. Content not needed anymore?

class CacheManager(Service):
    """KB4IT Cache Manager"""

    def initialize(self):
        """"""
        self.new = {}
        self.old = {}

    def configure(self, cache_dir, db_dir, source_dir):
        self.cache_dir = cache_dir
        self.db_dir = db_dir
        self.source_dir = source_dir
        self.log.debug(f"[CACHE] - Cache dir: '{self.cache_dir}'")
        self.log.debug(f"[CACHE] - DB dir: '{self.db_dir}'")
        self.log.debug(f"[CACHE] - Source dir: '{self.source_dir}'")
        self.old = self._load(self.source_dir)

    def _load(self, path):
        """C0111: Missing function docstring (missing-docstring)."""
        project_name = valid_filename(path)
        cache_file = os.path.join(self.db_dir, f"kbdict-{project_name}.json")
        try:
            kbdict = json_load(cache_file)
            self.log.debug(f"[CACHE] - Cache loaded from file '{cache_file}'")
        except FileNotFoundError:
            kbdict = {}
            kbdict['document'] = {}
            kbdict['metadata'] = {}
            self.log.debug(f"[CACHE] - Cache file not found. Created a new one")
        except Exception as error:
            self.log.error(f"[CACHE] - There was an error reading the cache file '{cache_file}'")
            sys.exit()
        self.log.debug(f"[CACHE] - Entries loaded: {len(kbdict)}")
        return kbdict

    def add(self, id:str, content:str, keys:list, sort_attribute: str, force_compilation: bool):
        self.new['document'] = {}
        self.new['metadata'] = {}
        self.new['objects'] = {}
        self.new['document'][id] = {}

        # Update caches
        for key in keys:
            alist = keys[key]
            for value in alist:
                if len(value.strip()) == 0:
                    continue
                self.log.debug(f"[CACHE] - Doc['{id}'] Key['{key}'] Value['{value}']")
                if key == sort_attribute:
                    value = string_timestamp(value)

                # For each document and for each key/value linked to that document add an entry to kbdic['document']
                try:
                    values = self.new['document'][id][key]
                    if value not in values:
                        values.append(value)
                    self.new['document'][id][key] = sorted(values)
                except KeyError:
                    self.new['document'][id][key] = [value]

                # And viceversa, for each key/value add to kbdict['metadata'] all documents linked
                try:
                    documents = self.new['metadata'][key][value]
                    documents.append(id)
                    self.new[key][value] = sorted(documents, key=lambda y: y.lower())
                except KeyError:
                    if key not in self.new['metadata']:
                        self.new['metadata'][key] = {}
                    if value not in self.new['metadata'][key]:
                        self.new['metadata'][key][value] = [id]

        # Must be compiled?
        DOC_COMPILATION = False
        FORCE_ALL = force_compilation
        if not FORCE_ALL:
            # Get cached document path and check if it exists
            htmlId = id.replace('.adoc', '.html')
            cached_document = os.path.join(self.cache_dir, htmlId)
            cached_document_exists = os.path.exists(cached_document)

            # Compare the document with the one in the cache
            if not cached_document_exists:
                DOC_COMPILATION = True
                REASON = "Not cached"
            else:
                try:
                    hash_new = self.new['document'][id]['content_hash'] + self.new['document'][id]['metadata_hash']
                    hash_old = self.old['document'][id]['content_hash'] + self.old['document'][id]['metadata_hash']
                    self.log.debug(f"[CACHE] - DOC[{id}] Hash old: '{hash_old}'")
                    self.log.debug(f"[CACHE] - DOC[{id}] Hash new: '{hash_new}'")
                    DOC_COMPILATION = hash_new != hash_old
                    REASON = "[CACHE] - {id}: Hashes differ? %s" % DOC_COMPILATION
                except Exception as warning:
                    DOC_COMPILATION = True
                    REASON = warning
        else:
            REASON = "Forced"

        must_compile = DOC_COMPILATION or FORCE_ALL
        self.log.debug(f"[CACHE] - DOC[{id}] Compile? {must_compile}. Reason: {REASON}")

        # Create new KB4ITObject
        self.new['objects'][id] = KB4ITObject(id, content, keys, must_compile)
        self.log.debug(f"[CACHE] - DOC[{id}]: '{self.new['objects'][id].combined_hash}'")

    def get_caches(self) -> tuple(dict, dict):
        return (self.new, self.old)

    def get_new(self) -> dict:
        return self.new

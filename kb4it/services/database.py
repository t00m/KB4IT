#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: In-memory database for KB4IT
"""

from kb4it.core.service import Service
from kb4it.core.util import sort_dictionary
from kb4it.core.util import valid_filename
from kb4it.core.util import guess_datetime
# ~ from kb4it.core.util import timeit
from kb4it.core.util import get_hash_from_list
from kb4it.core.util import get_timestamp_yyyymmdd


class Database(Service):
    """KB4IT database class."""

    db = {}
    keys = {}
    keys_doc = {}
    sort_attribute = None
    sorted_docs = []
    cache_props = {}
    cache_docs_by_kvpath = {}
    cache_keys_by_doc = {}
    cache_docs_sorted_by_date = {}
    cache_all_values_for_key = {}

    def initialize(self):
        """Initialize database module."""
        self.srvbes = self.get_service('Backend')
        runtime = self.srvbes.get_runtime_dict()
        if runtime['sort_enabled']:
            self.sort_attribute = runtime['sort_attribute']
        else:
            self.sort_attribute = ''
        self.sorted_docs = []
        self.keys['all'] = []
        self.keys['blocked'] = ['Title', 'SystemPage']
        self.keys['custom'] = []
        self.keys['theme'] = []
        try:
            self.keys['ignored'] = repo['ignored_keys']
        except:
            # FIXME: raises error when the command line option -r
            # is not passed
            self.keys['ignored'] = []
        self.ignore_key('Title')
        self.db = {}

    def del_document(self, docId):
        """Delete a document node from database."""
        adoc = "%s.adoc" % docId
        try:
            del self.db[adoc]
            self.log.debug("[DATABASE] - DOC[%s] deleted from database", docId)
            self.sort_database()
        except KeyError:
            self.log.debug("[DATABASE] - DOC[%s] not found in database", docId)

    def add_document(self, docId: str):
        """Add a new document node to the database ('name.adoc')"""
        self.db[docId] = {}
        self.log.debug("[DATABASE] - DOC[%s] added to database", docId)

    def add_document_key(self, docId, key, value):
        """Add a new key/value node for a given document."""
        try:
            alist = self.db[docId][key]
            alist.append(value)
            self.db[docId][key] = alist
        except KeyError:
            self.db[docId][key] = [value]

        self.log.debug("[DATABASE] - DOC[%s] KEY[%s] VALUE[%s] added", docId, key, value)

    def get_blocked_keys(self):
        """Return blocked keys."""
        return self.keys['blocked']

    def get_ignored_keys(self):
        """Return ignored keys."""
        return self.keys['ignored']

    def ignore_key(self, key):
        """Add given key to ignored keys list."""
        self.keys['ignored'].append(key)

    # ~ @timeit
    def sort_database(self):
        """
        Build a list of documents.
        Documents sorted by the given date attribute in descending order.
        """
        runtime = self.srvbes.get_runtime_dict()
        if len(self.sorted_docs) == 0:
            if runtime['sort_enabled']:
                self.sorted_docs = self.sort_by_date(list(self.db.keys()))
            else:
                self.sorted_docs = list(self.db.keys())

    # ~ # ~ @timeit
    def sort_by_date(self, doclist):
        """Build a list of documents sorted by timestamp desc."""
        md5hash = get_hash_from_list(sorted(doclist))
        if not md5hash in self.cache_docs_sorted_by_date:
            adict = {}
            for docId in doclist:
                if not self.is_system(docId):
                    sdate = self.get_doc_timestamp(docId)
                    if sdate is None:
                        continue
                    dt = guess_datetime(sdate)
                    adict[docId] = dt #.strftime("%Y%m%d")
            sorted_docs = [docId for docId, _ in sort_dictionary(adict)]
            self.cache_docs_sorted_by_date[md5hash] = sorted_docs
        return self.cache_docs_sorted_by_date[md5hash]

    # ~ @timeit
    def get_documents(self):
        """Return the list of sorted docs."""
        self.sort_database()
        return self.sorted_docs

    def get_documents_count(self):
        return len(self.get_documents())

    # ~ @timeit
    def get_doc_timestamp(self, docId) -> str:
        """Get timestamp for a given document."""
        try:
            return self.db[docId][self.sort_attribute][0]
        except KeyError as error:
            self.log.debug(f"[DATABASE] - Document '{docId}' doesn't have the sort attribute {error}")
            return None

    def is_system(self, docId):
        return 'SystemPage' in self.get_doc_properties(docId).keys()

    # ~ @timeit
    def get_doc_properties(self, docId):
        """Return a dictionary with the properties of a given docId.
        Additionally, the dictionary will contain an extra entry foreach
        property with its Url:
        """
        try:
            return self.cache_props[docId]
        except KeyError:
            props = {}
            try:
                for key in self.db[docId]:
                    if key == 'Title':
                        props[key] = self.db[docId][key][0]
                        key_url = "%s_Url" % key
                        props[key_url] = docId.replace('.adoc', '.html')
                    else:
                        props[key] = self.db[docId][key]
                        for value in self.db[docId][key]:
                            key_value_url = "%s_%s_Url" % (key, value)
                            props[key_value_url] = "%s_%s.html" % (valid_filename(key), valid_filename(value))
            except Exception as warning:
                # FIXME: Document why it is not necessary
                pass
            self.cache_props[docId] = props
            return self.cache_props[docId]

    def get_values(self, docId, key):
        """Return a list of values given a document and a key."""
        try:
            return self.db[docId][key]
        except KeyError:
            return ['']

    # ~ @timeit
    def get_all_values_for_key(self, key):
        """Return a list of all values for a given key sorted alphabetically."""
        try:
            return self.cache_all_values_for_key[key]
        except KeyError:
            values = []
            for docId in self.db:
                try:
                    values.extend(self.db[docId][key])
                except KeyError:
                    pass
            values = list(set(values))
            values.sort(key=lambda y: y.lower())
            self.cache_all_values_for_key[key] = values
            return self.cache_all_values_for_key[key]

    def get_custom_keys(self, docId):
        """Return a list of custom keys sorted alphabetically."""
        try:
            return self.keys_doc[docId]
        except KeyError:
            custom_keys = []
            keys = self.get_doc_keys(docId)
            for key in keys:
                if key not in self.keys['ignored']:
                    custom_keys.append(key)
            custom_keys.sort(key=lambda y: y.lower())
            self.keys_doc[docId] = custom_keys
            return self.keys_doc[docId]

    def get_keys(self):
        """Return dictionary of keys (ignored, theme, and all)"""
        self.get_all_keys()
        self.get_theme_keys()
        return self.keys

    def get_all_keys(self):
        """Return all keys in the database sorted alphabetically."""
        if len(self.keys['all']) > 0:
            return self.keys['all']

        keys = set()
        database = self.get_documents()
        for docId in database:
            for key in self.get_doc_keys(docId):
                if key not in self.keys['blocked']:
                    keys.add(key)
        keys = list(keys)
        keys.sort(key=lambda y: y.lower())
        self.keys['all'] = keys
        return self.keys['all']

    def get_theme_keys(self):
        """Return all keys in the database sorted alphabetically."""
        if len(self.keys['theme']) > 0:
            return self.keys['theme']

        keys = set(self.get_all_keys())
        database = self.get_documents()
        for key in self.keys['ignored']:
            try:
                keys.remove(key)
            except KeyError:
                pass
        for key in self.keys['blocked']:
            try:
                keys.remove(key)
            except KeyError:
                pass
        keys = list(keys)
        keys.sort(key=lambda y: y.lower())
        self.keys['theme'] = keys
        return self.keys['theme']

    # ~ @timeit
    def get_docs_by_key_value(self, key, value):
        """Return a list documents for a given key/value sorted by date."""
        kvpath = f"{key}-{value}"
        cached = kvpath in self.cache_docs_by_kvpath
        if not cached:
            docs = []
            for docId in self.db:
                if key in self.db[docId]:
                    if value in self.db[docId][key]:
                        docs.append(docId)
            self.cache_docs_by_kvpath[kvpath] = self.sort_by_date(docs)
            self.log.debug(f"Found {len(self.cache_docs_by_kvpath[kvpath])} docs for K[{key}] V[{value}]")
        return self.cache_docs_by_kvpath[kvpath]

    def get_docs_by_date_range(self, ds, de) -> []:
        doclist = []
        for docId in self.db:
            ts = self.get_doc_timestamp(docId)
            if ts is None:
                continue
            dt = guess_datetime(ts)
            if dt >= ds and dt <= de:
                doclist.append(docId)
        return doclist

    def get_doc_keys(self, docId):
        """Return a list of keys for a given docId sorted alphabetically."""
        try:
            return self.cache_keys_by_doc[docId]
        except KeyError:
            keys = []
            try:
                for key in self.db[docId]:
                    keys.append(key)
                keys.sort(key=lambda y: y.lower())
            except Exception as error:
                self.log.debug("[DATABASE] - Doc[%s] is not in the database (system page?)", docId)
            self.cache_keys_by_doc[docId] = keys
            return self.cache_keys_by_doc[docId]

    def get_sort_attribute(self):
        return self.sort_attribute

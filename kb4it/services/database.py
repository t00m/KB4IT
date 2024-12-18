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
        backend = self.get_service('Backend')
        runtime = backend.get_runtime_dict()
        try:
            repo = backend.get_repo_dict()
            self.sort_attribute = repo['sort']
        except AttributeError:
            repo = {}
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
        self.db = {}

    def del_document(self, doc):
        """Delete a document node from database."""
        adoc = "%s.adoc" % doc
        try:
            del self.db[adoc]
            self.log.debug("[DATABASE] - DOC[%s] deleted from database", doc)
            self.sort_database()
        except KeyError:
            self.log.debug("[DATABASE] - DOC[%s] not found in database", doc)

    def add_document(self, doc: str):
        """Add a new document node to the database ('name.adoc')"""
        self.db[doc] = {}
        self.log.trace("[DATABASE] - DOC[%s] added to database", doc)

    def add_document_key(self, doc, key, value):
        """Add a new key/value node for a given document."""
        try:
            alist = self.db[doc][key]
            alist.append(value)
            self.db[doc][key] = alist
        except KeyError:
            self.db[doc][key] = [value]

        self.log.trace("[DATABASE] - DOC[%s] KEY[%s] VALUE[%s] added", doc, key, value)

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
        if len(self.sorted_docs) == 0:
            self.sorted_docs = self.sort_by_date(list(self.db.keys()))

    # ~ # ~ @timeit
    def sort_by_date(self, doclist):
        """Build a list of documents sorted by timestamp desc."""
        md5hash = get_hash_from_list(sorted(doclist))
        if not md5hash in self.cache_docs_sorted_by_date:
            adict = {}
            for doc in doclist:
                if not self.is_system(doc):
                    sdate = self.get_doc_timestamp(doc)
                    dt = guess_datetime(sdate)
                    adict[doc] = dt #.strftime("%Y%m%d")
            sorted_docs = [doc for doc, _ in sort_dictionary(adict)]
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
    def get_doc_timestamp(self, doc):
        """Get timestamp for a given document."""
        try:
            return self.db[doc][self.sort_attribute][0]
        except KeyError as error:
            self.log.warning(f"[DATABASE] - Document '{doc}' doesn't have the sort attribute {error}")
            #FIXME: should return a datetime.now() timestamp as a fix?
            return ''


    def is_system(self, doc):
        return 'SystemPage' in self.get_doc_properties(doc).keys()

    # ~ @timeit
    def get_doc_properties(self, doc):
        """Return a dictionary with the properties of a given doc.
        Additionally, the dictionary will contain an extra entry foreach
        property with its Url:
        """
        try:
            return self.cache_props[doc]
        except KeyError:
            props = {}
            try:
                for key in self.db[doc]:
                    if key == 'Title':
                        props[key] = self.db[doc][key][0]
                        key_url = "%s_Url" % key
                        props[key_url] = doc.replace('.adoc', '.html')
                    else:
                        props[key] = self.db[doc][key]
                        for value in self.db[doc][key]:
                            key_value_url = "%s_%s_Url" % (key, value)
                            props[key_value_url] = "%s_%s.html" % (valid_filename(key), valid_filename(value))
            except Exception as warning:
                # FIXME: Document why it is not necessary
                pass
            self.cache_props[doc] = props
            return self.cache_props[doc]

    def get_values(self, doc, key):
        """Return a list of values given a document and a key."""
        try:
            return self.db[doc][key]
        except KeyError:
            return ['']

    # ~ @timeit
    def get_all_values_for_key(self, key):
        """Return a list of all values for a given key sorted alphabetically."""
        try:
            return self.cache_all_values_for_key[key]
        except KeyError:
            values = []
            for doc in self.db:
                try:
                    values.extend(self.db[doc][key])
                except KeyError:
                    pass
            values = list(set(values))
            values.sort(key=lambda y: y.lower())
            self.cache_all_values_for_key[key] = values
            return self.cache_all_values_for_key[key]

    def get_custom_keys(self, doc):
        """Return a list of custom keys sorted alphabetically."""
        try:
            return self.keys_doc[doc]
        except KeyError:
            custom_keys = []
            keys = self.get_doc_keys(doc)
            for key in keys:
                if key not in self.keys['ignored']:
                    custom_keys.append(key)
            custom_keys.sort(key=lambda y: y.lower())
            self.keys_doc[doc] = custom_keys
            return self.keys_doc[doc]

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
        for doc in database:
            for key in self.get_doc_keys(doc):
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
            for doc in self.db:
                if key in self.db[doc]:
                    if value in self.db[doc][key]:
                        docs.append(doc)
            self.cache_docs_by_kvpath[kvpath] = self.sort_by_date(docs)
            self.log.debug(f"Found {len(self.cache_docs_by_kvpath[kvpath])} docs for K[{key}] V[{value}]")
        return self.cache_docs_by_kvpath[kvpath]

    def get_doc_keys(self, doc):
        """Return a list of keys for a given doc sorted alphabetically."""
        try:
            return self.cache_keys_by_doc[doc]
        except KeyError:
            keys = []
            try:
                for key in self.db[doc]:
                    keys.append(key)
                keys.sort(key=lambda y: y.lower())
            except Exception as error:
                self.log.debug("[DATABASE] - Doc[%s] is not in the database (system page?)", doc)
            self.cache_keys_by_doc[doc] = keys
            return self.cache_keys_by_doc[doc]


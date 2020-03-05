#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RDF Graph In Memory database module.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: module to allow kb4it create a RDF graph
"""


from kb4it.src.core.mod_srv import Service
from kb4it.src.core.mod_utils import guess_datetime, sort_dictionary


class KB4ITDB(Service):
    """KB4IT database class."""

    db = {}
    sorted_docs = []
    blocked_keys = ['Title', 'Timestamp']
    ignored_keys = blocked_keys

    def initialize(self):
        """Initialize database module."""

        # Get sort attribute or default timestamp
        params = self.app.get_params()
        self.sort_attribute = params.SORT_ATTRIBUTE

    def add_document(self, doc):
        """Add a new document node to the database."""
        self.db[doc] = {}

    def add_document_key(self, doc, key, value):
        """Add a new key/value node for a given document."""
        try:
            alist = self.db[doc][key]
            alist.append(value)
            self.db[doc][key] = alist
        except KeyError:
            self.db[doc][key] = [value]

        self.log.debug("\t\t\tKey '%s' with value '%s' linked to document: %s", key, value, doc)

    def get_blocked_keys(self):
        return self.blocked_keys

    def get_ignored_keys(self):
        return self.ignored_keys

    def ignore_key(self, key):
        self.ignored_keys.append(key)

    def sort_database(self, attribute='Timestamp'):
        """Build a list of documents sorted by the given date attribute
        in descending order"""
        adict = {}
        for doc in self.db:
            adict[doc] = self.get_doc_timestamp(doc)
        alist = sort_dictionary(adict)
        for doc, timestamp in alist:
            self.sorted_docs.append(doc)

    def sort_by_date(self, doclist, attribute='Timestamp'):
        """Build a list of documents sorted by timestamp desc."""
        sorted_docs = []
        adict = {}
        for doc in doclist:
            adict[doc] = self.get_doc_timestamp(doc)
        alist = sort_dictionary(adict)
        for doc, timestamp in alist:
            sorted_docs.append(doc)
        return sorted_docs

    def get_documents(self):
        return self.sorted_docs

    def get_doc_timestamp(self, doc):
        """Get timestamp for a given document."""
        try:
            timestamp = self.db[doc][self.sort_attribute][0]
        except:
            timestamp = self.db[doc]['Timestamp'][0]
        return timestamp

    def get_doc_properties(self, doc):
        return self.db[doc]

    def get_values(self, doc, key):
        """Get a list of values given a document and a key."""
        try:
            return self.db[doc][key]
        except KeyError:
            return ['']

    def get_all_values_for_key(self, key):
        """Get all values for a given key."""
        values = []
        for doc in self.db:
            try:
                values.extend(self.db[doc][key])
            except KeyError:
                pass
        values = list(set(values))
        values.sort(key=lambda y: y.lower())
        return values

    def get_custom_keys(self, doc):
        """Get a list of custom keys."""
        custom_keys = []
        keys = self.get_doc_keys(doc)
        for key in keys:
            if key not in self.ignored_keys:
                custom_keys.append(key)
        custom_keys.sort(key=lambda y: y.lower())
        return custom_keys

    def get_all_keys(self):
        """Get all keys in the database."""
        blocked_keys = self.get_blocked_keys()
        keys = set()
        for doc in self.db:
            for key in self.get_doc_keys(doc):
                if key not in blocked_keys:
                    keys.add(key)
        keys = list(keys)
        keys.sort(key=lambda y: y.lower())
        return keys

    def get_docs_by_key_value(self, key, value):
        """Get a list of documents given a key and a value for that key."""
        docs = []
        for doc in self.db:
            try:
                if value in self.db[doc][key]:
                    docs.append(doc)
            except KeyError:
                pass
        return docs

    def get_doc_keys(self, doc):
        """Get keys for a given doc."""
        keys = []
        for key in self.db[doc]:
            keys.append(key)
        keys.sort(key=lambda y: y.lower())
        return keys

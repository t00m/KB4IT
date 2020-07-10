#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RDF Graph In Memory database module.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: In-memory database module
"""


from kb4it.core.service import Service
from kb4it.core.util import guess_datetime, sort_dictionary


class KB4ITDB(Service):
    """KB4IT database class."""

    db = {}
    sort_attribute = None
    sorted_docs = []
    blocked_keys = []
    ignored_keys = []

    def initialize(self):
        """Initialize database module."""
        params = self.app.get_params()
        self.sort_attribute = params.SORT_ATTRIBUTE
        self.db = {}
        self.sorted_docs = []
        self.ignored_keys = self.blocked_keys = ['Title', 'Timestamp']

    def del_document(self, doc):
        """Delete a document node from database."""
        adoc = "%s.adoc" % doc
        try:
            del self.db[adoc]
            self.log.debug("[DB] - DOC[%s] deleted from database", doc)
            self.sort_database()
        except KeyError:
            self.log.debug("[DB] - DOC[%s] not found in database", doc)

    def add_document(self, doc):
        """Add a new document node to the database."""
        self.db[doc] = {}
        self.log.debug("[DB] - DOC[%s] added to database", doc)

    def add_document_key(self, doc, key, value):
        """Add a new key/value node for a given document."""
        try:
            alist = self.db[doc][key]
            alist.append(value)
            self.db[doc][key] = alist
        except KeyError:
            self.db[doc][key] = [value]

        self.log.debug("[DB] - DOC[%s] KEY[%s] VALUE[%s] added", doc, key, value)

    def get_blocked_keys(self):
        """Return blocked keys."""
        return self.blocked_keys

    def get_ignored_keys(self):
        """Return ignored keys."""
        return self.ignored_keys

    def ignore_key(self, key):
        """Add given key to ignored keys list."""
        self.ignored_keys.append(key)

    def sort_database(self):
        """
        Build a list of documents.

        Documents sorted by the given date attribute in descending order.
        """
        self.sorted_docs = self.sort_by_date(list(self.db.keys()))

    def sort_by_date(self, doclist):
        """Build a list of documents sorted by timestamp desc."""
        sorted_docs = []
        adict = {}
        for doc in doclist:
            sdate = self.get_doc_timestamp(doc)
            ts = guess_datetime(sdate)
            if ts is not None:
                adict[doc] = ts
            else:
                self.log.error("[DB] - Doc '%s' doesn't have a valid timestamp?", doc)
        alist = sort_dictionary(adict)
        for doc, timestamp in alist:
            sorted_docs.append(doc)
        return sorted_docs

    def get_documents(self):
        """Return the list of sorted docs."""
        return self.sorted_docs

    def get_doc_timestamp(self, doc):
        """Get timestamp for a given document."""
        try:
            timestamp = self.db[doc][self.sort_attribute][0]
        except:
            timestamp = self.db[doc]['Timestamp'][0]
        return timestamp

    def get_doc_properties(self, doc):
        """Return a dictionary with the properties of a given doc."""
        return self.db[doc]

    def get_values(self, doc, key):
        """Return a list of values given a document and a key."""
        try:
            return self.db[doc][key]
        except KeyError:
            return ['']

    def get_all_values_for_key(self, key):
        """Return a list of all values for a given key sorted alphabetically."""
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
        """Return a list of custom keys sorted alphabetically."""
        custom_keys = []
        keys = self.get_doc_keys(doc)
        for key in keys:
            if key not in self.ignored_keys:
                custom_keys.append(key)
        custom_keys.sort(key=lambda y: y.lower())
        return custom_keys

    def get_all_keys(self):
        """Return all keys in the database sorted alphabetically."""
        blocked_keys = self.get_blocked_keys()
        keys = set()
        database = self.get_documents()
        for doc in database:
            for key in self.get_doc_keys(doc):
                if key not in blocked_keys:
                    keys.add(key)
        keys = list(keys)
        keys.sort(key=lambda y: y.lower())
        return keys

    def get_docs_by_key_value(self, key, value):
        """Return a list documents for a given key/value sorted by date."""
        docs = []
        for doc in self.db:
            try:
                if value in self.db[doc][key]:
                    docs.append(doc)
            except KeyError:
                pass
        return self.sort_by_date(docs)

    def get_doc_keys(self, doc):
        """Return a list of keys for a given doc sorted alphabetically."""
        keys = []
        for key in self.db[doc]:
            keys.append(key)
        keys.sort(key=lambda y: y.lower())
        return keys

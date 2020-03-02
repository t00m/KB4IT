#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RDF Graph In Memory database module.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: module to allow kb4it create a RDF graph
"""
import operator
from kb4it.src.core.mod_srv import Service

EOHMARK = """// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE"""
BLOCKED_KEYS = ['Title', 'Timestamp']
IGNORE_KEYS = BLOCKED_KEYS


class KB4ITDB(Service):
    """KB4IT database class."""

    params = None
    db = {}
    source_path = None
    sorted_docs = []
    maxvk = 0

    def initialize(self):
        """Initialize database module."""
        self.params = self.app.get_params()
        self.source_path = self.params.SOURCE_PATH

    def add_document(self, doc, timestamp):
        """Add a new document node to the graph."""
        self.db[doc] = {}
        self.db[doc]['Timestamp'] = timestamp
        self.log.debug("\t\t\t%s created/modified on %s", doc, timestamp)

    def add_document_key(self, doc, key, value):
        """Add a new key node to a document."""
        try:
            alist = self.db[doc][key]
            alist.append(value)
            self.db[doc][key] = alist
        except KeyError:
            self.db[doc][key] = [value]

        self.log.debug("\t\t\tKey '%s' with value '%s' linked to document: %s", key, value, doc)

    def ignore_key(self, key):
        IGNORE_KEYS.append(key)

    def sort(self, attribute='Timestamp'):
        """Build a list of documents sorted by timestamp desc."""
        adict = {}
        for doc in self.db:
            try:
                adict[doc] = self.db[doc][attribute]
            except:
                adict[doc] = self.db[doc]['Timestamp']
        alist = sorted(adict.items(), key=operator.itemgetter(1), reverse=True)
        for doc, timestamp in alist:
            self.sorted_docs.append(doc)
        # ~ self.sorted_docs.reverse()


    def sort_by_date(self, doclist, attribute='Timestamp'):
        """Build a list of documents sorted by timestamp desc."""
        sorted_docs = []
        adict = {}
        for doc in doclist:
            try:
                adict[doc] = self.db[doc][attribute]
            except:
                adict[doc] = self.db[doc]['Timestamp']
        alist = sorted(adict.items(), key=operator.itemgetter(1), reverse=True)
        for doc, timestamp in alist:
            sorted_docs.append(doc)
        # ~ sorted_docs.reverse()
        # ~ for doc in sorted_docs:
            # ~ start = self.get_values(doc, 'Start')[0]
            # ~ timestamp = self.get_values(doc, 'Timestamp')
            # ~ self.log.error("%s -> A[%s] T[%s]", doc, start, timestamp)
        # ~ self.log.error(" ")
        return sorted_docs

    def get_documents(self):
        return self.sorted_docs

    def get_doc_timestamp(self, doc):
        """Get timestamp for a given document."""
        params = self.app.get_params()

        # Get sort attribute
        try:
            attribute = params.SORT_ATTRIBUTE
        except:
            attribute = 'Timestamp'

        # Get doc timestamp for that attribute or use default timestamp
        try:
            timestamp = self.db[doc][attribute][0]
        except:
            timestamp = self.db[doc]['Timestamp']

        return timestamp

    def get_html_values_from_key(self, doc, key):
        """Return the html link for a value."""
        html = []

        values = self.get_values(doc, key)
        # ~ self.log.debug("\t\t\t[%s][%s] = %s", doc, key, values)
        for value in values:
            url = "%s_%s.html" % (key, value)
            html.append((url, value))
        return html

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

    def get_ignore_keys(self):
        return IGNORE_KEYS

    def get_custom_keys(self, doc):
        """Get a list of custom keys."""
        custom_keys = []
        keys = self.get_doc_keys(doc)
        for key in keys:
            if key not in IGNORE_KEYS:
                custom_keys.append(key)
        custom_keys.sort(key=lambda y: y.lower())
        return custom_keys

    def get_all_keys(self):
        """Get all keys in the database."""
        keys = []
        for doc in self.db:
            for key in self.get_doc_keys(doc):
                if key not in ['Title', 'Timestamp']:
                    keys.append(key)
        keys = list(set(keys))
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
        docs.sort(key=lambda y: y.lower())
        ltitles = []
        dtitles = {}
        for doc in docs:
            title = self.get_values(doc, 'Title')[0]
            ltitles.append(title)
            dtitles[title] = doc
        ltitles.sort()
        ldocs = []
        for title in ltitles:
            ldocs.append(dtitles[title])
        return ldocs

    def get_doc_keys(self, doc):
        """Get keys for a given doc."""
        keys = []
        for key in self.db[doc]:
            keys.append(key)
        keys.sort(key=lambda y: y.lower())
        return keys

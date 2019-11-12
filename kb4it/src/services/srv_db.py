#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RDF Graph In Memory database module.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: module to allow kb4it create a RDF graph
"""

from kb4it.src.core.mod_srv import Service

EOHMARK = """// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE"""
HEADER_KEYS = ['Author', 'Category', 'Scope', 'Status', 'Team', 'Priority']
IGNORE_KEYS = HEADER_KEYS + ['Title']


class KB4ITDB(Service):
    """KB4IT database class."""

    params = None
    db = {}
    source_path = None

    def initialize(self):
        """Initialize database module."""
        self.params = self.app.get_params()
        self.source_path = self.params.SOURCE_PATH

    def get_database(self):
        """Get a pointer to the database."""
        return self.db

    def add_document(self, doc):
        """Add a new document node to the graph."""
        self.db[doc] = {}
        self.log.debug("\t\t\tCreated new document: %s", doc)

    def add_document_key(self, doc, key, value):
        """Add a new key node to a document."""
        try:
            alist = self.db[doc][key]
            alist.append(value)
            self.db[doc][key] = alist
        except KeyError:
            self.db[doc][key] = [value]
        self.log.debug("\t\t\tKey '%s' with value '%s' linked to document: %s", key, value, doc)

    def get_html_values_from_key(self, doc, key):
        """Return the html link for a value."""
        html = []

        values = self.get_values(doc, key)
        self.log.debug("\t\t\t[%s][%s] = %s", doc, key, values)
        for value in values:
            url = "%s_%s.html" % (key, value)
            html.append((url, value))
        return html

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
            if key not in IGNORE_KEYS:
                custom_keys.append(key)
        custom_keys.sort(key=lambda y: y.lower())
        return custom_keys

    def get_all_keys(self):
        """Get all keys in the database."""
        keys = []
        for doc in self.db:
            for key in self.get_doc_keys(doc):
                if key != 'Title':
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

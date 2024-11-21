#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RDF Graph In Memory database module.
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: In-memory database module
"""

from kb4it.core.service import Service
from kb4it.core.util import sort_dictionary
from kb4it.core.util import valid_filename
from kb4it.core.util import guess_datetime


class Database(Service):
    """KB4IT database class."""

    db = {}
    keys = {}
    sort_attribute = None
    sorted_docs = []


    def initialize(self):
        """Initialize database module."""
        try:
            repo = self.app.get_repo_conf()
            self.sort_attribute = repo['sort']
        except:
            pass
        self.sorted_docs = []
        self.srvbes = self.get_service('Backend')
        repoconf = self.srvbes.get_repo_parameters()
        self.keys['all'] = []
        self.keys['blocked'] = ['Timestamp', 'Title']
        self.keys['custom'] = []
        self.keys['theme'] = []
        try:
            self.keys['ignored'] = repoconf['ignored_keys']
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

    def add_document(self, doc):
        """Add a new document node to the database."""
        self.db[doc] = {}
        self.log.debug("[DATABASE] - DOC[%s] added to database", doc)

    def add_document_key(self, doc, key, value):
        """Add a new key/value node for a given document."""
        try:
            alist = self.db[doc][key]
            alist.append(value)
            self.db[doc][key] = alist
        except KeyError:
            self.db[doc][key] = [value]

        self.log.debug("[DATABASE] - DOC[%s] KEY[%s] VALUE[%s] added", doc, key, value)

    def get_blocked_keys(self):
        """Return blocked keys."""
        return self.keys['blocked']

    def get_ignored_keys(self):
        """Return ignored keys."""
        return self.keys['ignored']

    def ignore_key(self, key):
        """Add given key to ignored keys list."""
        self.keys['ignored'].append(key)

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
        can_sort = True
        for doc in doclist:
            sdate = self.get_doc_timestamp(doc)
            ts = guess_datetime(sdate)
            if ts is not None:
                adict[doc] = ts.strftime("%Y%m%d")
            else:
                self.log.warning("[DATABASE] - Doc '%s' doesn't have a valid timestamp?", doc)
                self.log.warning("[DATABASE] - Sorting is disabled")
                can_sort = False
        if can_sort:
            alist = sort_dictionary(adict)
            for doc, timestamp in alist:
                sorted_docs.append(doc)
            return sorted_docs
        else:
            return doclist

    def get_documents(self):
        """Return the list of sorted docs."""
        return self.sorted_docs

    def get_doc_timestamp(self, doc):
        """Get timestamp for a given document."""
        found = False
        timestamp = ''
        for sort_attribute in self.sort_attribute:
            try:
                timestamp = self.db[doc][sort_attribute][0]
                found = True
            except:
                pass

        if not found:
            try:
                timestamp = self.db[doc]['Timestamp'][0]
            except:
                pass
        return timestamp

    def get_doc_properties(self, doc):
        """Return a dictionary with the properties of a given doc.
        Additionally, the dictionary will contain an extra entry foreach
        property with its Url:
        """
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

        return props

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
        if len(self.keys['custom']) > 0:
            return self.keys['custom']

        custom_keys = []
        keys = self.get_doc_keys(doc)
        for key in keys:
            if key not in self.keys['ignored']:
                custom_keys.append(key)
        custom_keys.sort(key=lambda y: y.lower())
        self.keys['custom'] = custom_keys
        return self.keys['custom']

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
        try:
            for key in self.db[doc]:
                keys.append(key)
            keys.sort(key=lambda y: y.lower())
        except Exception as error:
            self.log.debug("[DATABASE] - Doc[%s] is not in the database (system page?)", doc)
        return keys

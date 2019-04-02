#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: module to allow kb4it create a RDF graph
"""

from rdflib import URIRef
from rdflib import Literal
from rdflib.namespace import Namespace, NamespaceManager
from rdflib import RDF
from rdflib import ConjunctiveGraph

# Semantic Web Ontologies: W3C and KB4IT
RDF = Namespace(RDF)
KB4IT = Namespace(u"https://t00mlabs.net/ontologies/kb4it/")

NSBINDINGS = {
    u"rdf"   : RDF,
    u"kb4it" : KB4IT
}

class KB4ITGraph:
    """
    This class creates a RDF graph based on attributes for each doc.
    Also it has convenient function to ask the graph
    """
    def __init__(self, path=None):
        """
        If not path is passed it build a graph in memory. Otherwise, it
        creates a persistent graph in disk.
        """
        if path is not None:
            # Create persistent Graph in disk
            self.path = path
            self.graph = ConjunctiveGraph('Sleepycat', URIRef("kb4it://"))
            graph_path = path + SEP + 'kb4it.graph'
            self.graph.store.open(graph_path)
        else:
            # Create Graph in Memory
            self.graph = ConjunctiveGraph('IOMemory')

        # Assign namespaces to the Namespace Manager of this graph
        namespace_manager = NamespaceManager(ConjunctiveGraph())
        for ns in NSBINDINGS:
            namespace_manager.bind(ns, NSBINDINGS[ns])
        self.graph.namespace_manager = namespace_manager


    def __uniq_sort(self, result):
        alist = list(result)
        aset = set(alist)
        alist = list(aset)
        alist.sort()
        return alist


    def subjects(self, predicate, object):
        """
        Returns a list of sorted and uniques subjects given a predicate
        and an object.
        """
        return self.__uniq_sort(self.graph.subjects(predicate, object))


    def predicates(self, subject=None, object=None):
        """
        Returns a list of sorted and uniques predicates given a subject
        and an object.
        """
        return self.__uniq_sort(self.graph.predicates(subject, object))


    def objects(self, subject, predicate):
        """
        Returns a list of sorted and uniques objects given a subject
        and an predicate.
        """
        return self.__uniq_sort(self.graph.objects(subject, predicate))


    def value(self, subject=None, predicate=None, object=None, default=None, any=True):
        """
        Returns a value given the subject and the predicate.
        """
        return self.graph.value(subject, predicate, object, default, any)


    def add_document(self, doc):
        """
        Add a new document to the graph.
        """
        subject = URIRef(doc)
        predicate = RDF['type']
        object = URIRef(KB4IT['Document'])
        self.graph.add([subject, predicate, object])


    def add_document_attribute(self, doc, attribute, value):
        """
        Add a new attribute to a document
        """
        predicate = 'has%s' % attribute
        subject = URIRef(doc)
        predicate = KB4IT[predicate]
        object = Literal(value)
        self.graph.add([subject, predicate, object])


    def get_attributes(self):
        """
        Get all predicates except RFD.type and Title
        """
        blacklist = set()
        blacklist.add(RDF['type'])
        blacklist.add(KB4IT['hasTitle'])
        alist = list(self.graph.predicates(None, None))
        aset = set(alist) - blacklist
        alist = list(aset)
        alist.sort()
        return alist


    def serialize(self):
        """
        Serialize graph to pretty xml format
        """
        return self.graph.serialize(format='pretty-xml')


    def close(self):
        """
        Close the graph if it is persistent.
        FIXME: check if it is open
        """
        self.graph.store.close()

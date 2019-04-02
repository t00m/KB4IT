#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# Version: 0.4
# License: GPLv3
# Description: Build a static documentation site based on Asciidoc
#              sources with Semantic Web technologies.
"""

import os
import glob
import argparse
import atexit
import tempfile
import shutil
import subprocess
import datetime as dt
from datetime import datetime
import traceback as tb
from concurrent.futures import ThreadPoolExecutor as Executor

from .rdfdb import *
from .constants import *
from .utils import *

class SWKB4IT:
    def __init__(self, params):
        self.log = None
        self.tmpdir = tempfile.mkdtemp()
        self.source_path = None
        self.target_path = None
        self.numdocs = 0
        self.check_parameters(params)
        atexit.register(lambda adir=self.tmpdir: shutil.rmtree(self.tmpdir))
        self.graph = KB4ITGraph()


    def check_parameters(self, params):
        self.log = get_logger(params.LOGLEVEL)
        self.log.debug("Checking parameters")
        self.log.debug("Parameters: %s" % params)
        self.source_path = params.SOURCE_PATH
        self.keys = params.KEYS

        if self.source_path is None:
            self.source_path = os.path.abspath(KB4IT_SCRIPT_DIR + '/source')

        if not os.path.exists(self.source_path):
            os.makedirs(self.source_path)
            self.log.debug("\tCreated source path: %s", self.source_path)

        self.target_path = params.TARGET_PATH
        if self.target_path is None:
            self.target_path = os.path.abspath(os.path.curdir + '/target')
            self.log.debug("\tNo target path provided. Using: %s", self.target_path)

        if not os.path.exists(self.target_path):
            os.makedirs(self.target_path)
            self.log.debug("\tTarget path %s created", self.target_path)

        self.log.debug("\tScript directory: %s", KB4IT_SCRIPT_DIR)
        self.log.debug("\tResources directory: %s", KB4IT_RES_DIR)
        self.log.info("\tSource directory: %s", self.source_path)
        self.log.info("\tTarget directory: %s", self.target_path)
        self.log.debug("\tTemporary directory: %s", self.tmpdir)


    def set_filter(self, filter):
        self.filter = filter


    def get_filter(self):
        return self.filter

    def get_source_docs(self, path):
        if path[:-1] != os.path.sep:
            path = path + os.path.sep

        pattern = os.path.join(path) + '*.adoc'
        docs = glob.glob(pattern)
        self.numdocs = len(docs)
        self.log.info("\tGet source docs: %d documents", self.numdocs)

        return docs


    def copy_docs(self, docs, target):
        for doc in docs:
            shutil.copy(doc, target)
        self.log.debug("\t%d docs copied to %s" % (len(docs), target))


    def get_keys(self, s=None, o=None):
        return self.graph.predicates(s, o)


    def get_metadata(self, doc):
        try:
            # Create a new node in the graph (a document)
            self.graph.add_document(doc)

            # Get lines
            fdoc = self.source_path + SEP + doc
            line = open(fdoc, 'r').readlines()

            # Add document title (first line) to graph
            title = line[0][2:-1]
            self.graph.add_document_attribute(doc, 'Title', title)

            # read the rest of properties until watermark
            for n in range(1, len(line)):
                if line[n].startswith(':'):
                    key = line[n][1:line[n].rfind(':')]
                    alist = nosb(line[n][len(key)+2:-1].split(','))
                    for elem in alist:
                        self.graph.add_document_attribute(doc, key, elem)
                elif line[n].startswith(EOHMARK):
                    # Stop processing if EOHMARK is found
                    break
        except Exception as error:
            self.log.error(error)
            self.log.error("Document %s could not be processed" % doc)
            self.log.error(tb.format_exc())


    def create_recents_page(self):
        """
        In order this page makes sense, this script should be
        executed periodically from crontab.
        """
        TOP_NAV_BAR = self.get_template('TPL_TOP_NAV_BAR')
        docname = "%s/%s" % (self.tmpdir, 'recents.adoc')
        with open(docname, 'w') as frec:
            relset = set()
            today = datetime.now()
            lastweek = today - dt.timedelta(weeks=1)
            lastmonth = today - dt.timedelta(days=31)
            strtoday = "%d-%02d-%02d" % (today.year, today.month, today.day)

            # TODAY
            docs = self.graph.subjects(RDF['type'], URIRef(KB4IT['Document']))
            for doc in docs:
                revdate = self.graph.value(doc, KB4IT['hasRevdate'])
                if revdate == Literal(strtoday):
                    relset.add(doc)

            page = '= Last documents added\n\n'
            page += '== Today (%d)\n\n' % len(relset)
            page += """[options="header", width="100%", cols="60%,20%,20%"]\n"""
            page += "|===\n"
            page += "|Document |Category | Status\n"

            for doc in relset:
                title = self.graph.value(doc, KB4IT['hasTitle'])
                category = self.graph.value(doc, KB4IT['hasCategory'])
                status = self.graph.value(doc, KB4IT['hasStatus'])
                page += "|<<%s#,%s>>\n" % (doc, title)
                page += "|<<Category_%s.adoc#,%s>>\n" % (category, category)
                page += "|<<Status_%s.adoc#,%s>>\n" % (status, status)

            page += "|==="

            # WEEK
            for doc in docs:
                revdate = datetime.strptime(self.graph.value(doc, KB4IT['hasRevdate']), "%Y-%m-%d")
                if revdate <= today and revdate >= lastweek:
                    relset.add(doc)

            page += '\n\n== This week (%d)\n\n' %  len(relset)
            page += """[options="header", width="100%", cols="60%,20%,20%"]\n"""
            page += "|===\n"
            page += "|Document |Category | Status\n"
            for doc in relset:
                title = self.graph.value(doc, KB4IT['hasTitle'])
                category = self.graph.value(doc, KB4IT['hasCategory'])
                status = self.graph.value(doc, KB4IT['hasStatus'])
                page += "|<<%s#,%s>>\n" % (doc, title)
                page += "|<<%s#,%s>>\n" % (doc, category)
                page += "|<<%s#,%s>>\n" % (doc, status)
            page += "|==="

            # MONTH
            for doc in docs:
                revdate = datetime.strptime(self.graph.value(doc, KB4IT['hasRevdate']), "%Y-%m-%d")
                if revdate <= today and revdate >= lastmonth:
                    relset.add(doc)

            page += '\n\n== This month (%d)\n\n' % len(relset)
            page += """[options="header", width="100%", cols="60%,20%,20%"]\n"""
            page += "|===\n"
            page += "|Document |Category | Status\n"
            for doc in relset:
                title = self.graph.value(doc, KB4IT['hasTitle'])
                category = self.graph.value(doc, KB4IT['hasCategory'])
                status = self.graph.value(doc, KB4IT['hasStatus'])
                page += "|<<%s#,%s>>\n" % (doc, title)
                page += "|<<%s#,%s>>\n" % (doc, category)
                page += "|<<%s#,%s>>\n" % (doc, status)
            page += "|===\n\n"

            page += TOP_NAV_BAR
            frec.write(page)


    def create_key_page(self, key, values):
        html = self.get_template('TPL_KEY_PAGE')
        tagcloud = self.create_tagcloud_from_key(key)
        alist = ''
        for value in values:
            alist += "* <<%s_%s.adoc#,%s>>\n" % (key, value, value)

        return html % (tagcloud, alist)


    def process_docs(self):
        TOP_NAV_BAR = self.get_template('TPL_TOP_NAV_BAR')
        attributes = self.graph.get_attributes()
        for attribute in attributes:
            key = attribute[attribute.rfind('/') + 4:]
            docname = "%s/%s.adoc" % (self.tmpdir, key)
            values = self.graph.objects(None, attribute)
            html = self.create_key_page(key, list(values))
            with open(docname, 'w') as fkey:
                TPL_METAKEY = self.get_template('TPL_METAKEY')
                fkey.write(TPL_METAKEY % key)
                fkey.write(html)
                for value in values:
                    # Create .adoc from value
                    docname = "%s/%s_%s.adoc" % (self.tmpdir, key, value)
                    with open(docname, 'w') as fvalue:
                        TPL_VALUE = self.get_template('TPL_VALUE')
                        fvalue.write(TPL_VALUE % (key, value))

                        # Search documents related to this key/value
                        docs = self.graph.subjects(RDF['type'], URIRef(KB4IT['Document']))
                        for doc in docs:
                            try:
                                objects = self.graph.objects(doc, attribute)
                                if Literal(value) in list(objects):
                                    title = self.graph.value(doc, KB4IT['hasTitle'])
                                    fvalue.write("* <<%s#,%s>>\n" % (os.path.basename(doc)[:-5], title))
                            except Exception as error:
                                self.log.error(error)
                                self.log.error(tb.format_exc())
                        fvalue.write("\n%s\n" % TOP_NAV_BAR)

                fkey.write("\n%s\n" % TOP_NAV_BAR)

        self.create_recents_page()
        self.create_index_all()
        self.create_index_page()
        self.create_all_keys_page()
        self.log.info("4. Document's metadata processed")

    def create_tagcloud_from_key(self, key):
        dkeyurl = {}
        docs = list(self.graph.subjects(RDF['type'], URIRef(KB4IT['Document'])))
        for doc in docs:
            try:
                predicate = KB4IT['has%s' % key]
                tags = self.graph.objects(doc, predicate)
                url = os.path.basename(doc)[:-5]
                for tag in tags:
                    try:
                        urllist = dkeyurl[tag]
                        surllist = set(urllist)
                        surllist.add(url)
                        dkeyurl[tag] = list(surllist)
                    except:
                        surllist = set()
                        surllist.add(url)
                        dkeyurl[tag] = list(surllist)
            except Exception as error:
                self.log.error(error)
                self.log.error(tb.format_exc())

        max_frequency = set_max_frequency(dkeyurl)
        lwords = []

        for word in dkeyurl:
            if len(word) > 0:
                lwords.append(word)

        if len(lwords) > 0:
            lwords.sort()

            html = "<div class=\"tagcloud\">"
            for word in lwords:
                frequency = len(dkeyurl[word])
                size = get_font_size(frequency, max_frequency)
                url = "%s_%s.html" % (key, word)
                chunk = "<div class=\"tagcloud-word\"><a style=\"text-decoration: none;\" href=\"%s\"><span style=\"font-size:%dpt;\">%s</span></a></div>" % (url, size, word)
                html += chunk
            html += "</div>"
        else:
            html = ''

        return html


    def create_index_all(self):
        docname = "%s/all.adoc" % (self.tmpdir)
        TPL_METAKEY = self.get_template('TPL_METAKEY')
        TOP_NAV_BAR = self.get_template('TPL_TOP_NAV_BAR')
        with open(docname, 'w') as fall:
            fall.write(TPL_METAKEY % "All documents")
            doclist = []
            docs = self.graph.subjects(RDF['type'], URIRef(KB4IT['Document']))
            for doc in docs:
                doclist.append(doc)
            doclist.sort()
            for doc in doclist:
                title = self.graph.value(doc, KB4IT['hasTitle'])
                fall.write(". <<%s#,%s>>\n" % (os.path.basename(doc)[:-5], title))
            fall.write("\n%s\n" % TOP_NAV_BAR)


    def create_index_page(self):
        TPL_INDEX = self.get_template('TPL_INDEX')
        TOP_NAV_BAR = self.get_template('TPL_TOP_NAV_BAR')
        total = 0
        cats = self.graph.objects(None, KB4IT['hasCategory'])
        cols = '^,'*len(cats)
        tblcats = """[options="header", width="100%%", cols="%s"]\n""" % cols[:-1]
        tblcats += "|===\n"
        for cat in cats:
            tblcats += "|%s\n" % cat
        for cat in cats:
            tblcats += "|<<Category_%s.adoc#,%d>>\n" % (cat, len(self.graph.subjects(KB4IT['hasCategory'], cat)))
        tblcats += "|===\n"
        tblareas = self.create_tagcloud_from_key('Scope')
        tagcloud = self.create_tagcloud_from_key('Tag')
        tblkeys = """[options="header", width="100%", cols="80%,>"]\n"""
        tblkeys += "|===\n"
        tblkeys += "|Key\n"
        tblkeys += "|Docs\n"
        for attribute in self.graph.get_attributes():
            key = attribute[attribute.rfind('/')+4:]
            values = self.graph.objects(None, attribute)
            tblkeys += "|<<%s#,%s>>\n" % (key, key)
            tblkeys += "|<<%s.adoc#,%d>>\n\n" % (key, len(values))
            total += len(values)
        tblkeys += "|==="
        with open('%s/index.adoc' % self.tmpdir, 'w') as findex:
            content = TPL_INDEX % (self.numdocs, tblcats, tblareas, tagcloud, tblkeys)
            findex.write(content)
            findex.write(TOP_NAV_BAR)


    def create_all_keys_page(self):
        TPL_KEYS = self.get_template('TPL_KEYS')
        TOP_NAV_BAR = self.get_template('TPL_TOP_NAV_BAR')
        with open('%s/keys.adoc' % self.tmpdir, 'w') as fkeys:
            fkeys.write(TPL_KEYS)
            all_keys = self.graph.get_attributes()
            for swkey in all_keys:
                key = swkey[swkey.rfind('/')+4:]
                cloud = self.create_tagcloud_from_key(key)
                if len(cloud) > 0:
                    fkeys.write("\n\n== %s\n\n" % key)
                    fkeys.write("\n++++\n%s\n++++\n" % cloud)
            fkeys.write("\n%s\n" % TOP_NAV_BAR)


    def compile_docs(self):
        # copy online resources to target path
        resources_dir_source = KB4IT_SCRIPT_DIR + SEP + 'resources/online'
        resources_dir_target = self.target_path + SEP + 'resources'
        #~ jquery_dir_source = KB4IT_SCRIPT_DIR + SEP + 'resources/online/js/jquery'
        self.log.debug("Copying contents from %s to %s", resources_dir_source, resources_dir_target)
        resources_dir_tmp = self.tmpdir + SEP + 'resources'
        shutil.copytree(resources_dir_source, resources_dir_target)
        shutil.copytree(resources_dir_source, resources_dir_tmp)
        #~ copydir(jquery_dir_source, self.target_path + '/')

        adocprops = ''
        for prop in ADOCPROPS:
            if ADOCPROPS[prop] is not None:
                if '%s' in ADOCPROPS[prop]:
                    adocprops += '-a %s=%s \\\n' % (prop, ADOCPROPS[prop] % self.target_path)
                else:
                    adocprops += '-a %s=%s \\\n' % (prop, ADOCPROPS[prop])
            else:
                adocprops += '-a %s \\\n' % prop
        self.log.debug("\tParameters passed to Asciidoc:\n%s" % adocprops)

        with Executor(max_workers=MAX_WORKERS) as exe:
            docs = self.get_source_docs(self.tmpdir)
            jobs = []
            jobcount = 0

            n = 0
            for doc in docs:
                cmd = "asciidoctor %s -b html5 -D %s %s" % (adocprops, self.tmpdir, doc)
                #~ self.log.debug(cmd)
                job = exe.submit(self.exec_cmd, (doc, cmd, n))
                jobs.append(job)
                n = n + 1

            for job in jobs:
                res = job.result()
                doc, rc, j = res
                jobcount += 1
                if jobcount % MAX_WORKERS == 0:
                    pct = int(jobcount * 100 / len(docs))
                    self.log.info("\tCompiling: %3s%% done", str(pct))
            self.log.info("\tCompiling: 100% done")
            self.log.info("5. Documents compiled successfully.")


    def exec_cmd(self, data):
        """
        Execute an operating system command an return:
        - document
        - True if success, False if not
        - res is the output
        """
        doc, cmd, res = data
        process = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
        outs, errs = process.communicate()
        if errs is None:
            return doc, True, res
        else:
            self.log.debug("Command: %s", cmd)
            self.log.debug("Compiling %s: Error: %s", (doc, errs))
            return doc, False, res


    def get_html_values_from_attribute(self, doc, predicate):
        """
        Returns the html link for the value/s returned fo a specific
        predicate.
        """
        html = ''

        try:
            values = self.graph.objects(URIRef(doc), predicate)
            for value in values:
                if len(value) > 0:
                    key = predicate[predicate.rfind('/')+4:]
                    html += "<a class=\"metadata\" href=\"%s_%s.html\">%s</a> " % (key, value, value)
                else:
                    html = ''
        except Exception as error:
            self.log.error(error)
            self.log.error(tb.format_exc())

        return html


    def get_custom_keys(self, doc):
        header_keys = [RDF['type'], KB4IT['hasCategory'], KB4IT['hasScope'], KB4IT['hasStatus'], KB4IT['hasDepartment'], KB4IT['hasTeam'], KB4IT['hasTag'], KB4IT['hasAuthor'], KB4IT['hasRevdate'], KB4IT['hasRevnumber'], KB4IT['hasTitle']]
        custom_keys = []
        keys = self.get_keys(s=URIRef(doc))
        for key in keys:
            if key not in header_keys:
                custom_keys.append(key)
        custom_keys.sort()

        return custom_keys


    def get_template(self, template):
        DIR_SCRIPT = os.path.dirname(__file__)
        return open('%s/resources/offline/templates/%s.tpl' % (DIR_SCRIPT, template), 'r').read()


    def create_metadata_section(self, doc):
        """
        Returns a html block for displaying key and custom attributes
        """
        try:
            html = self.get_template('TPL_METADATA_SECTION_HEADER')
            author = self.get_html_values_from_attribute(doc, KB4IT['hasAuthor'])
            revdate = self.get_html_values_from_attribute(doc, KB4IT['hasRevdate'])
            revnumber = self.get_html_values_from_attribute(doc, KB4IT['hasRevnumber'])
            category = self.get_html_values_from_attribute(doc, KB4IT['hasCategory'])
            scope = self.get_html_values_from_attribute(doc, KB4IT['hasScope'])
            status = self.get_html_values_from_attribute(doc, KB4IT['hasStatus'])
            dept = self.get_html_values_from_attribute(doc, KB4IT['hasDepartment'])
            team = self.get_html_values_from_attribute(doc, KB4IT['hasTeam'])
            tags = self.get_html_values_from_attribute(doc, KB4IT['hasTag'])
            METADATA_SECTION_BODY = self.get_template('TPL_METADATA_SECTION_BODY')
            tc_author = self.create_tagcloud_from_key('Author')
            tc_revdate = self.create_tagcloud_from_key('Revdate')
            tc_revision = self.create_tagcloud_from_key('Revnumber')
            tc_category = self.create_tagcloud_from_key('Category')
            tc_scope = self.create_tagcloud_from_key('Scope')
            tc_status = self.create_tagcloud_from_key('Status')
            tc_department = self.create_tagcloud_from_key('Department')
            tc_team = self.create_tagcloud_from_key('Team')
            tc_tag = self.create_tagcloud_from_key('Tag')
            html += METADATA_SECTION_BODY % (author, revdate, revnumber, \
                                            category, scope, status, \
                                            dept, team, tags, tc_author, \
                                            tc_revdate, tc_revision, \
                                            tc_category, tc_scope, \
                                            tc_status, tc_department, \
                                            tc_team, tc_tag)

            custom_keys = self.get_custom_keys(doc)
            custom_props = ''
            for key in custom_keys:
                values = self.get_html_values_from_attribute(doc, key)
                if len(values) > 0:
                    swkey = key[key.rfind('/')+4:]
                    row = """<tr><td class="mdkey"><a href=\"%s.html">%s</a></td><td class="mdval" colspan="3">%s</td></tr>\n""" % (swkey, swkey, values)
                    custom_props += row

            if len(custom_props) > 0:
                html += "[TIP]\n"
                html += "====\n\n"
                html += "++++\n"
                html += """<table class="metadata">\n"""
                html += custom_props
                html += "</table>\n"
                html += "++++\n\n"
                html += "====\n"

            METADATA_SECTION_FOOTER = self.get_template('TPL_METADATA_SECTION_FOOTER')
            html += METADATA_SECTION_FOOTER % doc
        except Exception as error:
            msgerror = "%s -> %s" % (doc, error)
            self.log.error(msgerror)
            html = ''
            self.log.error(tb.format_exc())

        return html


    def preprocessing(self, docs):
        """Extract metadata from source docs into a dict.
           Create metadata section for each adoc and insert it
           after the EOHMARK.
           In this way, after being compiled into HTML, final adocs are
           browsable throught its metadata.
        """
        TOP_NAV_BAR = self.get_template('TPL_TOP_NAV_BAR')
        docs.sort()
        for source in docs:
            docname = os.path.basename(source)
            self.log.debug("\tProcessing source doc (Part I): %s" % docname)

            # Get metadata
            try:
                self.get_metadata(docname)
            except Exception as error:
                msgerror = "Source file %s: could not be processed: %s" % (docname, error)
                self.log.error(msgerror)

        for source in docs:
            try:
                docname = os.path.basename(source)
                self.log.debug("\tProcessing source doc (Part II): %s" % docname)
                # Create metadata section
                meta_section = self.create_metadata_section(docname)

                # Replace EOHMARK with metadata section
                with open(source) as source_adoc:
                    srcadoc = source_adoc.read()
                    newadoc = srcadoc.replace(EOHMARK, meta_section, 1)
                    newadoc += TOP_NAV_BAR

                    # Write new adoc to temporary dir
                    target = "%s/%s" % (self.tmpdir, docname)
                    with open(target, 'w') as target_adoc:
                        target_adoc.write(newadoc)
            except Exception as error:
                msgerror = "Source file %s: could not be processed: %s" % (docname, error)
                self.log.error(msgerror)

        self.log.info("3. Preprocessed %d docs" % len(docs))


    def create_target(self):
        pattern = self.source_path + SEP + '*.adoc'
        files = glob.glob(pattern)
        for filename in files:
            shutil.copy(filename, self.target_path)

        pattern = self.tmpdir + SEP + '*.html'
        files = glob.glob(pattern)
        for filename in files:
            shutil.copy(filename, self.target_path)

        self.log.info("6. Compiled documents copied to target directory")


    def delete_target_contents(self):
        if not os.path.exists(self.target_path):
            self.log.debug("\tTarget directory %s does not exists", self.target_path)
        else:
            for file_object in os.listdir(self.target_path):
                file_object_path = os.path.join(self.target_path, file_object)
                if os.path.isfile(file_object_path):
                    os.unlink(file_object_path)
                else:
                    shutil.rmtree(file_object_path)
            self.log.debug("\tContents of directory %s deleted successfully", self.target_path)
        self.log.info("1. Target directory clean")



    def run(self):
        """
        Start script execution following this flow:
        1. Delete contents of target directory (if any)
        2. Get source documents
        3. Preprocess documents (get metadata)
        4. Process documents in a temporary dir
        5. Compile documents to html with asciidoc
        6. Copy all documents to target path
        7. Copy source docs to target directory
        """
        self.log.info("KB4IT - Knowledge Base for IT")

        self.log.debug("\tStarting execution")

        # 1. Delete contents of target directory (if any)
        self.delete_target_contents()

        # 2. Get source documents
        docs = self.get_source_docs(self.source_path)
        self.log.info("2. Got %d docs from source directory", len(docs))

        # 3. Preprocess documents (get metadata)
        self.preprocessing(docs)

        # 4. Process documents in a temporary dir
        self.process_docs()

        # 5. Compile documents to html with asciidoc
        dcomps = datetime.now()
        self.compile_docs()
        dcompe = datetime.now()
        totaldocs = len(self.get_source_docs(self.tmpdir))
        comptime = dcompe - dcomps
        self.log.info("\tCompilation time: %d seconds", comptime.seconds)
        self.log.info("\tNumber of compiled docs: %d", totaldocs)
        try:
            self.log.info("\tCompilation Avg. Speed: %d docs/sec", int((totaldocs/comptime.seconds)))
        except ZeroDivisionError:
            self.log.info("\tCompilation Avg. Speed: %d docs/sec", int((totaldocs/1)))

        # 6. Copy all documents to target path
        self.create_target()

        # 7. Copy source docs to target directory
        self.copy_docs(docs, self.target_path)
        self.log.info("7. Source docs copied to target directory")
        self.log.info("Execution finished")


    def stop(self):
        """
        Save graph to file before exiting.
        """
        rdf = self.graph.serialize()
        graph_path = self.target_path + SEP + 'kb4it.rdf'
        with open(graph_path, 'wb') as frdf:
            frdf.write(rdf)

def main():
    parser = argparse.ArgumentParser(description='KB4IT by Tomás Vírseda')
    # ~ parser.add_argument('-p', '--property', dest='PROPERTY', help='Generate documentation only for a specific property/value.', required=True)
    parser.add_argument('-sp', '--source-path', dest='SOURCE_PATH', help='Path for Asciidoc source files.', required=True)
    parser.add_argument('-tp', '--target-path', dest='TARGET_PATH', help='Path for output files')
    parser.add_argument('-k', '--keys', dest='KEYS', help='filter source documents based on a list of comma-sepparate key=value')
    parser.add_argument('-v',  '--verbosity',   dest='LOGLEVEL',    help='Increase output verbosity', action='store', default='INFO')
    parser.add_argument('--version', action='version', version='%s %s' % ('KB4IT', '0.5'))
    params = parser.parse_args()
    DSG = SWKB4IT(params)
    try:
        DSG.run()
        DSG.stop()
        finish_ok()
    except Exception as error:
        DSG.stop()
        finish_ko(error)

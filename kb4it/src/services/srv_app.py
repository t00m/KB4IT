#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module with the application logic.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: module holding the application logic
"""

import os
import glob
import shutil
import tempfile
import datetime
from concurrent.futures import ThreadPoolExecutor as Executor
from kb4it.src.core.mod_env import LPATH, GPATH
from kb4it.src.core.mod_env import ADOCPROPS, MAX_WORKERS, EOHMARK
from kb4it.src.core.mod_srv import Service
from kb4it.src.core.mod_utils import valid_filename, load_current_kbdict
from kb4it.src.core.mod_utils import template, exec_cmd, job_done, delete_target_contents
from kb4it.src.core.mod_utils import get_source_docs, get_metadata, get_hash_from_dict
from kb4it.src.core.mod_utils import save_current_kbdict, copy_docs, copydir
from kb4it.src.core.mod_utils import get_author_icon
from kb4it.src.services.srv_db import HEADER_KEYS

EOHMARK = """// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE"""


class Application(Service):
    """Missing class docstring (missing-docstring)."""

    params = None
    target_path = None
    source_path = None
    cache_path = None
    graph = None
    tmpdir = None
    numdocs = 0
    kbdict_new = {}
    kbdict_cur = {}
    cached_docs = []

    def initialize(self):
        """Missing method docstring."""
        self.tmpdir = tempfile.mkdtemp(prefix=LPATH['TMP'])
        self.params = self.app.get_params()
        if self.params.TARGET_PATH is None:
            self.target_path = LPATH['WWW']
        else:
            self.target_path = os.path.realpath(self.params.TARGET_PATH)
        self.source_path = os.path.realpath(self.params.SOURCE_PATH)
        self.get_services()
        self.cache_path = os.path.join(LPATH['CACHE'], valid_filename(self.source_path))
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)

        self.kbdict_cur = load_current_kbdict(self.source_path)
        self.kbdict_new['document'] = {}
        self.kbdict_new['metadata'] = {}

    def get_cache_path(self):
        """Missing method docstring."""
        return self.cache_path

    def get_source_path(self):
        """Missing method docstring."""
        return self.source_path

    def get_target_path(self):
        """Missing method docstring."""
        return self.target_path

    def get_temp_dir(self):
        """Missing method docstring."""
        return self.tmpdir

    def get_services(self):
        """Missing method docstring."""
        self.srvdtb = self.get_service('DB')
        self.srvbld = self.get_service('Builder')

    def get_numdocs(self):
        """Missing method docstring."""
        return self.numdocs

    def process_docs(self):
        """Missing method docstring."""
        # Get all available keys
        available_keys = self.srvdtb.get_all_keys()
        # Check if any of the core keys is missing
        missing = []
        for key in HEADER_KEYS:
            if key not in available_keys:
                self.log.debug("Adding missing key: %s", key)
                missing.append(key)
        available_keys.extend(missing)

        # Process
        for key in available_keys:
            if key == 'Title':
                break

            self.log.debug("          Processing key: %s", key)
            values = self.srvdtb.get_all_values_for_key(key)
            for value in values:
                try:
                    filename = "%s_%s.adoc" % (valid_filename(key), valid_filename(value))
                    docname = os.path.join(self.tmpdir, filename)
                    doc_new = self.kbdict_new['metadata'][key][value]
                    doc_old = self.kbdict_cur['metadata'][key][value]
                    doc_changed = doc_new != doc_old
                    file_cached = "%s_%s.html" % (valid_filename(key), valid_filename(value))
                    cached_document = os.path.join(self.cache_path, file_cached)
                    cache_exists = os.path.exists(cached_document)
                    if doc_changed:
                        FORCE_DOC_COMPILATION = True
                    else:
                        if cache_exists:
                            FORCE_DOC_COMPILATION = False
                        else:
                            FORCE_DOC_COMPILATION = True
                except KeyError:
                    FORCE_DOC_COMPILATION = True

                if FORCE_DOC_COMPILATION:
                    # Create .adoc from value

                    with open(docname, 'w') as fvalue:
                        # Search documents related to this key/value
                        related_docs = set()
                        for doc in self.srvdtb.get_database():
                            objects = self.srvdtb.get_values(doc, key)
                            for obj in objects:
                                if value == obj:
                                    related_docs.add(doc)

                        # GRID START
                        DOC_CARD_FILTER_DATA_TITLE = template('DOC_CARD_FILTER_DATA_TITLE')
                        html = ''
                        for doc in related_docs:
                            title = self.srvdtb.get_values(doc, 'Title')[0]
                            doc_card = self.srvbld.get_doc_card(doc)
                            card_search_filter = DOC_CARD_FILTER_DATA_TITLE % (valid_filename(title), doc_card)
                            html += """%s""" % card_search_filter

                        TPL_VALUE = template('VALUE')
                        fvalue.write(TPL_VALUE % (valid_filename(key), key, value, html))
                else:
                    docname = "%s_%s.html" % (valid_filename(key), valid_filename(value))
                    filename = os.path.join(self.cache_path, docname)
                    self.cached_docs.append(filename)

                # ~ self.log.debug("Force compilation for [%s][%s]: %s", key, value, FORCE_DOC_COMPILATION)
            docname = "%s/%s.adoc" % (self.tmpdir, valid_filename(key))
            html = self.srvbld.create_key_page(key, values)
            with open(docname, 'w') as fkey:
                fkey.write(html)

        self.srvbld.create_all_keys_page()
        self.srvbld.create_index_all()
        self.srvbld.create_index_page()
        # ~ self.srvbld.create_search_page()
        self.log.debug("          Document's metadata processed")

    def compile_docs(self):
        """Missing method docstring."""
        # copy online resources to target path
        resources_dir_source = GPATH['ONLINE']
        resources_dir_tmp = os.path.join(self.tmpdir, 'resources')
        shutil.copytree(resources_dir_source, resources_dir_tmp)

        adocprops = ''
        for prop in ADOCPROPS:
            if ADOCPROPS[prop] is not None:
                if '%s' in ADOCPROPS[prop]:
                    adocprops += '-a %s=%s ' % (prop, ADOCPROPS[prop] % self.target_path)
                else:
                    adocprops += '-a %s=%s ' % (prop, ADOCPROPS[prop])
            else:
                adocprops += '-a %s ' % prop
        self.log.debug("          Parameters passed to Asciidoc: %s", adocprops)

        with Executor(max_workers=MAX_WORKERS) as exe:
            docs = get_source_docs(self.tmpdir)
            jobs = []
            jobcount = 0
            num = 1
            self.log.debug("          Generating %d jobs. Please, wait.", len(docs))
            for doc in docs:
                cmd = "asciidoctor -s %s -b html5 -D %s %s" % (adocprops, self.tmpdir, doc)
                # ~ self.log.debug("\t%s", cmd)
                job = exe.submit(exec_cmd, (doc, cmd, num))
                job.add_done_callback(job_done)
                # ~ self.log.debug("Job[%4d]: %s will be compiled", num, os.path.basename(doc))
                jobs.append(job)
                num = num + 1

            for job in jobs:
                adoc, res, jobid = job.result()
                self.log.debug("          Job[%4d]: %s compiled successfully", jobid, os.path.basename(adoc))
                jobcount += 1
                if jobcount % MAX_WORKERS == 0:
                    pct = int(jobcount * 100 / len(docs))
                    self.log.info("         %3s%% done", str(pct))

    def preprocessing(self, docs):
        """
        Extract metadata from source docs into a dict.

        Create metadata section for each adoc and insert it after the
        EOHMARK.

        In this way, after being compiled into HTML, final adocs are
        browsable throught its metadata.
        """
        docs.sort(key=lambda y: y.lower())
        for source in docs:
            docname = os.path.basename(source)
            self.kbdict_new['document'][docname] = {}
            self.log.debug("          Preprocessing DOC[%s]", docname)

            # Create a new node in the graph (a document)
            self.srvdtb.add_document(docname)

            # Get content
            with open(source) as source_adoc:
                srcadoc = source_adoc.read()

            # Get metadata
            docpath = os.path.join(self.source_path, docname)
            keys = get_metadata(docpath)

            # KBDICT
            # Document Content Hash
            self.kbdict_new['document'][docname]['content_hash'] = get_hash_from_dict({'content': srcadoc})
            # Document Metadata Hash
            self.kbdict_new['document'][docname]['metadata_hash'] = get_hash_from_dict(keys)

            for key in keys:
                alist = keys[key]
                for elem in alist:
                    self.srvdtb.add_document_key(docname, key, elem)
                    # Documents per [key, value]
                    try:
                        documents = self.kbdict_new['metadata'][key][elem]
                        documents.append(docname)
                        self.kbdict_new[key][elem] = sorted(documents, key=lambda y: y.lower())
                    except KeyError:
                        if key not in self.kbdict_new['metadata']:
                            self.kbdict_new['metadata'][key] = {}
                        if elem not in self.kbdict_new['metadata'][key]:
                            self.kbdict_new['metadata'][key][elem] = [docname]

            # Compare
            try:
                doc_new_mdt_hash = self.kbdict_new['document'][docname]['metadata_hash']
                doc_cur_mdt_hash = self.kbdict_cur['document'][docname]['metadata_hash']
                doc_new_cnt_hash = self.kbdict_new['document'][docname]['content_hash']
                doc_cur_cnt_hash = self.kbdict_cur['document'][docname]['content_hash']
                changed_metadata = doc_new_mdt_hash != doc_cur_mdt_hash
                changed_content = doc_new_cnt_hash != doc_cur_cnt_hash
                cached_document = os.path.join(self.cache_path, docname.replace('.adoc', '.html'))
                cache_exists = os.path.exists(cached_document)
                changed_document = changed_metadata or changed_content
                if changed_document:
                    FORCE_DOC_COMPILATION = True
                else:
                    if cache_exists:
                        FORCE_DOC_COMPILATION = False
                    else:
                        FORCE_DOC_COMPILATION = True
            except KeyError:
                FORCE_DOC_COMPILATION = True

            if FORCE_DOC_COMPILATION:
                # Create metadata section
                meta_section = self.srvbld.create_metadata_section(docname)

                # Replace EOHMARK with metadata section
                newadoc = srcadoc.replace(EOHMARK, meta_section, 1)

                # Write new adoc to temporary dir
                target = "%s/%s" % (self.tmpdir, valid_filename(docname))
                with open(target, 'w') as target_adoc:
                    target_adoc.write(newadoc)
            else:
                # ~ CACHE_DIR = os.path.join(LPATH['CACHE'], valid_filename(self.source_path))
                filename = os.path.join(self.cache_path, docname.replace('.adoc', '.html'))
                self.cached_docs.append(filename)

            # ~ self.log.debug("Force compilation for DOC[%s]: %s", docname, FORCE_DOC_COMPILATION)

        # ~ self.log.error("\n%s", pprint.pformat(self.kbdict_new, indent=4))
        save_current_kbdict(self.kbdict_new, self.source_path)

        self.log.debug("3. Preprocessed %d docs", len(docs))

    def create_target(self):
        """
        Copy asciidoc sources from Source path to Target Path.

        Copy html files from Temporary path to Target Path.
        """
        # Source files to be copied
        tmpdir = self.get_temp_dir()
        pattern = os.path.join(self.source_path, '*.adoc')
        files = glob.glob(pattern)
        copy_docs(files, self.target_path)

        # HTML files to be copied
        pattern = os.path.join(tmpdir, '*.html')
        files = glob.glob(pattern)
        copy_docs(files, self.target_path)

    def run(self):
        """Start script execution following this flow.

        1. Get source documents
        2. Preprocess documents (get metadata)
        3. Process documents in a temporary dir
        4. Compile documents to html with asciidoc
        5. Delete contents of target directory (if any)
        6. Copy all documents to target path
        7. Copy source docs to target directory
        8. Copy HTML files from target to cache (for delta compiling)
        """
        self.log.info("KB4IT - Knowledge Base for IT")

        # check if target directory exists. If not, create it:
        if not os.path.exists(self.target_path):
            os.makedirs(self.target_path)

        # Check if help and about documents exists. If not, use the default ones
        file_about = os.path.join(self.source_path, 'about.adoc')
        file_help = os.path.join(self.source_path, 'help.adoc')
        doc_about = os.path.exists(file_about)
        doc_help = os.path.exists(file_help)
        if not doc_about:
            tmp_about = os.path.join(self.tmpdir, 'about.adoc')
            with open(tmp_about, 'w') as fabout:
                fabout.write(template('PAGE_ABOUT'))
                self.log.warning("Added missing 'about.adoc' document")

        if not doc_help:
            tmp_help = os.path.join(self.tmpdir, 'help.adoc')
            with open(tmp_help, 'w') as fhelp:
                fhelp.write(template('PAGE_HELP'))
                self.log.warning("Added missing 'help.adoc' document")

        # Get source documents
        self.log.info("   START: Looking for documents in: %s", self.source_path)
        docs = get_source_docs(self.source_path)
        self.numdocs = len(docs)
        if self.numdocs == 0:
            self.log.warning("No .adoc files found in: %s", self.source_path)
            self.log.info("Setting up a new repository")
            docs = get_source_docs(GPATH['ADOCS'])
            copy_docs(docs, self.source_path)
            self.numdocs = len(docs)
        self.log.info("     END: Found %d asciidoc documents", self.numdocs)

        # Preprocess documents (get metadata)
        self.log.info("   START: Preprocessing source documents")
        self.preprocessing(docs)
        self.log.info("     END: Metadata extracted successfully")

        # Process documents in a temporary dir
        self.log.info("   START: Processing all documents")
        self.process_docs()
        self.log.info("     END: Documents, keys and values converted to asciidoc")

        # Compile documents to html with asciidoc
        self.log.info("   START: Compiling all documents")
        self.log.info("          0% done")
        dcomps = datetime.datetime.now()
        self.compile_docs()
        dcompe = datetime.datetime.now()
        totaldocs = len(get_source_docs(self.tmpdir))
        comptime = dcompe - dcomps
        self.log.info("          100% done")
        self.log.info("          Compilation time: %d seconds", comptime.seconds)
        self.log.info("          Number of compiled docs: %d", totaldocs)
        try:
            self.log.info("          Compilation Avg. Speed: %d docs/sec",
                          int((totaldocs/comptime.seconds)))
        except ZeroDivisionError:
            self.log.info("          Compilation Avg. Speed: %d docs/sec",
                          int((totaldocs/1)))
        self.log.info("     END: All documents compiled")

        # Delete contents of target directory (if any)
        self.log.info("   START: Deleting contents in target directory")
        delete_target_contents(self.target_path)
        self.log.info("     END: Deleted target contents in: %s", self.target_path)

        # Copy compiled documents to target path
        self.log.info("   START: Copying compiled docs to target path")
        self.create_target()
        self.log.info("     END: Documents copied successfully to: %s", self.target_path)

        # Copy cached documents to target path
        self.log.info("   START: Copying cached documents to target path")
        copy_docs(self.cached_docs, self.target_path)
        self.log.info("     END: Cached documents copied successfully to: %s", self.target_path)

        # Copy source docs to target directory
        self.log.info("   START: Copying original asciidocs sources to target directory")
        copy_docs(docs, self.target_path)
        self.log.info("     END: Source docs copied to: %s", self.target_path)

        # copy source resources to target path
        source_resources_dir = os.path.join(self.source_path, 'resources')
        if os.path.exists(source_resources_dir):
            resources_dir_target = os.path.join(self.target_path, 'resources')
            self.log.info("   START: Copying local resources...")
            self.log.info("          From: %s", source_resources_dir)
            self.log.info("          To: %s", resources_dir_target)
            copydir(source_resources_dir, resources_dir_target)
            self.log.info("     END: Local resources copied ")

        # copy global online resources to target path
        global_resources_dir = GPATH['ONLINE']
        resources_dir_target = os.path.join(self.target_path, 'resources')
        self.log.info("   START: Copying global resources...")
        self.log.info("          From: %s", global_resources_dir)
        self.log.info("          To: %s", resources_dir_target)
        copydir(global_resources_dir, resources_dir_target)
        self.log.info("     END: Global resources copied")

        self.log.info("   START: Copying HTML files to cache...")
        pattern = os.path.join(self.target_path, '*.html')
        html_files = glob.glob(pattern)
        # ~ CACHE_DIR = os.path.join(LPATH['CACHE'], valid_filename(self.source_path))

        self.log.info("          From: %s", self.target_path)
        self.log.info("          To: %s", self.cache_path)
        copy_docs(html_files, self.cache_path)
        self.log.info("     END: Cache filled in")

        self.log.info("   START: Remove temporary directory: %s", self.tmpdir)
        shutil.rmtree(self.tmpdir)
        self.log.info("     END: Directory %s deleted successfully", self.tmpdir)

        self.log.info("KB4IT - Execution finished")
        self.log.info("Browse your documentation repository:")
        self.log.info("%s/index.html", os.path.abspath(self.target_path))

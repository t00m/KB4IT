#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module with the application logic.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: module holding the application logic
"""

import os
import sys
import glob
import shutil
import pprint
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
from kb4it.src.core.mod_utils import get_author_icon, last_dt_modification
from kb4it.src.services.srv_db import HEADER_KEYS

EOHMARK = """// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE"""


class Application(Service):
    """Missing class docstring (missing-docstring)."""
    runtime = {}
    kbdict_new = {}
    kbdict_cur = {}

    def initialize(self):
        """Initialize application structure"""

        # Get params from command line
        parameters = self.app.get_params()

        # Initialize directories
        self.runtime['dir'] = {}
        self.runtime['dir']['tmp'] = tempfile.mkdtemp(prefix=LPATH['TMP']+'/')
        if parameters.TARGET_PATH is None:
            self.runtime['dir']['target'] = LPATH['WWW']
        else:
            self.runtime['dir']['target'] = os.path.realpath(parameters.TARGET_PATH)
        self.runtime['dir']['source'] = os.path.realpath(parameters.SOURCE_PATH)
        self.runtime['dir']['cache'] = os.path.join(LPATH['CACHE'], valid_filename(self.runtime['dir']['source']))
        if not os.path.exists(self.runtime['dir']['cache']):
            os.makedirs(self.runtime['dir']['cache'])

        # Initialize docs structure
        self.runtime['docs'] = {}
        self.runtime['docs']['count'] = 0
        self.runtime['docs']['bag'] = []
        self.runtime['docs']['cached'] = []

        # Load cache dictionary and initialize the new one
        self.kbdict_cur = load_current_kbdict(self.runtime['dir']['source'])
        self.kbdict_new['document'] = {}
        self.kbdict_new['metadata'] = {}

        # Get services
        self.get_services()

    # ~ def get_cache_path(self):
        # ~ """Get cache path."""
        # ~ return self.runtime['dir']['cache']

    def get_source_path(self):
        """Get asciidoctor sources path."""
        return self.runtime['dir']['source']

    # ~ def get_target_path(self):
        # ~ """Get target path."""
        # ~ return self.runtime['dir']['target']

    def get_temp_dir(self):
        """Get temporary working path."""
        return self.runtime['dir']['tmp']

    def get_services(self):
        """Missing method docstring."""
        self.srvdtb = self.get_service('DB')
        self.srvbld = self.get_service('Builder')

    def get_numdocs(self):
        """Missing method docstring."""
        return self.runtime['docs']['count']


    def stage_1_check_environment(self):
        """Check environment."""
        self.log.info("Stage 1\tCheck environment")
        self.log.debug("\t\tCache directory: %s", self.runtime['dir']['cache'])
        self.log.debug("\t\tWorking directory: %s", self.runtime['dir']['tmp'])
        self.log.debug("\t\tSource directory: %s", self.runtime['dir']['source'])
        # check if target directory exists. If not, create it:
        if not os.path.exists(self.runtime['dir']['target']):
            os.makedirs(self.runtime['dir']['target'])
        self.log.debug("\t\tTarget directory: %s", self.runtime['dir']['target'])

        # Check if help and about documents exists. If not, use the default ones
        file_about = os.path.join(self.runtime['dir']['source'], 'about.adoc')
        file_help = os.path.join(self.runtime['dir']['source'], 'help.adoc')
        doc_about = os.path.exists(file_about)
        doc_help = os.path.exists(file_help)
        if not doc_about:
            tmp_about = os.path.join(self.runtime['dir']['tmp'], 'about.adoc')
            with open(tmp_about, 'w') as fabout:
                fabout.write(template('PAGE_ABOUT'))
                self.log.info("\t\tAdded missing 'about.adoc' document")

        if not doc_help:
            tmp_help = os.path.join(self.runtime['dir']['tmp'], 'help.adoc')
            with open(tmp_help, 'w') as fhelp:
                fhelp.write(template('PAGE_HELP'))
                self.log.info("\t\tAdded missing 'help.adoc' document")

    def stage_2_get_source_documents(self):
        """Get Asciidoctor source documents."""
        self.log.info("Stage 2\tGet Asciidoctor source documents")
        self.runtime['docs']['bag'] = get_source_docs(self.runtime['dir']['source'])
        self.runtime['docs']['count'] = len(self.runtime['docs']['bag'])
        if self.runtime['docs']['count'] == 0:
            self.log.error("\tNo asciidoctor files found in: %s", self.runtime['dir']['source'])
            self.log.error("\tExecution finished.")
            sys.exit()
        self.log.info("\t\tFound %d asciidoctor documents:", self.runtime['docs']['count'])
        for doc in self.runtime['docs']['bag']:
            self.log.debug("\t\t\t%s", doc)

    def stage_3_preprocessing(self):
        """
        Extract metadata from source docs into a dict.

        Create metadata section for each adoc and insert it after the
        EOHMARK.

        In this way, after being compiled into HTML, final adocs are
        browsable throught its metadata.
        """
        self.log.info("Stage 3\tPreprocessing")
        for source in self.runtime['docs']['bag']:
            docname = os.path.basename(source)
            self.kbdict_new['document'][docname] = {}
            self.log.debug("\t\tPreprocessing DOC[%s]", docname)

            # Add a new document to the database
            self.srvdtb.add_document(docname)

            # Get content
            with open(source) as source_adoc:
                srcadoc = source_adoc.read()

            # Get metadata
            docpath = os.path.join(self.runtime['dir']['source'], docname)
            keys = get_metadata(docpath)
            # To track changes in a document, hashes for metadata and content are created.
            # Comparing them with those in the cache, KB4IT determines if a document must be
            # compiled again. Very useful to reduce the compilation time.

            # Get Document Content and Metadata Hash
            self.kbdict_new['document'][docname]['content_hash'] = get_hash_from_dict({'content': srcadoc})
            self.kbdict_new['document'][docname]['metadata_hash'] = get_hash_from_dict(keys)
            self.kbdict_new['document'][docname]['timestamp'] = last_dt_modification(source).isoformat()
            cached_document = os.path.join(self.runtime['dir']['cache'], docname.replace('.adoc', '.html'))
            cached_document_exists = os.path.exists(cached_document)
            # Get documents per [key, value] and add them to kbdict
            for key in keys:
                alist = keys[key]
                for value in alist:
                    self.srvdtb.add_document_key(docname, key, value)
                    try:
                        documents = self.kbdict_new['metadata'][key][value]
                        documents.append(docname)
                        self.kbdict_new[key][value] = sorted(documents, key=lambda y: y.lower())
                    except KeyError:
                        if key not in self.kbdict_new['metadata']:
                            self.kbdict_new['metadata'][key] = {}
                        if value not in self.kbdict_new['metadata'][key]:
                            self.kbdict_new['metadata'][key][value] = [docname]

            # Compare the document with the one in the cache
            self.log.debug("\t\t\tDoes document %s exist in cache? %s", docname, cached_document_exists)
            if not cached_document_exists:
                FORCE_DOC_COMPILATION = True
            else:
                try:
                    # Compare timestamps for source/cache documents
                    doc_ts_new = self.kbdict_new['document'][docname]['timestamp']
                    doc_ts_cur = self.kbdict_cur['document'][docname]['timestamp']
                    if doc_ts_new > doc_ts_cur:
                        FORCE_DOC_COMPILATION = True
                    else:
                        FORCE_DOC_COMPILATION = False
                except KeyError:
                    FORCE_DOC_COMPILATION = True

            self.kbdict_new['document'][docname]['compile'] = FORCE_DOC_COMPILATION

            # Force compilation if document (content or metadata) has changed
            if FORCE_DOC_COMPILATION:
                # Create metadata section
                meta_section = self.srvbld.create_metadata_section(docname)

                # Replace EOHMARK with metadata section
                newadoc = srcadoc.replace(EOHMARK, meta_section, 1)

                # Write new adoc to temporary dir
                target = "%s/%s" % (self.runtime['dir']['tmp'], valid_filename(docname))
                with open(target, 'w') as target_adoc:
                    target_adoc.write(newadoc)
            else:
                filename = os.path.join(self.runtime['dir']['cache'], docname.replace('.adoc', '.html'))
                self.runtime['docs']['cached'].append(filename)

        # Save current status for the next run
        save_current_kbdict(self.kbdict_new, self.runtime['dir']['source'])

        self.log.info("\t\tPreprocessed %d docs", len(self.runtime['docs']['bag']))

    def stage_4_processing(self):
        """Process all documents."""
        self.log.info("Stage 4\tProcessing")
        # Get all available keys
        available_keys = self.srvdtb.get_all_keys()
        # Check if any of the core keys is missing
        missing = []
        for key in HEADER_KEYS:
            if key not in available_keys:
                self.log.debug("\t\tAdding missing key: %s", key)
                missing.append(key)
        available_keys.extend(missing)


        # Process
        for key in available_keys:
            self.log.debug("\t\t* Processing Key: %s", key)
            values = self.srvdtb.get_all_values_for_key(key)
            for value in values:
                self.log.debug("\t\t\tRelated documents for %s: %s", key, value)
                try:
                    FORCE_DOC_COMPILATION = False
                    filename = "%s_%s.adoc" % (valid_filename(key), valid_filename(value))
                    docname = os.path.join(self.runtime['dir']['tmp'], filename)
                    self.kbdict_new['document']
                    rel_docs = self.kbdict_new['metadata'][key][value]
                    for adoc in rel_docs:
                        self.log.debug("\t\t\t\t- Doc '%s'. Compile again? %s", adoc, self.kbdict_new['document'][adoc]['compile'])
                        FORCE_DOC_COMPILATION = FORCE_DOC_COMPILATION or self.kbdict_new['document'][adoc]['compile']
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
                    filename = os.path.join(self.runtime['dir']['cache'], docname)
                    self.runtime['docs']['cached'].append(filename)

                self.log.debug("\t\t\t\tForce compilation for %s: %s? %s", key, value, FORCE_DOC_COMPILATION)
            docname = "%s/%s.adoc" % (self.runtime['dir']['tmp'], valid_filename(key))
            html = self.srvbld.create_key_page(key, values)
            with open(docname, 'w') as fkey:
                fkey.write(html)

        self.srvbld.create_all_keys_page()
        self.srvbld.create_index_all()
        self.srvbld.create_index_page()

    def stage_5_compilation(self):
        """Compile documents to html with asciidoctor."""
        self.log.info("Stage 5\tCompilation")
        dcomps = datetime.datetime.now()

        # copy online resources to target path
        resources_dir_source = GPATH['ONLINE']
        resources_dir_tmp = os.path.join(self.runtime['dir']['tmp'], 'resources')
        shutil.copytree(resources_dir_source, resources_dir_tmp)

        adocprops = ''
        for prop in ADOCPROPS:
            if ADOCPROPS[prop] is not None:
                if '%s' in ADOCPROPS[prop]:
                    adocprops += '-a %s=%s ' % (prop, ADOCPROPS[prop] % self.runtime['dir']['target'])
                else:
                    adocprops += '-a %s=%s ' % (prop, ADOCPROPS[prop])
            else:
                adocprops += '-a %s ' % prop
        self.log.debug("\t\tParameters passed to Asciidoctor: %s", adocprops)

        with Executor(max_workers=MAX_WORKERS) as exe:
            docs = get_source_docs(self.runtime['dir']['tmp'])
            jobs = []
            jobcount = 0
            num = 1
            self.log.debug("\t\tGenerating jobs. Please, wait")
            for doc in docs:
                cmd = "asciidoctor -s %s -b html5 -D %s %s" % (adocprops, self.runtime['dir']['tmp'], doc)
                job = exe.submit(exec_cmd, (doc, cmd, num))
                job.add_done_callback(job_done)
                self.log.debug("\t\tJob[%4d]: %s will be compiled", num, os.path.basename(doc))
                # ~ self.log.debug("\t\tJob[%4d]: %s", num, cmd)
                jobs.append(job)
                num = num + 1
            self.log.debug("\t\t%d jobs created. Starting compilation", num - 1)
            self.log.info("\t\t0% done")
            for job in jobs:
                adoc, res, jobid = job.result()
                self.log.debug("\t\tJob[%d/%d]:\t%s compiled successfully", jobid, num - 1, os.path.basename(adoc))
                jobcount += 1
                if jobcount % MAX_WORKERS == 0:
                    pct = int(jobcount * 100 / len(docs))
                    self.log.info("\t\t%3s%% done", str(pct))

        dcompe = datetime.datetime.now()
        totaldocs = len(get_source_docs(self.runtime['dir']['tmp']))
        comptime = dcompe - dcomps
        self.log.info("\t\t100% done")
        self.log.info("\t\tCompilation time: %d seconds", comptime.seconds)
        self.log.info("\t\tNumber of compiled docs: %d", totaldocs)
        try:
            self.log.info("\t\tCompilation Avg. Speed: %d docs/sec",
                          int((totaldocs/comptime.seconds)))
        except ZeroDivisionError:
            self.log.info("\t\tCompilation Avg. Speed: %d docs/sec",
                          int((totaldocs/1)))

    def stage_6_clean_target(self):
        """Delete contents of target directory (if any)."""
        self.log.info("Stage 6\tClean target directory")
        delete_target_contents(self.runtime['dir']['target'])
        self.log.info("\t\tDeleted target contents in: %s", self.runtime['dir']['target'])

    def stage_7_refresh_target(self):
        """Refresh target directory."""
        self.log.info("Stage 7\tRefresh target directory")
        # Copy compiled documents to target path
        pattern = os.path.join(self.runtime['dir']['source'], '*.adoc')
        files = glob.glob(pattern)
        copy_docs(files, self.runtime['dir']['target'])
        self.log.info("\t\tCopy %d asciidoctor sources from source path to target Path", len(files))

        pattern = os.path.join(self.runtime['dir']['tmp'], '*.html')
        files = glob.glob(pattern)
        copy_docs(files, self.runtime['dir']['target'])
        self.log.info("\t\tCopy %d html files from temporary path to target path", len(files))

        copy_docs(self.runtime['docs']['cached'], self.runtime['dir']['target'])
        self.log.info("\t\tCopied %d cached documents successfully to target path", len(self.runtime['docs']['cached']))

        copy_docs(self.runtime['docs']['bag'], self.runtime['dir']['target'])
        self.log.info("\t\tCopied %d Asciidoctor source docs copied to target path", len(self.runtime['docs']['bag']))

        source_resources_dir = os.path.join(self.runtime['dir']['source'], 'resources')
        if os.path.exists(source_resources_dir):
            resources_dir_target = os.path.join(self.runtime['dir']['target'], 'resources')
            copydir(source_resources_dir, resources_dir_target)
            self.log.info("\t\tCopied local resources to target path")

        global_resources_dir = GPATH['ONLINE']
        resources_dir_target = os.path.join(self.runtime['dir']['target'], 'resources')
        copydir(global_resources_dir, resources_dir_target)
        self.log.info("\t\tCopied global resources to target path")

        pattern = os.path.join(self.runtime['dir']['target'], '*.html')
        html_files = glob.glob(pattern)
        copy_docs(html_files, self.runtime['dir']['cache'])
        self.log.info("\t\tCopying HTML files to cache...")

    def stage_8_remove_temporary_dir(self):
        """Remove temporary dir."""
        self.log.info("Stage 8\tRemove temporary directory")
        shutil.rmtree(self.runtime['dir']['tmp'])
        self.log.info("\t\tTemporary directory %s deleted successfully", self.runtime['dir']['tmp'])

    def stage_9_print_missing_icons(self):
        """Print list of missing icons."""
        self.log.info("Stage 9\tMissing icons report")
        missing_icons = self.srvbld.get_missing_icons()
        if len(missing_icons) > 0:
            self.log.warning("\t\tThe following author icons are missing:")
            for author in missing_icons:
                self.log.warning("\t\t%s: %s", author, missing_icons[author])
        else:
            self.log.warning("\t\tNo missing icons.")

    def run(self):
        """Start script execution following this flow.

        1. Check environment
        2. Get source documents
        3. Preprocess documents (get metadata)
        4. Process documents in a temporary dir
        5. Compile documents to html with asciidoctor
        6. Delete contents of target directory (if any)
        7. Refresh target directory
        8. Remove temporary directory
        """
        self.log.info("KB4IT - Knowledge Base for IT")

        self.stage_1_check_environment()
        self.stage_2_get_source_documents()
        self.stage_3_preprocessing()
        self.stage_4_processing()
        self.stage_5_compilation()
        self.stage_6_clean_target()
        self.stage_7_refresh_target()
        self.stage_8_remove_temporary_dir()
        self.stage_9_print_missing_icons()

        self.log.info("KB4IT - Execution finished")
        self.log.info("Browse your documentation repository:")
        self.log.info("%s/index.html", os.path.abspath(self.runtime['dir']['target']))
        # ~ pprint.pprint(self.runtime)

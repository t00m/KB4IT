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
import time
import json
import random
import threading
import shutil
import tempfile
import datetime
import operator
from concurrent.futures import ThreadPoolExecutor as Executor
from kb4it.src.core.mod_env import LPATH, GPATH, APP, ADOCPROPS, MAX_WORKERS, EOHMARK
from kb4it.src.core.mod_srv import Service
from kb4it.src.core.mod_utils import get_human_datetime
from kb4it.src.core.mod_utils import extract_toc, valid_filename, load_current_kbdict
from kb4it.src.core.mod_utils import exec_cmd, delete_target_contents
from kb4it.src.core.mod_utils import get_source_docs, get_asciidoctor_attributes, get_hash_from_dict
from kb4it.src.core.mod_utils import save_current_kbdict, copy_docs, copydir
from kb4it.src.core.mod_utils import file_timestamp
from kb4it.src.core.mod_utils import guess_datetime, string_timestamp


class Application(Service):
    """C0111: Missing function docstring (missing-docstring)."""
    runtime = {} # Dictionary of runtime properties
    kbdict_new = {} # New compilation cache
    kbdict_cur = {} # Cached data

    def initialize(self):
        """Initialize application structure"""

        # Get params from command line
        self.parameters = self.app.get_params()
        self.log.debug(self.app.get_params())

        # Initialize directories
        self.runtime['dir'] = {}
        self.runtime['dir']['tmp'] = tempfile.mkdtemp(prefix=LPATH['TMP']+'/')
        if self.parameters.TARGET_PATH is None:
            self.runtime['dir']['target'] = LPATH['WWW']
        else:
            self.runtime['dir']['target'] = os.path.realpath(self.parameters.TARGET_PATH)
        self.runtime['dir']['source'] = os.path.realpath(self.parameters.SOURCE_PATH)
        self.runtime['dir']['cache'] = os.path.join(LPATH['CACHE'], valid_filename(self.runtime['dir']['source']))
        if not os.path.exists(self.runtime['dir']['cache']):
            os.makedirs(self.runtime['dir']['cache'])

        # if SORT attribute is given, use it instead of the OS timestamp
        if self.parameters.SORT_ATTRIBUTE is None:
            self.runtime['sort_attribute'] = 'Timestamp'
        else:
            self.runtime['sort_attribute'] = self.parameters.SORT_ATTRIBUTE
        self.log.info("Sort attribute: %s", self.runtime['sort_attribute'])

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

        # Select theme
        self.theme_load()

    def theme_load(self):
        """Load custom user theme, global theme or default."""

        # custom theme requested by user via command line properties
        self.runtime['theme'] =  {}
        self.runtime['theme']['path'] = self.theme_search(self.parameters.THEME)
        if self.runtime['theme']['path'] is None:
            self.runtime['theme']['path'] = os.path.join(GPATH['THEMES'], 'default')
            self.log.warning("Fallback to default theme")

        theme_conf = os.path.join(self.runtime['theme']['path'], "theme.adoc")
        if not os.path.exists(theme_conf):
            self.log.error("Theme config file not found: %s", theme_conf)
            sys.exit(-1)

        # load theme configuration
        with open(theme_conf, 'r') as fth:
            theme = json.load(fth)
            for prop in theme:
                self.runtime['theme'][prop] = theme[prop]

        self.log.debug("Theme: %s", theme['name'])
        for prop in theme:
            if prop != 'name':
                self.log.debug("\t%s: %s", prop.title(), theme[prop])

        # Get theme directories
        self.runtime['theme']['templates'] = os.path.join(self.runtime['theme']['path'], 'templates')
        self.runtime['theme']['logic'] = os.path.join(self.runtime['theme']['path'], 'logic')

        # Get date-based attributes from theme. Date attributes aren't
        # displayed as properties but used to build events pages.
        try:
            ignored_keys = self.runtime['theme']['ignored_keys']
            for key in ignored_keys:
                self.log.debug("\tIgnoring key: %s", key)
                self.srvdtb.ignore_key(key)
        except KeyError:
            self.log.warning("No ignored_keys defined in this theme")

        # Register theme service
        sys.path.insert(0, self.runtime['theme']['logic'])
        try:
            from theme import Theme
            self.app.register_service('Theme', Theme())
            self.srvthm = self.get_service('Theme')
        except Exception as error:
            self.log.warning("Theme scripts for '%s' couldn't be loaded", self.runtime['theme']['id'])
            self.log.error(error)
            raise
        self.log.info("Loaded theme '%s': %s", self.runtime['theme']['id'], self.runtime['theme']['path'])

    def theme_search(self, theme):
        """Search custom theme"""

        if theme is None:
            # No custom theme passed in arguments. Autodetect.
            self.log.debug("Autodetecting theme from source path")
            source_path = self.runtime['dir']['source']
            source_resources_path = os.path.join(source_path, 'resources')
            source_themes_path = os.path.join(source_resources_path, 'themes')
            all_themes = os.path.join(source_themes_path, '*')
            self.log.debug("Looking for first theme ocurrence in: %s", all_themes)
            try:
                theme_path = glob.glob(all_themes)[0]
                self.log.debug("Found theme path: %s", theme_path)
                return theme_path
            except:
                theme_path = None
                self.log.debug("Theme not found", theme_path)
                return None

        found = False

        # Search in sources path
        source_path = self.runtime['dir']['source']
        theme_rel_path = os.path.join(os.path.join('resources', 'themes'), theme)
        theme_path = os.path.join(self.runtime['dir']['source'], theme_rel_path)
        if os.path.exists(theme_path):
            found = True
        else:
            # Search for theme in KB4IT global theme
            theme_path = os.path.join(GPATH['THEMES'], theme)
            if os.path.exists(theme_path):
                found = True

        if found:
            # Return custom theme
            self.log.debug("Found theme %s in local repository: %s" % (theme, theme_path))
            return theme_path
        else:
            # Fallback to default
            self.log.debug("Theme not found in local repository: %s." % theme)
            return None

    def get_runtime_properties(self):
        return self.runtime

    def get_runtime_parameter(self, parameter):
        return self.runtime[parameter]

    def get_theme_properties(self):
        return self.runtime['theme']

    def get_theme_property(self, prop):
        return self.runtime['theme'][prop]

    def get_source_path(self):
        """Get asciidoctor sources path."""
        return self.runtime['dir']['source']

    def get_target_path(self):
        """Get target path."""
        return self.runtime['dir']['target']

    def get_temp_path(self):
        """Get temporary working path."""
        return self.runtime['dir']['tmp']

    def get_services(self):
        """C0111: Missing function docstring (missing-docstring)."""
        self.srvdtb = self.get_service('DB')
        self.srvbld = self.get_service('Builder')

    def get_numdocs(self):
        """C0111: Missing function docstring (missing-docstring)."""
        return self.runtime['docs']['count']

    def highlight_metadata_section(self, source):
        """C0111: Missing function docstring (missing-docstring)."""
        content = source.replace(self.srvbld.template('HTML_TAG_METADATA_OLD'), self.srvbld.template('HTML_TAG_METADATA_NEW'), 1)
        return content

    def apply_transformations(self, source):
        """C0111: Missing function docstring (missing-docstring)."""
        content = source.replace(self.srvbld.template('HTML_TAG_TOC_OLD'), self.srvbld.template('HTML_TAG_TOC_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_SECT1_OLD'), self.srvbld.template('HTML_TAG_SECT1_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_SECT2_OLD'), self.srvbld.template('HTML_TAG_SECT2_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_SECT3_OLD'), self.srvbld.template('HTML_TAG_SECT3_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_SECT4_OLD'), self.srvbld.template('HTML_TAG_SECT4_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_SECTIONBODY_OLD'), self.srvbld.template('HTML_TAG_SECTIONBODY_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_PRE_OLD'), self.srvbld.template('HTML_TAG_PRE_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_H2_OLD'), self.srvbld.template('HTML_TAG_H2_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_H3_OLD'), self.srvbld.template('HTML_TAG_H3_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_H4_OLD'), self.srvbld.template('HTML_TAG_H4_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_TABLE_OLD'), self.srvbld.template('HTML_TAG_TABLE_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_TABLE_OLD_2'), self.srvbld.template('HTML_TAG_TABLE_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_ADMONITION_ICON_NOTE_OLD'), self.srvbld.template('HTML_TAG_ADMONITION_ICON_NOTE_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_ADMONITION_ICON_TIP_OLD'), self.srvbld.template('HTML_TAG_ADMONITION_ICON_TIP_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_ADMONITION_ICON_IMPORTANT_OLD'), self.srvbld.template('HTML_TAG_ADMONITION_ICON_IMPORTANT_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_ADMONITION_ICON_CAUTION_OLD'), self.srvbld.template('HTML_TAG_ADMONITION_ICON_CAUTION_NEW'))
        content = content.replace(self.srvbld.template('HTML_TAG_ADMONITION_ICON_WARNING_OLD'), self.srvbld.template('HTML_TAG_ADMONITION_ICON_WARNING_NEW'))
        return content

    def stage_01_check_environment(self):
        """Check environment."""
        self.log.info("Stage 1\tCheck environment")
        self.log.info("\t\tCache directory: %s", self.runtime['dir']['cache'])
        self.log.info("\t\tWorking directory: %s", self.runtime['dir']['tmp'])
        self.log.info("\t\tSource directory: %s", self.runtime['dir']['source'])
        self.log.info("\t\tTheme: %s (%s)", self.runtime['theme']['id'], self.runtime['theme']['name'])
        # check if target directory exists. If not, create it:
        if not os.path.exists(self.runtime['dir']['target']):
            os.makedirs(self.runtime['dir']['target'])
        self.log.debug("\t\tTarget directory: %s", self.runtime['dir']['target'])

    def stage_02_get_source_documents(self):
        """Get Asciidoctor source documents."""
        self.log.info("Stage 2\tGet Asciidoctor source documents")
        self.runtime['docs']['bag'] = get_source_docs(self.runtime['dir']['source'])
        self.runtime['docs']['count'] = len(self.runtime['docs']['bag'])
        if self.runtime['docs']['count'] == 0:
            themeid = self.get_theme_property('id')
            if themeid == 'default':
                self.log.error("\tNo asciidoctor files found in: %s", self.runtime['dir']['source'])
                self.log.error("\tExecution finished.")
                sys.exit()
            else:
                self.log.warning("No source files found.")
        self.log.info("\t\tFound %d asciidoctor documents", self.runtime['docs']['count'])
        for doc in self.runtime['docs']['bag']:
            self.log.debug("\t\t\t%s", doc)

    def stage_03_preprocessing(self):
        """
        Extract metadata from source docs into a dict.

        Create metadata section for each adoc and insert it after the
        EOHMARK.

        In this way, after being compiled into HTML, final adocs are
        browsable throught its metadata.
        """
        self.log.info("Stage 3\tPreprocessing")
        tsdict = {}
        for source in self.runtime['docs']['bag']:
            docname = os.path.basename(source)
            self.kbdict_new['document'][docname] = {}
            self.log.debug("\t\tPreprocessing DOC[%s]", docname)

            # Add a new document to the database
            self.srvdtb.add_document(docname)

            # Get datetime timestamp from filesystem and add it as
            # attribute
            timestamp = file_timestamp(source)
            self.srvdtb.add_document_key(docname, 'Timestamp', timestamp)

            # Get content
            with open(source) as source_adoc:
                srcadoc = source_adoc.read()

            # Get metadata
            docpath = os.path.join(self.runtime['dir']['source'], docname)
            keys = get_asciidoctor_attributes(docpath)

            # To track changes in a document, hashes for metadata and content are created.
            # Comparing them with those in the cache, KB4IT determines if a document must be
            # compiled again. Very useful to reduce the compilation time.

            # Get Document Content and Metadata Hashes
            self.kbdict_new['document'][docname]['content_hash'] = get_hash_from_dict({'content': srcadoc})
            self.kbdict_new['document'][docname]['metadata_hash'] = get_hash_from_dict(keys)
            self.kbdict_new['document'][docname]['Timestamp'] = timestamp

            # Generate caches
            for key in keys:
                alist = keys[key]
                for value in alist:
                    nc = len(value.strip())
                    if nc == 0:
                        continue
                    try:
                        if key in self.runtime['theme']['date_attributes']:
                            value = string_timestamp(value)
                    except:
                        pass

                    if key == 'Tag':
                        value = value.lower()
                    self.srvdtb.add_document_key(docname, key, value)

                    # For each document and for each key/value linked to that document add an entry to kbdic['document']
                    try:
                        values = self.kbdict_new['document'][docname][key]
                        if value not in values:
                            values.append(value)
                        self.kbdict_new['document'][docname][key] = sorted(values)
                    except:
                        self.kbdict_new['document'][docname][key] = [value]

                    # And viceversa, for each key/value add to kbdict['metadata'] all documents linked
                    try:
                        documents = self.kbdict_new['metadata'][key][value]
                        documents.append(docname)
                        self.kbdict_new[key][value] = sorted(documents, key=lambda y: y.lower())
                    except KeyError:
                        if key not in self.kbdict_new['metadata']:
                            self.kbdict_new['metadata'][key] = {}
                        if value not in self.kbdict_new['metadata'][key]:
                            self.kbdict_new['metadata'][key][value] = [docname]

            # Get cached document path and check if it exists
            cached_document = os.path.join(self.runtime['dir']['cache'], docname.replace('.adoc', '.html'))
            cached_document_exists = os.path.exists(cached_document)

            # Compare the document with the one in the cache
            self.log.debug("\t\t\tDoes document %s exist in cache? %s", docname, cached_document_exists)

            if not cached_document_exists:
                FORCE_DOC_COMPILATION = True
            else:
                try:
                    # Compare timestamps for each source/cached document.
                    #If timestamp differs, compile it again.
                    SORT_ATTRIBUTE = self.runtime['sort_attribute']
                    try:
                        doc_ts_new = guess_datetime(self.kbdict_new['document'][docname][SORT_ATTRIBUTE])
                    except:
                        doc_ts_new = guess_datetime(self.kbdict_new['document'][docname]['Timestamp'])

                    try:
                        doc_ts_cur = guess_datetime(self.kbdict_cur['document'][docname][SORT_ATTRIBUTE])
                    except:
                        doc_ts_cur = guess_datetime(self.kbdict_cur['document'][docname]['Timestamp'])

                    if doc_ts_new > doc_ts_cur:
                        FORCE_DOC_COMPILATION = True
                    else:
                        FORCE_DOC_COMPILATION = False
                except KeyError:
                    FORCE_DOC_COMPILATION = True

            # Save compilation status
            self.kbdict_new['document'][docname]['compile'] = FORCE_DOC_COMPILATION

            # Force compilation (from command line)?
            if self.parameters.FORCE == True:
                FORCE_ALL = True
            else:
                FORCE_ALL = False

            if FORCE_DOC_COMPILATION or FORCE_ALL:
                newadoc = srcadoc.replace(EOHMARK, '', 1)

                # Write new adoc to temporary dir
                target = "%s/%s" % (self.runtime['dir']['tmp'], valid_filename(docname))
                self.log.debug("\t\t\tDocument %s will be compiled again" % valid_filename(docname))
                with open(target, 'w') as target_adoc:
                    target_adoc.write(newadoc)
            else:
                filename = os.path.join(self.runtime['dir']['cache'], docname.replace('.adoc', '.html'))
                self.runtime['docs']['cached'].append(filename)
                self.log.debug("\t\t\tDocument %s is cached. It won't be compiled." % valid_filename(docname))

        # Save current status for the next run
        save_current_kbdict(self.kbdict_new, self.runtime['dir']['source'])

        # Build a list of documents sorted by timestamp
        self.srvdtb.sort_database()
        self.log.info("\t\tPreprocessed %d docs", len(self.runtime['docs']['bag']))


    def stage_04_processing(self):
        """Process all documents."""
        self.log.info("Stage 4\tProcessing keys")
        all_keys = set(self.srvdtb.get_all_keys())
        ign_keys = set(self.srvdtb.get_ignored_keys())
        available_keys = list(all_keys - ign_keys)

        for key in available_keys:
            FORCE_DOC_KEY_COMPILATION = False
            FORCE_DOC_COMPILATION = False
            values = self.srvdtb.get_all_values_for_key(key)
            for value in values:
                FORCE_DOC_COMPILATION = False # Missing flag fix issue #48!!!
                try:
                    related_docs_new = self.kbdict_new['metadata'][key][value]
                except:
                    related_docs_new = []

                try:
                    related_docs_cur = self.kbdict_new['metadata'][key][value]
                except:
                    related_docs_cur = []

                if related_docs_new != related_docs_cur:
                    FORCE_DOC_KEY_COMPILATION = True

                FORCE_DOC_COMPILATION = FORCE_DOC_COMPILATION or FORCE_DOC_KEY_COMPILATION

                try:
                    for adoc in related_docs_new:
                        FORCE_DOC_COMPILATION = FORCE_DOC_COMPILATION or self.kbdict_new['document'][adoc]['compile']
                except KeyError:
                    FORCE_DOC_COMPILATION = True

                if self.parameters.FORCE == True:
                    FORCE_ALL = True
                else:
                    FORCE_ALL = False

                COMPILE_AGAIN = FORCE_DOC_COMPILATION or FORCE_ALL
                if COMPILE_AGAIN:
                    # Create .adoc from value
                    sorted_docs = self.srvdtb.sort_by_date(related_docs_new)
                    basename = "%s_%s" % (valid_filename(key), valid_filename(value))
                    self.srvthm.build_pagination(basename, sorted_docs)
                else:
                    docname = "%s_%s.html" % (valid_filename(key), valid_filename(value))
                    filename = os.path.join(self.runtime['dir']['cache'], docname)
                    self.runtime['docs']['cached'].append(filename)

                FORCE_DOC_KEY_COMPILATION = FORCE_DOC_KEY_COMPILATION or COMPILE_AGAIN
            self.log.debug("\t\t\t* Key: %s - Compile? %s", key, FORCE_DOC_KEY_COMPILATION)

            #FIXME: Force key compilation
            FORCE_DOC_KEY_COMPILATION = True
            if FORCE_DOC_KEY_COMPILATION:
                docname = "%s/%s.adoc" % (self.runtime['dir']['tmp'], valid_filename(key))
                html = self.srvthm.create_page_key(key, values)
                with open(docname, 'w') as fkey:
                    fkey.write(html)

        self.srvthm.build()

    def stage_05_compilation(self):
        """Compile documents to html with asciidoctor."""
        self.log.info("Stage 5\tCompilation")
        dcomps = datetime.datetime.now()

        # copy online resources to target path
        # ~ resources_dir_source = GPATH['THEMES']
        resources_dir_tmp = os.path.join(self.runtime['dir']['tmp'], 'resources')
        shutil.copytree(GPATH['RESOURCES'], resources_dir_tmp)
        self.log.debug("\t\tResources copied to '%s'", resources_dir_tmp)

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
                cmd = "asciidoctor -q -s %s -b html5 -D %s %s" % (adocprops, self.runtime['dir']['tmp'], doc)
                job = exe.submit(exec_cmd, (doc, cmd, num))
                job.add_done_callback(self.srvthm.build_page)
                self.log.debug("\t\tJob[%4d]: %s will be compiled", num, os.path.basename(doc))
                # ~ self.log.debug("\t\tJob[%4d]: %s", num, cmd)
                jobs.append(job)
                num = num + 1
            self.log.info("\t\tCreated %d jobs. Starting compilation", num - 1)
            # ~ self.log.info("\t\t%3s%% done", "0")
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

    def stage_06_extras(self):
        """Include other stuff."""
        pass

    def stage_07_clean_target(self):
        """Delete contents of target directory (if any)."""
        self.log.info("Stage 6\tClean target directory")
        delete_target_contents(self.runtime['dir']['target'])
        self.log.info("\t\tDeleted target contents in: %s", self.runtime['dir']['target'])

    def stage_08_refresh_target(self):
        """Refresh target directory."""
        self.log.info("Stage 7\tRefresh target directory")

        # Copy asciidocs documents to target path
        pattern = os.path.join(self.runtime['dir']['source'], '*.adoc')
        files = glob.glob(pattern)
        docsdir = os.path.join(self.runtime['dir']['target'], 'sources')
        os.makedirs(docsdir)
        copy_docs(files, docsdir)
        self.log.info("\t\tCopy %d asciidoctor sources from source path to target path", len(files))

        # Copy compiled documents to target path
        pattern = os.path.join(self.runtime['dir']['tmp'], '*.html')
        files = glob.glob(pattern)
        copy_docs(files, self.runtime['dir']['target'])
        self.log.info("\t\tCopy %d html files from temporary path to target path", len(files))

        # Copy cached documents to target path
        copy_docs(self.runtime['docs']['cached'], self.runtime['dir']['target'])
        self.log.info("\t\tCopied %d cached documents successfully to target path", len(self.runtime['docs']['cached']))

        # ???
        # ~ copy_docs(self.runtime['docs']['bag'], self.runtime['dir']['target'])
        # ~ self.log.info("\t\tCopied %d Asciidoctor source docs copied to target path", len(self.runtime['docs']['bag']))

        # Copy global resources to target path
        # FIXME: copy common resources, default theme and choosen theme
        resources_dir_target = os.path.join(self.runtime['dir']['target'], 'resources')
        global_resources_dir = GPATH['RESOURCES']
        # ~ COMMON_RES_DIR = os.path.join(global_resources_dir, 'common')
        theme_target_dir = os.path.join(resources_dir_target, 'themes')
        theme = self.get_theme_properties()
        DEFAULT_THEME = os.path.join(GPATH['THEMES'], 'default')
        CUSTOM_THEME_ID = theme['id']
        CUSTOM_THEME_PATH = theme['path']
        copydir(DEFAULT_THEME, os.path.join(theme_target_dir, 'default'))
        copydir(CUSTOM_THEME_PATH, os.path.join(theme_target_dir, CUSTOM_THEME_ID))
        copydir(GPATH['COMMON'], os.path.join(resources_dir_target, 'common'))
        self.log.info("\t\tCopied global resources to target path")

        # Copy local resources to target path
        source_resources_dir = os.path.join(self.runtime['dir']['source'], 'resources')
        if os.path.exists(source_resources_dir):
            resources_dir_target = os.path.join(self.runtime['dir']['target'], 'resources')
            copydir(source_resources_dir, resources_dir_target)
            self.log.info("\t\tCopied local resources to target path")

        # Copy back all HTML files from target to cache
        # Fixme: should cache contents be deleted before copying?
        pattern = os.path.join(self.runtime['dir']['target'], '*.html')
        html_files = glob.glob(pattern)
        copy_docs(html_files, self.runtime['dir']['cache'])
        self.log.info("\t\tCopying HTML files to cache...")

        # Copy JSON database to target path so it can be queried from others applications
        save_current_kbdict(self.kbdict_new, self.runtime['dir']['target'], 'kb4it')
        self.log.info("\t\tCopied JSON database to target")

    def stage_09_remove_temporary_dir(self):
        """Remove temporary dir."""
        self.log.info("Stage 8\tRemove temporary directory")
        shutil.rmtree(self.runtime['dir']['tmp'])
        self.log.info("\t\tTemporary directory %s deleted successfully", self.runtime['dir']['tmp'])


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

        self.stage_01_check_environment()
        self.srvthm.generate_sources()
        self.stage_02_get_source_documents()
        self.stage_03_preprocessing()
        self.stage_04_processing()
        self.stage_05_compilation()
        self.stage_06_extras()
        self.stage_07_clean_target()
        self.stage_08_refresh_target()
        self.stage_09_remove_temporary_dir()

        self.log.info("KB4IT - Execution finished")
        self.log.info("Browse your documentation repository:")
        self.log.info("sensible-browser %s/index.html", os.path.abspath(self.runtime['dir']['target']))


#!/usr/bin/env python
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Cleaner service
"""

import os
import glob
import shutil

from kb4it.core.env import ENV
from kb4it.core.service import Service
from kb4it.core.util import copy_docs, copydir
from kb4it.core.util import exec_cmd, delete_target_contents

class Deployer(Service):
    """KB4IT Cleaner Service"""

    def _initialize(self):
        """Initialize workflow module."""
        self.srvbes = self.app.get_service('Backend')
        self.log.debug(f"[DEPLOYER] - START")

    def execute(self):
        self.step_00_copy_source_to_cache()
        self.step_01_delete_temporary_target_contents()
        self.step_02_copy_temporary_files_to_distributed_directory()
        self.step_03_clear_target()
        self.step_04_copy_sources_to_target()
        self.step_05_copy_compiled_to_cache()
        self.step_06_copy_all_to_cache()
        self.step_07_copy_compiled_documents_to_target()
        self.step_08_copy_global_resources_to_target()
        self.step_09_copy_html_to_cache()
        self.step_10_copy_kbdict_to_target()

    def step_00_copy_source_to_cache(self):
        pattern = os.path.join(self.srvbes.get_path('source'), '*.*')
        extra = glob.glob(pattern)
        copy_docs(extra, self.srvbes.get_path('cache'))

    def step_01_delete_temporary_target_contents(self):
        delete_target_contents(self.srvbes.get_path('dist'))
        self.log.debug(f"Distributed files deleted")

    def step_02_copy_temporary_files_to_distributed_directory(self):
        distributed = self.srvbes.get_value('docs', 'targets')
        for adoc in distributed:
            source = os.path.join(self.srvbes.get_path('tmp'), adoc)
            target = self.srvbes.get_path('www')
            try:
                shutil.copy(source, target)
            except Exception as warning:
                # FIXME
                # ~ self.log.warning(warning)
                # ~ self.log.warning("[CLEANUP] - Missing source file: %s", source)
                pass
        self.log.debug(f"Copy temporary files to distributed directory")

    def step_03_clear_target(self):
        delete_target_contents(self.srvbes.get_path('target'))
        self.log.debug(f"Deleted target contents in: %s", self.srvbes.get_path('target'))

    # Refresh target
    def step_04_copy_sources_to_target(self):
        # Copy asciidocs documents to target/sources
        pattern = os.path.join(self.srvbes.get_path('source'), '*.adoc')
        files = glob.glob(pattern)
        docsdir = os.path.join(self.srvbes.get_path('target'), 'sources')
        os.makedirs(docsdir, exist_ok=True)
        copy_docs(files, docsdir)
        self.log.debug(f"STATS - Copied {len(files)} asciidoctor sources to target path")

    def step_05_copy_compiled_to_cache(self):
        # Copy compiled documents to cache path
        pattern = os.path.join(self.srvbes.get_path('tmp'), '*.html')
        files = glob.glob(pattern)
        copy_docs(files, self.srvbes.get_path('cache'))
        self.log.debug(f"STATS - Copied {len(files)} html files from temporary path to cache path")

    def step_06_copy_all_to_cache(self):
        # Copy objects in temporary target to cache path
        pattern = os.path.join(self.srvbes.get_path('tmp'), '*.*')
        files = glob.glob(pattern)
        copy_docs(files, self.srvbes.get_path('cache'))
        self.log.debug(f"STATS - Copied {len(files)} html files from temporary target to cache path")

    def step_07_copy_compiled_documents_to_target(self):
        runtime = self.srvbes.get_dict('runtime')
        # Copy cached documents to target path
        n = 0
        for filename in sorted(runtime['docs']['targets']):
            source = os.path.join(self.srvbes.get_path('cache'), filename)
            target = os.path.join(self.srvbes.get_path('target'), filename)
            try:
                shutil.copy(source, target)
            except FileNotFoundError as error:
                self.log.error(error)
                self.log.error("Consider to run the command again with the option -force")
                self.app.stop()
            n += 1
        self.log.debug(f"STATS - Copied {n} cached documents successfully to target path")

    def step_08_copy_global_resources_to_target(self):
        # Copy global resources to target path
        resources_dir_target = os.path.join(self.srvbes.get_path('target'), 'resources')
        theme_target_dir = os.path.join(resources_dir_target, 'themes')
        theme = self.srvbes.get_dict('theme')
        DEFAULT_THEME = os.path.join(ENV['GPATH']['THEMES'], 'default')
        CUSTOM_THEME_ID = theme['id']
        CUSTOM_THEME_PATH = theme['path']
        copydir(DEFAULT_THEME, os.path.join(theme_target_dir, 'default'))
        copydir(CUSTOM_THEME_PATH, os.path.join(theme_target_dir, CUSTOM_THEME_ID))
        copydir(ENV['GPATH']['COMMON'], os.path.join(resources_dir_target, 'common'))
        self.log.debug("STATS - Copied global resources to target path")

        # Copy local resources to target path
        source_resources_dir = os.path.join(self.srvbes.get_path('source'), 'resources')
        if os.path.exists(source_resources_dir):
            resources_dir_target = os.path.join(self.srvbes.get_path('target'), 'resources')
            copydir(source_resources_dir, resources_dir_target)
            self.log.debug(f"Copied local resources to target path")

    def step_09_copy_html_to_cache(self):
        # Copy back all HTML files from target to cache
        delete_target_contents(self.srvbes.get_path('cache'))
        pattern = os.path.join(self.srvbes.get_path('target'), '*.html')
        html_files = glob.glob(pattern)
        copy_docs(html_files, self.srvbes.get_path('cache'))
        self.log.debug("Copying HTML files back to cache...")

    def step_10_copy_kbdict_to_target(self):
        # Copy JSON database to target path so it can be queried from
        # others applications
        # ~ self.save_kbdict(self.kbdict_new, self.srvbes.get_path('target'), 'kb4it')
        # ~ self.log.debug("Copied JSON database to target")
        pass

    def _finalize(self):
        self.log.debug(f"[DEPLOYER] - END")

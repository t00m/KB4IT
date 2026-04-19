#!/usr/bin/env python

"""
Service Deployer.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

import glob
import os
import shutil

from kb4it.core.env import ENV
from kb4it.core.service import Service
from kb4it.core.util import copy_docs, copydir, delete_target_contents


class Deployer(Service):
    """KB4IT Deployer Service."""

    def _initialize(self):
        """Initialize deployer service."""
        self.srvbes = self.app.get_service("Backend")

    def execute(self):
        """Deploy website build by KB4IT."""
        self.log.debug("[DEPLOYER] START")
        self.log.debug("[DEPLOYER] DEPLOY_BEGIN")

        source_files = glob.glob(os.path.join(self.srvbes.get_path("source"), "*.*"))
        source_adocs = [f for f in source_files if f.endswith(".adoc")]
        tmp_files = glob.glob(os.path.join(self.srvbes.get_path("tmp"), "*.*"))

        self.step_00_copy_source_to_cache(source_files)
        # ~ self.step_02_copy_temporary_files_to_distributed_directory()
        self.step_03_clear_target()
        self.step_04_copy_sources_to_target(source_adocs)
        self.step_06_copy_all_to_cache(tmp_files)
        self.step_07_copy_compiled_documents_to_target()
        self.step_08_copy_global_resources_to_target()
        self.step_09_copy_html_to_cache()
        self.step_10_copy_kbdict_to_target()
        self.step_11_cleanup()
        self.log.debug("[DEPLOYER] END")

    def step_00_copy_source_to_cache(self, files):
        """Copy all from source directory to cache."""
        copy_docs(files, self.srvbes.get_path("cache"))

    def step_02_copy_temporary_files_to_distributed_directory(self):
        """Copy temporary files to distributed directory."""
        distributed = self.srvbes.get_value("docs", "targets")
        for adoc in distributed:
            source = os.path.join(self.srvbes.get_path("cache"), adoc)
            target = self.srvbes.get_path("www")
            try:
                shutil.copy(source, target)
            except Exception as warning:
                # FIXME
                self.log.warning(f"[DEPLOYER] WARN {warning}")
                self.log.warning(f"[DEPLOYER] SOURCE_MISSING path={source}")
                continue
        self.log.debug("[DEPLOYER] COPY_TMP_TO_DIST")

    def step_03_clear_target(self):
        """Clear target directory."""
        delete_target_contents(self.srvbes.get_path("target"))
        self.log.debug(f"[DEPLOYER] TARGET_CLEARED path={self.srvbes.get_path('target')}")

    # Refresh target
    def step_04_copy_sources_to_target(self, files):
        """Place a copy of sources in the target directory."""
        docsdir = os.path.join(self.srvbes.get_path("target"), "sources")
        os.makedirs(docsdir, exist_ok=True)
        copy_docs(files, docsdir)
        self.log.debug(f"[DEPLOYER] COPIED_SOURCES_TO_TARGET n={len(files)}")

    def step_06_copy_all_to_cache(self, files):
        """Copy objects in temporary directory to cache path."""
        copy_docs(files, self.srvbes.get_path("cache"))
        self.log.debug(f"[DEPLOYER] COPIED_ALL_TO_CACHE n={len(files)}")

    def step_07_copy_compiled_documents_to_target(self):
        """Copy cached documents to target path."""
        runtime = self.srvbes.get_dict("runtime")

        n = 0
        for filename in sorted(runtime["docs"]["targets"]):
            source = os.path.join(self.srvbes.get_path("cache"), filename)
            target = os.path.join(self.srvbes.get_path("target"), filename)
            try:
                shutil.copy(source, target)
            except FileNotFoundError as error:
                self.log.error(f"[DEPLOYER] ERROR {error}")
                self.log.error("[DEPLOYER] HINT rerun with -force")
                self.print_traceback()
                self.app.stop()
            n += 1
        self.log.debug(f"[DEPLOYER] COPIED_CACHED_TO_TARGET n={n}")

    def step_08_copy_global_resources_to_target(self):
        """Copy global resources to target path."""
        resources_dir_target = os.path.join(
            self.srvbes.get_path("target"), "resources")
        theme_target_dir = os.path.join(resources_dir_target, "themes")
        theme = self.srvbes.get_dict("theme")
        if not theme.get("id") or not theme.get("path"):
            self.log.error("[DEPLOYER] THEME_NOT_LOADED")
            self.app.stop(error=True)
        DEFAULT_THEME = os.path.join(ENV["GPATH"]["THEMES"], "default")
        CUSTOM_THEME_ID = theme["id"]
        CUSTOM_THEME_PATH = theme["path"]
        copydir(DEFAULT_THEME, os.path.join(theme_target_dir, "default"))
        copydir(CUSTOM_THEME_PATH, os.path.join(
            theme_target_dir, CUSTOM_THEME_ID))
        copydir(ENV["GPATH"]["COMMON"], os.path.join(
            resources_dir_target, "common"))
        self.log.debug("[DEPLOYER] COPIED_GLOBAL_RESOURCES")

        # Copy local resources to target path
        source_resources_dir = os.path.join(
            self.srvbes.get_path("source"), "resources")
        if os.path.exists(source_resources_dir):
            resources_dir_target = os.path.join(
                self.srvbes.get_path("target"), "resources"
            )
            copydir(source_resources_dir, resources_dir_target)
            self.log.debug("[DEPLOYER] COPIED_LOCAL_RESOURCES")

    def step_09_copy_html_to_cache(self):
        """Copy back all HTML files from target to cache."""
        dir_cache = self.srvbes.get_path("cache")
        dir_target = self.srvbes.get_path("target")
        delete_target_contents(dir_cache)
        pattern = os.path.join(dir_target, "*.html")
        html_files = glob.glob(pattern)
        copy_docs(html_files, dir_cache)
        self.log.debug("[DEPLOYER] COPIED_HTML_BACK_TO_CACHE")

    def step_10_copy_kbdict_to_target(self):
        """Copy JSON database to target path."""
        # FIXME
        # ~ self.save_kbdict(self.kbdict_new, self.srvbes.get_path('target'), 'kb4it')
        # ~ self.log.debug("Copied JSON database to target")

    def step_11_cleanup(self):
        """Cleanup temporary files."""
        delete_target_contents(self.srvbes.get_path("tmp"))
        delete_target_contents(self.srvbes.get_path("www"))
        os.unlink(self.app.get_log_file())
        self.log.debug("[DEPLOYER] CLEANUP")

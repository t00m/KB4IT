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
from kb4it.core.exceptions import ThemeError
from kb4it.core.service import Service
from kb4it.core.util import SOURCE_EXT_RE, copy_docs, copydir, delete_target_contents


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
        source_docs = [f for f in source_files if SOURCE_EXT_RE.search(f)]
        tmp_files = glob.glob(os.path.join(self.srvbes.get_path("tmp"), "*.*"))

        self.step_00_copy_source_to_cache(source_files)
        if self.srvbes.get_value("repo", "publish_sources") is False:
            self.step_04b_remove_sources_from_target()
        else:
            self.step_04_copy_sources_to_target(source_docs)
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

    def step_03_clear_target(self):
        """Clear target directory."""
        delete_target_contents(self.srvbes.get_path("target"))
        self.log.debug(f"[DEPLOYER] TARGET_CLEARED path={self.srvbes.get_path('target')}")

    def step_04_copy_sources_to_target(self, files):
        """Incrementally sync source Markdown files to target/sources/."""
        docsdir = os.path.join(self.srvbes.get_path("target"), "sources")
        os.makedirs(docsdir, exist_ok=True)
        expected = {os.path.basename(f) for f in files}
        n_copied = n_deleted = 0
        for filepath in files:
            dest = os.path.join(docsdir, os.path.basename(filepath))
            if not os.path.exists(dest) or os.path.getmtime(filepath) > os.path.getmtime(dest):
                shutil.copy(filepath, dest)
                n_copied += 1
        for filename in os.listdir(docsdir):
            if filename not in expected:
                os.unlink(os.path.join(docsdir, filename))
                n_deleted += 1
                self.log.debug(f"[DEPLOYER] STALE_SOURCE_DELETED file={filename}")
        self.log.debug(f"[DEPLOYER] SOURCES_TO_TARGET copied={n_copied} deleted={n_deleted}")

    def step_04b_remove_sources_from_target(self):
        """Remove target/sources/ when the repo does not publish its Markdown sources."""
        docsdir = os.path.join(self.srvbes.get_path("target"), "sources")
        if os.path.isdir(docsdir):
            shutil.rmtree(docsdir)
            self.log.debug(f"[DEPLOYER] SOURCES_REMOVED path={docsdir}")

    def step_06_copy_all_to_cache(self, files):
        """Copy objects in temporary directory to cache path."""
        copy_docs(files, self.srvbes.get_path("cache"))
        self.log.debug(f"[DEPLOYER] COPIED_ALL_TO_CACHE n={len(files)}")

    def step_07_copy_compiled_documents_to_target(self):
        """Incrementally sync compiled HTML to target: copy expected, delete stale."""
        runtime = self.srvbes.get_dict("runtime")
        expected = runtime["docs"]["targets"]
        dir_cache = self.srvbes.get_path("cache")
        dir_target = self.srvbes.get_path("target")

        n_copied = n_deleted = 0
        for filename in sorted(expected):
            source = os.path.join(dir_cache, filename)
            target = os.path.join(dir_target, filename)
            try:
                shutil.copy(source, target)
                n_copied += 1
            except FileNotFoundError as error:
                self.log.error(f"[DEPLOYER] ERROR {error}")
                self.log.error("[DEPLOYER] HINT rerun with -force")
                return

        for filename in os.listdir(dir_target):
            if not filename.endswith('.html'):
                continue
            if filename not in expected:
                os.unlink(os.path.join(dir_target, filename))
                n_deleted += 1
                self.log.debug(f"[DEPLOYER] STALE_HTML_DELETED file={filename}")

        self.log.debug(f"[DEPLOYER] HTML_TO_TARGET copied={n_copied} deleted={n_deleted}")

    def step_08_copy_global_resources_to_target(self):
        """Copy global resources to target path."""
        resources_dir_target = os.path.join(
            self.srvbes.get_path("target"), "resources")
        theme_target_dir = os.path.join(resources_dir_target, "themes")
        theme = self.srvbes.get_dict("theme")
        if not theme.get("id") or not theme.get("path"):
            self.log.error("[DEPLOYER] THEME_NOT_LOADED")
            raise ThemeError("Theme not loaded for deployment")
        DEFAULT_THEME = os.path.join(ENV["GPATH"]["THEMES"], "default")
        CUSTOM_THEME_ID = theme["id"]
        CUSTOM_THEME_PATH = theme["path"]
        deploy_dirs = theme.get("deploy_dirs")
        if deploy_dirs is None:
            copydir(DEFAULT_THEME, os.path.join(theme_target_dir, "default"))
            copydir(CUSTOM_THEME_PATH, os.path.join(theme_target_dir, CUSTOM_THEME_ID))
            copydir(ENV["GPATH"]["COMMON"], os.path.join(resources_dir_target, "common"))
            self.log.debug("[DEPLOYER] COPIED_GLOBAL_RESOURCES")
        else:
            msg = "theme.json 'deploy_dirs' must be a list of folder names"
            if not isinstance(deploy_dirs, list) or not all(isinstance(d, str) for d in deploy_dirs):
                raise ThemeError(msg)
            if any(d in ("", ".", "..") or os.path.basename(d) != d for d in deploy_dirs):
                raise ThemeError(msg)
            if os.path.basename(CUSTOM_THEME_ID) != CUSTOM_THEME_ID or CUSTOM_THEME_ID in ("", ".", ".."):
                raise ThemeError(f"Theme id is not a plain name: {CUSTOM_THEME_ID}")
            theme_dest = os.path.join(theme_target_dir, CUSTOM_THEME_ID)
            stale_dirs = (theme_dest, os.path.join(theme_target_dir, "default"),
                          os.path.join(resources_dir_target, "common"))
            # Every path to remove must stay inside the target directory.
            target_real = os.path.realpath(self.srvbes.get_path("target"))
            for stale in stale_dirs:
                stale_real = os.path.realpath(stale)
                if stale_real == target_real or os.path.commonpath([target_real, stale_real]) != target_real:
                    raise ThemeError(f"Theme deploy path outside target: {stale}")
            # Start clean so folders dropped from the list do not linger in the target.
            for stale in stale_dirs:
                if os.path.isdir(stale):
                    shutil.rmtree(stale)
            for name in deploy_dirs:
                source = os.path.join(CUSTOM_THEME_PATH, name)
                if os.path.isdir(source):
                    copydir(source, os.path.join(theme_dest, name))
                else:
                    self.log.warning(f"[DEPLOYER] DEPLOY_DIR_MISSING name={name}")
            self.log.debug(f"[DEPLOYER] COPIED_THEME_DIRS dirs={','.join(deploy_dirs)}")

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

    def step_11_cleanup(self):
        """Cleanup temporary files."""
        delete_target_contents(self.srvbes.get_path("tmp"))
        www_path = os.path.realpath(self.srvbes.get_path("www"))
        target_path = os.path.realpath(self.srvbes.get_path("target"))
        if www_path != target_path:
            delete_target_contents(self.srvbes.get_path("www"))
        log_file = self.app.get_log_file()
        if os.path.exists(log_file):
            os.unlink(log_file)
        self.log.debug("[DEPLOYER] CLEANUP")

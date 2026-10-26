#!/usr/bin/env python

"""
Service Deployer.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

import glob
import os
import re
import shutil
from typing import Any

from kb4it.core.env import ENV
from kb4it.core.exceptions import CompilationError, ThemeError
from kb4it.core.files import prune_tree, sync_file, sync_tree
from kb4it.core.log import get_logger
from kb4it.core.mdconfig import pygments_css
from kb4it.core.service import Service
from kb4it.core.util import SOURCE_EXT_RE, delete_target_contents, timeit

# A tag that loads a render file; text that only names the folder does not count.
RENDER_REF = re.compile(r'(?:src|href)="[^"]*resources/render/')
# Same rule for the Markdown editor files.
EDITOR_REF = re.compile(r'(?:src|href)="[^"]*resources/editor/')
# Folders under target/resources that only KB4IT fills; each build mirrors them.
ASSET_REFS = {"render": RENDER_REF, "editor": EDITOR_REF}


class Deployer(Service):
    """KB4IT Deployer Service."""

    def __init__(self, backend: Any, theme: Any, log_file: str | None = None) -> None:
        """Deployer of one build; log_file is the temporary log removed at the end."""
        super().__init__()
        self.log = get_logger(self.modname)
        self.started = True
        self.srvbes = backend
        self.srvthm = theme
        self.log_file = log_file
        self.missing = []

    def execute(self):
        """Deploy website build by KB4IT."""
        self.log.debug("[DEPLOYER] START")
        self.log.debug("[DEPLOYER] DEPLOY_BEGIN")

        source_files = glob.glob(os.path.join(self.srvbes.get_path("source"), "*.*"))
        source_docs = [f for f in source_files if SOURCE_EXT_RE.search(f)]
        tmp_files = glob.glob(os.path.join(self.srvbes.get_path("tmp"), "*.*"))

        if self.srvbes.get_value("repo", "publish_sources") is False:
            self.step_04b_remove_sources_from_target()
        else:
            self.step_04_copy_sources_to_target(source_docs)
        self.step_05_add_head_meta(tmp_files)
        self.step_06_copy_all_to_cache(tmp_files)
        self.step_07_copy_compiled_documents_to_target()
        self.step_08_copy_global_resources_to_target()
        self.step_09_copy_html_to_cache()
        self.step_10_copy_kbdict_to_target()
        self.step_11_cleanup()
        self.log.debug("[DEPLOYER] END")

    @timeit
    def step_04_copy_sources_to_target(self, files):
        """Incrementally sync source Markdown files to target/sources/."""
        docsdir = os.path.join(self.srvbes.get_path("target"), "sources")
        os.makedirs(docsdir, exist_ok=True)
        expected = {os.path.basename(f) for f in files}
        n_copied = n_deleted = 0
        for filepath in files:
            n_copied += sync_file(filepath, os.path.join(docsdir, os.path.basename(filepath)))
        for filename in os.listdir(docsdir):
            if filename not in expected:
                os.unlink(os.path.join(docsdir, filename))
                n_deleted += 1
                self.log.debug(f"[DEPLOYER] STALE_SOURCE_DELETED file={filename}")
        self.log.debug(f"[DEPLOYER] SOURCES_TO_TARGET copied={n_copied} deleted={n_deleted}")

    @timeit
    def step_04b_remove_sources_from_target(self):
        """Remove target/sources/ when the repo does not publish its Markdown sources."""
        docsdir = os.path.join(self.srvbes.get_path("target"), "sources")
        if os.path.isdir(docsdir):
            shutil.rmtree(docsdir)
            self.log.debug(f"[DEPLOYER] SOURCES_REMOVED path={docsdir}")

    @timeit
    def step_05_add_head_meta(self, files):
        """Add description, Open Graph and canonical tags to the pages built in this run."""
        theme = self.srvthm
        n = 0
        for path in files:
            if not path.endswith(".html"):
                continue
            with open(path, encoding="utf-8") as fh:
                html = fh.read()
            new = theme.inject_head_meta(html, os.path.basename(path))
            hooks = getattr(self.srvbes, "hooks", None)
            if hooks is not None and hooks.has("on_page"):
                new = hooks.call("on_page", os.path.basename(path), new, doc=os.path.basename(path))
                if not isinstance(new, str):
                    raise CompilationError("Hook on_page must return the page HTML")
            if new != html:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new)
                n += 1
        self.log.debug(f"[DEPLOYER] HEAD_META pages={n}")

    @timeit
    def step_06_copy_all_to_cache(self, files):
        """Copy the files built in this run from the temporary directory to the cache, keeping their times."""
        dir_cache = self.srvbes.get_path("cache")
        os.makedirs(dir_cache, exist_ok=True)
        for path in files:
            sync_file(path, os.path.join(dir_cache, os.path.basename(path)))
        self.log.debug(f"[DEPLOYER] COPIED_ALL_TO_CACHE n={len(files)}")

    @timeit
    def step_07_copy_compiled_documents_to_target(self):
        """Incrementally sync compiled HTML to target: copy new and changed pages, delete stale.

        A page whose target copy has the cache copy's size and time is left alone. A page missing from the cache does not stop the others; it is recorded in
        self.missing and the build fails at the end. Only pages an earlier build
        recorded as its own are deleted, so files the user keeps in the target
        survive; the first build after an upgrade has no record and deletes nothing.
        """
        runtime = self.srvbes.get_dict("runtime")
        expected = runtime["docs"]["targets"]
        dir_cache = self.srvbes.get_path("cache")
        dir_target = self.srvbes.get_path("target")

        n_copied = n_deleted = 0
        for filename in sorted(expected):
            source = os.path.join(dir_cache, filename)
            target = os.path.join(dir_target, filename)
            try:
                n_copied += sync_file(source, target)
            except FileNotFoundError:
                self.log.error(f"[DEPLOYER] PAGE_MISSING page={filename}")
                self.missing.append(filename)
        if self.missing:
            self.log.error("[DEPLOYER] HINT rebuild with --force")

        previous = self.srvbes.get_deployed_before()
        if previous is None:
            self.log.debug("[DEPLOYER] STALE_SWEEP_SKIPPED reason=no_record")
            previous = []
        for filename in sorted(set(previous) - set(expected)):
            # A plain page name only: the record is data read from disk, never a path to follow.
            if not isinstance(filename, str) or not filename.endswith(".html") or os.path.basename(filename) != filename:
                continue
            stale = os.path.join(dir_target, filename)
            if os.path.isfile(stale):
                os.unlink(stale)
                n_deleted += 1
                self.log.debug(f"[DEPLOYER] STALE_HTML_DELETED file={filename}")
        self.srvbes.set_deployed(expected)

        n_unchanged = len(expected) - n_copied - len(self.missing)
        self.log.debug(f"[DEPLOYER] HTML_TO_TARGET copied={n_copied} unchanged={n_unchanged} deleted={n_deleted}")

    @timeit
    def step_08_copy_global_resources_to_target(self):
        """Sync theme, common and local resources into the target: copy new or changed files, delete stale ones.

        The folders only KB4IT fills (the theme, default, common, render and editor) are mirrored. Files copied
        from source/resources and overrides/static are recorded; one the repository no longer has is deleted at
        the next build. Files nobody recorded, such as those the user put in the target, are never deleted.
        """
        target = self.srvbes.get_path("target")
        resources_dir_target = os.path.join(target, "resources")
        theme_target_dir = os.path.join(resources_dir_target, "themes")
        theme = self.srvbes.get_dict("theme")
        if not theme.get("id") or not theme.get("path"):
            self.log.error("[DEPLOYER] THEME_NOT_LOADED")
            raise ThemeError("Theme not loaded for deployment")
        DEFAULT_THEME = os.path.join(ENV["GPATH"]["THEMES"], "default")
        CUSTOM_THEME_ID = theme["id"]
        CUSTOM_THEME_PATH = theme["path"]

        # Repository files, copied last; the mirrors below must not delete them.
        local = []
        static = os.path.join(getattr(self.srvbes, "overrides_dir", "") or "", "static")
        if getattr(self.srvbes, "overrides_dir", None) and os.path.isdir(static):
            local.append(("OVERRIDES_STATIC", static, target))
        source_resources_dir = os.path.join(self.srvbes.get_path("source"), "resources")
        if os.path.exists(source_resources_dir):
            local.append(("LOCAL_RESOURCES", source_resources_dir, resources_dir_target))
        keep = set()
        for _name, origin, dest in local:
            keep |= self._planned(origin, dest)

        n_copied = n_deleted = 0
        provided = set()  # files the mirrors put in the target; never stale repository files
        deploy_dirs = theme.get("deploy_dirs")
        if deploy_dirs is None:
            for origin, dest in ((DEFAULT_THEME, os.path.join(theme_target_dir, "default")),
                                 (CUSTOM_THEME_PATH, os.path.join(theme_target_dir, CUSTOM_THEME_ID)),
                                 (ENV["GPATH"]["COMMON"], os.path.join(resources_dir_target, "common"))):
                copied, deleted, files = sync_tree(origin, dest, keep=keep)
                n_copied += copied
                n_deleted += deleted
                provided |= files
            self.log.debug(f"[DEPLOYER] COPIED_GLOBAL_RESOURCES copied={n_copied} deleted={n_deleted}")
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
            target_real = os.path.realpath(target)
            for stale in stale_dirs:
                stale_real = os.path.realpath(stale)
                if stale_real == target_real or os.path.commonpath([target_real, stale_real]) != target_real:
                    raise ThemeError(f"Theme deploy path outside target: {stale}")
            # Only the listed folders stay: the rest of the theme folder, default and common go.
            wanted = {os.path.join(theme_dest, name) for name in deploy_dirs
                      if os.path.isdir(os.path.join(CUSTOM_THEME_PATH, name))}
            for name in deploy_dirs:
                if os.path.join(theme_dest, name) not in wanted:
                    self.log.warning(f"[DEPLOYER] DEPLOY_DIR_MISSING name={name}")
            n_deleted += self._prune_except(theme_dest, wanted, keep)
            for stale in stale_dirs[1:]:
                n_deleted += prune_tree(stale, keep)
                self._remove_if_empty(stale)
            for name in deploy_dirs:
                dest = os.path.join(theme_dest, name)
                if dest in wanted:
                    copied, deleted, files = sync_tree(os.path.join(CUSTOM_THEME_PATH, name), dest, keep=keep)
                    n_copied += copied
                    n_deleted += deleted
                    provided |= files
            self.log.debug(f"[DEPLOYER] COPIED_THEME_DIRS dirs={','.join(deploy_dirs)} "
                           f"copied={n_copied} deleted={n_deleted}")

        # Stylesheet for build-time code highlighting; outside resources/common, which some themes do not deploy.
        settings = getattr(self.srvbes, "markdown", None)
        if settings is not None and settings.highlight == "pygments":
            css_path = os.path.join(resources_dir_target, "pygments.css")
            os.makedirs(os.path.dirname(css_path), exist_ok=True)
            self._write_if_changed(css_path, pygments_css(settings))
            self.log.debug(f"[DEPLOYER] PYGMENTS_CSS path={css_path}")

        provided |= self.deploy_page_assets(keep)

        # Files of the repository's overrides/static folder go into the site root, source/resources into
        # target/resources; one recorded by the previous build and gone from the repository is deleted.
        deployed = set()
        for name, origin, dest in local:
            copied, _deleted, files = sync_tree(origin, dest, mirror=False)
            deployed |= {os.path.relpath(path, target).replace(os.sep, "/") for path in files}
            self.log.debug(f"[DEPLOYER] COPIED_{name} path={origin} copied={copied}")
        self._delete_stale_static(target, deployed, provided)
        self.srvbes.set_static(deployed)

    @staticmethod
    def _planned(origin, dest):
        """Absolute paths in dest of the files under origin."""
        paths = set()
        for root, _dirs, files in os.walk(origin):
            rel = os.path.relpath(root, origin)
            folder = dest if rel == os.curdir else os.path.join(dest, rel)
            paths |= {os.path.normpath(os.path.join(folder, name)) for name in files}
        return paths

    @staticmethod
    def _prune_except(folder, children, keep):
        """Delete the entries of folder that are not in children (absolute paths), sparing kept files."""
        deleted = 0
        if not os.path.isdir(folder):
            return deleted
        for entry in os.listdir(folder):
            path = os.path.join(folder, entry)
            if path in children:
                continue
            if os.path.isdir(path) and not os.path.islink(path):
                deleted += prune_tree(path, keep)
                Deployer._remove_if_empty(path)
            elif os.path.normpath(path) not in keep:
                os.unlink(path)
                deleted += 1
        return deleted

    @staticmethod
    def _remove_if_empty(folder):
        """Remove folder when nothing in it was kept."""
        try:
            os.rmdir(folder)
        except OSError:
            pass  # missing, or it still holds a kept file

    @staticmethod
    def _write_if_changed(path, text):
        """Write text to path unless the file already holds it, so its time stays and later syncs skip it."""
        try:
            with open(path, encoding="utf-8") as fh:
                if fh.read() == text:
                    return
        except FileNotFoundError:
            pass
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def _delete_stale_static(self, target, deployed, provided):
        """Delete the files the previous build copied from the repository and that it no longer has.

        A path a mirrored folder provided in this build (a theme file a repository file used to replace) stays.
        """
        previous = self.srvbes.get_static_before() or []
        pages = set(self.srvbes.get_dict("runtime")["docs"]["targets"])
        target_real = os.path.realpath(target)
        n_deleted = 0
        for rel in sorted(set(previous) - deployed):
            # The record is data read from disk: a relative path inside the target, never a page of this build.
            if not isinstance(rel, str) or not rel or os.path.isabs(rel) or rel in pages:
                continue
            path = os.path.join(target, *rel.split("/"))
            if os.path.normpath(path) in provided:
                continue
            real = os.path.realpath(path)
            if real == target_real or os.path.commonpath([target_real, real]) != target_real:
                continue
            if os.path.isfile(path) and not os.path.islink(path):
                os.unlink(path)
                n_deleted += 1
                self.log.debug(f"[DEPLOYER] STALE_STATIC_DELETED file={rel}")
        self.log.debug(f"[DEPLOYER] STATIC_TO_TARGET files={len(deployed)} deleted={n_deleted}")

    @timeit
    def deploy_page_assets(self, keep=()):
        """Mirror the render (Mermaid, KaTeX) and editor files into the target when a page loads them, else remove them.

        Pages from earlier builds count too, so an incremental build keeps what an older page needs. Each page
        is read once; the regular expression only runs on pages that name the folder at all. Return the absolute
        paths of the files deployed.
        """
        provided = set()
        target = self.srvbes.get_path("target")
        needed = dict.fromkeys(ASSET_REFS, False)
        for path in glob.glob(os.path.join(target, "*.html")):
            if all(needed.values()):
                break
            with open(path, "rb") as fh:
                data = fh.read()
            for name, pattern in ASSET_REFS.items():
                if not needed[name] and f"resources/{name}/".encode() in data:
                    needed[name] = pattern.search(data.decode("utf-8", errors="replace")) is not None
        for name, used in needed.items():
            dest = os.path.join(target, "resources", name)
            if used:
                provided |= sync_tree(os.path.join(ENV["GPATH"]["RESOURCES"], name), dest, keep=keep)[2]
            elif os.path.isdir(dest):
                prune_tree(dest, keep)
                self._remove_if_empty(dest)
            self.log.debug(f"[DEPLOYER] {name.upper()}_ASSETS deployed={used}")
        return provided

    @timeit
    def step_09_copy_html_to_cache(self):
        """Make the cache hold the target's HTML pages: copy new or changed ones, delete the rest."""
        dir_cache = self.srvbes.get_path("cache")
        dir_target = self.srvbes.get_path("target")
        os.makedirs(dir_cache, exist_ok=True)
        pages = {os.path.basename(path) for path in glob.glob(os.path.join(dir_target, "*.html"))}
        copied = 0
        for name in pages:
            copied += sync_file(os.path.join(dir_target, name), os.path.join(dir_cache, name))
        deleted = 0
        for entry in os.listdir(dir_cache):
            if entry in pages:
                continue
            path = os.path.join(dir_cache, entry)
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                os.unlink(path)
            deleted += 1
        self.log.debug(f"[DEPLOYER] COPIED_HTML_BACK_TO_CACHE copied={copied} deleted={deleted}")

    @timeit
    def step_10_copy_kbdict_to_target(self):
        """Copy JSON database to target path."""

    @timeit
    def step_11_cleanup(self):
        """Cleanup temporary files."""
        delete_target_contents(self.srvbes.get_path("tmp"))
        www_path = os.path.realpath(self.srvbes.get_path("www"))
        target_path = os.path.realpath(self.srvbes.get_path("target"))
        if www_path != target_path:
            delete_target_contents(self.srvbes.get_path("www"))
        log_file = self.log_file
        if log_file and os.path.exists(log_file):
            os.unlink(log_file)
        self.log.debug("[DEPLOYER] CLEANUP")

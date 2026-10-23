#!/usr/bin/env python

"""
Backend module for initialization.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kb4it.core.types import Runtime

from kb4it.core.env import ENV
from kb4it.core.exceptions import ConfigError, KB4ITError, ThemeError
from kb4it.core.log import redirect_logs, release_log_file
from kb4it.core.paths import check_target, resolve_repo_path
from kb4it.core.service import Service
from kb4it.core.util import get_source_docs, json_load, json_save, timeit
from kb4it.services.pipeline import Pipeline


def _dir_contains(parent, child) -> bool:
    """Return True if *child* is *parent* or lives inside it."""
    parent = os.path.realpath(str(parent))
    child = os.path.realpath(str(child))
    return parent == child or child.startswith(parent + os.sep)


class Backend(Service):
    """(Second) KB4IT Initialization."""

    def _initialize(self):
        """Initialize application structure."""
        # force_all: rebuild everything. The command line or repo.json asks for it, or the
        # build decides it (an unreadable or older cache); params and repo stay as given.
        self.runtime: Runtime = {"theme": {}, "force_all": False}  # type: ignore[typeddict-item]
        self.repo = {}  # Only build and info load a repo.json
        self.pipeline = None  # Processor, Compiler and Deployer of this build, from the end of stage 1
        self.params = self.app.get_params()  # Get params from command line

        if self.params.get("action") in ("build", "info"):
            config_file = self.params.get("config")
            if config_file is None:
                raise ConfigError("No config file specified")

            # Check if it exists
            config_path = Path(config_file).absolute()
            if config_path.exists():
                try:
                    self.log.debug(f"[BACKEND] CONFIG_FILE path={config_path}")
                    self.repo = json_load(config_path)
                    self.log.debug("[BACKEND] CONFIG_LOADED")
                except AttributeError as error:
                    self.log.error("[BACKEND] CONFIG_PARSE_FAIL")
                    raise ConfigError(f"Config parse failed: {error}") from error
                except Exception as error:
                    self.log.error(f"[BACKEND] ERROR {error}")
                    raise ConfigError(f"Config load failed: {error}") from error
                self._validate_config()
            else:
                self.log.error(f"[BACKEND] CONFIG_MISSING path={config_path}")
                raise ConfigError(f"Config file not found: {config_path}")

            self.runtime["force_all"] = bool(self.params.get("force") or self.repo.get("force"))
            self.runtime["dir"] = {}
            dir_root = config_path.parent.parent.absolute()
            source, target = self._resolve_source_target(dir_root)
            # Before anything touches the disk: the deployer sweeps the target.
            check_target(target, dir_root, source)
            self.runtime["dir"]["source"] = source
            self.runtime["dir"]["target"] = target
            dir_var = Path.joinpath(dir_root, "var")
            dir_log = Path.joinpath(dir_var, "log")
            dir_tmp = Path.joinpath(dir_var, "tmp")
            dir_cache = Path.joinpath(dir_var, "cache")
            dir_www = Path.joinpath(dir_var, "www")
            dir_db = Path.joinpath(dir_var, "db")

            self.runtime["dir"]["root"] = dir_root
            self.runtime["dir"]["tmp"] = dir_tmp
            self.runtime["dir"]["www"] = dir_www
            self.runtime["dir"]["cache"] = dir_cache
            self.runtime["dir"]["log"] = dir_log
            self.runtime["dir"]["db"] = dir_db

            if self.runtime["force_all"]:
                # Force clears KB4IT's build artifacts only. It must never
                # delete the user's source or target, which may be nested
                # inside var when an app stores them under <root>/var/...
                # (rmtree of the whole var once wiped a repo's sources).
                source_dir = self.runtime["dir"]["source"]
                target_dir = self.runtime["dir"]["target"]
                for key in ("tmp", "cache", "www"):
                    artifact = self.runtime["dir"][key]
                    if _dir_contains(artifact, source_dir) or _dir_contains(artifact, target_dir):
                        self.log.warning(
                            f"[BACKEND] FORCE_SKIP path={artifact} reason=holds_source_or_target")
                        continue
                    shutil.rmtree(artifact, ignore_errors=True)
                # Reset the incremental cache without touching other data that
                # may share var/db (e.g. an embedding app's own database).
                kbdict_file = Path.joinpath(dir_db, "kbdict.json")
                if os.path.exists(kbdict_file):
                    # Keep the list of pages KB4IT wrote, so the deployer can still sweep them.
                    self.deployed_kept = self._read_deployed(kbdict_file)
                    os.unlink(kbdict_file)
                self.log.debug("[BACKEND] VAR_CLEARED scope=build_artifacts reason=force")

            for entry in self.runtime["dir"]:
                if entry not in ["source", "target", "root"]:
                    dirname = self.runtime["dir"][entry]
                    if not os.path.exists(dirname):
                        os.makedirs(dirname, exist_ok=True)

            # Activate application log
            app_log_file = Path.joinpath(dir_log, "kb4it.log")
            release_log_file(app_log_file)
            # Rotate the existing log before redirecting
            if app_log_file.exists():
                shutil.copy2(app_log_file, app_log_file.with_suffix('.log.old'))
            self.runtime["logfile"] = app_log_file
            self.log.debug(f"[BACKEND] LOG_FILE path={app_log_file}")
            if os.path.exists(app_log_file):
                os.unlink(app_log_file)
            kb4it_temp_log = self.app.get_log_file()
            if os.path.exists(kb4it_temp_log):
                shutil.copy(kb4it_temp_log, app_log_file)
            redirect_logs(app_log_file)

            # Initialize docs structure
            self.runtime["docs"] = {}
            self.runtime["docs"]["count"] = 0
            self.runtime["docs"]["bag"] = []
            self.runtime["docs"]["targets"] = set()

            # Get services
            self.get_services()

    REQUIRED_CONFIG_KEYS = ("source", "target", "theme", "title")

    def _validate_config(self):
        """Validate required keys are present in repo.json."""
        missing = [k for k in self.REQUIRED_CONFIG_KEYS if k not in self.repo]
        if missing:
            for key in missing:
                self.log.error(f"[BACKEND] CONFIG_KEY_MISSING key={key}")
            raise ConfigError(f"Missing required config keys: {missing}")
        # Fail early on a bad markdown block or a missing extension package.
        from kb4it.core.mdconfig import load_settings
        from kb4it.services.addpage import check_editor_setting
        check_editor_setting(self.repo)
        self.markdown = load_settings(self.repo)
        from kb4it.core.publish import site_url
        self.site_url = site_url(self.repo)
        overrides = self.repo.get("overrides", "overrides")
        if not isinstance(overrides, str) or not overrides.strip():
            raise ConfigError("repo.json 'overrides' must be a folder path")
        root = Path(self.params["config"]).absolute().parent.parent
        self.overrides_dir = resolve_repo_path(overrides, root)
        from kb4it.core.hooks import load_hooks
        self.hooks = load_hooks(self.repo, root)
        if self.hooks.has("on_config"):
            repo = self.hooks.call("on_config", dict(self.repo))
            if not isinstance(repo, dict):
                raise ConfigError("Hook on_config must return the settings dictionary")
            self.repo = repo

    def _resolve_source_target(self, dir_root):
        """Resolve source and target against the repository root, falling back to old cwd-relative configs."""
        raw_source, raw_target = self.repo["source"], self.repo["target"]
        source = resolve_repo_path(raw_source, dir_root)
        target = resolve_repo_path(raw_target, dir_root)
        legacy_source = os.path.realpath(os.path.expanduser(os.path.expandvars(raw_source)))
        if not os.path.exists(source) and os.path.exists(legacy_source):
            self.log.warning(f"[BACKEND] PATH_CWD_RELATIVE key=source path={legacy_source}")
            self.log.warning("[BACKEND] HINT make source and target relative to the repository root")
            source = legacy_source
            target = os.path.realpath(os.path.expanduser(os.path.expandvars(raw_target)))
        return source, target

    def _resolve_theme_path_override(self):
        """Resolve the optional repo.json `theme_path` field to a real, absolute path.

        Returns None when the field is absent. Raises ConfigError if it is set to
        anything other than a non-empty string. Relative paths are anchored to the
        repository root (the parent of the config file's parent), matching the
        convention used for source/target resolution elsewhere.
        """
        raw = self.repo.get("theme_path")
        if raw is None:
            return None
        if not isinstance(raw, str) or not raw.strip():
            raise ConfigError("repo.json 'theme_path' must be a non-empty string")
        config_file = self.params.get("config")
        root = Path(config_file).absolute().parent.parent if config_file else Path.cwd()
        return resolve_repo_path(raw, root)

    _PLAN_RUNTIME_KEYS = {"ncd", "nck", "K_PATH", "KV_PATH"}

    def get_value(self, domain: str, key: str):
        """Get value from key given a domain."""
        if domain == "runtime" and key in self._PLAN_RUNTIME_KEYS:
            plan = self.get_plan()
            if plan is not None:
                if key == "ncd":
                    return plan.doc_count
                if key == "nck":
                    return plan.key_count
                if key == "K_PATH":
                    return plan.K_PATH
                if key == "KV_PATH":
                    return plan.KV_PATH
        if domain == "app":
            adict = self.params
        elif domain == "docs":
            adict = self.runtime["docs"]
        elif domain == "repo":
            adict = self.repo
        elif domain == "runtime":
            adict = self.runtime
        elif domain == "theme":
            adict = self.runtime["theme"]
        else:
            return None
        return adict.get(key)

    def get_plan(self):
        """Return the current BuildPlan from the Processor (or None if not yet available)."""
        srvprc = getattr(self, "srvprc", None)
        if srvprc is None:
            return None
        return srvprc.get_plan()

    def set_value(self, domain: str, key: str, value: str | int | bool):
        """Set a value for a specific key in a given domain."""
        if domain == "app":
            adict = self.params
        elif domain == "runtime":
            adict = self.runtime
        else:
            adict = None

        if adict is None:
            self.log.error(f"[BACKEND] DOMAIN_UNKNOWN domain={domain}")
        else:
            adict[key] = value

    def get_dict(self, domain: str) -> dict:
        """Get dict by domain."""
        if domain == "app":
            adict = self.params
        elif domain == "docs":
            adict = self.runtime["docs"]
        elif domain == "repo":
            adict = self.repo
        elif domain == "runtime":
            adict = self.runtime
        elif domain == "theme":
            adict = self.runtime["theme"]
        else:
            adict = None
        return adict

    def get_path(self, name: str):
        """Get path by name."""
        return self.runtime.get("dir", {}).get(name)

    @staticmethod
    def _read_deployed(path):
        """Return the list of deployed pages stored in a kbdict.json, or None."""
        try:
            deployed = json_load(path).get("deployed")
        except Exception:
            return None
        return deployed if isinstance(deployed, list) else None

    def load_kbdict(self):
        """Load KB4IT dictionary."""
        kb4it_dbfile = os.path.join(self.get_path("db"), "kbdict.json")
        empty_kbdict = {"document": {}, "metadata": {}}
        # A forced or upgraded build starts from an empty dictionary but still knows its pages.
        deployed = getattr(self, "deployed_kept", None)
        if deployed is None and os.path.exists(kb4it_dbfile):
            deployed = self._read_deployed(kb4it_dbfile)
        if deployed is not None:
            empty_kbdict["deployed"] = deployed
        try:
            kbdict = json_load(kb4it_dbfile)
            self.log.debug(f"[BACKEND] KBDICT_LOAD path={kb4it_dbfile}")
            stored_version = kbdict.get("kb4it_version")
            current_version = ENV["APP"]["version"]
            if stored_version != current_version:
                self.log.warning(
                    f"[BACKEND] KBDICT_VERSION_MISMATCH stored={stored_version} current={current_version}"
                )
                self.runtime["force_all"] = True
                return empty_kbdict
        except FileNotFoundError:
            kbdict = empty_kbdict
        except (ValueError, AttributeError) as error:
            # Unreadable cache (a truncated write, a hand edit): rebuild everything; the next save replaces it.
            self.log.warning(f"[BACKEND] KBDICT_CORRUPT path={kb4it_dbfile} reason={error}")
            self.runtime["force_all"] = True
            return empty_kbdict
        except Exception as error:
            self.log.error(f"[BACKEND] KBDICT_LOAD_FAIL path={kb4it_dbfile}")
            raise KB4ITError(f"kbdict load failed: {error}") from error
        self.log.debug(f"[BACKEND] KBDICT_ENTRIES n={len(kbdict)}")
        return kbdict

    def save_kbdict(self, kbdict):
        """Save kb4it dictionary."""
        kb4it_dbfile = os.path.join(self.get_path("db"), "kbdict.json")
        kbdict["kb4it_version"] = ENV["APP"]["version"]
        json_save(kb4it_dbfile, kbdict)
        self.log.debug(f"[BACKEND] KBDICT_SAVED path={kb4it_dbfile}")

    def add_target(self, aid, hid):
        """Add documents to be compiled."""
        self.runtime["docs"]["targets"].add(hid)
        self.log.debug(f"[BACKEND] ADD_TARGET doc={aid} resource={hid}")

    def get_services(self):
        """Get services needed."""
        self.srvbld = self.get_service("Builder")

    @property
    def srvprc(self):
        """The Processor of this build, once the pipeline exists."""
        return self.pipeline.processor if self.pipeline is not None else None

    def start_pipeline(self):
        """Make the Processor, Compiler and Deployer of this build; the theme must be loaded."""
        self.pipeline = Pipeline(self, self.get_service("DB"), self.get_service("Theme"), self.params,
                                 callbacks=getattr(self.app, "callbacks", None),
                                 log_file=self.app.get_log_file())

    def get_kb_dict(self):
        """Shortcut to Processor method."""
        return self.srvprc.get_kb_dict()

    def commit_kbdict(self):
        """Write the new kbdict once the whole build succeeded.

        A failed or interrupted build leaves the previous kbdict.json in place, so the next
        incremental build compiles again every document that changed since the last good one.
        """
        self.save_kbdict(self.srvprc.get_kb_dict())
        self.log.debug("[BACKEND] KBDICT_COMMIT")

    def get_deployed_before(self):
        """Pages the previous build wrote into the target, or None if it did not record them."""
        deployed = self.srvprc.kbdict_cur.get("deployed")
        return deployed if isinstance(deployed, list) else None

    def set_deployed(self, pages):
        """Record the pages this build wrote into the target; saved with the kbdict."""
        self.srvprc.get_kb_dict()["deployed"] = sorted(pages)

    def get_events_before(self):
        """Documents of each event page after the last successful build, or None if it did not record them."""
        events = self.srvprc.kbdict_cur.get("events")
        return events if isinstance(events, dict) else None

    def set_events(self, pages):
        """Record the documents of each event page of this build; saved with the kbdict."""
        self.srvprc.get_kb_dict()["events"] = pages

    def get_kbdict_key(self, key, new=True):
        """Shortcut to Processor method."""
        return self.srvprc.get_kbdict_key(key, new)

    def get_kbdict_value(self, key, value, new=True):
        """Shortcut to Processor method."""
        return self.srvprc.get_kbdict_value(key, value, new)

    @timeit
    def stage_01_check_environment(self):
        """Check environment."""
        frontend = self.get_service("Frontend")
        self.log.debug("[BACKEND] CHECKS_START")
        self.log.debug(f"[BACKEND] DIR name=cache path={self.get_path('cache')}")
        self.log.debug(f"[BACKEND] DIR name=tmp path={self.get_path('tmp')}")
        self.log.debug(f"[BACKEND] DIR name=www path={self.get_path('www')}")

        # Check if source directory exists. If not, stop application
        if not os.path.exists(self.get_path("source")):
            self.log.error(f"[BACKEND] SOURCE_MISSING path={self.get_path('source')}")
            raise ConfigError(f"Source directory not found: {self.get_path('source')}")
        self.log.debug(f"[BACKEND] DIR name=source path={self.get_path('source')}")

        # check if target directory exists. If not, create it:
        if not os.path.exists(self.get_path("target")):
            os.makedirs(self.get_path("target"), exist_ok=True)
        self.log.debug(f"[BACKEND] DIR name=target path={self.get_path('target')}")

        theme_name = self.get_value("repo", "theme")
        if theme_name is None:
            self.log.debug("[BACKEND] THEME_MISSING")
            raise ConfigError("Theme name missing from repo config")
        else:
            theme_override = self._resolve_theme_path_override()
            if theme_override is not None:
                self.log.info(f"[BACKEND] THEME_PATH_OVERRIDE path={theme_override}")
                frontend.set_theme_path_override(theme_override)
            theme_path = frontend.theme_search(theme_name)
            if theme_path is not None:
                result = frontend.theme_load(os.path.basename(theme_path))
                if result is None and not self.runtime["theme"].get("id"):
                    self.log.error(f"[BACKEND] THEME_LOAD_FAIL name={theme_name}")
                    raise ThemeError(f"Theme load failed: {theme_name}")
                else:
                    frontend._validate_required_templates(self.runtime["theme"])
                    self._apply_target_subdir()
                    self.start_pipeline()
            else:
                self.log.error(f"[BACKEND] THEME_NOT_FOUND name={theme_name}")
                raise ThemeError(f"Theme not found: {theme_name}")
        self.log.debug("[BACKEND] CHECKS_END")

    def _apply_target_subdir(self):
        """Let the theme build into a sub-folder of target (apphelp versions); the target becomes site_root/sub."""
        sub = self.get_service("Theme").target_subdir()
        if not sub:
            return
        if os.path.basename(sub) != sub or sub in (".", "..") or not re.fullmatch(r"[A-Za-z0-9._-]+", sub):
            raise ThemeError(f"Version folder must be a plain name such as 0.9, not {sub!r}")
        root = self.runtime["dir"]["target"]
        self.runtime["dir"]["site_root"] = root
        self.runtime["dir"]["target"] = os.path.join(root, sub)
        os.makedirs(self.runtime["dir"]["target"], exist_ok=True)
        if getattr(self, "site_url", None):
            self.site_url = f"{self.site_url}{sub}/"
        self.log.info(f"[BACKEND] TARGET_SUBDIR name={sub} path={self.runtime['dir']['target']}")

    @timeit
    def stage_02_get_source_documents(self):
        """Get source documents from source directory."""
        self.log.debug("[BACKEND] SOURCES_START")
        sources_path = self.get_path("source")

        # Allow theme to generate documents first
        self.srvthm = self.get_service("Theme")

        self.runtime["docs"]["format"] = "md"

        # Older versions wrote about_kb4it.md into source/; remove it only if it is the untouched generated file.
        generated_head = "---\nSystemPage: Yes\n---\n# About KB4IT\n"
        legacy = os.path.join(sources_path, "about_kb4it.md")
        if os.path.exists(legacy):
            with open(legacy, encoding="utf-8") as fh:
                head = fh.read(len(generated_head))
            if head == generated_head:
                os.unlink(legacy)
                self.log.info(f"[BACKEND] GENERATED_SOURCE_REMOVED path={legacy}")

        # Remove stale .adoc system files left over from older repos.
        for stale_name in ("about_kb4it.adoc", "about_app.adoc"):
            stale_path = os.path.join(sources_path, stale_name)
            if os.path.exists(stale_path):
                os.unlink(stale_path)
                self.log.debug(f"[BACKEND] STALE_REMOVED path={stale_path}")

        # Collect all source documents
        self.runtime["docs"]["bag"] = get_source_docs(sources_path)
        basenames = [os.path.basename(f) for f in self.runtime["docs"]["bag"]]
        self.runtime["docs"]["filenames"] = basenames
        self.runtime["docs"]["count"] = len(self.runtime["docs"]["bag"])
        self.log.debug(f"[BACKEND] DOCS_FOUND n={self.runtime['docs']['count']}")
        self.log.debug("[BACKEND] SOURCES_END")

    @timeit
    def stage_03_process_sources(self):
        """Extract, Analyze and Transform."""
        self.log.debug("[BACKEND] EXTRACTION_START")
        self.srvprc.step_00_extraction()
        self.log.debug("[BACKEND] EXTRACTION_END")
        self.log.debug("[BACKEND] ANALYSIS_START")
        self.srvprc.step_01_analysis()
        self.log.debug("[BACKEND] ANALYSIS_END")
        self.log.debug("[BACKEND] TRANSFORMATION_START")
        self.srvprc.step_02_transformation()
        self.log.debug("[BACKEND] TRANSFORMATION_END")

    @timeit
    def stage_04_process_theme(self):
        """Run theme logic."""
        self.log.debug("[BACKEND] THEME_START")
        self.srvthm.build()
        self.log.debug("[BACKEND] THEME_END")

    @timeit
    def stage_05_compilation(self):
        """Compile Markdown documents to HTML."""
        self.pipeline.compiler.execute()

    @timeit
    def stage_06_deploy(self):
        """Recreate target."""
        self.pipeline.deployer.execute()

#!/usr/bin/env python

"""
Backend module for initialization.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
"""

import os
import shutil
from pathlib import Path

from kb4it.core.env import ENV
from kb4it.core.log import redirect_logs
from kb4it.core.service import Service
from kb4it.core.util import (get_hash_from_content, get_hash_from_file,
                             get_source_docs, json_load, json_save)
from kb4it.services.compiler import Compiler
from kb4it.services.deployer import Deployer
from kb4it.services.processor import Processor


class Backend(Service):
    """(Second) KB4IT Initialization."""

    def _initialize(self):
        """Initialize application structure."""
        self.runtime = {"theme": {}}  # Dictionary of runtime properties
        self.params = self.app.get_params()  # Get params from command line

        if self.params.get("action") in ("build", "info"):
            config_file = self.params.get("config")
            if config_file is None:
                self.app.stop(error=True)

            # Check if it exists
            config_path = Path(config_file).absolute()
            if config_path.exists():
                try:
                    self.log.debug(f"[BACKEND] CONFIG_FILE path={config_path}")
                    self.repo = json_load(config_path)
                    self.log.debug("[BACKEND] CONFIG_LOADED")
                    self._validate_config()
                except AttributeError as error:
                    self.log.error("[BACKEND] CONFIG_PARSE_FAIL")
                    self.log.error(f"[BACKEND] ERROR {error}")
                    self.app.stop(error=True)
                except Exception as error:
                    self.log.error(f"[BACKEND] ERROR {error}")
                    self.app.stop(error=True)
            else:
                self.log.error(f"[BACKEND] CONFIG_MISSING path={config_path}")
                self.app.stop(error=True)

            # Params-level force (e.g. from TUI) takes priority over repo.json
            if not self.params.get("force"):
                self.params["force"] = self.repo.get("force") or False
            self.runtime["dir"] = {}
            self.runtime["dir"]["source"] = os.path.realpath(
                self.repo["source"])
            self.runtime["dir"]["target"] = os.path.realpath(
                self.repo["target"])

            dir_root = config_path.parent.parent.absolute()
            dir_var = Path.joinpath(dir_root, "var")
            dir_log = Path.joinpath(dir_var, "log")
            dir_tmp = Path.joinpath(dir_var, "tmp")
            dir_cache = Path.joinpath(dir_var, "cache")
            dir_www = Path.joinpath(dir_var, "www")
            dir_db = Path.joinpath(dir_var, "db")

            self.runtime["dir"]["tmp"] = dir_tmp
            self.runtime["dir"]["www"] = dir_www
            self.runtime["dir"]["cache"] = dir_cache
            self.runtime["dir"]["log"] = dir_log
            self.runtime["dir"]["db"] = dir_db

            if self.params.get("force"):
                shutil.rmtree(dir_var, ignore_errors=True)
                self.log.debug(f"[BACKEND] VAR_CLEARED path={dir_var} reason=force")

            for entry in self.runtime["dir"]:
                if entry not in ["source", "target"]:
                    dirname = self.runtime["dir"][entry]
                    if not os.path.exists(dirname):
                        os.makedirs(dirname, exist_ok=True)

            # Activate application log
            app_log_file = Path.joinpath(dir_log, "kb4it.log")
            # Rotate the existing log before redirecting
            if app_log_file.exists():
                shutil.copy2(app_log_file, app_log_file.with_suffix('.log.old'))
            self.runtime["logfile"] = app_log_file
            self.log.debug(f"[BACKEND] LOG_FILE path={app_log_file}")
            if os.path.exists(app_log_file):
                os.unlink(app_log_file)
            kb4it_temp_log = self.app.get_log_file()
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
            self.app.stop(error=True)

    def get_value(self, domain: str, key: str):
        """Get value from key given a domain."""
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

    def load_kbdict(self):
        """Load KB4IT dictionary."""
        kb4it_dbfile = os.path.join(self.get_path("db"), "kbdict.json")
        empty_kbdict = {"document": {}, "metadata": {}}
        try:
            kbdict = json_load(kb4it_dbfile)
            self.log.debug(f"[BACKEND] KBDICT_LOAD path={kb4it_dbfile}")
            stored_version = kbdict.get("kb4it_version")
            current_version = ENV["APP"]["version"]
            if stored_version != current_version:
                self.log.warning(
                    f"[BACKEND] KBDICT_VERSION_MISMATCH stored={stored_version} current={current_version}"
                )
                self.params["force"] = True
                return empty_kbdict
        except FileNotFoundError:
            kbdict = empty_kbdict
        except Exception as error:
            self.log.error(f"[BACKEND] KBDICT_LOAD_FAIL path={kb4it_dbfile}")
            self.log.error(f"[BACKEND] ERROR {error}")
            self.app.stop(error=True)
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
        self.app.register_service("Processor", Processor())
        self.srvprc = self.get_service("Processor")

    def get_kb_dict(self):
        """Shortcut to Processor method."""
        return self.srvprc.get_kb_dict()

    def get_kbdict_key(self, key, new=True):
        """Shortcut to Processor method."""
        return self.srvprc.get_kbdict_key(key, new)

    def get_kbdict_value(self, key, value, new=True):
        """Shortcut to Processor method."""
        return self.srvprc.get_kbdict_value(key, value, new)

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
            self.app.stop(error=True)
        self.log.debug(f"[BACKEND] DIR name=source path={self.get_path('source')}")

        # check if target directory exists. If not, create it:
        if not os.path.exists(self.get_path("target")):
            os.makedirs(self.get_path("target"), exist_ok=True)
        self.log.debug(f"[BACKEND] DIR name=target path={self.get_path('target')}")

        theme_name = self.get_value("repo", "theme")
        if theme_name is None:
            self.log.debug("[BACKEND] THEME_MISSING")
            self.app.stop(error=True)
        else:
            theme_path = frontend.theme_search(theme_name)
            if theme_path is not None:
                result = frontend.theme_load(os.path.basename(theme_path))
                if result is None and not self.runtime["theme"].get("id"):
                    self.log.error(f"[BACKEND] THEME_LOAD_FAIL name={theme_name}")
                    self.app.stop(error=True)
                else:
                    frontend._validate_required_templates(self.runtime["theme"])
            else:
                self.log.error(f"[BACKEND] THEME_NOT_FOUND name={theme_name}")
                self.log.error("[BACKEND] CHECKS_END")
                self.app.stop(error=True)
        self.log.debug("[BACKEND] CHECKS_END")

    def stage_02_get_source_documents(self):
        """Get source documents from source directory."""
        self.log.debug("[BACKEND] SOURCES_START")
        sources_path = self.get_path("source")

        # Allow theme to generate documents first
        self.srvthm = self.get_service("Theme")

        # System file basenames,  excluded from user-file collection
        system_basenames = {"about_kb4it.md", "about_app.md"}

        self.runtime["docs"]["format"] = "md"

        # Generate about_kb4it.md (regenerate when content changes)
        var = self.srvbld.get_theme_var()
        TPL_PAGE_ABOUT_KB4IT = self.srvbld.template("PAGE_ABOUT_KB4IT")
        about_kb4it_content = TPL_PAGE_ABOUT_KB4IT.render(var=var)
        about_kb4it_target = os.path.join(sources_path, "about_kb4it.md")
        if os.path.exists(about_kb4it_target):
            if get_hash_from_content(about_kb4it_content) != get_hash_from_file(about_kb4it_target):
                with open(about_kb4it_target, "w", encoding="utf-8") as fout:
                    fout.write(about_kb4it_content)
                self.log.debug("[BACKEND] ABOUT_KB4IT_UPDATED")
        else:
            with open(about_kb4it_target, "w", encoding="utf-8") as fout:
                fout.write(about_kb4it_content)
            self.log.debug("[BACKEND] ABOUT_KB4IT_CREATED")

        # Generate about_app.md if missing (user-editable placeholder)
        about_app_target = os.path.join(sources_path, "about_app.md")
        if not os.path.exists(about_app_target):
            about_app_tpl = os.path.join(ENV["GPATH"]["TEMPLATES"], "md", "PAGE_ABOUT_APP.tpl")
            shutil.copy(about_app_tpl, about_app_target)
            self.log.warning("[BACKEND] ABOUT_APP_CREATED")

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

    def stage_04_process_theme(self):
        """Run theme logic."""
        self.log.debug("[BACKEND] THEME_START")
        self.srvthm.build()
        self.log.debug("[BACKEND] THEME_END")

    def stage_05_compilation(self):
        """Compile Markdown documents to HTML."""
        self.app.register_service("Compiler", Compiler())
        compiler = self.app.get_service("Compiler")
        compiler.execute()

    def stage_06_deploy(self):
        """Recreate target."""
        self.app.register_service("Deployer", Deployer())
        deployer = self.app.get_service("Deployer")
        deployer.execute()

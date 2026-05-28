#!/usr/bin/env python
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Workflow module
"""

import json
import os
import stat
import time

from kb4it.core.env import ENV
from kb4it.core.service import Service
from kb4it.core.util import copydir, json_load, json_save, get_source_docs, get_document_attributes


class Workflow(Service):
    """KB4IT workflow class."""

    def _initialize(self):
        """Initialize workflow module."""
        pass

    def list_themes(self):
        """Print all installed themes to the log."""
        self.log.info("[WORKFLOW] ACTION name=list_themes")
        frontend = self.get_service("Frontend")
        frontend.theme_list()

    def list_apps(self, theme):
        """Print all apps available for a given theme to the log."""
        self.log.debug(f"[WORKFLOW] ACTION name=list_apps theme={theme}")
        frontend = self.get_service("Frontend")
        frontend.apps_list(theme)

    def list_projects(self):
        """Print all projects created by the user to stdout."""
        self.log.info("[WORKFLOW] ACTION name=list_projects")
        projects_file = os.path.join(ENV["LPATH"]["ROOT"], "projects.json")
        if not os.path.exists(projects_file):
            print("No projects found.")
            return

        try:
            data = json_load(projects_file)
            projects = data.get("projects", [])
            if not projects:
                print("No projects found.")
                return

            print(f"{'Name':<30} {'Config Path'}")
            print("-" * 80)
            for proj in projects:
                print(f"{proj['name']:<30} {proj['config']}")
        except Exception as e:
            self.log.error(f"[WORKFLOW] PROJECTS_LOAD_ERROR reason={e}")
            print(f"Error loading projects: {e}")

    def _save_project(self, name, config_path):
        """Save project to projects.json registry."""
        projects_file = os.path.join(ENV["LPATH"]["ROOT"], "projects.json")
        projects = []
        if os.path.exists(projects_file):
            try:
                data = json_load(projects_file)
                projects = data.get("projects", [])
            except Exception:
                pass

        # Avoid duplicates
        if any(p["config"] == config_path for p in projects):
            return

        projects.append({"name": name, "config": config_path})
        try:
            json_save(projects_file, {"projects": projects})
            self.log.info(f"[WORKFLOW] PROJECT_REGISTERED name={name}")
        except Exception as e:
            self.log.error(f"[WORKFLOW] PROJECT_SAVE_ERROR reason={e}")

    def verify_sources(self):
        """Verify project sources and display non-conformant ones."""
        self.log.info("[WORKFLOW] ACTION name=verify_sources")
        backend = self.app.get_service("Backend")
        config_file = backend.get_value("app", "config")
        
        if config_file is None or not os.path.exists(config_file):
            print("Error: Configuration file not found.")
            return

        try:
            repo = json_load(config_file)
            source_dir = repo.get("source")
            if not source_dir:
                print("Error: 'source' directory not defined in config.")
                return
            
            # Resolve relative path if needed
            if not os.path.isabs(source_dir):
                source_dir = os.path.join(os.path.dirname(config_file), "..", source_dir)
                source_dir = os.path.abspath(source_dir)

            if not os.path.exists(source_dir):
                print(f"Error: Source directory not found: {source_dir}")
                return

            docs = get_source_docs(source_dir)
            if not docs:
                print(f"No source documents found in {source_dir}")
                return

            print(f"Verifying {len(docs)} source documents in {source_dir}...")
            non_conformant = []
            for doc in docs:
                _keys, success, reason = get_document_attributes(doc)
                if not success:
                    non_conformant.append((doc, reason))

            if non_conformant:
                print("\nNon-conformant source files found:")
                print("-" * 80)
                for doc, reason in non_conformant:
                    print(f"{os.path.abspath(doc)} (Reason: {reason})")
                print("-" * 80)
                print(f"Total: {len(non_conformant)} non-conformant files.")
            else:
                print("\nAll source documents are conformant.")

        except Exception as e:
            self.log.error(f"[WORKFLOW] VERIFY_ERROR reason={e}")
            print(f"Error during verification: {e}")

    def info_repository(self):
        """Print repository configuration fields to stdout."""
        backend = self.app.get_service("Backend")
        config_file = backend.get_value("app", "config")
        if config_file is not None and os.path.exists(config_file):
            repo = json_load(config_file)
            print(f"                     Title: {repo.get('title')}")
            print(f"                   Tagline: {repo.get('tagline')}")
            print(f"                Theme used: {repo.get('theme')}")
            print(f"            Docs sorted by: Date")
            print(f"         Force compilation: {repo.get('force')}")
            print(f"         Number of workers: {repo.get('workers')}")
            print(f"  Website target directory: {repo.get('target')}")
            print(f"Documents source directory: {repo.get('source')}")

    def create_repository(self):
        """Initialise a new repository from the chosen theme's example skeleton."""
        self.log.info("[WORKFLOW] ACTION name=create_repository")
        frontend = self.app.get_service("Frontend")
        params = self.app.get_params()
        self.log.debug(f"[WORKFLOW] PARAMS {params}")
        initialize = False
        theme, repo_path = params["theme"], params["repo_path"]
        self.log.debug(f"[WORKFLOW] THEME name={theme}")
        self.log.debug(f"[WORKFLOW] REPO_PATH path={repo_path}")
        theme_path = frontend.theme_search(theme=theme)
        if theme_path is None:
            self.log.error(f"[WORKFLOW] THEME_NOT_FOUND name={theme}")
            self.log.info("[WORKFLOW] LIST_AVAILABLE_THEMES")
            frontend.theme_list()
        else:
            if not os.path.exists(repo_path):
                self.log.warning(f"[WORKFLOW] REPO_PATH_MISSING path={repo_path}")
                os.makedirs(repo_path, exist_ok=True)
                self.log.warning(f"[WORKFLOW] REPO_PATH_CREATED path={repo_path}")
            initialize = True

        if initialize:
            self.log.info(f"[WORKFLOW] REPO_PATH path={repo_path}")
            self.log.info(f"[WORKFLOW] THEME_USE name={theme} path={theme_path}")
            app_name = params.get("app", "default") or "default"
            repo_demo = os.path.join(theme_path, "apps", app_name)
            if not os.path.isdir(repo_demo):
                repo_demo = os.path.join(theme_path, "example", "repo")
            self.log.info(f"[WORKFLOW] APP_TEMPLATE name={app_name} path={repo_demo}")
            copydir(repo_demo, repo_path)
            source_dir = os.path.join(repo_path, "source")
            target_dir = os.path.join(repo_path, "target")
            bin_dir = os.path.join(repo_path, "bin")
            script = os.path.join(bin_dir, "compile.sh")
            config_file = os.path.join(repo_path, "config", "repo.json")
            with open(config_file, encoding="utf-8") as fc:
                repoconf = json.load(fc)
            repoconf["source"] = source_dir
            repoconf["target"] = target_dir
            with open(config_file, "w", encoding="utf-8") as fc:
                json.dump(repoconf, fc, sort_keys=True, indent=4)
            os.makedirs(bin_dir, exist_ok=True)
            with open(script, "w", encoding="utf-8") as fs:
                fs.write(f"kb4it -L INFO build {config_file}")
            os.chmod(
                script,
                stat.S_IRUSR
                | stat.S_IRGRP
                | stat.S_IWUSR
                | stat.S_IWGRP
                | stat.S_IXUSR
                | stat.S_IXGRP,
            )
            self.log.info("[WORKFLOW] REPO_INITIALIZED")
            self.log.info(f"[WORKFLOW] HINT compile_script path={script}")
            self.log.info(f"[WORKFLOW] HINT source_dir path={source_dir}")
            self.log.info(f"[WORKFLOW] HINT target_dir path={target_dir}")
            self.log.info(f"[WORKFLOW] HINT config_file path={config_file}")
            self.log.info("[WORKFLOW] HINT help command='kb4it -h'")

            # Register project in projects.json
            repo_title = repoconf.get("title") or os.path.basename(repo_path)
            self._save_project(repo_title, config_file)

    def build_website(self):
        """Build workflow:
        1. Check environment
        2. Get source documents
        3. Preprocess documents (get metadata)
        4. Process documents in a temporary dir
        5. Compile Markdown documents to HTML
        6. Theme Post activities
        7. Deploy
        """
        t0 = time.perf_counter()

        backend = self.get_service("Backend")
        repo = backend.get_dict("repo")
        repo_title = repo["title"]
        repo_theme = repo["theme"]
        self.log.info(f"[WORKFLOW] BUILD theme={repo_theme} repo={repo_title}")

        self.log.info("[WORKFLOW] STAGE n=1 name=check_environment")
        backend.stage_01_check_environment()
        theme = self.get_service("Theme")

        self.log.info("[WORKFLOW] STAGE n=2 name=get_sources")
        theme.generate_sources()
        backend.stage_02_get_source_documents()

        self.log.info("[WORKFLOW] STAGE n=3 name=process_sources")
        backend.stage_03_process_sources()
        plan = backend.get_plan()
        if plan is not None:
            self.log.info(
                f"[WORKFLOW] PLAN docs={plan.doc_count}"
                f" keys={plan.key_count}"
                f" kv={plan.kv_count}"
            )

        self.log.info("[WORKFLOW] STAGE n=4 name=process_theme")
        backend.stage_04_process_theme()

        self.log.info("[WORKFLOW] STAGE n=5 name=compilation")
        backend.stage_05_compilation()

        self.log.info("[WORKFLOW] STAGE n=6 name=theme_post")
        theme.post_activities()

        self.log.info("[WORKFLOW] STAGE n=7 name=deploy")
        backend.stage_06_deploy()

        # Build summary
        runtime = backend.get_dict("runtime")
        plan = backend.get_plan()
        docs_total = runtime["docs"].get("count", 0)
        compiled   = plan.doc_count if plan is not None else 0
        skipped    = docs_total - compiled
        keys_compiled = plan.key_count if plan is not None else 0
        kv_compiled   = plan.kv_count if plan is not None else 0
        elapsed = time.perf_counter() - t0

        self.log.info(
            f"[WORKFLOW] SUMMARY"
            f" docs_total={docs_total}"
            f" compiled={compiled}"
            f" skipped={skipped}"
            f" keys_compiled={keys_compiled}"
            f" kv_pages_compiled={kv_compiled}"
        )
        self.log.info(f"[WORKFLOW] TOTAL_TIME elapsed={elapsed:.2f}s")

        # Report
        homepage = os.path.join(
            os.path.abspath(backend.get_path("target")), "index.html"
        )
        self.log.info("[WORKFLOW] BUILD_COMPLETE")
        self.log.info(f"[WORKFLOW] URL {homepage}")
        self.log.info(f"[WORKFLOW] LOG path={backend.get_value('runtime', 'logfile')}")
        self.log.info("[WORKFLOW] END")

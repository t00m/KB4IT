#!/usr/bin/env python
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Workflow module
"""

import json
import os
import shlex
import shutil
import stat
import sys
import time

from kb4it.core import trace
from kb4it.core.env import ENV
from kb4it.core.exceptions import CompilationError, KB4ITError, ThemeError
from kb4it.core.lock import registry_lock
from kb4it.core.service import Service
from kb4it.core.util import copydir, delete_target_contents, json_load, json_save, quarantine
from kb4it.services.verify import VerifyMixin


def build_script(config_file, platform=None):
    """Return (file name, content, executable) of the one-command build script for this platform.

    The config path is quoted, so knowledge bases in folders with spaces build too.
    """
    platform = sys.platform if platform is None else platform
    if platform == "win32":
        return "compile.cmd", f'@echo off\r\nkb4it -L INFO build "{config_file}"\r\n', False
    return "compile.sh", f"#!/bin/sh\nkb4it -L INFO build {shlex.quote(str(config_file))}\n", True


class Workflow(VerifyMixin, Service):
    """KB4IT workflow class."""

    def _initialize(self):
        """Initialize workflow module."""
        pass

    def list_themes(self):
        """Print all installed themes to the log."""
        self.log.info("[WORKFLOW] ACTION name=list_themes")
        frontend = self.get_service("Frontend")
        frontend.theme_list()

    def doctor(self):
        """Print the installation report; raise when a bundled file or theme is missing (SI-07)."""
        from kb4it.core.doctor import report
        self.log.debug("[WORKFLOW] ACTION name=doctor")
        lines, problems = report()
        for line in lines:
            print(line)
        for problem in problems:
            print(f"PROBLEM    {problem}")
            self.log.error(f"[WORKFLOW] DOCTOR_PROBLEM {problem}")
        if problems:
            raise KB4ITError(f"Installation incomplete: {len(problems)} problem(s)")
        print("No problems found.")

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
        with registry_lock():
            self._save_project_locked(name, config_path)

    def _save_project_locked(self, name, config_path):
        projects_file = os.path.join(ENV["LPATH"]["ROOT"], "projects.json")
        projects = []
        if os.path.exists(projects_file):
            try:
                data = json_load(projects_file)
                projects = data["projects"]
                if not isinstance(projects, list):
                    raise TypeError("'projects' is not a list")
            except (ValueError, KeyError, TypeError) as error:
                kept = quarantine(projects_file)
                self.log.warning(f"[WORKFLOW] PROJECTS_CORRUPT path={projects_file} kept={kept} reason={error}")
                projects = []

        # Avoid duplicates
        if any(p["config"] == config_path for p in projects):
            return

        projects.append({"name": name, "config": config_path})
        try:
            json_save(projects_file, {"projects": projects})
            self.log.info(f"[WORKFLOW] PROJECT_REGISTERED name={name}")
        except Exception as e:
            self.log.error(f"[WORKFLOW] PROJECT_SAVE_ERROR reason={e}")

    @staticmethod
    def _theme_tag(backend):
        """'techdoc/1.0.0+3f9a1c0b7e21': the theme identity as one log value."""
        theme = backend.get_dict("runtime").get("theme") or {}
        return f"{theme.get('id', '?')}/{theme.get('version') or 'unversioned'}+{theme.get('fingerprint', '?')}"

    def info_repository(self):
        """Print repository configuration fields to stdout."""
        backend = self.app.get_service("Backend")
        config_file = backend.get_value("app", "config")
        if config_file is not None and os.path.exists(config_file):
            repo = json_load(config_file)
            print(f"                     KB4IT: {ENV['APP']['build_version']}")
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
            raise ThemeError(f"Theme not found: {theme}")
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
            copydir(repo_demo, repo_path, keep_existing=True)
            # The theme's own config always replaces an old one, so the theme matches the request.
            shutil.copyfile(os.path.join(repo_demo, "config", "repo.json"), os.path.join(repo_path, "config", "repo.json"))
            source_dir = os.path.join(repo_path, "source")
            target_dir = os.path.join(repo_path, "target")
            # Git cannot store empty folders, so a sample app may ship without them.
            os.makedirs(source_dir, exist_ok=True)
            os.makedirs(target_dir, exist_ok=True)
            bin_dir = os.path.join(repo_path, "bin")
            config_file = os.path.abspath(os.path.join(repo_path, "config", "repo.json"))
            with open(config_file, encoding="utf-8") as fc:
                repoconf = json.load(fc)
            # Relative to the repository root, so the repository can move and work in CI.
            repoconf["source"] = "source"
            repoconf["target"] = "target"
            # kb4it create --index yes|no (and the TUI choice): may search engines index the site?
            index = params.get("index")
            if index is not None:
                seo = repoconf.get("seo") if isinstance(repoconf.get("seo"), dict) else {}
                repoconf["seo"] = {**seo, "index": index == "yes"}
            with open(config_file, "w", encoding="utf-8") as fc:
                json.dump(repoconf, fc, sort_keys=True, indent=4)
            os.makedirs(bin_dir, exist_ok=True)
            name, content, executable = build_script(config_file)
            script = os.path.join(bin_dir, name)
            with open(script, "w", encoding="utf-8", newline="") as fs:
                fs.write(content)
            if executable:
                os.chmod(script, stat.S_IRUSR | stat.S_IRGRP | stat.S_IWUSR | stat.S_IWGRP | stat.S_IXUSR | stat.S_IXGRP)
            self.log.info("[WORKFLOW] REPO_INITIALIZED")
            repo_abs = os.path.abspath(repo_path)
            self.app.next_steps = [
                f"Your knowledge base is ready at {repo_abs}.",
                f"Write documents in {os.path.join(repo_abs, 'source')}/ and copy or delete the samples there.",
                f"Preview the site with: kb4it serve {config_file}",
            ]

            # Register project in projects.json
            repo_title = repoconf.get("title") or os.path.basename(repo_path)
            self._save_project(repo_title, config_file)

    def _failed_pages(self) -> dict:
        """Pages the compiler could not make or the deployer could not find, with the reason."""
        failed = {}
        pipeline = getattr(self.get_service("Backend"), "pipeline", None)
        if pipeline is None:
            return failed
        for name, reason in pipeline.compiler.failed:
            failed[name] = reason
        for name in pipeline.deployer.missing:
            failed.setdefault(name, "missing from the cache")
        return failed

    def build_website(self):
        """Build the website; with the trace parameter (kb4it build --trace), record its timings in var/log/trace.json."""
        if not self.app.get_params().get("trace"):
            self._build_website()
            return
        trace.start()
        try:
            with trace.span("build"):
                self._build_website()
        finally:
            backend = self.get_service("Backend")
            result = trace.stop(backend.get_path("log") or ENV["LPATH"]["LOG"])
            if result is not None:
                path, events = result
                self.log.info(f"[WORKFLOW] TRACE path={path}")
                print("\n".join(trace.summary(events)))
                print(f"Trace: {path} (open it in https://ui.perfetto.dev)")

    def _build_website(self):
        """Build workflow:
        1. Check environment
        2. Get source documents
        3. Preprocess documents (get metadata)
        4. Process documents in a temporary dir
        5. Compile Markdown documents to HTML
        6. Theme Post activities
        7. Deploy
        8. Theme post deploy activities
        """
        t0 = time.perf_counter()

        backend = self.get_service("Backend")
        repo = backend.get_dict("repo")
        repo_title = repo["title"]
        repo_theme = repo["theme"]
        self.log.info(f"[WORKFLOW] BUILD theme={repo_theme} repo={repo_title}")

        self.log.info("[WORKFLOW] STAGE n=1 name=check_environment")
        with trace.span("1 check_environment"):
            backend.stage_01_check_environment()
        theme = self.get_service("Theme")

        # A failed build leaves files in tmp; clear them before anything writes there.
        delete_target_contents(backend.get_path("tmp"))

        self.log.info("[WORKFLOW] STAGE n=2 name=get_sources")
        with trace.span("2 get_sources"):
            with trace.span("theme.generate_sources"):
                theme.generate_sources()
            backend.stage_02_get_source_documents()

        self.log.info("[WORKFLOW] STAGE n=3 name=process_sources")
        with trace.span("3 process_sources"):
            backend.stage_03_process_sources()
        plan = backend.get_plan()
        if plan is not None:
            self.log.info(
                f"[WORKFLOW] PLAN docs={plan.doc_count}"
                f" keys={plan.key_count}"
                f" kv={plan.kv_count}"
            )

        self.log.info("[WORKFLOW] STAGE n=4 name=process_theme")
        with trace.span("4 process_theme"):
            backend.stage_04_process_theme()

        self.log.info("[WORKFLOW] STAGE n=5 name=compilation")
        with trace.span("5 compilation"):
            backend.stage_05_compilation()

        self.log.info("[WORKFLOW] STAGE n=6 name=theme_post")
        with trace.span("6 theme_post"):
            theme.post_activities()

        self.log.info("[WORKFLOW] STAGE n=7 name=deploy")
        with trace.span("7 deploy"):
            backend.stage_06_deploy()

        self.log.info("[WORKFLOW] STAGE n=8 name=theme_post_deploy")
        with trace.span("8 theme_post_deploy"):
            with trace.span("theme.post_deploy_activities"):
                theme.post_deploy_activities()
            with trace.span("theme.write_search_index"):
                theme.write_search_index()
            with trace.span("theme.write_sitemap"):
                theme.write_sitemap()
            with trace.span("theme.write_feed"):
                theme.write_feed()

        # Build summary
        runtime = backend.get_dict("runtime")
        plan = backend.get_plan()
        docs_total = runtime["docs"].get("count", 0)
        compiled   = plan.doc_count if plan is not None else 0
        invalid    = plan.invalid_count if plan is not None else 0
        profiles   = plan.profile_count if plan is not None else 0
        skipped    = docs_total - compiled - invalid - profiles
        keys_compiled = plan.key_count if plan is not None else 0
        kv_compiled   = plan.kv_count if plan is not None else 0
        failed = self._failed_pages()
        if not failed:
            with trace.span("commit_kbdict"):
                backend.commit_kbdict()
        elapsed = time.perf_counter() - t0

        self.log.info(
            f"[WORKFLOW] SUMMARY"
            f" docs_total={docs_total}"
            f" compiled={compiled}"
            f" skipped={skipped}"
            f" invalid={invalid}"
            f" keys_compiled={keys_compiled}"
            f" kv_pages_compiled={kv_compiled}"
            f" failed={len(failed)}"
            f" kb4it={ENV['APP']['build_version']}"
            f" theme={self._theme_tag(backend)}"
        )
        self.log.info(f"[WORKFLOW] TOTAL_TIME elapsed={elapsed:.2f}s")

        hooks = getattr(backend, "hooks", None)
        if hooks is not None and hooks.has("on_build_end"):
            summary = {"docs_total": docs_total, "compiled": compiled, "skipped": skipped, "invalid": invalid,
                       "keys_compiled": keys_compiled, "kv_pages_compiled": kv_compiled,
                       "failed": len(failed), "elapsed": round(elapsed, 2)}
            hooks.call("on_build_end", str(backend.get_path("target")), summary)

        if failed:
            names = ", ".join(sorted(failed))
            self.log.error(f"[WORKFLOW] PAGES_FAILED n={len(failed)} pages={names}")
            raise CompilationError(f"{len(failed)} page(s) could not be built: {names}")

        # Report
        homepage = os.path.join(
            os.path.abspath(backend.get_path("target")), "index.html"
        )
        self.log.info("[WORKFLOW] BUILD_COMPLETE")
        self.log.info(f"[WORKFLOW] URL {homepage}")
        self.log.info(f"[WORKFLOW] LOG path={backend.get_value('runtime', 'logfile')}")
        self.log.info("[WORKFLOW] END")

#!/usr/bin/env python
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Workflow module
"""

import json
import os
import stat

from kb4it.core.service import Service
from kb4it.core.util import copydir
from kb4it.core.util import json_load


class Workflow(Service):
    """KB4IT workflow class."""

    def _initialize(self):
        """Initialize workflow module."""
        pass

    def list_themes(self):
        self.log.info("[WORKFLOW] ACTION name=list_themes")
        frontend = self.get_service("Frontend")
        frontend.theme_list()

    def list_apps(self, theme):
        self.log.debug(f"[WORKFLOW] ACTION name=list_apps theme={theme}")
        frontend = self.get_service("Frontend")
        frontend.apps_list(theme)

    def info_repository(self):
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
            repo_demo = os.path.join(theme_path, "example", "repo")
            copydir(repo_demo, repo_path)
            source_dir = os.path.join(repo_path, "source")
            target_dir = os.path.join(repo_path, "target")
            bin_dir = os.path.join(repo_path, "bin")
            script = os.path.join(bin_dir, "compile.sh")
            config_file = os.path.join(repo_path, "config", "repo.json")
            with open(config_file) as fc:
                repoconf = json.load(fc)
            repoconf["source"] = source_dir
            repoconf["target"] = target_dir
            with open(config_file, "w") as fc:
                json.dump(repoconf, fc, sort_keys=True, indent=4)
            os.makedirs(bin_dir, exist_ok=True)
            with open(script, "w") as fs:
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

    def build_website(self):
        """Build workflow:
        1. Check environment
        2. Get source documents
        3. Preprocess documents (get metadata)
        4. Process documents in a temporary dir
        5. Compile documents to html with asciidoctor
        6. Deploy
        7. Theme Post activities
        """
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

        self.log.info("[WORKFLOW] STAGE n=4 name=process_theme")
        backend.stage_04_process_theme()

        self.log.info("[WORKFLOW] STAGE n=5 name=compilation")
        backend.stage_05_compilation()

        self.log.info("[WORKFLOW] STAGE n=7 name=theme_post")
        theme.post_activities()

        self.log.info("[WORKFLOW] STAGE n=6 name=deploy")
        backend.stage_06_deploy()

        # Report
        homepage = os.path.join(
            os.path.abspath(backend.get_path("target")), "index.html"
        )
        self.log.info("[WORKFLOW] BUILD_COMPLETE")
        self.log.info(f"[WORKFLOW] URL {homepage}")
        self.log.info(f"[WORKFLOW] LOG path={backend.get_value('runtime', 'logfile')}")
        self.log.info("[WORKFLOW] END")

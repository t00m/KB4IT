#!/usr/bin/env python
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Workflow module
"""

import os
import json
import stat
import pprint

from kb4it.core.service import Service
from kb4it.core.util import copydir
from kb4it.core.util import timeit
from kb4it.core.util import json_load

class Workflow(Service):
    """KB4IT workflow class."""

    def _initialize(self):
        """Initialize workflow module."""
        pass

    def list_themes(self):
        self.log.info("KB4IT action: list available themes")
        frontend = self.get_service('Frontend')
        frontend.theme_list()

    def list_apps(self, theme):
        self.log.debug(f"KB4IT action: list available apps for theme '{theme}'")
        frontend = self.get_service('Frontend')
        frontend.apps_list(theme)

    def info_repository(self):
        backend = self.app.get_service('Backend')
        config_file = backend.get_value('app', 'config')
        if config_file is not None and os.path.exists(config_file):
            repo = json_load(config_file)
            print(f"                     Title: {repo.get('title')}")
            print(f"                   Tagline: {repo.get('tagline')}")
            print(f"                Theme used: {repo.get('theme')}")
            print(f"            Docs sorted by: {repo.get('sort')}")
            print(f"         Force compilation: {repo.get('force')}")
            print(f"         Number of workers: {repo.get('workers')}")
            print(f"  Website target directory: {repo.get('target')}")
            print(f"Documents source directory: {repo.get('source')}")

    def create_repository(self):
        self.log.info("KB4IT action: create new repository")
        backend = self.app.get_service('Backend')
        frontend = self.app.get_service('Frontend')
        params = self.app.get_params()
        self.log.debug(params)
        initialize = False
        theme, repo_path = params['theme'], params['repo_path']
        self.log.debug(f"Theme: {theme}")
        self.log.debug(f"Repository path: {repo_path}")
        theme_path = frontend.theme_search(theme=theme)
        if theme_path is None:
            self.log.error(f"Theme '{theme}' doesn't exist.")
            self.log.info("This is the list of themes available:")
            frontend.theme_list()
        else:
            if not os.path.exists(repo_path):
                self.log.warning(f"Repository path '{repo_path}' does not exist")
                os.makedirs(repo_path, exist_ok=True)
                self.log.warning(f"Repository path '{repo_path}' created")
            initialize = True

        if initialize:
            self.log.info(f"Repository path: {repo_path}")
            self.log.info(f"Using theme '{theme}' from path '{theme_path}'")
            repo_demo = os.path.join(theme_path, 'example', 'repo')
            copydir(repo_demo, repo_path)
            source_dir = os.path.join(repo_path, 'source')
            target_dir = os.path.join(repo_path, 'target')
            bin_dir = os.path.join(repo_path, 'bin')
            script = os.path.join(bin_dir, 'compile.sh')
            config_file = os.path.join(repo_path, 'config', 'repo.json')
            with open(config_file) as fc:
                repoconf = json.load(fc)
            repoconf['source'] = source_dir
            repoconf['target'] = target_dir
            with open(config_file, 'w') as fc:
                json.dump(repoconf, fc, sort_keys=True, indent=4)
            os.makedirs(bin_dir, exist_ok=True)
            with open(script, 'w') as fs:
                fs.write(f'kb4it -L INFO build {config_file}')
            os.chmod(script, stat.S_IRUSR | stat.S_IRGRP | stat.S_IWUSR | stat.S_IWGRP | stat.S_IXUSR | stat.S_IXGRP)
            self.log.info(f"Repository initialized")
            self.log.info(f"You can compile it by executing '{script}'")
            self.log.info(f"Add your documents in '{source_dir}'")
            self.log.info(f"Documents to be published in '{target_dir}'")
            self.log.info(f"Check your repository settings in '{config_file}'")
            self.log.info(f"For more KB4IT options, execute: kb4it -h")

    # ~ @timeit
    def build_website(self):
        """Build workflow:
        1. Check environment
        2. Get source documents
        3. Preprocess documents (get metadata)
        4. Process documents in a temporary dir
        5. Compile documents to html with asciidoctor
        6. Delete contents of target directory (if any)
        7. Refresh target directory
        8. Remove temporary directory
        """
        backend = self.get_service('Backend')
        # ~ backend.busy()
        repo = backend.get_dict('repo')
        repo_title = repo['title']
        repo_theme = repo['theme']
        self.log.info(f"Building a website for repository '{repo_title}'")
        self.log.info(f"Using theme '{repo_theme}'")
        self.log.info(f"Check environment")
        backend.stage_01_check_environment()
        self.log.info(f"Allow theme to generate sources")
        theme = self.get_service('Theme')
        theme.generate_sources()
        self.log.info(f"Get source documents")
        backend.stage_02_get_source_documents()
        self.log.info(f"Preprocessing")
        backend.stage_03_preprocessing()
        self.log.info(f"Backend processing")
        backend.stage_04_processing()
        self.log.info(f"Theme processing")
        backend.stage_06_theme()
        self.log.info(f"Compilation")
        backend.stage_05_compilation()
        # ~ self.log.info(f"Clean up target")
        # ~ backend.stage_07_clean_target()
        # ~ self.log.info(f"Refresh target")
        # ~ backend.stage_08_refresh_target()
        self.log.info(f"Deploy")
        backend.stage_07_deploy()
        self.log.info(f"Theme post activities")
        theme.post_activities()
        homepage = os.path.join(os.path.abspath(backend.get_path('target')), 'index.html')
        self.log.info(f"Repository website built")
        self.log.info(f"URL: {homepage}")
        self.log.info(f"Full log: {backend.get_value('runtime', 'logfile')}")
        self.log.info(f"The End")
        # ~ backend.free()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Workflow module
"""

import os
import json
import stat

from kb4it.core.service import Service
from kb4it.core.util import copydir

class Workflow(Service):
    """KB4IT workflow class."""

    def initialize(self):
        """Initialize workflow module."""
        pass

    def list_themes(self):
        self.log.info("[WORKFLOW] - KB4IT action: list available themes")
        frontend = self.get_service('Frontend')
        frontend.theme_list()

    def create_repository(self):
        self.log.info("[WORKFLOW] - KB4IT action: create new repository")
        backend = self.app.get_service('Backend')
        frontend = self.app.get_service('Frontend')
        params = self.app.get_params()
        initialize = False
        theme, repo_path = params.theme, params.repo_path
        self.log.debug(f"[WORKFLOW] - \tTheme: {theme}")
        self.log.debug(f"[WORKFLOW] - \tRepository path: {repo_path}")
        theme_path = frontend.theme_search(theme=theme)
        if theme_path is None:
            self.log.error(f"[WORKFLOW] - \tTheme '{theme}' doesn't exist.")
            self.log.info("[WORKFLOW] - \tThis is the list of themes available:")
            frontend.theme_list()
        else:
            if not os.path.exists(repo_path):
                self.log.warning(f"[WORKFLOW] - \tRepository path '{repo_path}' does not exist")
                os.makedirs(repo_path, exist_ok=True)
                self.log.warning(f"[WORKFLOW] - \tRepository path '{repo_path}' created")
            initialize = True

        if initialize:
            self.log.info(f"[WORKFLOW] - Repository path: {repo_path}")
            self.log.info(f"[WORKFLOW] - Using theme '{theme}' from path '{theme_path}'")
            repo_demo = os.path.join(theme_path, 'example', 'repo')
            copydir(repo_demo, repo_path)
            source_dir = os.path.join(repo_path, 'source')
            target_dir = os.path.join(repo_path, 'target')
            bin_dir = os.path.join(repo_path, 'bin')
            script = os.path.join(bin_dir, 'compile.sh')
            config_file = os.path.join(repo_path, 'config', 'repo.json')
            with open(config_file, 'r') as fc:
                repoconf = json.load(fc)
            repoconf['source'] = source_dir
            repoconf['target'] = target_dir
            with open(config_file, 'w') as fc:
                json.dump(repoconf, fc, sort_keys=True, indent=4)
            os.makedirs(bin_dir, exist_ok=True)
            with open(script, 'w') as fs:
                fs.write(f'kb4it -L INFO build {config_file}')
            os.chmod(script, stat.S_IRUSR | stat.S_IRGRP | stat.S_IWUSR | stat.S_IWGRP | stat.S_IXUSR | stat.S_IXGRP)
            self.log.info(f"[WORKFLOW] - \tRepository initialized")
            self.log.info(f"[WORKFLOW] - \tYou can compile it by executing '{script}'")
            self.log.info(f"[WORKFLOW] - \tAdd your documents in '{source_dir}'")
            self.log.info(f"[WORKFLOW] - \tDocuments to be published in '{target_dir}'")
            self.log.info(f"[WORKFLOW] - \tCheck your repository settings in '{config_file}'")
            self.log.info(f"[WORKFLOW] - \tFor more KB4IT options, execute: kb4it -h")

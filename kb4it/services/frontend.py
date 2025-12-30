#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module with the application logic.
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: module holding the application logic
"""

import re
import os
from os.path import abspath
import sys
import glob
import json
import shutil
import tempfile
import datetime
from concurrent.futures import ThreadPoolExecutor as Executor

from kb4it.core.env import ENV
from kb4it.core.util import json_load
from kb4it.core.service import Service


class Frontend(Service):
    """KB4I Application Class.
    This class manages the Frontend (Themes).
    """
    srvthm = None

    def initialize(self):
        """"""
        backend = self.get_service('Backend')
        self.runtime = backend.get_runtime_dict()

    def theme_list(self):
        self.log.debug(" - List of themes available")

        self.log.debug(" - 1) Search themes installed globally (%s)", ENV['GPATH']['THEMES'])
        global_themes = os.listdir(ENV['GPATH']['THEMES'])
        n = 1
        for dirname in global_themes:
            try:
                self.theme_load(dirname)
                self.log.info(f" - [{n}] - (G) Theme '{self.runtime['theme']['id']}' ({self.runtime['theme']['description']})")
                n += 1
            except Exception as error:
                # ~ self.print_traceback()
                self.log.debug(" - \tTheme Id: '%s' NOT valid", dirname)
                raise

        self.log.debug(" - 2) Search themes installed locally (%s)", ENV['LPATH']['THEMES'])
        local_themes = os.listdir(ENV['LPATH']['THEMES'])
        if len(local_themes) > 0:
            for dirname in local_themes:
                self.log.debug("Looking for a theme in %s", dirname)
                try:
                    self.theme_load(dirname)
                    self.log.info(" - (L) Theme Id: '%s' (%s - %s)", self.runtime['theme']['id'], self.runtime['theme']['name'], self.runtime['theme']['description'])
                    n += 1
                except Exception as error:
                    self.print_traceback()
                    self.log.debug(" - Theme Id: '%s' NOT valid", dirname)
        if n == 0:
            self.log.info(" - No themes available")
        self.app.stop()

    def apps_list(self, theme: str):
        theme_path = self.theme_search(theme)
        if theme_path is not None:
            self.log.info(f" - List of apps available for theme '{theme}'")
            self.log.debug(f"Theme '{theme}' path: {theme_path}")
            apps_path = os.path.join(theme_path, 'apps', '*.json')
            apps = glob.glob(apps_path)
            for app in apps:
                app_name = os.path.basename(app)[:-5]
                self.log.info(f" - \tApp: '{app_name}'")
        else:
            self.log.error(f"Theme '{theme}' not found")

        self.app.stop()

    def theme_load(self, theme_name=None):
        """Load custom user theme, global theme or default."""
        if theme_name is None:
            theme_name = self.parameters.THEME

        # custom theme requested by user via command line properties
        self.runtime['theme'] = {}
        self.runtime['theme']['path'] = self.theme_search(theme_name)
        if self.runtime['theme']['path'] is None:
            return None
            self.runtime['theme']['path'] = os.path.join(ENV['GPATH']['THEMES'], 'default')
            self.log.warning(" - Fallback to default theme")

        theme_conf = os.path.join(self.runtime['theme']['path'], "theme.json")
        if not os.path.exists(theme_conf):
            self.log.warning(" - Theme config file not found: %s", theme_conf)
        else:
            # load theme configuration
            try:
                with open(theme_conf, 'r') as fth:
                    theme = json.load(fth)
                    for prop in theme:
                        self.runtime['theme'][prop] = theme[prop]
                self.log.debug(" - \tTheme %s v%s for KB4IT v%s", theme['name'], theme['version'], theme['kb4it'])
            except:
                self.log.error(" - \tTheme configuration file not valid: %s", theme_conf)
                return

            # Get theme directories
            self.runtime['theme']['templates'] = os.path.join(self.runtime['theme']['path'], 'templates')
            self.runtime['theme']['framework'] = os.path.join(self.runtime['theme']['path'], 'framework')
            self.runtime['theme']['images'] = os.path.join(self.runtime['theme']['path'], 'images')
            self.runtime['theme']['logic'] = os.path.join(self.runtime['theme']['path'], 'logic')

            # Register theme service
            sys.path.insert(0, self.runtime['theme']['logic'])
            try:
                from theme import Theme
                self.app.register_service('Theme', Theme())
                srvthm = self.get_service('Theme')
                self.log.debug("Theme '%s' loaded successfully", self.runtime['theme']['id'])
            except Exception as error:
                self.log.error("Theme '%s' couldn't be loaded:", self.runtime['theme']['id'])
                self.log.error(error)
                raise
            # ~ self.log.debug(" - Loaded theme '%s'", self.runtime['theme']['id'])

    def theme_search(self, theme=None):
        """Search custom theme."""
        if theme is None:
            # No custom theme passed in arguments. Autodetect.
            self.log.debug(" - Autodetecting theme from source path")
            source_path = self.runtime['dir']['source']
            source_resources_path = os.path.join(source_path, 'resources')
            source_themes_path = os.path.join(source_resources_path, 'themes')
            all_themes = os.path.join(source_themes_path, '*')
            self.log.debug(f" - Looking for first theme ocurrence in: {all_themes}")
            try:
                theme_path = glob.glob(all_themes)[0]
            except IndexError:
                theme_path = None
        else:
            self.log.debug(f" - \tFound directory for theme: '{theme}'")
            # Search in sources path
            source_path = self.runtime['dir']['source']
            theme_rel_path = os.path.join(os.path.join('resources', 'themes'))
            theme_path_source = os.path.join(source_path, theme_rel_path, theme) #theme_rel_path, theme)
            theme_path_opt = os.path.join(ENV['LPATH']['THEMES'], theme)
            theme_path_global = os.path.join(ENV['GPATH']['THEMES'], theme)
            # ~ self.log.debug(f" - From sources: {theme_path_source}")
            # ~ self.log.debug(f" - From optional: {theme_path_opt}") # DEPRECATE
            # ~ self.log.debug(f" - From global: {theme_path_global}")
            found = False
            for path in [theme_path_source, theme_path_opt, theme_path_global]:
                theme_config = os.path.join(path, 'theme.json')
                if not os.path.exists(theme_config):
                    theme_path = None
                else:
                    theme_path = path
                    break
        self.log.debug(f" - \tPath to theme '{theme}' found in: {theme_path}")
        return theme_path

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
from kb4it.core.service import Service


class Frontend(Service):
    """KB4I Application Class.
    This class manages the Frontend (Themes).
    """
    srvthm = None

    def get_services(self):
        """Get services needed."""
        self.srvdtb = self.get_service('DB')
        # ~ self.srvbes = self.get_service('Backend')

    def initialize(self, params:dict):
        """"""
        # ~ self.get_services()
        # ~ self.runtime = self.srvbes.get_runtime()
        self.log.info("[FRONTEND] - Paramters received:")
        self.log.info(f"[FRONTEND] - \t{params}")

    def set_config(self, repo: dict, runtime: dict):
        self.repo = repo
        self.runtime = runtime

    def theme_list(self):
        self.log.debug("[FRONTEND] - List of themes availables")

        self.log.debug("[FRONTEND] - Installed globally (%s)", ENV['GPATH']['THEMES'])
        global_themes = os.listdir(ENV['GPATH']['THEMES'])
        n = 0
        for dirname in global_themes:
            try:
                self.theme_load(dirname)
                self.log.info("[FRONTEND] - (G) Theme Id: '%s' (%s - %s)", self.runtime['theme']['id'], self.runtime['theme']['name'], self.runtime['theme']['description'])
                n += 1
            except Exception as error:
                # ~ self.print_traceback()
                self.log.debug("[FRONTEND] - Theme Id: '%s' NOT valid", dirname)

        self.log.debug("[FRONTEND] - Installed locally (%s)", ENV['LPATH']['THEMES'])
        local_themes = os.listdir(ENV['LPATH']['THEMES'])
        if len(local_themes) > 0:
            for dirname in local_themes:
                self.log.debug("Looking for a theme in %s", dirname)
                try:
                    self.theme_load(dirname)
                    self.log.info("[FRONTEND] - (L) Theme Id: '%s' (%s - %s)", self.runtime['theme']['id'], self.runtime['theme']['name'], self.runtime['theme']['description'])
                    n += 1
                except Exception as error:
                    self.print_traceback()
                    self.log.debug("[FRONTEND] - Theme Id: '%s' NOT valid", dirname)
        if n == 0:
            self.log.info("[FRONTEND] - No themes available")
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
            self.log.warning("[FRONTEND] - Fallback to default theme")

        theme_conf = os.path.join(self.runtime['theme']['path'], "theme.json")
        if not os.path.exists(theme_conf):
            self.log.warning("[FRONTEND] - Theme config file not found: %s", theme_conf)
        else:
            # load theme configuration
            try:
                with open(theme_conf, 'r') as fth:
                    theme = json.load(fth)
                    for prop in theme:
                        self.runtime['theme'][prop] = theme[prop]
                self.log.debug("[FRONTEND] - Name: %s" % self.runtime['theme']['name'])
                self.log.debug("[FRONTEND] - Theme %s v%s for KB4IT v%s", theme['name'], theme['version'], theme['kb4it'])
            except:
                self.log.error("[FRONTEND] - Theme configuration file not valid: %s", theme_conf)
                return

            # Get theme directories
            self.runtime['theme']['templates'] = os.path.join(self.runtime['theme']['path'], 'templates')
            self.runtime['theme']['framework'] = os.path.join(self.runtime['theme']['path'], 'framework')
            self.runtime['theme']['images'] = os.path.join(self.runtime['theme']['path'], 'images')
            self.runtime['theme']['logic'] = os.path.join(self.runtime['theme']['path'], 'logic')

            # Get date-based attributes from theme. Date attributes aren't
            # displayed as properties but used to build events pages.
            try:
                ignored_keys = self.runtime['theme']['ignored_keys']
                for key in ignored_keys:
                    self.srvdtb.ignore_key(key)
                self.log.debug("[FRONTEND] - Ignored keys defined by this theme: %s", ', '.join(ignored_keys))
            except KeyError:
                self.log.debug("[FRONTEND] - No ignored_keys defined in this theme")

            # Register theme service
            sys.path.insert(0, self.runtime['theme']['logic'])
            try:
                from theme import Theme
                self.app.register_service('Theme', Theme())
                self.srvthm = self.get_service('Theme')
            except Exception as error:
                self.log.warning("[FRONTEND] - Theme scripts for '%s' couldn't be loaded", self.runtime['theme']['id'])
                self.log.error("[FRONTEND] - %s", error)
                raise
            self.log.debug("[FRONTEND] - Loaded theme '%s'", self.runtime['theme']['id'])

    def theme_search(self, theme=None):
        """Search custom theme."""
        if theme is None:
            # No custom theme passed in arguments. Autodetect.
            self.log.debug("[FRONTEND] - Autodetecting theme from source path")
            source_path = self.runtime['dir']['source']
            source_resources_path = os.path.join(source_path, 'resources')
            source_themes_path = os.path.join(source_resources_path, 'themes')
            all_themes = os.path.join(source_themes_path, '*')
            self.log.debug(f"[FRONTEND] - Looking for first theme ocurrence in: {all_themes}")
            try:
                theme_path = glob.glob(all_themes)[0]
            except IndexError:
                theme_path = None
        else:
            self.log.debug(f"[FRONTEND] - Looking for theme: '{theme}'")
            # Search in sources path
            source_path = self.runtime['dir']['source']
            theme_rel_path = os.path.join(os.path.join('resources', 'themes'))
            theme_path_source = os.path.join(source_path, theme_rel_path, theme) #theme_rel_path, theme)
            theme_path_opt = os.path.join(ENV['LPATH']['THEMES'], theme)
            theme_path_global = os.path.join(ENV['GPATH']['THEMES'], theme)
            self.log.debug(f"[FRONTEND] - From sources: {theme_path_source}")
            self.log.debug(f"[FRONTEND] - From optional: {theme_path_opt}") # DEPRECATE
            self.log.debug(f"[FRONTEND] - From global: {theme_path_global}")
            found = False
            for path in [theme_path_source, theme_path_opt, theme_path_global]:
                theme_config = os.path.join(path, 'theme.json')
                if not os.path.exists(theme_config):
                    theme_path = None
                else:
                    theme_path = path
                    break
        self.log.debug(f"[FRONTEND] - Path to theme '{theme}' found in: {theme_path}")
        return theme_path

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

from kb4it.core.env import LPATH, GPATH #, APP, ADOCPROPS, MAX_WORKERS, EOHMARK
from kb4it.core.service import Service
# ~ from kb4it.core.util import valid_filename, load_kbdict
# ~ from kb4it.core.util import exec_cmd, delete_target_contents
# ~ from kb4it.core.util import get_source_docs, get_asciidoctor_attributes
# ~ from kb4it.core.util import get_hash_from_file, get_hash_from_dict
# ~ from kb4it.core.util import save_kbdict, copy_docs, copydir
# ~ from kb4it.core.util import file_timestamp
# ~ from kb4it.core.util import string_timestamp


class Frontend(Service):
    """KB4I Application Class.

    This class manages the Frontend (Themes).
    """
    srvthm = None

    def get_services(self):
        """Get services needed."""
        self.srvdtb = self.get_service('DB')
        self.backend = self.get_service('Backend')

    def initialize(self):
        """"""
        self.get_services()
        self.runtime = self.backend.get_runtime_properties()

    def theme_list(self):
        self.log.info("[THEME] - List of themes availables")

        self.log.debug("[THEME] - Installed globally (%s)", GPATH['THEMES'])
        global_themes = os.listdir(GPATH['THEMES'])
        n = 0
        for dirname in global_themes:
            try:
                self.theme_load(dirname)
                self.log.info("[THEME] - (G) Theme Id: '%s' (%s - %s)", self.runtime['theme']['id'], self.runtime['theme']['name'], self.runtime['theme']['description'])
                n += 1
            except Exception as error:
                # ~ self.print_traceback()
                self.log.debug("[THEME] - Theme Id: '%s' NOT valid", dirname)

        self.log.debug("[THEME] - Installed locally (%s)", LPATH['THEMES'])
        local_themes = os.listdir(LPATH['THEMES'])
        if len(local_themes) > 0:
            for dirname in local_themes:
                try:
                    self.theme_load(dirname)
                    self.log.info("[THEME] - (L) Theme Id: '%s' (%s - %s)", self.runtime['theme']['id'], self.runtime['theme']['name'], self.runtime['theme']['description'])
                    n += 1
                except Exception as error:
                    self.print_traceback()
                    self.log.debug("[THEME] - Theme Id: '%s' NOT valid", dirname)
        if n == 0:
            self.log.info("[THEME] - No themes available")
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
            self.runtime['theme']['path'] = os.path.join(GPATH['THEMES'], 'default')
            self.log.warning("[THEME] - Fallback to default theme")

        theme_conf = os.path.join(self.runtime['theme']['path'], "theme.adoc")
        if not os.path.exists(theme_conf):
            self.log.error("[THEME] - Theme config file not found: %s", theme_conf)
            sys.exit(-1)

        # load theme configuration
        with open(theme_conf, 'r') as fth:
            theme = json.load(fth)
            for prop in theme:
                self.runtime['theme'][prop] = theme[prop]
        self.log.debug("[THEME] - Name: %s" % self.runtime['theme']['name'])

        self.log.debug("[THEME] - Theme %s v%s for KB4IT v%s", theme['name'], theme['version'], theme['kb4it'])

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
                self.log.debug("[THEME] - Ignored key(s) defined by this theme: %s", key)
                self.srvdtb.ignore_key(key)
        except KeyError:
            self.log.debug("[THEME] - No ignored_keys defined in this theme")

        # Register theme service
        sys.path.insert(0, self.runtime['theme']['logic'])
        try:
            from theme import Theme
            self.log.debug(type(Theme))
            self.app.register_service('Theme', Theme())
            self.log.warning("Registered Service Theme")
            self.srvthm = self.get_service('Theme')
        except Exception as error:
            self.log.warning("[THEME] - Theme scripts for '%s' couldn't be loaded", self.runtime['theme']['id'])
            self.log.error("[THEME] - %s", error)
            raise
        self.log.debug("[THEME] - Loaded theme '%s'", self.runtime['theme']['id'])

    def theme_search(self, theme=None):
        """Search custom theme."""
        if theme is None:
            # No custom theme passed in arguments. Autodetect.
            self.log.debug("[THEME] - Autodetecting theme from source path")
            source_path = self.backend.get_source_path()
            source_resources_path = os.path.join(source_path, 'resources')
            source_themes_path = os.path.join(source_resources_path, 'themes')
            all_themes = os.path.join(source_themes_path, '*')
            self.log.debug("[THEME] - Looking for first theme ocurrence in: %s", all_themes)
            try:
                theme_path = glob.glob(all_themes)[0]
            except IndexError:
                theme_path = None
        else:
            self.log.debug("[THEME] - Looking for theme: %s", theme)
            # Search in sources path
            source_path = self.backend.get_source_path()
            theme_rel_path = os.path.join(os.path.join('resources', 'themes'), theme)
            theme_path = os.path.join(self.backend.get_source_path(), theme_rel_path)
            if not os.path.exists(theme_path):
                # Search for theme in KB4IT global theme
                theme_path = os.path.join(GPATH['THEMES'], theme)
                if not os.path.exists(theme_path):
                    # No theme found
                    theme_path = None
        self.log.debug("[THEME] - Path to theme: %s", theme_path)
        return theme_path

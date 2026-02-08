#!/usr/bin/env python

"""
Module with the application logic.
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: module holding the application logic
"""

import os
import shutil
from pathlib import Path

from kb4it.core.env import ENV
from kb4it.core.service import Service
from kb4it.core.util import valid_filename
from kb4it.core.util import get_source_docs, get_asciidoctor_attributes
from kb4it.core.util import get_hash_from_file, get_hash_from_dict, get_hash_from_list
from kb4it.core.util import string_timestamp
from kb4it.core.util import json_load, json_save
from kb4it.core.perf import timeit
from kb4it.core.log import redirect_logs


class Backend(Service):
    """Backend class for managing the main logic workflow.
    """

    def _initialize(self):
        """Initialize application structure."""
        self.runtime = {}        # Dictionary of runtime properties
        self.kbdict_new = {}     # New compilation cache
        self.kbdict_cur = {}     # Cached data
        self.force_keys = set()  # List of keys which must be compiled (forced)

        # Get params from command line
        self.params = self.app.get_params()

        # Check command line param for config file
        action = self.params.get('action')
        if action in ('build', 'info'):
            config_file = self.params.get('config')
            if config_file is None:
                self.app.stop(error=True)

            # Check if it exists
            config_path = Path(config_file).absolute()
            if config_path.exists():
                try:
                    self.log.debug(f"CONF[REPO] Config file: {config_path}")
                    self.repo = json_load(config_path)
                    self.log.debug(f"CONF[REPO] Configuration loaded successfully")
                except AttributeError as error:
                    self.log.error(f"Repository config couldn't be parsed (probably not well formed)")
                    self.log.error(error)
                    self.app.stop(error=True)
                except Exception as error:
                    self.log.error(error)
                    self.app.stop(error=True)
            else:
                self.log.error(f"Config path '{config_path}' does not exist")
                self.app.stop(error=True)

            root_path = config_path.parent
            dir_source = self.repo.get('dir_source') or Path(root_path, 'source')
            dir_target = self.repo.get('dir_target') or Path(root_path, 'target')

            self.params['force'] = self.repo.get('force') or False


            self.runtime['dir'] = {}
            self.runtime['dir']['source'] = os.path.realpath(self.repo['source'])
            self.runtime['dir']['target'] = os.path.realpath(self.repo['target'])

            dir_src = Path(self.get_path('source'))
            dir_root = dir_src.parent.absolute()
            dir_var = Path.joinpath(dir_root, 'var')
            dir_log = Path.joinpath(dir_var, 'log')
            dir_tmp = Path.joinpath(dir_var, 'tmp')
            dir_cache = Path.joinpath(dir_var, 'cache')
            dir_www = Path.joinpath(dir_var, 'www')
            dir_dist = Path.joinpath(dir_var, 'dist')
            dir_db = Path.joinpath(dir_var, 'db')

            self.runtime['dir']['tmp'] = dir_tmp
            self.runtime['dir']['www'] = dir_www
            self.runtime['dir']['dist'] = dir_dist
            self.runtime['dir']['cache'] = dir_cache
            self.runtime['dir']['log'] = dir_log
            self.runtime['dir']['db'] = dir_db

            for entry in self.runtime['dir']:
                create_directory = False
                dirname = self.runtime['dir'][entry]
                if entry not in ['source', 'target']:
                    dirname = self.runtime['dir'][entry]
                    if not os.path.exists(dirname):
                        os.makedirs(dirname, exist_ok=True)
                        # ~ create_directory = True
                        # ~ self.log.debug(f"    \tCreate directory {dirname}? {create_directory}")

            # Activate application log
            app_log_file = Path.joinpath(dir_log, "kb4it.log")
            self.runtime['logfile'] = app_log_file
            self.log.debug(f"CONF[APP] LOG_FILE[{app_log_file}]")
            if os.path.exists(app_log_file):
                os.unlink(app_log_file)
            kb4it_temp_log = self.app.get_log_file()
            shutil.copy(kb4it_temp_log, app_log_file)
            redirect_logs(app_log_file)

            self.runtime['sort_attribute'] = self.repo.get('sort')
            if self.runtime['sort_attribute'] is None:
                self.log.error("No property 'sort' defined in repository config")
                self.app.stop(error=True)

            # Initialize docs structure
            self.runtime['docs'] = {}
            self.runtime['docs']['count'] = 0
            self.runtime['docs']['bag'] = []
            self.runtime['docs']['targets'] = set()

            # Load cache dictionary from last run
            self.kbdict_cur = self.load_kbdict()

            # And initialize the new one
            self.kbdict_new['document'] = {}
            self.kbdict_new['metadata'] = {}

            # Get services
            self.get_services()

    def get_value(self, domain: str, key: str):
        if domain == 'app':
            adict = self.params
        elif domain == 'docs':
            adict = self.runtime['docs']
        elif domain == 'kbcur':
            adict = self.kbdict_cur
        elif domain == 'kbnew':
            adict = self.kbdict_new
        elif domain == 'repo':
            adict = self.repo
        elif domain == 'runtime':
            adict = self.runtime
        elif domain == 'theme':
            adict = self.runtime['theme']
        else:
            return None
        return adict.get(key)

    def set_value(self, doamin: str, key: str, value: str|int|bool):
        if domain == 'app':
            adict = self.params
        adict[key] = value


    def get_dict(self, domain: str) -> dict:
        if domain == 'app':
            return self.params
        elif domain == 'docs':
            return self.runtime['docs']
        elif domain == 'kbcur':
            return self.kbdict_cur
        elif domain == 'kbnew':
            return self.kbdict_new
        elif domain == 'repo':
            return self.repo
        elif domain == 'runtime':
            return self.runtime
        elif domain == 'theme':
            return self.runtime['theme']
        else:
            return None

    def get_path(self, name: str):
        return self.runtime['dir'].get(name)

    def load_kbdict(self):
        """C0111: Missing function docstring (missing-docstring)."""
        KB4IT_DB_FILE = os.path.join(self.get_path('db'), "kbdict.json")
        try:
            kbdict = json_load(KB4IT_DB_FILE)
            self.log.debug(f"[CONF] - Loading KBDICT from {KB4IT_DB_FILE}")
        except FileNotFoundError:
            kbdict = {}
            kbdict['document'] = {}
            kbdict['metadata'] = {}
        except Exception as error:
            self.log.error(f"There was an error reading file {KB4IT_DB_FILE}")
            self.log.error(error)
            self.app.stop(error=True)
        self.log.debug(f"[CONF] - Current kbdict entries: {len(kbdict)}")
        return kbdict

    def save_kbdict(self, kbdict):
        """C0111: Missing function docstring (missing-docstring)."""
        KB4IT_DB_FILE = os.path.join(self.get_path('db'), "kbdict.json")
        json_save(KB4IT_DB_FILE, kbdict)
        self.log.debug(f"[CONF] - KBDICT {KB4IT_DB_FILE} saved")

    def add_target(self, adocId, htmlId):
        """All objects received by this method will be appended to the
        list of objects that will be copied to the target directory.
        """
        self.runtime['docs']['targets'].add(htmlId)
        self.log.debug(f"DOC[{adocId}] targets to RESOURCE[{htmlId}]")

    def get_services(self):
        """Get services needed."""
        self.srvdtb = self.get_service('DB')
        self.srvbld = self.get_service('Builder')

        from kb4it.services.processor import Processor
        self.app.register_service('Processor', Processor())
        self.srvprc = self.get_service('Processor')

    def stage_01_check_environment(self):
        """Check environment."""
        frontend = self.get_service('Frontend')
        self.log.debug(f"[CHECKS] - START")
        self.log.debug(f"CONF[APP] DIR[CACHE] VALUE[{self.get_path('cache')}]")
        self.log.debug(f"CONF[APP] DIR[WORKDIR] VALUE[{self.get_path('tmp')}]")
        self.log.debug(f"CONF[APP] DIR[DISTRIBUTION] VALUE[{self.get_path('dist')}]")
        self.log.debug(f"CONF[APP] DIR[TMPWWW] VALUE[{self.get_path('www')}]")

        # Check if source directory exists. If not, stop application
        if not os.path.exists(self.get_path('source')):
            self.log.error(f"Source directory '{self.get_path('source')}' doesn't exist.")
            self.app.stop(error=True)
        self.log.debug(f"CONF[APP] DIR[SOURCE] VALUE[{self.get_path('source')}]")

        # check if target directory exists. If not, create it:
        if not os.path.exists(self.get_path('target')):
            os.makedirs(self.get_path('target'), exist_ok=True)
        self.log.debug(f"CONF[APP] DIR[TARGET] VALUE[{self.get_path('target')}]")

        theme_name = self.get_value('repo', 'theme')
        if theme_name is None:
            self.log.debug(f"Theme not provided.")
            self.app.stop(error=True)
        else:
            theme_path = frontend.theme_search(theme_name)
            if theme_path is not None:
                frontend.theme_load(os.path.basename(theme_path))
            else:
                self.log.error(f"Theme '{theme_name}' not found")
                self.log.error(f"[CHECKS] - END")
                self.app.stop(error=True)
        self.log.debug(f"[CHECKS] - END")


    def stage_02_get_source_documents(self):
        """Get Asciidoctor documents from source directory."""
        self.log.debug(f"[SOURCES] - START")
        sources_path = self.get_path('source')

        # Firstly, allow theme to generate documents
        self.srvthm = self.get_service('Theme')

        # If 'about_app.adoc' doesn't exist, create one from template
        # FIXME: if no file exists, tell theme
        about_app_source = os.path.join(sources_path, 'about_app.adoc')
        if not os.path.exists(about_app_source):
            about_app_default = os.path.join(ENV['GPATH']['TEMPLATES'], 'PAGE_ABOUT_APP.tpl')
            shutil.copy(about_app_default, about_app_source)
            self.log.warning("  - Added missing 'About App' to your sources")

        # Then, get them
        self.runtime['docs']['bag'] = get_source_docs(sources_path)
        basenames = []
        for filepath in self.runtime['docs']['bag']:
            basenames.append(os.path.basename(filepath))
        self.runtime['docs']['filenames'] = basenames
        self.runtime['docs']['count'] = len(self.runtime['docs']['bag'])
        self.log.debug(f"STATS - Found {self.runtime['docs']['count']} asciidoctor documents in source directory")
        self.log.debug(f"[SOURCES] - END")


    def stage_03_preprocessing(self):
        """
        Extract metadata from source docs into a dict.
        Create metadata section for each adoc and insert it after the
        EOHMARK.
        In this way, after being compiled into HTML, final adocs are
        browsable throught its metadata.
        """
        self.log.debug(f"[EXTRACTION] - START")
        self.srvprc.step_00_extraction()

    def get_kb_dict(self):
        return self.srvprc.get_kb_dict()

    def get_kbdict_key(self, key, new=True):
        return self.srvprc.get_kbdict_key(self, key, new=True)

    def get_kbdict_value(self, key, value, new=True):
        return self.srvprc.get_kbdict_value(self, key, new=True)

    def stage_04_processing(self):
        """Process all keys/values got from documents.
        The algorithm detects which keys/values have changed and compile
        them again. This avoid recompile the whole database, saving time
        and CPU.
        """
        self.srvprc.stage_04_processing()


    def stage_05_compilation(self):
        """Compile documents to html with asciidoctor."""
        from kb4it.services.compiler import Compiler
        self.app.register_service('Compiler', Compiler())
        compiler = self.app.get_service('Compiler')
        compiler.execute()
        return


    def stage_06_theme(self):
        self.log.debug(f"[PROCESSING THEME] - START")
        self.srvthm.build()
        self.log.debug(f"[PROCESSING THEME] - END")



    def stage_07_deploy(self):
        from kb4it.services.deployer import Deployer
        self.app.register_service('Deployer', Deployer())
        deployer = self.app.get_service('Deployer')
        deployer.execute()

    def _finalize(self):
        pass

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
from kb4it.core.service import Service
from kb4it.core.util import get_source_docs
from kb4it.core.util import get_hash_from_file
from kb4it.core.util import get_hash_from_content
from kb4it.core.util import json_load
from kb4it.core.util import json_save
from kb4it.core.log import redirect_logs
from kb4it.services.processor import Processor
from kb4it.services.compiler import Compiler
from kb4it.services.deployer import Deployer

class Backend(Service):
    """(Second) KB4IT Initialization."""

    def _initialize(self):
        """Initialize application structure."""
        self.runtime = {}                   # Dictionary of runtime properties
        self.params = self.app.get_params() # Get params from command line

        # Check command line param for config file
        # ~ action = self.params.get('action')
        if self.params.get('action') in ('build', 'info'):
            config_file = self.params.get('config')
            if config_file is None:
                self.app.stop(error=True)

            # Check if it exists
            config_path = Path(config_file).absolute()
            if config_path.exists():
                try:
                    self.log.debug(f"CONF[REPO] Config file: {config_path}")
                    self.repo = json_load(config_path)
                    self.log.debug("CONF[REPO] Configuration loaded")
                except AttributeError as error:
                    self.log.error("Repo config couldn't be parsed")
                    self.log.error(error)
                    self.app.stop(error=True)
                except Exception as error:
                    self.log.error(error)
                    self.app.stop(error=True)
            else:
                self.log.error(f"Config path '{config_path}' does not exist")
                self.app.stop(error=True)

            self.params['force'] = self.repo.get('force') or False
            self.runtime['dir'] = {}
            self.runtime['dir']['source'] = os.path.realpath(self.repo['source'])
            self.runtime['dir']['target'] = os.path.realpath(self.repo['target'])

            # ~ dir_src = Path(self.get_path('source'))
            dir_root = Path(self.get_path('source')).parent.absolute()
            dir_var = Path.joinpath(dir_root, 'var')
            dir_log = Path.joinpath(dir_var, 'log')
            dir_tmp = Path.joinpath(dir_var, 'tmp')
            dir_cache = Path.joinpath(dir_var, 'cache')
            dir_www = Path.joinpath(dir_var, 'www')
            dir_db = Path.joinpath(dir_var, 'db')

            self.runtime['dir']['tmp'] = dir_tmp
            self.runtime['dir']['www'] = dir_www
            self.runtime['dir']['cache'] = dir_cache
            self.runtime['dir']['log'] = dir_log
            self.runtime['dir']['db'] = dir_db

            for entry in self.runtime['dir']:
                dirname = self.runtime['dir'][entry]
                if entry not in ['source', 'target']:
                    dirname = self.runtime['dir'][entry]
                    if not os.path.exists(dirname):
                        os.makedirs(dirname, exist_ok=True)

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

            # Get services
            self.get_services()

    def get_value(self, domain: str, key: str):
        """Get value from key given a domain."""
        if domain == 'app':
            adict = self.params
        elif domain == 'docs':
            adict = self.runtime['docs']
        elif domain == 'repo':
            adict = self.repo
        elif domain == 'runtime':
            adict = self.runtime
        elif domain == 'theme':
            adict = self.runtime['theme']
        else:
            return None
        return adict.get(key)

    def set_value(self, domain: str, key: str, value: str | int | bool):
        """Set a value for a specific key in a given domain."""
        if domain == 'app':
            adict = self.params
        elif domain == 'runtime':
            adict = self.runtime
        else:
            adict = None

        if adict is None:
            self.log.error(f"Dictionary doesn't exist for domain {domain}")
        else:
            adict[key] = value

    def get_dict(self, domain: str) -> dict:
        """Get dict by domain."""
        if domain == 'app':
            adict = self.params
        elif domain == 'docs':
            adict = self.runtime['docs']
        elif domain == 'repo':
            adict = self.repo
        elif domain == 'runtime':
            adict = self.runtime
        elif domain == 'theme':
            adict = self.runtime['theme']
        else:
            adict = None
        return adict

    def get_path(self, name: str):
        """Get path by name."""
        return self.runtime['dir'].get(name)

    def load_kbdict(self):
        """Load KB4IT dictionary."""
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
        """Save kb4it dictionary."""
        KB4IT_DB_FILE = os.path.join(self.get_path('db'), "kbdict.json")
        json_save(KB4IT_DB_FILE, kbdict)
        self.log.debug(f"[CONF] - KBDICT {KB4IT_DB_FILE} saved")

    def add_target(self, adocId, htmlId):
        """Add documents to be compiled."""
        self.runtime['docs']['targets'].add(htmlId)
        self.log.debug(f"DOC[{adocId}] targets to RESOURCE[{htmlId}]")

    def get_services(self):
        """Get services needed."""
        self.srvbld = self.get_service('Builder')
        self.app.register_service('Processor', Processor())
        self.srvprc = self.get_service('Processor')

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
        frontend = self.get_service('Frontend')
        self.log.debug("[CHECKS] - START")
        self.log.debug(f"CONF[APP] DIR[CACHE] VALUE[{self.get_path('cache')}]")
        self.log.debug(f"CONF[APP] DIR[WORKDIR] VALUE[{self.get_path('tmp')}]")
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
            self.log.debug("Theme not provided.")
            self.app.stop(error=True)
        else:
            theme_path = frontend.theme_search(theme_name)
            if theme_path is not None:
                frontend.theme_load(os.path.basename(theme_path))
            else:
                self.log.error(f"Theme '{theme_name}' not found")
                self.log.error("[CHECKS] - END")
                self.app.stop(error=True)
        self.log.debug("[CHECKS] - END")

    def stage_02_get_source_documents(self):
        """Get Asciidoctor documents from source directory."""
        self.log.debug("[SOURCES] - START")
        sources_path = self.get_path('source')

        # Firstly, allow theme to generate documents
        self.srvthm = self.get_service('Theme')

        # If 'about_kb4it.adoc' doesn't exist, create one from template
        var = self.srvbld.get_theme_var()
        NEW_VERSION = False
        TPL_PAGE_ABOUT_KB4IT = self.srvbld.template('PAGE_ABOUT_KB4IT')
        about_kb4it_content = TPL_PAGE_ABOUT_KB4IT.render(var=var)
        about_kb4it_target = os.path.join(sources_path, 'about_kb4it.adoc')
        if os.path.exists(about_kb4it_target):
            # About KB4IT asciidoc page is already in sources
            # Then, check if hashes matches with the KB4IT's one.
            md5_source = get_hash_from_content(about_kb4it_content)
            md5_target = get_hash_from_file(about_kb4it_target)
            if md5_source != md5_target:
                NEW_VERSION = True
        else:
            NEW_VERSION = True

        if NEW_VERSION:
            # FIXME: Force compilation if new KB4IT version?
            # Yes. But starting with v0.8 and major.minor versions.
            # Skip patches.
            self.log.debug("[DOC] - Added/Replaced 'About KB4IT' to your sources")
            with open(about_kb4it_target, 'w', encoding='utf-8') as fout:
                fout.write(about_kb4it_content)

        # If 'about_app.adoc' doesn't exist, create one from template
        about_app_source = os.path.join(sources_path, 'about_app.adoc')
        if not os.path.exists(about_app_source):
            about_app_default = os.path.join(ENV['GPATH']['TEMPLATES'], 'PAGE_ABOUT_APP.tpl')
            shutil.copy(about_app_default, about_app_source)
            self.log.warning("[DOC] - Added missing 'About App' to your sources")

        # Then, get them
        self.runtime['docs']['bag'] = get_source_docs(sources_path)
        basenames = []
        for filepath in self.runtime['docs']['bag']:
            basenames.append(os.path.basename(filepath))
        self.runtime['docs']['filenames'] = basenames
        self.runtime['docs']['count'] = len(self.runtime['docs']['bag'])
        self.log.debug(f"STATS - Found {self.runtime['docs']['count']} docs")
        self.log.debug("[SOURCES] - END")

    def stage_03_process_sources(self):
        """Extract, Analyze and Transform."""
        self.log.debug("[EXTRACTION] - START")
        self.srvprc.step_00_extraction()
        self.srvprc.step_01_analysis()
        self.srvprc.step_02_transformation()

    def stage_04_process_theme(self):
        """Run theme logic."""
        self.log.debug("[PROCESSING THEME] - START")
        self.srvthm.build()
        self.log.debug("[PROCESSING THEME] - END")

    def stage_05_compilation(self):
        """Compile documents to html with asciidoctor."""
        self.app.register_service('Compiler', Compiler())
        compiler = self.app.get_service('Compiler')
        compiler.execute()

    def stage_06_deploy(self):
        """Recreate target."""
        self.app.register_service('Deployer', Deployer())
        deployer = self.app.get_service('Deployer')
        deployer.execute()

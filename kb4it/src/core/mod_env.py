#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Environment module.

# File: mod_env.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: Environment variables module
"""

import os
from os.path import abspath
import sys
import glob


ROOT = abspath(sys.modules[__name__].__file__ + "/../../../")
USER_DIR = os.path.expanduser('~')

APP = {}
APP['shortname'] = "KB4IT"

# Local paths
LPATH = {}
LPATH['ROOT'] = os.path.join(USER_DIR, ".%s" % APP['shortname'].lower())
LPATH['ETC'] = os.path.join(LPATH['ROOT'], 'etc')
LPATH['VAR'] = os.path.join(LPATH['ROOT'], 'var')
LPATH['DB'] = os.path.join(LPATH['VAR'], 'db')
LPATH['PLUGINS'] = os.path.join(LPATH['VAR'], 'plugins')
LPATH['LOG'] = os.path.join(LPATH['VAR'], 'log')
LPATH['TMP'] = os.path.join(LPATH['VAR'], 'tmp')
LPATH['CACHE'] = os.path.join(LPATH['VAR'], 'cache')
LPATH['DB'] = os.path.join(LPATH['VAR'], 'db')
LPATH['WWW'] = os.path.join(LPATH['VAR'], 'www')
LPATH['EXPORT'] = os.path.join(LPATH['VAR'], 'export')
LPATH['OPT'] = os.path.join(LPATH['ROOT'], 'opt')

# Global paths
GPATH = {}
GPATH['ROOT'] = ROOT
GPATH['DATA'] = os.path.join(GPATH['ROOT'], 'kb4it')
GPATH['RESOURCES'] = os.path.join(GPATH['ROOT'], 'resources')
GPATH['OFFLINE'] = os.path.join(GPATH['RESOURCES'], 'offline')
GPATH['APPDATA'] = os.path.join(GPATH['OFFLINE'], 'appdata')
GPATH['ADOCS'] = os.path.join(GPATH['OFFLINE'], 'sources')
GPATH['TEMPLATES'] = os.path.join(GPATH['OFFLINE'], 'templates')
GPATH['DOCINFO'] = os.path.join(GPATH['OFFLINE'], 'docinfo')
GPATH['ONLINE'] = os.path.join(GPATH['RESOURCES'], 'online')
GPATH['IMAGES'] = os.path.join(GPATH['ONLINE'], 'images')
GPATH['AUTHORS'] = os.path.join(GPATH['IMAGES'], 'authors')
GPATH['SHARE'] = os.path.join(GPATH['DATA'], 'share')
GPATH['DOC'] = os.path.join(GPATH['SHARE'], 'docs')
GPATH['RES'] = os.path.join(GPATH['DATA'], 'res')
GPATH['HELP'] = os.path.join(GPATH['DATA'], 'help')
GPATH['HELP_HTML'] = os.path.join(GPATH['HELP'], 'html')

VERSION = open(os.path.join(GPATH['APPDATA'], 'VERSION'), 'r').read()

# App Info
APP['name'] = "Knowledge Base For IT"
APP['license'] = "The code is licensed under the terms of the  GPL v3\n\
                  so you're free to grab, extend, improve and fork the \
                  code\nas you want"
APP['copyright'] = "Copyright \xa9 2019 Tomás Vírseda"
APP['desc'] = ""
APP['version'] = VERSION
APP['authors'] = ["Tomás Vírseda <tomasvirseda@gmail.com>"]
APP['documenters'] = ["Tomás Vírseda <tomasvirseda@gmail.com>"]

# Configuration, SAP Notes Database and Log files
FILE = {}
FILE['CNF'] = os.path.join(LPATH['ETC'], APP['shortname'].lower(), '.ini')
FILE['LOG'] = os.path.join(LPATH['LOG'] + APP['shortname'].lower(), '.log')
FILE['HELP_INDEX'] = os.path.join(GPATH['HELP_HTML'], 'index.html')
FILE['FOOTER'] = os.path.join(GPATH['DOCINFO'], 'footer.html')
FILE['HEADER'] = os.path.join(GPATH['DOCINFO'], 'header.html')
FILE['AUTHOR_UNKNOWN'] = os.path.join(GPATH['AUTHORS'], 'author_unknown.png')
# ~ FILE['KBDICT'] = LPATH['DB'] + 'kbdict.json'

MAX_WORKERS = 30
EOHMARK = """// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE"""
ADOCPROPS = {
    'source-highlighter': 'coderay',
    'toc': 'left',
    'toclevels': '3',
    'icons'                 :   'font',
    # ~ 'experimental'          :   None,
    # ~ 'linkcss'               :   None,
    # ~ 'stylesheet'            :   'kb4it.css',
    # ~ 'stylesdir'             :   'resources/uikit/css',
    # ~ 'imagesdir'             :   'resources/images',
    # ~ 'scriptsdir'            :   'resources/uikit/js',
    # ~ 'iconfont-remote!'      :   None,
    # ~ 'iconfont-name'         :   'fontawesome-4.7.0',
    # ~ 'experimental'          :   None,
    # ~ 'docinfo'               :   'shared',
    # ~ 'docinfodir'            :   'resources/docinfo',
}

TEMPLATES = {}
for filename in glob.glob(os.path.join(GPATH['TEMPLATES'], '*.tpl')):
    template = os.path.basename(filename)[:-4]
    TEMPLATES[template] = open(filename, 'r').read()

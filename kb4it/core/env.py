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

ROOT = abspath(sys.modules[__name__].__file__ + "/../../")
USER_DIR = os.path.expanduser('~')

# App Info
APP = {}
APP['name'] = "Knowledge Base For IT"
APP['shortname'] = "KB4IT"
APP['description'] = "KB4IT is a static website generator based on \
                      Asciidoctor sources mainly for technical \
                      documentation purposes."
APP['license'] = 'GPL v3'
APP['license_long'] = "The code is licensed under the terms of the  GPL v3\n\
                  so you're free to grab, extend, improve and fork the \
                  code\nas you want"
APP['copyright'] = "Copyright \xa9 2019 Tomás Vírseda"
APP['desc'] = ""
APP['version'] = '0.7.6.8'
APP['author'] = 'Tomás Vírseda'
APP['author_email'] = 'tomasvirseda@gmail.com'
APP['documenters'] = ["Tomás Vírseda <tomasvirseda@gmail.com>"]
APP['website'] = 'https://github.com/t00m/KB4IT'

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
LPATH['DISTRIBUTED'] = os.path.join(LPATH['CACHE'], 'distributed')
LPATH['DB'] = os.path.join(LPATH['VAR'], 'db')
LPATH['WWW'] = os.path.join(LPATH['VAR'], 'www')
LPATH['EXPORT'] = os.path.join(LPATH['VAR'], 'export')
LPATH['OPT'] = os.path.join(LPATH['ROOT'], 'opt')
LPATH['THEMES'] = os.path.join(LPATH['OPT'], 'themes')

# Global paths
GPATH = {}
GPATH['ROOT'] = ROOT
GPATH['DATA'] = os.path.join(GPATH['ROOT'], 'kb4it')
GPATH['RESOURCES'] = os.path.join(GPATH['ROOT'], 'resources')
GPATH['ONLINE'] = os.path.join(GPATH['RESOURCES'], 'online')
GPATH['IMAGES'] = os.path.join(GPATH['ONLINE'], 'images')
GPATH['COMMON'] = os.path.join(GPATH['RESOURCES'], 'common')
GPATH['THEMES'] = os.path.join(GPATH['RESOURCES'], 'themes')
GPATH['APPDATA'] = os.path.join(GPATH['COMMON'], 'appdata')
GPATH['RES'] = os.path.join(GPATH['DATA'], 'res')


# Configuration, SAP Notes Database and Log files
FILE = {}
FILE['CNF'] = os.path.join(LPATH['ETC'], APP['shortname'].lower(), '.ini')
FILE['LOG'] = os.path.join(LPATH['LOG'] + APP['shortname'].lower(), '.log')

# Compilation stuff
MAX_WORKERS = 30
EOHMARK = """// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE"""
ADOCPROPS = {
    'source-highlighter': 'coderay',
    'toc': 'left',
    'toclevels': '3',
    'icons': 'font',
    'linkcss': None,
}

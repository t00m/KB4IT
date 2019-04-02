#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: constants module
"""

import os

KB4IT_NAME = 'KB4IT'
KB4IT_VERSION = '0.5'
KB4IT_LICENSE = 'GPL v3'
KB4IT_DESC = 'A static website generator for documentation repositories based on Asciidoc sources'


SEP = os.sep
KB4IT_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
KB4IT_RES_DIR = KB4IT_SCRIPT_DIR + SEP + 'resources'
MAX_WORKERS = 30
EOHMARK = """// END-OF-HEADER. DO NOT MODIFY OR DELETE THIS LINE"""
ADOCPROPS = {
    'source-highlighter'    :   'coderay',
    'stylesheet'            :   'kb4it.css',
    'stylesdir'             :   'resources/css',
    'imagesdir'             :   'resources/images',
    'scriptsdir'            :   'resources/js/jquery',
    'toc'                   :   'left',
    'toclevels'             :   '6',
    'icons'                 :   'font',
    'iconfont-remote!'      :   None,
    'iconfont-name'         :   'fontawesome-4.7.0',
    'experimental'          :   None,
    'linkcss'               :   None,
    'docinfo1'              :   'shared-header',
    'docinfo2'              :   'shared-footer',
    'docinfodir'            :   'resources/docinfo',
    #~ 'noheader'              :   None,
    #~ 'nofooter'              :   None,
}

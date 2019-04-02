#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Authors: Tomás Vírseda <tomasvirseda@gmail.com>
# KB4IT is a static website generator based on Asciidoc sources
# Copyright (C) 2016-2017 Tomás Vírseda
#
# KB4IT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# KB4IT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with KB4IT.  If not, see <http://www.gnu.org/licenses/gpl.html>

import os
import subprocess
from setuptools import setup


with open('README') as f:
    long_description = f.read()

def add_data():
    try:
        data_files = [
            ('kb4it/resources/offline/templates',
                [
                    'kb4it/resources/offline/templates/TPL_INDEX.tpl',
                    'kb4it/resources/offline/templates/TPL_KEY_PAGE.tpl',
                    'kb4it/resources/offline/templates/TPL_KEYS.tpl',
                    'kb4it/resources/offline/templates/TPL_METADATA_SECTION_BODY.tpl',
                    'kb4it/resources/offline/templates/TPL_METADATA_SECTION_FOOTER.tpl',
                    'kb4it/resources/offline/templates/TPL_METADATA_SECTION_HEADER.tpl',
                    'kb4it/resources/offline/templates/TPL_METAKEY.tpl',
                    'kb4it/resources/offline/templates/TPL_METAVALUE.tpl',
                    'kb4it/resources/offline/templates/TPL_TOP_NAV_BAR.tpl',
                    'kb4it/resources/offline/templates/TPL_VALUE.tpl',
                ]),
            ('kb4it/resources/online/css',
                [
                    'kb4it/resources/online/css/coderay-asciidoctor.css',
                    'kb4it/resources/online/css/fontawesome-4.7.0.css',
                    'kb4it/resources/online/css/kb4it.css',
                    'kb4it/resources/online/css/print.css',
                ]),
            ('kb4it/resources/online/fonts',
                [
                    'kb4it/resources/online/fonts/fontawesome-webfont.woff',
                    'kb4it/resources/online/fonts/fontawesome-webfont.svg',
                    'kb4it/resources/online/fonts/fontawesome-webfont.eot',
                    'kb4it/resources/online/fonts/fontawesome-webfont.woff2',
                    'kb4it/resources/online/fonts/fontawesome-webfont.ttf',
                ]),
            ('kb4it/resources/online/docinfo',
                [
                    'kb4it/resources/online/docinfo/docinfo.html',
                    'kb4it/resources/online/docinfo/docinfo-footer.html',
                ]),
            ('kb4it/resources/online/js/jquery',
                [
                    'kb4it/resources/online/js/jquery/AUTHORS.txt',
                    'kb4it/resources/online/js/jquery/jquery-ui.css',
                    'kb4it/resources/online/js/jquery/jquery-ui.js',
                    'kb4it/resources/online/js/jquery/jquery-ui.min.css',
                    'kb4it/resources/online/js/jquery/jquery-ui.min.js',
                    'kb4it/resources/online/js/jquery/jquery-ui.structure.css',
                    'kb4it/resources/online/js/jquery/jquery-ui.structure.min.css',
                    'kb4it/resources/online/js/jquery/jquery-ui.theme.css',
                    'kb4it/resources/online/js/jquery/jquery-ui.theme.min.css',
                    'kb4it/resources/online/js/jquery/LICENSE.txt',
                    'kb4it/resources/online/js/jquery/package.json',
                ]),
            ('kb4it/resources/online/js/jquery/external/jquery',
                [
                    'kb4it/resources/online/js/jquery/external/jquery/jquery.js',
                ]),
            ('kb4it/resources/online/js/jquery/images',
                [
                    'kb4it/resources/online/js/jquery/images/ui-icons_444444_256x240.png',
                    'kb4it/resources/online/js/jquery/images/ui-icons_555555_256x240.png',
                    'kb4it/resources/online/js/jquery/images/ui-icons_777620_256x240.png',
                    'kb4it/resources/online/js/jquery/images/ui-icons_777777_256x240.png',
                    'kb4it/resources/online/js/jquery/images/ui-icons_cc0000_256x240.png',
                    'kb4it/resources/online/js/jquery/images/ui-icons_ffffff_256x240.png',
                ]),
            ("kb4it/resources/share/docs",
                    [
                    'AUTHORS',
                    'LICENSE',
                    'README',
                    'INSTALL',
                    'CREDITS',
                    'Changelog'
                    ]),
            ]

        if not os.path.isdir('mo'):
            os.mkdir('mo')
        for pofile in os.listdir('po'):
            if pofile.endswith('po'):
                lang = pofile.strip('.po')
                modir = os.path.join('mo', lang)
                if not os.path.isdir(modir):
                    os.mkdir(modir)
                mofile = os.path.join(modir, 'kb4it.mo')
                subprocess.call('msgfmt {} -o {}'.format(os.path.join('po', pofile), mofile), shell=True)
                data_files.append(['share/locale/{}/LC_MESSAGES/'.format(lang), [mofile]])
        return data_files
    except Exception as error:
        print ("ERROR: %s" % error)
        return []

if os.name == 'posix':
    data_files = add_data()
else:
    data_files = []

try:
    bcommit = subprocess.check_output("svn info", shell=True)
    ucommit = bcommit.decode(encoding='UTF-8')
    icommit = int(ucommit.split('\n')[6].split(':')[1])
    dcommit = ucommit.split('\n')[11][19:29]
except Exception as error:
    dcommit = 'None'
    icommit = 0


setup(
    name='kb4it',
    version='0.5.3',
    author='Tomás Vírseda',
    author_email='tomasvirseda@gmail.com',
    url='https://github.com/t00m/KB4IT',
    description='A static website generator based on Asciidoc sources and Asciidoctor processor and publishing toolchain.',
    long_description=long_description,
    download_url = 'https://github.com/t00m/KB4IT/archive/master.zip',
    license='GPLv3',
    packages=['kb4it'],
    # distutils does not support install_requires, but pip needs it to be
    # able to automatically install dependencies
    install_requires=[
          'rdflib',
    ],
    include_package_data=True,
    data_files=data_files,
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Topic :: Documentation',
        'Topic :: Utilities'
    ],
    entry_points={
        'console_scripts': [
            'kb4it = kb4it.kb4it:main',
            ],
        },
)

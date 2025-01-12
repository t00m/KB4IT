#!/usr/bin/python3
# -*- coding: utf-8 -*-

import semver

PYPROJECT_TOML_TEMPLATE = """dynamic = [ "classifiers" ]

classifiers = [
 "Development Status :: 4 - Beta",
 "Environment :: Console",
 "Environment :: Web Environment",
 "Intended Audience :: Developers",
 "Intended Audience :: Information Technology",
 "Intended Audience :: System Administrators",
 "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
 "Natural Language :: English",
 "Operating System :: POSIX :: Linux",
 "Programming Language :: Python :: 3",
 "Topic :: Documentation",
 "Topic :: Software Development :: Documentation",
 "Topic :: Utilities",
]

[tool.poetry]
name = "KB4IT"
version = "{version}" # Replace with ENV['APP']['version']
description = "A static website generator based on Asciidoctor sources."
authors = ["Tomás Vírseda <replace_with_author_email>"] # Replace with ENV['APP']['author_email']
license = "GPL-3.0-or-later"
homepage = "https://github.com/t00m/KB4IT"
repository = "https://github.com/t00m/KB4IT"
keywords = ["static-site-generator", "asciidoctor", "documentation"]

[tool.poetry.dependencies]
python = "^3.8" # Adjust the version as needed
Mako = "1.3.6"
lxml = "*"

# [tool.poetry.extras]
# Additional features or dependencies can be added here

# [tool.poetry.include]
# README.rst = true
# kb4it/VERSION = true
# kb4it/resources/** = true

[tool.poetry.scripts]
kb4it = "kb4it.core.main:main"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
"""

current = open('kb4it/VERSION', 'r').read()
print("Current version: %s" % current)
version = semver.VersionInfo.parse(current).bump_build()
print("Next build: %s" % version)
with open('kb4it/VERSION', 'w') as fv:
    fv.write(str(version))

with open('pyproject.toml', 'w') as ftoml:
    ftoml.write(str(PYPROJECT_TOML_TEMPLATE.format(version=version)))

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
KB4IT module. Entry point.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Theme restaurant config generator
"""
class ThemeConf:

    conf = {
        "title": "Repository title",
        "source": "Absolute path for source directory",
        "target": "Absolute path for target directory",
        "theme": "restaurant",
        "sort": "Comma-separated list of properties to be used for sorting (typically date-alike properties)",
        "ignored_keys": "Comma-separated list of properties to be ignored during the generation of the 'properties' page (typically date-alike properties)" ,
        "events": "Comma-separated list of categories to be used as events (and depending on the sort property/properties)",
        "date_attributes": ["Published"],
        "git": "Use a git server to manage the document versioning? (false or true)",
        "git_server": "git server address",
        "git_user": "Git user",
        "git_repo": "Git repository",
        "git_path": "Path in the git server to the directory with the documentation",
        "git_branch": "Git branch (typically master or main)",
        "logging": "Level of messages severity (DEBUG/INFO/WARNING/ERROR)",
        "logfile": "Absolute path for the logging file.",
        "force": "Force compilation Useful if the theme logic/templates or any other theme stuff change (true or false)"
    }

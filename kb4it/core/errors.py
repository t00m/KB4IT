#!/usr/bin/env python

"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: KB4IT Custom Exceptions
"""

import os


class KB4ITError(Exception):
    """Base class for other exceptions"""
    pass

class KB4ITRepositoryConfigFileNotFoundError(KB4ITError):
    """Exception raised if the repository configuration file is not
    found.
    """
    pass

def check_repo_config_file(configfile: str = None):
    if configfile is None:
        raise

try:
    configfile = input("Repository configuration file: ")
    print("Config file: {} ({})".format(configfile, type(configfile)))
    if configfile is None or len(configfile) == 0 or not os.path.exists(configfile):
        raise KB4ITRepositoryConfigFileNotFoundError(configfile)
except KB4ITRepositoryConfigFileNotFoundError:
    print("Repository configuration file not found")


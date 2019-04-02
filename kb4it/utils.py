#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: utils module
"""

import os
import sys
import logging
import traceback as tb
import shutil

def copydir(source, dest):
    """Copy a directory structure overwriting existing files
    https://gist.github.com/dreikanter/5650973#gistcomment-835606
    """
    for root, dirs, files in os.walk(source):
        if not os.path.isdir(root):
            os.makedirs(root)

        for file in files:
            rel_path = root.replace(source, '').lstrip(os.sep)
            dest_path = os.path.join(dest, rel_path)

            if not os.path.isdir(dest_path):
                os.makedirs(dest_path)

            shutil.copyfile(os.path.join(root, file), os.path.join(dest_path, file))

def set_max_frequency(dkeyurl):
    """
    Calculate and set max frequency
    """
    max_frequency = 1
    for keyword in dkeyurl:
        cur_frequency = len(dkeyurl[keyword])
        if cur_frequency > max_frequency:
            max_frequency = cur_frequency

    return max_frequency


def get_font_size(frequency, max_frequency):
    """
    Get font size for a word based in its frequency
    """
    if frequency > 1:
        proportion = int((frequency * 100) / max_frequency)
    else:
        proportion = 1

    size = 8
    if proportion < 2: size = 8
    elif proportion >= 2 and proportion < 10: size = 10
    elif proportion in range(10, 19): size = 12
    elif proportion in range(20, 29): size = 14
    elif proportion in range(30, 39): size = 18
    elif proportion in range(40, 49): size = 26
    elif proportion in range(50, 59): size = 30
    elif proportion in range(60, 69): size = 36
    elif proportion in range(70, 79): size = 42
    elif proportion in range(80, 89): size = 48
    elif proportion in range(90, 99): size = 54
    elif proportion == 100: size = 72

    return size


def nosb(alist, lower=False):
    """
    return a new list of elements, forcing them to lowercase if
    necessary.
    """
    newlist = []
    for item in alist:
        if len(item) > 0:
            if lower:
                item = item.lower()
            newlist.append(item.strip())
    newlist.sort()

    return newlist


def finish_ko(msg):
    """
    Raise error if it finishes abnormally
    """
    print("Program finished abnormally: %s" % msg)
    print(tb.format_exc())
    sys.exit(-1)


def finish_ok():
    """
    It finishes script gracefully
    """
    sys.exit(0)


def get_logger(level='INFO'):
    """Returns a logger.
    """
    log = logging.getLogger('log')
    if level == 'DEBUG':
        log.setLevel(logging.DEBUG)
    elif level == 'INFO':
        log.setLevel(logging.INFO)
    elif level == 'WARNING':
        log.setLevel(logging.WARNING)
    elif level == 'ERROR':
        log.setLevel(logging.ERROR)
    else:
        log.setLevel(logging.INFO)

    # Redirect log to stdout
    formatter = logging.Formatter("%(levelname)7s | %(lineno)4d  | %(asctime)s | %(message)s")
    ch = logging.StreamHandler()    # Create console handler
    ch.setLevel(logging.DEBUG)       # Set logging devel
    ch.setFormatter(formatter)      # add formatter to console handler
    log.addHandler(ch)              # add console handler to logger

    return log

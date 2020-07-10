#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Utils functions used along the project.

# File: srv_utils.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: Generic functions module
"""

import os
import re
import glob
import json
import math
import shutil
import hashlib
import operator
import subprocess
import traceback as tb
from datetime import datetime
from kb4it.core.env import LPATH, EOHMARK
from kb4it.core.log import get_logger

log = get_logger('KB4ITUtil')


def load_kbdict(source_path):
    """C0111: Missing function docstring (missing-docstring)."""
    source_path = valid_filename(source_path)
    KB4IT_DB_FILE = os.path.join(LPATH['DB'], 'kbdict-%s.json' % source_path)
    try:
        with open(KB4IT_DB_FILE, 'r') as fkb:
            kbdict = json.load(fkb)
    except FileNotFoundError:
        kbdict = {}
    log.debug("Current kbdict entries: %d", len(kbdict))
    return kbdict


def save_kbdict(kbdict, path, name=None):
    """C0111: Missing function docstring (missing-docstring)."""
    if name is None:
        target_path = valid_filename(path)
        KB4IT_DB_FILE = os.path.join(LPATH['DB'], 'kbdict-%s.json' % target_path)
    else:
        KB4IT_DB_FILE = os.path.join(path, '%s.json' % name)

    with open(KB4IT_DB_FILE, 'w') as fkb:
        json.dump(kbdict, fkb)
        log.debug("KBDICT %s saved", KB4IT_DB_FILE)


def copy_docs(docs, target):
    """C0111: Missing function docstring (missing-docstring)."""
    for doc in docs:
        try:
            shutil.copy('%s' % doc, target)
            log.debug("%s copied to %s", doc, target)
        except FileNotFoundError:
            log.warning("%s not found", doc)
    log.debug("%d documents copied to '%s'", len(docs), target)


def copydir(source, dest):
    """Copy a directory structure overwriting existing files.

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

            try:
                shutil.copyfile(os.path.join(root, file), os.path.join(dest_path, file))
            except PermissionError:
                log.warning("Check permissions for file: %s", file)


def get_source_docs(path):
    """C0111: Missing function docstring (missing-docstring)."""
    if path[:-1] != os.path.sep:
        path = path + os.path.sep

    pattern = os.path.join(path) + '*.adoc'
    docs = glob.glob(pattern)
    docs.sort(key=lambda y: y.lower())
    log.debug("\tFound %d asciidoctor documents", len(docs))

    return docs


def get_traceback():
    """Get traceback."""
    return tb.format_exc()


def exec_cmd(data):
    """Execute an operating system command.

    Return:
    - document
    - True if success, False if not
    - res is the output
    """
    doc, cmd, res = data
    process = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
    outs, errs = process.communicate()
    if errs is None:
        compiled = True
    else:
        compiled = False
        log.debug("Compiling %s: Error: %s", doc, errs)
    return doc, compiled, res


def set_max_frequency(dkeyurl):
    """Calculate and set max frequency."""
    max_frequency = 1
    for keyword in dkeyurl:
        cur_frequency = len(dkeyurl[keyword])
        if cur_frequency > max_frequency:
            max_frequency = cur_frequency

    return max_frequency


def get_font_size(frequency, max_frequency):
    """Get font size for a word based in its frequency."""
    proportion = int(math.log((frequency * 100) / max_frequency))

    if proportion < 1:
        size = 8
    elif proportion in range(1, 2):
        size = 10
    elif proportion in range(2, 3):
        size = 18
    elif proportion in range(3, 4):
        size = 36
    elif proportion in range(4, 5):
        size = 72
    else:
        size = 72

    return size


def extract_toc(source):
    """C0111: Missing function docstring (missing-docstring)."""
    toc = ''
    items = []
    lines = source.split('\n')
    s = e = n = 0

    for line in lines:
        if line.find("toctitle") > 0:
            s = n + 1
        if s > 0:
            if line.startswith('</div>') and n > s:
                e = n
                break
        n = n + 1

    if s > 0 and e > s:
        for line in lines[s:e]:
            if line.startswith('<li><a href='):
                modifier = """<li><a class="uk-link-heading" """
                line = line.replace("<li><a ", modifier)
            else:
                line = line.replace("sectlevel1", "uk-nav uk-nav-default")
                line = line.replace("sectlevel2", "uk-nav-sub")
                line = line.replace("sectlevel3", "uk-nav-sub")
                line = line.replace("sectlevel4", "uk-nav-sub")
            items.append(line)
        toc = '\n'.join(items)
    return toc


def delete_target_contents(target_path):
    """C0111: Missing function docstring (missing-docstring)."""
    if os.path.exists(target_path):
        if os.path.isdir(target_path):
            for file_object in os.listdir(target_path):
                file_object_path = os.path.join(target_path, file_object)
                if os.path.isfile(file_object_path):
                    os.unlink(file_object_path)
                else:
                    shutil.rmtree(file_object_path)
            log.debug("Contents of directory '%s' deleted successfully", target_path)
        elif os.path.isfile(target_path):
            os.unlink(target_path)
            log.debug("File '%s' deleted successfully", target_path)


def delete_files(files):
    """Delete a list of given files."""
    for path in files:
        try:
            if os.path.exists(path):
                os.unlink(path)
        except FileNotFoundError as error:
            log.warning(error)
            log.warning(files)


def get_asciidoctor_attributes(docpath):
    """Get Asciidoctor attributes from a given document."""
    props = {}
    try:
        # Get lines
        line = open(docpath, 'r').readlines()

        # Add document title (first line) to graph
        title = line[0][2:-1]
        title = title.strip()

        # Proceed only if document has a title
        if len(title) > 0:
            props['Title'] = [title]

            # read the rest of properties until watermark
            for n in range(1, len(line)):
                if line[n].startswith(':'):
                    key = line[n][1:line[n].find(':', 1)]
                    values = line[n][len(key)+2:-1].split(',')
                    props[key] = [value.strip() for value in values]
                elif line[n].startswith(EOHMARK):
                    # Stop processing if EOHMARK is found
                    break
    except IndexError as error:
        basename = os.path.basename(docpath)
        log.error("Document %s could not be processed. Empty?" % basename)
        props = {}

    return props


def get_hash_from_file(path):
    """Get the SHA256 hash for a given filename."""
    if os.path.exists(path):
        content = open(path, 'r').read()
        m = hashlib.sha256()
        m.update(content.encode())
        return m.hexdigest()
    else:
        return None


def get_hash_from_dict(adict):
    """Get the SHA256 hash for a given dictionary."""
    alist = []
    for key in adict:
        alist.append(key.lower())
        elements = adict[key]
        for elem in elements:
            alist.append(elem.lower())
    alist.sort(key=lambda y: y.lower())
    string = ' '.join(alist)
    m = hashlib.sha256()
    m.update(string.encode())
    return m.hexdigest()


def valid_filename(s):
    """Return the given string converted to a string that can be used for a clean filename.

    Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'

    Borrowed from:
    https://github.com/django/django/blob/master/django/utils/text.py
    """
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def guess_datetime(sdate):
    """Return (guess) a datetime object for a given string."""
    found = False
    patterns = ["%d/%m/%Y", "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S",
                "%d.%m.%Y", "%d.%m.%Y %H:%M", "%d.%m.%Y %H:%M:%S",
                "%d-%m-%Y", "%d-%m-%Y %H:%M", "%d-%m-%Y %H:%M:%S",
                "%Y/%m/%d", "%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S",
                "%Y.%m.%d", "%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S",
                "%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d", "%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S.%f",
                "%Y.%m.%d", "%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S.%f",
                "%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S.%f"]
    for pattern in patterns:
        if not found:
            try:
                td = datetime.strptime(sdate, pattern)
                ts = td.strftime("%Y-%m-%d %H:%M:%S")
                timestamp = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                found = True
            except ValueError:
                timestamp = None
    return timestamp


def file_timestamp(filename):
    """Return last modification datetime normalized of a file."""
    t = os.path.getmtime(filename)
    sdate = datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
    return sdate


def string_timestamp(string):
    """Return datetime object from a given timestamp."""
    dt = guess_datetime(string)
    sdate = dt.strftime("%Y-%m-%d %H:%M:%S")
    # ~ print ("%s -> %s" % (string, sdate))
    return sdate

def get_human_datetime(dt):
    """Return datetime for humans."""
    return "%s" % dt.strftime("%a, %b %d, %Y at %H:%M")


def fuzzy_date_from_timestamp(timestamp):
    """Get fuzzy human string from a given timestamp."""
    if type(timestamp) == str:
        d1 = guess_datetime(timestamp)
    else:
        d1 = timestamp

    now = datetime.now()
    if now >= d1:
        rdate = now - d1
        future = False
    else:
        rdate = d1 - now
        future = True

    if rdate.days > 0:
        if rdate.days <= 31:
            fuzzy = "%d days" % int(rdate.days)

        if rdate.days > 31 and rdate.days < 365:
            fuzzy = "%d months" % int((rdate.days/31))

        if rdate.days >= 365:
            years = int(rdate.days/365)
            months = int((rdate.days / years - 365) / 30)
            if months > 0:
                fuzzy = "%d years and %d months" % (years, months)
            else:
                if years > 1:
                    fuzzy = "%d years" % years
                else:
                    fuzzy = "1 year ago"

        if future:
            fuzzy_string = "In %s" % fuzzy
        else:
            fuzzy_string = "%s ago" % fuzzy
    else:
        hours = rdate.seconds / 3600
        minutes = rdate.seconds / 60
        if int(hours) > 0:
            fuzzy = "%d hours" % int(hours)
        elif int(minutes) > 0:
            fuzzy = "%d minutes" % int(minutes)
        elif int(rdate.seconds) > 0:
            fuzzy = "%d seconds" % int(rdate.seconds)
        elif int(rdate.seconds) == 0:
            fuzzy = "Right now"

        if future:
            fuzzy_string = "In %s" % fuzzy
        else:
            fuzzy_string = "%s ago" % fuzzy

    return fuzzy_string


def sort_dictionary(adict, reverse=True):
    """Return a reversed sorted list from a dictionary."""
    return sorted(adict.items(), key=operator.itemgetter(1), reverse=reverse)

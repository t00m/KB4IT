#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Utils service.

# File: srv_utils.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: Generic functions module
"""

import os
import re
import glob
import json
import time
import math
import shutil
import random
import hashlib
import threading
import subprocess
import traceback as tb
from datetime import datetime
from kb4it.src.core.mod_env import LPATH, GPATH, EOHMARK, FILE, TEMPLATES
from kb4it.src.core.mod_log import get_logger

log = get_logger('Utils')

HTML_HEADER = open(FILE['HEADER'], 'r').read()
HTML_FOOTER = open(FILE['FOOTER'], 'r').read()


def load_current_kbdict(source_path):
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


def save_current_kbdict(kbdict, source_path):
    """C0111: Missing function docstring (missing-docstring)."""
    source_path = valid_filename(source_path)
    KB4IT_DB_FILE = os.path.join(LPATH['DB'], 'kbdict-%s.json' % source_path)
    with open(KB4IT_DB_FILE, 'w') as fkb:
        json.dump(kbdict, fkb)
        log.debug("KBDICT %s saved", KB4IT_DB_FILE)


def copy_docs(docs, target):
    """C0111: Missing function docstring (missing-docstring)."""
    for doc in docs:
        shutil.copy('%s' % doc, target)
        log.debug("          %s copied to %s", doc, target)
    log.debug("          %d documents copied to '%s'", len(docs), target)


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


def template(name):
    """C0111: Missing function docstring (missing-docstring)."""
    # ~ TEMPLATE_PATH = os.path.join(GPATH['TEMPLATES'], "%s.tpl" % template)
    # ~ return open(TEMPLATE_PATH, 'r').read()
    return TEMPLATES[name]


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
    # ~ log.debug(cmd)
    process = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
    outs, errs = process.communicate()
    if errs is None:
        return doc, True, res
    else:
        log.debug("Compiling %s: Error: %s", doc, errs)
        return doc, False, res


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
        size = 9
    elif proportion in range(1, 2):
        size = 11
    elif proportion in range(2, 3):
        size = 18
    elif proportion in range(3, 4):
        size = 36
    elif proportion in range(4, 5):
        size = 72
    elif proportion > 5:
        size = 72

    return size


def nosb(alist, lower=False):
    """Return a new list of elements, forcing them to lowercase if necessary."""
    newlist = []
    for item in alist:
        if len(item) > 0:
            if lower:
                item = item.lower()
            newlist.append(item.strip())
    newlist.sort(key=lambda y: y.lower())

    return newlist


def get_labels(values):
    """C0111: Missing function docstring (missing-docstring)."""
    label_links = ''
    value_link = template('METADATA_VALUE_LINK')
    for page, text in values:
        if len(text) != 0:
            label_links += value_link % (valid_filename(page), text)
    return label_links


def apply_transformations(source):
    """C0111: Missing function docstring (missing-docstring)."""
    content = source.replace(template('TOC_OLD'), template('TOC_NEW'))
    content = content.replace(template('SECT1_OLD'), template('SECT1_NEW'))
    content = content.replace(template('SECT2_OLD'), template('SECT2_NEW'))
    content = content.replace(template('SECT3_OLD'), template('SECT3_NEW'))
    content = content.replace(template('SECT4_OLD'), template('SECT4_NEW'))
    content = content.replace(template('SECTIONBODY_OLD'), template('SECTIONBODY_NEW'))
    content = content.replace(template('H1_OLD'), template('H1_NEW'))
    content = content.replace(template('H2_OLD'), template('H2_NEW'))
    content = content.replace(template('H3_OLD'), template('H3_NEW'))
    content = content.replace(template('H4_OLD'), template('H4_NEW'))
    content = content.replace(template('TABLE_OLD'), template('TABLE_NEW'))
    # Admonitions
    content = content.replace(template('ADMONITION_ICON_NOTE_OLD'), template('ADMONITION_ICON_NOTE_NEW'))
    content = content.replace(template('ADMONITION_ICON_TIP_OLD'), template('ADMONITION_ICON_TIP_NEW'))
    content = content.replace(template('ADMONITION_ICON_IMPORTANT_OLD'), template('ADMONITION_ICON_IMPORTANT_NEW'))
    content = content.replace(template('ADMONITION_ICON_CAUTION_OLD'), template('ADMONITION_ICON_CAUTION_NEW'))
    content = content.replace(template('ADMONITION_ICON_WARNING_OLD'), template('ADMONITION_ICON_WARNING_NEW'))

    return content


def highlight_metadata_section(source):
    """C0111: Missing function docstring (missing-docstring)."""
    content = source.replace(template('METADATA_OLD'), template('METADATA_NEW'), 1)
    return content


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
                modifier = """<li class="uk-link-toggle"><a class="uk-link-heading" """
                line = line.replace("<li><a ", modifier)
            else:
                line = line.replace("sectlevel1", "uk-nav uk-nav-default")
                line = line.replace("sectlevel2", "uk-nav-sub")
                line = line.replace("sectlevel3", "uk-nav-sub")
                line = line.replace("sectlevel4", "uk-nav-sub")
            items.append(line)
        items.insert(0, template('TOC_HEADER_TITLE'))
        toc = '\n'.join(items)
    return toc


def job_done(future):
    """C0111: Missing function docstring (missing-docstring)."""
    time.sleep(random.random())
    x = future.result()
    cur_thread = threading.current_thread().name
    if cur_thread != x:
        adoc, rc, j = x
        log.debug("Job[%5d]: %s compiled", j, adoc)

        # Add header and footer to compiled doc
        htmldoc = adoc.replace('.adoc', '.html')
        if os.path.exists(htmldoc):
            adoc_title = open(adoc).readlines()[0]
            title = "<h1>%s</h1>\n" % adoc_title[2:-1]
            htmldoctmp = "%s.tmp" % htmldoc
            shutil.move(htmldoc, htmldoctmp)
            source = open(htmldoctmp, 'r').read()
            toc = extract_toc(source)
            content = apply_transformations(source)
            try:
                # ~ log.error(toc)
                if 'Metadata' in content:
                    content = highlight_metadata_section(content)
            except IndexError as error:
                # ~ log.error(error)
                # Some pages don't have toc section. Ignore it.
                pass

            with open(htmldoc, 'w') as fhtm:
                fhtm.write(HTML_HEADER % toc)
                fhtm.write(title)
                fhtm.write(content)
                fhtm.write(HTML_FOOTER)
            os.remove(htmldoctmp)
            # ~ log.debug("Temporary html document deleted: %s", htmldoctmp)
            return x


def create_directory(directory):
    """Create a given directory path."""
    log.debug("Checking if directory '%s' exists", directory)
    if not os.path.exists(directory):
        os.makedirs(directory)
        log.debug("Creating directory '%s'", directory)


def delete_target_contents(target_path):
    """C0111: Missing function docstring (missing-docstring)."""
    if os.path.exists(target_path):
        log.debug("\tTarget directory '%s' does not exists", target_path)
        for file_object in os.listdir(target_path):
            file_object_path = os.path.join(target_path, file_object)
            if os.path.isfile(file_object_path):
                os.unlink(file_object_path)
            else:
                shutil.rmtree(file_object_path)
        log.debug("          Contents of directory '%s' deleted successfully", target_path)


def get_metadata(docpath):
    """C0111: Missing function docstring (missing-docstring)."""
    props = {}
    try:
        # Get lines
        line = open(docpath, 'r').readlines()

        # Add document title (first line) to graph
        title = line[0][2:-1]
        props['Title'] = [title]

        # read the rest of properties until watermark
        for n in range(1, len(line)):
            if line[n].startswith(':'):
                key = line[n][1:line[n].rfind(':')]
                alist = nosb(line[n][len(key)+2:-1].split(','))
                props[key] = alist
            elif line[n].startswith(EOHMARK):
                # Stop processing if EOHMARK is found
                break
    except Exception as error:
        log.error(error)
        log.error("Document %s could not be processed" % docpath)
    return props


def uniq_sort(result):
    """Missing docstring."""
    alist = list(result)
    aset = set(alist)
    alist = list(aset)
    alist.sort(key=lambda y: y.lower())
    return alist


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


def setup_new_repository(target):
    """Set up a new repository if no source files found."""
    docs = get_source_docs(target)
    copy_docs(GPATH['ADOCS'], target)


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

def last_dt_modification(filename):
    """Return last modification datetime of a file """
    t = os.path.getmtime(filename)
    dt = datetime.fromtimestamp(t)
    return dt

def last_ts_modification(filename):
    """Return last modification human-readable datetime of a file """
    t = os.path.getmtime(filename)
    d = datetime.fromtimestamp(t)
    return "%s" % d.strftime("%Y/%m/%d %H:%M:%S")

def last_modification_date(filename):
    """Return last modification human-readable datetime of a file """
    t = os.path.getmtime(filename)
    d = datetime.fromtimestamp(t)
    return "%s" % d.strftime("%Y/%m/%d")

def last_modification(filename):
    """Return last modification human-readable datetime of a file """
    t = os.path.getmtime(filename)
    d = datetime.fromtimestamp(t)
    return "%s" % d.strftime("%A, %B %e, %Y at %H:%M:%S")

def get_author_icon(source_path, author):
    relpath = "resources/images/authors/%s.png" % valid_filename(author)
    abspath = os.path.join(source_path, relpath)

    if os.path.exists(abspath):
        return relpath
    else:
        return "resources/images/authors/author_unknown.png"

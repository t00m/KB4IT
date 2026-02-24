#!/usr/bin/python

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
import time
import pickle
import shutil
import hashlib
import operator
import subprocess
import multiprocessing
from functools import wraps
from datetime import datetime


from kb4it.core.env import ENV
from kb4it.core.log import get_logger

log = get_logger('Util')

cache_dt = {}
cache_ts_ymd = {}


def timeit(func):
    """Time a method for measuring performance."""
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        # ~ if total_time > 1:
            # ~ log.perf(f"[PERFORMANCE] {total_time:.4f}s => Stage {func.__name__}")
        # ~ else:
            # ~ log.trace(f"[PERFORMANCE] {total_time:.4f}s => Stage {func.__name__}")
        log.debug(f"[PERFORMANCE] {total_time:.4f}s => Stage {func.__name__}")
        return result
    return timeit_wrapper


def extract_sections_from_adoc(file_path: str) -> dict:
    """Extract sections from an AsciiDoc file."""
    sections = []

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    current_section = None
    start = None

    for i, line in enumerate(lines, 1):  # Start line counting at 1
        line = line.rstrip('\n')

        # Check if this is a section header (starts with '== ' but not more '=' signs)
        if line.startswith('== ') and not line.startswith('==='):
            # Save previous section if exists
            if current_section:
                sections.append({
                    'name': current_section,
                    'start': start,
                    'end': i - 1
                })

            # Start new section
            current_section = line[3:].strip()  # Remove '== ' prefix
            start = i

    # Add the last section
    if current_section:
        sections.append({
            'name': current_section,
            'start': start,
            'end': len(lines)
        })

    # As a dictionary with section names as keys
    sections_dict = {section['name']: {
        'start': section['start'],
        'end': section['end']
    } for section in sections}

    return sections_dict


def copy_docs(docs: list, target: str) -> None:
    """Copy a list of docs to target directory."""
    for doc in docs:
        try:
            shutil.copy(doc, target)
            log.debug(f"Copied {doc} to {target}")
        except FileNotFoundError:
            log.warning(f"File {doc} not found")
    log.debug(f"{len(docs)} documents copied to '{target}'")


def get_default_workers():
    """Calculate default number or workers.

    Workers = Number of CPU / 2
    Minimum workers = 1
    """
    ncpu = multiprocessing.cpu_count()
    workers = ncpu / 2
    return math.ceil(workers)


def copydir(source, dest):
    """Copy a directory structure overwriting existing files.

    https://gist.github.com/dreikanter/5650973#gistcomment-835606
    """
    for root, dirs, files in os.walk(source):
        if not os.path.isdir(root):
            os.makedirs(root, exist_ok=True)

        for file in files:
            rel_path = root.replace(source, '').lstrip(os.sep)
            dest_path = os.path.join(dest, rel_path)

            if not os.path.isdir(dest_path):
                os.makedirs(dest_path, exist_ok=True)

            try:
                shutil.copyfile(os.path.join(root, file), os.path.join(dest_path, file))
            except PermissionError:
                log.warning(f"Check permissions for file {file}")


def get_source_docs(path: str):
    """Get asciidoc documents from a given path."""
    pattern = os.path.join(path, '*.adoc')
    return glob.glob(pattern)


def exec_cmd(data):
    """Execute an operating system command.

    Return:
    - document
    - True if success, False if not
    - num is the job number
    """
    doc, cmd, num = data
    process = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
    outs, errs = process.communicate()
    if errs is None:
        compiled = True
    else:
        compiled = False
        log.debug("[UTIL] - Compiling %s: Error: %s", doc, errs)
    return doc, compiled, num


def set_max_frequency(dkeyurl):
    """Calculate and set max frequency."""
    max_frequency = 1
    for keyword in dkeyurl:
        cur_frequency = len(dkeyurl[keyword])
        max_frequency = max(max_frequency, cur_frequency)

    return max_frequency


def get_font_size(frequency, max_frequency):
    """Get font size for a word based in its frequency."""
    proportion = int(math.log((frequency * 100) / max_frequency))

    if max_frequency == 1:
        size = 10
    else:
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


def delete_target_contents(target_path: str) -> bool:
    """Delete contents from target directory."""
    error = False
    if os.path.exists(target_path):
        if os.path.isdir(target_path):
            for file_object in os.listdir(target_path):
                file_object_path = os.path.join(target_path, file_object)
                if os.path.isfile(file_object_path):
                    os.unlink(file_object_path)
                else:
                    shutil.rmtree(file_object_path)
            # ~ log.debug("[UTIL] - Contents of directory '%s' deleted successfully", target_path)
        elif os.path.isfile(target_path):
            os.unlink(target_path)
            # ~ log.debug("[UTIL] - File '%s' deleted successfully", target_path)
    else:
        log.error(f"Target path {target_path} does not exist")
        error = True
    return True


def delete_files(files):
    """Delete a list of given files."""
    for path in files:
        try:
            if os.path.exists(path):
                os.unlink(path)
        except FileNotFoundError as error:
            log.warning("[UTIL] - %s", error)
            log.warning("[UTIL] - %s", path)


def json_load(filepath: str) -> {}:
    """Load into a dictionary a file in json format."""
    with open(filepath, 'r', encoding='utf-8') as fin:
        adict = json.load(fin)
    return adict


def json_save(filepath: str, adict: {}) -> {}:
    """Save dictionary into a file in json format."""
    with open(filepath, 'w', encoding='utf-8') as fout:
        json.dump(adict, fout, sort_keys=True, indent=4)


def get_asciidoctor_attributes(docpath: str):
    """Get Asciidoctor attributes from a given document."""
    basename = os.path.basename(docpath)
    keys = {}
    valid = False
    title_found = False
    end_of_header_found = False

    try:
        lines = open(docpath, 'r', encoding='utf-8').readlines()
        title_found = False
        title_line = lines[0]

        if title_line.startswith('= '):
            title = title_line[2:-1].strip()
            if len(title) > 0:
                keys['Title'] = [title]
                title_found = True

        # Proceed only if document has a title
        if title_found:
            end_of_header_found = False
            # read the rest of properties until watermark
            for n in range(1, len(lines)):
                line = lines[n].strip()
                if line.startswith(':'):
                    key = line[1:line.find(':', 1)]
                    values = line[len(key) + 2:].split(',')
                    keys[key] = [value.strip() for value in values]
                elif line.startswith(ENV['CONF']['EOHMARK']):
                    # Stop processing if EOHMARK is found
                    end_of_header_found = True
                    break
            if not end_of_header_found:
                reason = f"Document '{basename}' doesn't have the END-OF-HEADER mark"
                log.error("Error: {reason}")
                keys = {}
        else:
            reason = f"Document '{basename}' doesn't have a title"
            log.error("Error: {reason}")
            keys = {}
    except IndexError as error:
        reason = "Document '{basename}' could not be processed. Empty?"
        log.error("Error: {reason}")
        keys = {}

    if title_found and end_of_header_found:
        valid = True
        reason = 'Success'

    return keys, valid, reason


def get_hash_from_content(content: str):
    """Get the md5 hash for any string."""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def get_hash_from_file(path):
    """Get the md5 hash for a given filename."""
    if os.path.exists(path):
        with open(path, 'rb') as fin:
            fhash = hashlib.file_digest(fin, 'md5').hexdigest()
    else:
        fhash = None
    return fhash


def get_hash_from_dict(adict):
    """Get the md5 hash for a given dictionary."""
    return hashlib.md5(pickle.dumps(adict)).hexdigest()


def get_hash_from_list(alist):
    """Get the md5 hash for a given list."""
    return hashlib.md5(pickle.dumps(alist)).hexdigest()


def valid_filename(s):
    """Return a clean filename.

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


def now():
    """Return datetime.now in isoformat."""
    return datetime.now().isoformat()


def get_year(timestamp: str) -> int:
    """Return year from timestamp."""
    return int(timestamp[:4])


def get_month(timestamp: str):
    """Return month from timestamp."""
    return int(timestamp[4:6])


def get_day(timestamp: str):
    """Return day from timestamp."""
    return int(timestamp[6:8])


def log_timestamp():
    """Return timestamp for logging purposes."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def kb4it_timestamp():
    """Return timestamp in KB4IT format."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def guess_datetime(sdate):
    """Guess a datetime object for a given string."""
    if sdate in cache_dt:
        return cache_dt[sdate]

    patterns = ["%d/%m/%Y", "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S",
                "%d.%m.%Y", "%d.%m.%Y %H:%M", "%d.%m.%Y %H:%M:%S",
                "%d-%m-%Y", "%d-%m-%Y %H:%M", "%d-%m-%Y %H:%M:%S",
                "%Y/%m/%d", "%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S",
                "%Y.%m.%d", "%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S",
                "%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d", "%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S.%f",
                "%Y.%m.%d", "%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S.%f",
                "%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]
    found = False
    for pattern in patterns:
        if not found:
            try:
                td = datetime.strptime(sdate, pattern)
                ts = td.strftime("%Y-%m-%d %H:%M:%S")
                timestamp = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                found = True
            except ValueError:
                timestamp = None
    cache_dt[sdate] = timestamp
    return timestamp


def string_timestamp(string):
    """Return datetime object from a given timestamp."""
    dt = guess_datetime(string)
    sdate = dt.strftime("%Y-%m-%d %H:%M:%S")
    # ~ print ("%s -> %s" % (string, sdate))
    return sdate


def get_human_datetime(dt):
    """Return datetime for humans."""
    return dt.strftime("%A, %B %d, %Y at %H:%M")


def get_human_datetime_day(dt):
    """Return day datetime for humans."""
    return dt.strftime("%A, %B %d, %Y")


def get_human_datetime_month(dt):
    """Return month datetime for humans."""
    return dt.strftime("%B, %Y")


def get_human_datetime_year(dt):
    """Return year datetime for humans."""
    return dt.strftime("%Y")


def get_timestamp_yyyymmdd(dt):
    """Return timestamp in yyyymmdd format."""
    if dt not in cache_ts_ymd:
        cache_ts_ymd[dt] = dt.strftime("%Y%m%d")
    return cache_ts_ymd[dt]


def sort_dictionary(adict, reverse=True):
    """Return a reversed sorted list from a dictionary."""
    return sorted(adict.items(), key=operator.itemgetter(1), reverse=reverse)


def ellipsize_text(text: str, max_length: int = 70):
    """Elipsize a given text given a max length."""
    if len(text) <= max_length:
        return text

    # Number of characters to show on each side of the ellipsis
    split_length = (max_length - 3) // 2

    # Handle odd max_length cases
    start = text[:split_length]
    end = text[-split_length:] if max_length % 2 == 0 else text[-split_length - 1:]

    return f"{start}...{end}"

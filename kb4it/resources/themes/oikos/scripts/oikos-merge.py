#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
# File: oikos-merge.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: utility to merge 'oikos' dictionaries into one
"""

import os
import csv
import sys
import pprint
import shutil
import operator
from collections import OrderedDict

def get_csvfiles(csvfiles):
    n = len(csvfiles)
    switcher = {
        0: (False, "No CSV files passed"),
        1: (False, "Only one CSV file passed. No merge necessary.")
    }
    return switcher.get(n, (True, "Merge files"))

def create_dict(csvfile):
    dictionary = {}
    n = 0
    with open(csvfile, newline='') as fcsv:
        sheet = csv.reader(fcsv, delimiter=',', quotechar='\"')
        for row in sheet:
            if n > 0:
                oid = row[0]
                dictionary[oid] = row[1:]
            n += 1
    print("\tcreate dict from %s with %d entries" % (csvfile, len(dictionary)))
    return dictionary

def sort_dictionary(dictionary):
    adict = {}
    for oid in dictionary:
        adict[oid] = dictionary[oid][0]
    alist = sorted(adict.items(), key=operator.itemgetter(1), reverse=True)
    new_dictionary = OrderedDict()
    for oid, date in alist:
        new_dictionary[oid] = dictionary[oid]
    print ("\tNew dictionary sorted by date")
    return new_dictionary

def backup(filename):
    bckfile = "%s.bck" % filename
    if os.path.exists(filename):
        shutil.copy(filename, bckfile)
        print("\tExisting %s backed up to %s" % (filename, bckfile))

def save_dictionary(dictionary):
    filename = "oikos.csv"
    backup(filename)
    writer = csv.writer(open(filename, 'w'), delimiter=',', quoting=csv.QUOTE_ALL)
    csvheader = ['Id', 'Date', 'Concept', 'Type', 'Category', 'From/To', 'Amount']
    writer.writerow(csvheader)
    for oid in dictionary:
        row = []
        row.append(oid)
        row.extend(dictionary[oid])
        writer.writerow(row)
    print ("Merge successful. Created %s" % filename)

def merge_csv(*dict_args):
    result = {}
    for csvfiles in list(dict_args):
        for csvfile in csvfiles:
            dictionary = create_dict(csvfile)
            result.update(dictionary)
    print ("\tMerge %d dictionarys into one with %d entries" % (len(csvfiles), len(result)))
    oikos = sort_dictionary(result)
    save_dictionary(oikos)
    return oikos


if __name__ == '__main__':
    try:
        csvfiles = sys.argv[1:]
        merge, reason = get_csvfiles(csvfiles)
        if merge:
            print("Merging %s into oikos.csv" % ', '.join(csvfiles))
            merge_csv(csvfiles)
        else:
            print (reason)
    except IndexError as error:
        print ("Usage: python3 oikos-merge.py csvfile1 csvfile2 ... csvfileN\n")
    except Exception as error:
        print(error)
        raise

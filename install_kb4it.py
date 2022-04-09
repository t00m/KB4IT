#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import os.path
import sys

def which(program):
    if sys.platform == 'win32':
        program = program + '.exe'

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


tests = []
results = {}

def test_python_3():
    results['python-3'] = {}
    results['python-3']['condition'] = "Python 3 installed"
    if sys.version_info.major == 3:
        results['python-3']['passed'] = True
        results['python-3']['error'] = "OK"
    else:
        results['python-3']['passed'] = False
        results['python-3']['error'] = "Python 3 not installed in this system"

def test_pip():
    results['pip'] = {}
    results['pip']['condition'] = "Pip installed"
    if which('pip'):
        results['pip']['passed'] = True
        results['pip']['error'] = "OK"
    else:
        results['pip']['passed'] = False
        results['pip']['error'] = "pip not installed in this system"

tests.append('test_python_3')
tests.append('test_pip')

for test in tests:
    eval("%s()" % test)

can_install = True
print("%-15s %-25s %-6s %-34s" % ("Test", "Condition", "Passed", "Error"))
print("%15s %25s %6s %34s" % (15*"=", 25*"=", 6*"=", 34*"="))
for test in results:
    can_install = can_install and results[test]['passed']
    print("%-15s %-25s %-6s %-34s" % (test, results[test]['condition'], results[test]['passed'], results[test]['error']))

print()

if can_install:
    print("All tests were successfull. KB4IT can be installed")
else:
    print("Some tests were not successfull. Please, check")



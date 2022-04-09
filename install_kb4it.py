#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

if sys.version_info.major != 3:
    print("KB4IT needs Python 3")
    exit()

os.system("python3 -m pip install . --user")


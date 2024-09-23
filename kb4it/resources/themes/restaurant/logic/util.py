#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Util module.

# File: util.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: useful functions for Restaurant theme
"""

import math

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

def set_max_frequency(dkeyurl):
    """Calculate and set max frequency."""
    max_frequency = 1
    for keyword in dkeyurl:
        cur_frequency = len(dkeyurl[keyword])
        if cur_frequency > max_frequency:
            max_frequency = cur_frequency

    return max_frequency

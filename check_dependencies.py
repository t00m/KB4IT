#!/usr/bin/env python3
# coding: utf-8
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os
import sys
import platform

# Checking dependencies!
not_installed = []

# Mako Template System
try:
    import rich
    print('python3-rich found')
    mako_is_installed = True
except:
    mako_is_installed = False
    print('Error : Rich not installed!')
    not_installed.append('python3-rich')

# Mako Template System
try:
    import mako
    print('python3-mako found')
    mako_is_installed = True
except:
    mako_is_installed = False
    print('Error : Mako not installed!')
    not_installed.append('python3-mako')

# psutil
try:
    import psutil
    print('python3-psutil found!')
except:
    print("Warning: python3-psutil not installed!")
    not_installed.append('python3-psutil')

# show error if dependencies are not installed. Then, exit!
if len(not_installed) > 0:
    print('########################')
    print('#######  ERROR  ########')
    print('########################')
    print('Some dependencies are not installed! : \n')
    print(', '.join(not_installed))
    sys.exit(-1)


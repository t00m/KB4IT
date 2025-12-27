#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import semver

current = open('kb4it/VERSION', 'r').read()
print("Current version: %s" % current)
version = semver.VersionInfo.parse(current).bump_build()
print("Next build: %s" % version)

# Update main VERSION file
with open('kb4it/VERSION', 'w') as fv:
    fv.write(str(version))
print(f"kb4it/VERSION updated to {version}")

# Update pyproject.toml
pattern = r'^version\s*=\s*"[^"]*"'
replacement = f'version = "{version}"'
content = open('pyproject.toml').read()
new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
with open('pyproject.toml', 'w') as fout:
  fout.write(new_content)

print(f"pyproject.toml updated to {version}")

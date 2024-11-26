#!/usr/bin/env python3

version_filepath = 'kb4it/VERSION'
oldver = open(version_filepath, 'r').read()
newver = oldver.replace('\n', '')
with open(version_filepath, 'w') as fout:
  fout.write(newver)
print(f"Version adjusted: {newver}")

#!/usr/bin/env bash
pip uninstall kb4it -y
python3 ./scripts/genbuild.py
pip install . --user


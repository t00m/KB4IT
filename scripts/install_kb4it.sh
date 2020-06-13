#!/usr/bin/env bash
# Install KB4IT locally
sudo apt install asciidoctor coderay ruby-coderay python3-setuptools
python3 setup.py install --user

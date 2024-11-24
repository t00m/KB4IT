#!/usr/bin/env bash
# Install KB4IT locally
#sudo apt install asciidoctor coderay ruby-coderay python3-setuptools
#python3 setup.py install --user
rm -rf build && pip3 install . --user --trusted-host files.pythonhosted.org --trusted-host pypi.org

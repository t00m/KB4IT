#!/usr/bin/env bash
# Install KB4IT locally
#~ sudo apt install asciidoctor coderay ruby-coderay python3-setuptools
#~ python3 setup.py install --user
pip uninstall kb4it -y --break-system-packages
python3 ./scripts/genbuild.py
pip3 install . --user --break-system-packages

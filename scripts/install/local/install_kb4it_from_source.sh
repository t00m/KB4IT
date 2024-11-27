#!/usr/bin/env bash
# Install KB4IT locally
#~ sudo apt install asciidoctor coderay ruby-coderay python3-setuptools
#~ python3 setup.py install --user

#!/bin/bash

detect_distro() {
    if [ -f /etc/os-release ]; then
        # Read the os-release file
        . /etc/os-release
        case "$ID" in
            debian)
                echo "Installing KB4IT in Debian"
                pip3 install . --user --trusted-host files.pythonhosted.org --trusted-host pypi.org --break-system-packages
                ;;
            ubuntu)
                echo "Installing KB4IT in Ubuntu (based on Debian)"
                pip3 install . --user --trusted-host files.pythonhosted.org --trusted-host pypi.org --break-system-packages
                ;;
            rhel | redhat)
                echo "Red Hat Enterprise Linux"
                pip3 install . --user --trusted-host files.pythonhosted.org --trusted-host pypi.org
                ;;
            centos)
                echo "CentOS"
                pip3 install . --user --trusted-host files.pythonhosted.org --trusted-host pypi.org
                ;;
            arch)
                echo "Arch Linux"
                echo "No instructions provided. Open a ticket (and if possible the command):"
                echo "https://github.com/t00m/KB4IT/issues"
                ;;
            *)
                echo "Unknown Linux distribution: $ID"
                echo "Open a ticket (and if possible the command):"
                echo "https://github.com/t00m/KB4IT/issues"
                ;;
        esac
    else
        echo "/etc/os-release not found. Cannot detect distribution."
        echo "Open a ticket (and if possible the command):"
        echo "https://github.com/t00m/KB4IT/issues"
    fi
}

echo "KB4IT installer"
echo "==============="

echo "Installing KB4IT from sources in user space (no root/admin privileges needed)"
echo ""
echo "Uninstalling previous version"
echo "-----------------------------"
pip uninstall kb4it -y --break-system-packages
echo ""
echo "Cleaning environment"
echo "-----------------"
rm -rf build/ dist/ KB4IT.egg-info/
echo "Deleted directories build/ dist/ KB4IT.egg-info/"
echo ""


echo "Installing KB4IT"
echo "----------------"
detect_distro
echo ""
echo "Installation finished"
echo "---------------------"
echo ""
echo "Notes:"
echo "------"
echo "If the installation was successful, it is very likely that the KB4IT script is installed in:"
echo "$HOME/.local/bin/kb4it"
echo ""
echo "Test installed version"
echo "----------------------"
$HOME/.local/bin/kb4it -v

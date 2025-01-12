#!/usr/bin/env bash
# Install KB4IT locally
#~ sudo apt install asciidoctor coderay ruby-coderay python3-setuptools
#~ python3 setup.py install --user

# Find all installed Python versions
latest_python=$(ls /usr/bin/python3.* 2>/dev/null | sort -V | tail -n 1)

# Check if a Python version was found
if [[ -z "$latest_python" ]]; then
  echo "No Python 3 versions found."
  exit 1
fi

# Output the latest Python version
echo "The latest Python version is: $latest_python"


# Find all installed PIP versions
latest_pip=$(ls /usr/bin/pip3.* 2>/dev/null | sort -V | tail -n 1)
echo "PIP: $latest_pip"

# Find all installed PIPX versions
latest_pipx=$(ls /usr/bin/pipx 2>/dev/null | sort -V | tail -n 1)
echo "PIPX: $latest_pipx"

# Check if a pipx version was found
if [[ -z "$latest_pipx" ]]; then
  echo "pipx not found."
  exit 1
fi

# Output the latest pipx version
echo "The latest pipx version is: $latest_pipx"

echo ""
echo ""

uninstall_kb4it() {
    $latest_pipx uninstall kb4it
}


install_kb4it() {
    $latest_pipx install . --force
}

echo "KB4IT installer"
echo "==============="

echo "Installing KB4IT from sources in user space (no root/admin privileges needed)"
echo ""
echo "Uninstalling previous version"
echo "-----------------------------"
uninstall_kb4it
echo ""
echo "Cleaning environment"
echo "-----------------"
rm -rf build/ dist/ KB4IT.egg-info/
echo "Deleted directories build/ dist/ KB4IT.egg-info/"
echo ""


echo "Installing KB4IT"
echo "----------------"
install_kb4it
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

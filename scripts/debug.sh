LOCAL_PYTHON_PACKAGES=`python3 -c "import site; print(site.getsitepackages()[0])"`
KB4IT_LIBRARY="$LOCAL_PYTHON_PACKAGES/kb4it-*"

rm -rf ./kb4it/__pycache__ ./kb4it/__pycache__/__init__.cpython-38.pyc ./kb4it/core/__pycache__ ./kb4it/core/__pycache__/kbo.cpython-38.pyc ./kb4it/core/__pycache__/__init__.cpython-38.pyc ./kb4it/core/__pycache__/env.cpython-38.pyc ./tmp/html/resources/themes/default/logic/__pycache__ ./tmp/html/resources/themes/default/logic/__pycache__/theme.cpython-38.pyc
rm -rf build dist
echo -n "Uninstalling KB4IT... "
pip3 uninstall kb4it -qy
echo "Done."
echo -n "Install KB4IT from sources... "
python3 setup.py -q install --user
echo "Done"
echo ""
echo "====================="
echo "Installation finished"
echo "====================="
echo ""
echo "KB4IT usage:"
$HOME/.local/bin/kb4it --help
echo ""
echo "Test application with these example commands:"
echo ""
echo "reset && $HOME/.local/bin/kb4it -theme techdoc -sort <date_attribute> -source <sources_dir> -target <target_dir> -log DEBUG"
echo "or"
echo "reset && $HOME/.local/bin/kb4it -source <sources_dir> -target <target_dir> -log DEBUG"
echo ""

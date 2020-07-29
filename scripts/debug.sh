LOCAL_PYTHON_PACKAGES=`python3 -c "import site; print(site.getsitepackages()[0])"`
KB4IT_LIBRARY="$LOCAL_PYTHON_PACKAGES/kb4it-*"

echo -n "Delete KB4IT caches... "
rm -rf ./kb4it/__pycache__
rm -rf ./kb4it/__pycache__/__init__.cpython-38.pyc
rm -rf ./kb4it/core/__pycache__
rm -rf ./kb4it/core/__pycache__/kbo.cpython-38.pyc
rm -rf ./kb4it/core/__pycache__/__init__.cpython-38.pyc
rm -rf ./kb4it/core/__pycache__/env.cpython-38.pyc
rm -rf ./tmp/html/resources/themes/default/logic/__pycache__
rm -rf ./tmp/html/resources/themes/default/logic/__pycache__/theme.cpython-38.pyc
rm -rf build dist
echo "Done."

echo -n "Uninstalling KB4IT... "
pip3 uninstall kb4it -qy
echo " Done."

echo -n "Installing KB4IT... "
python3 setup.py -q install --user
echo "   Done."
echo ""
echo ""
echo "`$HOME/.local/bin/kb4it --help`"


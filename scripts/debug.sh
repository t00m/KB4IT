LOCAL_PYTHON_PACKAGES=`python3 -c "import site; print(site.getsitepackages()[0])"`
KB4IT_LIBRARY="$LOCAL_PYTHON_PACKAGES/kb4it-*"
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
echo "Test application with this command:"
echo ""
echo "reset && $HOME/.local/bin/kb4it -sp demo-sources -tp demo --log DEBUG"
echo ""

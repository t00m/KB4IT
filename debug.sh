LOCAL_PYTHON_PACKAGES=`python3 -c "import site; print(site.getsitepackages()[0])"`
KB4IT_LIBRARY="$LOCAL_PYTHON_PACKAGES/kb4it-*"
reset
rm -rf $KB4IT_LIBRARY
rm -rf build
rm -rf kb4it.egg-info
# rm -rf $HOME/.kb4it
python3 setup.py install --user
echo ""
echo "====================="
echo "Installation finished"
echo "====================="
echo ""
echo "Test application with this command:"
echo ""
echo "reset && $HOME/.local/bin/kb4it -sp tests/ -log DEBUG"
echo ""

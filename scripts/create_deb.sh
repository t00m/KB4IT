pandoc -t plain pypi/README.rst -o README
reset && python3 setup.py --command-packages=stdeb.command bdist_deb

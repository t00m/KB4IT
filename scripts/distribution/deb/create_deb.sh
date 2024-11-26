#pandoc -t plain README.rst -o README
reset && rm -rf ./deb_dist && python3 setup.py --command-packages=stdeb.command bdist_deb && echo "Deb package built:" && find ./deb_dist | grep '.deb$' && echo "Install command: sudo dpkg -i ./deb_dist/pyhthon3-kb4it_<version>.deb"

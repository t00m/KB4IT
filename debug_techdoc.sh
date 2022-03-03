rm -rf build dist kb4it/__pycache__/ kb4it/core/__pycache__/ KB4IT.egg-info/
python3 genbuild.py 
./install_kb4it_local.sh && read && reset && kb4itng -r repo.json

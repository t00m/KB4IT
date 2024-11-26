import json
import urllib.request; 
s = urllib.request.urlopen('https://yourserver/kb4it.json').read().decode()
d = json.loads(s)

oldver = open('kb4it/resources/offline/appdata/VERSION', 'r').read()
newver = oldver.replace('\n', '')
with open('kb4it/resources/offline/appdata/VERSION', 'w') as fout:
  fout.write(newver)


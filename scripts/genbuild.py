import semver
current = open('kb4it/VERSION', 'r').read()
print("Current version: %s" % current)
version = semver.VersionInfo.parse(current).bump_build()
print("Next build: %s" % version)
with open('kb4it/VERSION', 'w') as fv:
    fv.write(str(version))

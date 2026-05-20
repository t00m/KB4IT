#!/usr/bin/env bash
# Build an RPM package for KB4IT using rpmbuild.
#
# Strategy: create a clean source tarball of the repo, invoke rpmbuild
# against scripts/distribution/rpm/kb4it.spec. Semver build metadata
# (after '+') maps to the RPM Release field because RPM Version cannot
# contain '+'.
#
# Output: ~/rpmbuild/RPMS/noarch/kb4it-<version>-<release>.<dist>.noarch.rpm
# Also copied to ./dist/.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

if ! command -v rpmbuild >/dev/null 2>&1; then
    echo "rpmbuild not found. Install 'rpm-build' (Fedora/RHEL) and 'rpmdevtools'."
    exit 1
fi

RAW_VERSION="$(cat kb4it/VERSION)"       # e.g. 0.7.31+build.0
RPM_VERSION="${RAW_VERSION%%+*}"         # 0.7.31
if [[ "${RAW_VERSION}" == *"+"* ]]; then
    RPM_RELEASE="${RAW_VERSION#*+}"      # build.0
    # Release must not contain '+' or '-'
    RPM_RELEASE="${RPM_RELEASE//+/.}"
    RPM_RELEASE="${RPM_RELEASE//-/.}"
else
    RPM_RELEASE="1"
fi
PKG_NAME="kb4it"
TARBALL="${PKG_NAME}-${RPM_VERSION}.tar.gz"

echo ">>> Preparing ~/rpmbuild tree"
mkdir -p "${HOME}/rpmbuild"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

echo ">>> Creating source tarball: ${TARBALL}"
# Tarball reflects the working tree (tracked files + untracked non-ignored
# files) rather than HEAD, so iteration works without requiring every
# change to be committed first.
if git -C "${REPO_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    # Drop entries that are tracked but no longer exist on disk (deleted
    # files that have not been committed yet), so tar does not abort.
    git -C "${REPO_ROOT}" ls-files --cached --others --exclude-standard -z \
        | while IFS= read -r -d '' f; do [ -e "${REPO_ROOT}/${f}" ] && printf '%s\0' "${f}"; done \
        | tar --null --files-from=- \
              --transform "s,^,${PKG_NAME}-${RPM_VERSION}/," \
              -czf "${HOME}/rpmbuild/SOURCES/${TARBALL}"
else
    # fallback: tar the working tree
    tar --transform "s,^,${PKG_NAME}-${RPM_VERSION}/," \
        --exclude-vcs --exclude='./dist' --exclude='./build' \
        -czf "${HOME}/rpmbuild/SOURCES/${TARBALL}" .
fi

echo ">>> Copying spec"
cp "${SCRIPT_DIR}/${PKG_NAME}.spec" "${HOME}/rpmbuild/SPECS/"

echo ">>> Building RPM"
rpmbuild -bb \
    --define "kb4it_version ${RPM_VERSION}" \
    --define "kb4it_release ${RPM_RELEASE}" \
    "${HOME}/rpmbuild/SPECS/${PKG_NAME}.spec"

echo ">>> Collecting artefacts"
mkdir -p "${REPO_ROOT}/dist"
# Scope the find pattern to the exact release, otherwise older builds left
# in ~/rpmbuild/RPMS/ get copied alongside the freshly built one.
find "${HOME}/rpmbuild/RPMS" -name "${PKG_NAME}-${RPM_VERSION}-${RPM_RELEASE}*.rpm" -print -exec cp {} "${REPO_ROOT}/dist/" \;

echo ""
echo "Install with:"
echo "  sudo dnf install ${REPO_ROOT}/dist/${PKG_NAME}-${RPM_VERSION}-*.rpm"

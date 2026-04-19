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
# git archive ensures we exclude .git, build artefacts, etc.
if git -C "${REPO_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "${REPO_ROOT}" archive --format=tar.gz \
        --prefix="${PKG_NAME}-${RPM_VERSION}/" \
        --output "${HOME}/rpmbuild/SOURCES/${TARBALL}" \
        HEAD
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
find "${HOME}/rpmbuild/RPMS" -name "${PKG_NAME}-${RPM_VERSION}-*.rpm" -print -exec cp {} "${REPO_ROOT}/dist/" \;

echo ""
echo "Install with:"
echo "  sudo dnf install ${REPO_ROOT}/dist/${PKG_NAME}-${RPM_VERSION}-*.rpm"

#!/usr/bin/env bash
# Build an RPM package for KB4IT using rpmbuild.
#
# Usage: build_rpm.sh [ARCH]      ARCH: x86_64 (default on x86_64) | aarch64
#
# Strategy: build the KB4IT wheel (DS-01) and download the dependency wheels for
# ARCH (wheels/download_wheels.sh), then pass them to rpmbuild as sources together
# with the documents. rpmbuild needs no network. Semver build metadata (after '+')
# maps to the RPM Release field because RPM Version cannot contain '+'.
#
# Output: dist/kb4it-<version>-<release>[.<dist>].<arch>.rpm
# The rpmbuild tree lives in dist/rpm_build/.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"
cd "${REPO_ROOT}"

if ! command -v rpmbuild >/dev/null 2>&1; then
    echo "rpmbuild not found. Install 'rpm-build' (Fedora/RHEL) or 'rpm' (Debian/Ubuntu)."
    exit 1
fi
if ! ARCH="$(arch_machine "${1:-$(uname -m)}")"; then
    echo "Usage: $(basename "$0") [x86_64|aarch64]" >&2
    exit 1
fi

RPM_VERSION="${KB4IT_VERSION%%+*}"           
if [[ "${KB4IT_VERSION}" == *"+"* ]]; then
    RPM_RELEASE="${KB4IT_VERSION#*+}"        # build.0
    # Release must not contain '+' or '-'
    RPM_RELEASE="${RPM_RELEASE//+/.}"
    RPM_RELEASE="${RPM_RELEASE//-/.}"
else
    RPM_RELEASE="1"
fi
PKG_NAME="kb4it"
TOPDIR="${OUT_DIR}/rpm_build"
SOURCES="${TOPDIR}/SOURCES"

# Boolean dependency: a python3 in the supported range, or any versioned interpreter
# of it (RHEL 9 ships python3 3.9 with python3.11 and python3.12 alongside).
LAST="${KB4IT_PYTHONS[${#KB4IT_PYTHONS[@]}-1]}"
NEXT="${LAST%%.*}.$(( ${LAST#*.} + 1 ))"
PY_REQUIRES="((python3 >= ${KB4IT_PYTHONS[0]} with python3 < ${NEXT})"
for py in "${KB4IT_PYTHONS[@]}"; do
    PY_REQUIRES+=" or python${py}"
done
PY_REQUIRES+=")"

echo ">>> Preparing ${TOPDIR}"
rm -rf "${TOPDIR}"
mkdir -p "${TOPDIR}"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

echo ">>> Collecting sources for ${ARCH}"
ensure_wheel
WHEEL="$(wheel_path)"
cp "${WHEEL}" "${SOURCES}/"
DEPS="$(ensure_dep_wheels "${ARCH}")"
tar -czf "${SOURCES}/${PKG_NAME}-${RPM_VERSION}-wheels-${ARCH}.tar.gz" -C "${DEPS}" .
tar -czf "${SOURCES}/${PKG_NAME}-${RPM_VERSION}-docs.tar.gz" LICENSE README.md CHANGELOG.md AUTHORS THANKS
cp "${SCRIPT_DIR}/${PKG_NAME}.spec" "${TOPDIR}/SPECS/"

echo ">>> Building RPM"
rpmbuild -bb --target "${ARCH}" \
    --define "_topdir ${TOPDIR}" \
    --define "kb4it_version ${RPM_VERSION}" \
    --define "kb4it_release ${RPM_RELEASE}" \
    --define "kb4it_summary ${KB4IT_SUMMARY}" \
    --define "kb4it_description ${KB4IT_DESCRIPTION}" \
    --define "kb4it_pythons ${KB4IT_PYTHONS[*]}" \
    --define "kb4it_python_requires ${PY_REQUIRES}" \
    --define "kb4it_wheel $(basename "${WHEEL}")" \
    --define "kb4it_wheel_version ${KB4IT_VERSION}" \
    "${TOPDIR}/SPECS/${PKG_NAME}.spec"

echo ">>> Collecting artefacts"
find "${TOPDIR}/RPMS" -name "${PKG_NAME}-${RPM_VERSION}-${RPM_RELEASE}*.rpm" -print -exec cp {} "${OUT_DIR}/" \;

echo ""
echo "Install with:"
echo "  sudo dnf install ${OUT_DIR}/${PKG_NAME}-${RPM_VERSION}-${RPM_RELEASE}*.${ARCH}.rpm"

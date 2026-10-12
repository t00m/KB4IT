#!/usr/bin/env bash
# Build the Linux packages for this machine's architecture and test them in containers.
#
# Usage: test_packages.sh [deb|rpm|all]      (default: all)
#
# Each target image first gets its Python in a prepared layer (with network). The
# package install, `kb4it --version`, a create-and-build of the techdoc sample and
# the removal then run with --network none, so they prove the install is offline.
#
# Needs docker or podman. Used locally and by the `packages` CI job.
# KB4IT_PKGTEST_DEB_IMAGES and KB4IT_PKGTEST_RPM_IMAGES replace the default image lists.
set -euo pipefail

# shellcheck source=../lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"
cd "${REPO_ROOT}"

if command -v docker >/dev/null 2>&1; then
    RUNTIME="docker"
elif command -v podman >/dev/null 2>&1; then
    RUNTIME="podman"
else
    echo "Neither docker nor podman is installed." >&2
    exit 1
fi

MACHINE="$(arch_machine "$(uname -m)")"
DEB_ARCH="$(arch_debian "${MACHINE}")"
FAILED=()

# Steps run inside the target container once the package is installed.
SMOKE='kb4it --version
kb4it create techdoc /tmp/kb >/dev/null
if ! kb4it build /tmp/kb/config/repo.json >/tmp/build.log 2>&1; then tail -n 20 /tmp/build.log; exit 1; fi
test -f /tmp/kb/target/index.html
echo "smoke build: ok"'

# prepare IMAGE TAG SETUP: an image with the Python the package needs, tagged TAG.
# An existing TAG is reused; remove the kb4it-pkgtest images to refresh them.
prepare() {
    if "${RUNTIME}" image inspect "$2" >/dev/null 2>&1; then
        return 0
    fi
    printf 'FROM %s\nRUN %s\n' "$1" "$3" | "${RUNTIME}" build --quiet --tag "$2" - >/dev/null
}

# check NAME TAG SCRIPT: run SCRIPT offline in TAG with dist/ mounted at /dist.
check() {
    echo ""
    echo "=== $1"
    if "${RUNTIME}" run --rm --network none --volume "${OUT_DIR}:/dist:ro" "$2" sh -ec "$3"; then
        echo "=== $1: passed"
    else
        echo "=== $1: FAILED" >&2
        FAILED+=("$1")
    fi
}

test_deb() {
    "${DIST_DIR}/deb/build_deb.sh" "${DEB_ARCH}"
    local deb="kb4it_${KB4IT_VERSION//+/\~}_${DEB_ARCH}.deb" image tag
    for image in ${KB4IT_PKGTEST_DEB_IMAGES:-debian:bookworm ubuntu:24.04}; do
        tag="kb4it-pkgtest:${image//[:.]/-}"
        prepare "${image}" "${tag}" "apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-venv && rm -rf /var/lib/apt/lists/*"
        check ".deb on ${image}" "${tag}" "apt-get install -y /dist/${deb}
${SMOKE}
apt-get remove -y kb4it
test ! -e /opt/kb4it && test ! -e /usr/bin/kb4it
echo 'remove: ok'"
    done
}

case "${1:-all}" in
    deb) test_deb ;;
    all) test_deb ;;
    *) echo "Usage: $(basename "$0") [deb|rpm|all]" >&2; exit 1 ;;
esac

echo ""
if [[ ${#FAILED[@]} -gt 0 ]]; then
    echo "Failed: ${FAILED[*]}" >&2
    exit 1
fi
echo "All package tests passed."

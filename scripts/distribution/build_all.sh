#!/usr/bin/env bash
# Build every KB4IT distribution artefact that the local environment supports.
#
# Each step is optional and is skipped if its prerequisites are missing,
# so this script is safe to run on any GNU/Linux host.
#
# Steps:
#   1. Python sdist + wheel      (requires python3)
#   2. Source tarball + zip      (requires git or tar)
#   3. Docker image              (requires docker or podman)
#   4. .deb package              (requires dpkg-deb)
#   5. .rpm package              (requires rpmbuild)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

run_step() {
    local name="$1" cmd="$2" test_cmd="$3"
    echo ""
    echo "============================================================"
    echo "  ${name}"
    echo "============================================================"
    if ! eval "${test_cmd}" >/dev/null 2>&1; then
        echo "  SKIP: prerequisites missing (${test_cmd})"
        return 0
    fi
    if ! bash -c "${cmd}"; then
        echo "  FAIL: ${name}" >&2
        FAILED+=("${name}")
    fi
}

FAILED=()

run_step "Python sdist + wheel" \
         "${SCRIPT_DIR}/build/build_python.sh" \
         "command -v python3"

run_step "Source tarball + zip" \
         "${SCRIPT_DIR}/tarball/build_tarball.sh" \
         "command -v tar"

run_step "Docker image" \
         "${SCRIPT_DIR}/docker/build.sh" \
         "command -v docker || command -v podman"

run_step ".deb package" \
         "SKIP_BUILD=1 ${SCRIPT_DIR}/deb/build_deb.sh" \
         "command -v dpkg-deb"

run_step ".rpm package" \
         "${SCRIPT_DIR}/rpm/build_rpm.sh" \
         "command -v rpmbuild"

echo ""
echo "============================================================"
echo "  Summary"
echo "============================================================"
if [[ ${#FAILED[@]} -eq 0 ]]; then
    echo "All applicable steps succeeded."
else
    echo "Failed steps:"
    for f in "${FAILED[@]}"; do echo "  - $f"; done
    exit 1
fi

echo ""
echo "Artefacts in ${REPO_ROOT}/dist/:"
ls -la "${REPO_ROOT}/dist/" 2>/dev/null || true

#!/usr/bin/env bash
# Build a clean source release tarball (.tar.gz) and a zip from the git HEAD.
# Excludes .git/, build/, dist/, caches, and local-only dirs.
#
# Output:
#   dist/KB4IT-<version>.tar.gz
#   dist/KB4IT-<version>.zip
#   dist/KB4IT-<version>.tar.gz.sha256
#   dist/KB4IT-<version>.zip.sha256
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

VERSION="$(cat kb4it/VERSION)"
PKG_NAME="KB4IT"
PREFIX="${PKG_NAME}-${VERSION}"
OUT_DIR="${REPO_ROOT}/dist"

mkdir -p "${OUT_DIR}"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo ">>> Creating ${PREFIX}.tar.gz via git archive"
    git archive --format=tar.gz --prefix="${PREFIX}/" \
        --output "${OUT_DIR}/${PREFIX}.tar.gz" HEAD

    echo ">>> Creating ${PREFIX}.zip via git archive"
    git archive --format=zip --prefix="${PREFIX}/" \
        --output "${OUT_DIR}/${PREFIX}.zip" HEAD
else
    echo ">>> Not a git repo, falling back to tar with excludes"
    tar --transform "s,^,${PREFIX}/," \
        --exclude-vcs \
        --exclude='./dist' \
        --exclude='./build' \
        --exclude='./.pixi' \
        --exclude='./.mypy_cache' \
        --exclude='./__pycache__' \
        --exclude='*.pyc' \
        -czf "${OUT_DIR}/${PREFIX}.tar.gz" .
fi

echo ">>> Computing checksums"
(cd "${OUT_DIR}" && sha256sum "${PREFIX}.tar.gz" > "${PREFIX}.tar.gz.sha256")
if [[ -f "${OUT_DIR}/${PREFIX}.zip" ]]; then
    (cd "${OUT_DIR}" && sha256sum "${PREFIX}.zip" > "${PREFIX}.zip.sha256")
fi

echo ""
ls -la "${OUT_DIR}"/${PREFIX}.*
echo ""
echo "Done."

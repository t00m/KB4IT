#!/usr/bin/env bash
# Install KB4IT via pipx from a user-chosen source.
#
# Usage:
#   install_pipx.sh [source|wheel|pypi|testpypi]
#     source    (default) Install from the current checkout (./)
#     wheel     Install from the newest wheel in ./dist (build first if none)
#     pypi      Install from production PyPI
#     testpypi  Install from TestPyPI (falls back to PyPI for deps)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

MODE="${1:-source}"

if ! command -v pipx >/dev/null 2>&1; then
    echo "pipx not found. Install it first (e.g. 'python3 -m pip install --user pipx && pipx ensurepath')."
    exit 1
fi

echo ">>> Uninstalling any previous KB4IT (ignoring failure)"
pipx uninstall kb4it || true

case "${MODE}" in
    source)
        echo ">>> Installing from source: ${REPO_ROOT}"
        pipx install . --force
        ;;
    wheel)
        # shellcheck source=../lib/common.sh
        source "${SCRIPT_DIR}/../lib/common.sh"
        ensure_wheel
        WHEEL="$(wheel_path)"
        echo ">>> Installing from wheel: ${WHEEL}"
        pipx install "${WHEEL}" --force
        ;;
    pypi)
        echo ">>> Installing from PyPI"
        pipx install KB4IT --force
        ;;
    testpypi)
        echo ">>> Installing from TestPyPI (deps resolved against PyPI)"
        pipx install \
            --pip-args "--index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/" \
            --force \
            KB4IT
        ;;
    *)
        echo "Unknown mode: ${MODE}"
        echo "Usage: $(basename "$0") [source|wheel|pypi|testpypi]"
        exit 1
        ;;
esac

echo ""
echo ">>> Verifying installation"
"${HOME}/.local/bin/kb4it" --version || kb4it --version

echo ""
echo "Done."

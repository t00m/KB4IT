#!/usr/bin/env bash
# Publish KB4IT to the production PyPI index (https://pypi.org/).
#
# Requires:
#   - A PyPI account with an API token
#   - ~/.pypirc configured with [pypi] section, OR
#   - Environment vars TWINE_USERNAME=__token__ TWINE_PASSWORD=<pypi-token>
#
# Behaviour:
#   - Builds fresh artifacts unless SKIP_BUILD=1
#   - Verifies artifacts with twine check before upload
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

# The build stamp needs git: a clean clone of the tag, never an export or a working tree (RA-11).
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Run this from a git clone (git clone --branch vX.Y.Z), not from an export: the build stamp needs git." >&2
    exit 1
fi

if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
    "${SCRIPT_DIR}/../build/build_python.sh"
fi

# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"
echo ""
echo ">>> Checking the wheel (the release stamp of tag v${KB4IT_VERSION})"
python3 scripts/devel/check_wheel_themes.py --release "${KB4IT_VERSION}" "$(wheel_path)"

echo ""
echo ">>> Installing twine"
python3 -m pip install --quiet --upgrade twine

echo ""
echo ">>> Checking artifacts"
python3 -m twine check dist/*

echo ""
read -r -p "Upload dist/* to PyPI (production)? [y/N] " confirm
if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo ">>> Uploading to PyPI"
python3 -m twine upload dist/*

echo ""
echo "Done. Package published to https://pypi.org/project/KB4IT/"

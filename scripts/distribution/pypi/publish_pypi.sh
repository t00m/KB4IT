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

if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
    "${SCRIPT_DIR}/../build/build_python.sh"
fi

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

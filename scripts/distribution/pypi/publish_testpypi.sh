#!/usr/bin/env bash
# Publish KB4IT to the TestPyPI index (https://test.pypi.org/).
# Use this to rehearse a release before publishing to production PyPI.
#
# Requires:
#   - A TestPyPI account with an API token
#   - ~/.pypirc with [testpypi] section, OR
#   - Environment vars TWINE_USERNAME=__token__ TWINE_PASSWORD=<testpypi-token>
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
echo ">>> Uploading to TestPyPI"
python3 -m twine upload --repository testpypi dist/*

echo ""
echo "Done. Verify with:"
echo "  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ KB4IT"

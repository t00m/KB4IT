#!/usr/bin/env bash
# Build the KB4IT sdist and wheel into <repo>/dist/.
#
# Removes earlier KB4IT wheels and sdists first, so later steps never pick a stale one.
# Uses `uv build` when uv is installed, otherwise `python3 -m build`.
set -euo pipefail

# shellcheck source=../lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"
cd "${REPO_ROOT}"

mkdir -p "${OUT_DIR}"
rm -f "${OUT_DIR}"/kb4it-*.whl "${OUT_DIR}"/kb4it-*.tar.gz

echo ">>> Building sdist and wheel of KB4IT ${KB4IT_VERSION}"
if command -v uv >/dev/null 2>&1; then
    uv build --out-dir "${OUT_DIR}"
else
    python3 -m build --outdir "${OUT_DIR}" .
fi

WHEEL="$(wheel_path)"
SDIST="${OUT_DIR}/kb4it-${KB4IT_VERSION}.tar.gz"
for f in "${WHEEL}" "${SDIST}"; do
    if [[ ! -f "${f}" ]]; then
        echo "Expected file not built: ${f}" >&2
        exit 1
    fi
done
echo "${WHEEL}"
echo "${SDIST}"

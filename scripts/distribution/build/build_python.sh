#!/usr/bin/env bash
# Build the KB4IT sdist and wheel into <repo>/dist/.
#
# Removes earlier KB4IT wheels and sdists first, so later steps never pick a stale one.
# Uses uv when it is installed, otherwise the Python build module.
set -euo pipefail

# shellcheck source=../lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"
cd "${REPO_ROOT}"

mkdir -p "${OUT_DIR}"
rm -f "${OUT_DIR}"/kb4it-*.whl "${OUT_DIR}"/kb4it-*.tar.gz

# The offline help is git-ignored and must be in the tree before packaging.
# It needs the extras (pymdownx, nh3, pygments). With uv they are fetched on the fly;
# without uv, python3 must already have KB4IT[extras]. A failure stops the build.
echo ">>> Building the offline help"
if command -v uv >/dev/null 2>&1; then
    uv run --no-project --with-requirements requirements.txt --with pymdown-extensions --with nh3 --with pygments python scripts/help/build_offline.py
else
    python3 scripts/help/build_offline.py
fi

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

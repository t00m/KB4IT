#!/usr/bin/env bash
# Download the wheels of KB4IT's dependencies for one Linux architecture, so the
# .deb and .rpm can install KB4IT without network access.
#
# Usage: download_wheels.sh ARCH      ARCH: amd64 | x86_64 | arm64 | aarch64
#
# Output: <repo>/dist/wheels/<x86_64|aarch64>/ with binary wheels for every Python
# version in KB4IT_PYTHONS (lib/common.sh). Fails when a dependency has no binary
# wheel for one of them.
set -euo pipefail

# shellcheck source=../lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"

if ! MACHINE="$(arch_machine "${1:-}")"; then
    echo "Usage: $(basename "$0") amd64|x86_64|arm64|aarch64" >&2
    exit 1
fi

if python3 -m pip --version >/dev/null 2>&1; then
    PIP=(python3 -m pip)
elif command -v uv >/dev/null 2>&1; then
    PIP=(uv run --no-project --with pip python -m pip)
else
    echo "Neither pip nor uv is available." >&2
    exit 1
fi

DEST="${OUT_DIR}/wheels/${MACHINE}"
rm -rf "${DEST}"
mkdir -p "${DEST}"

for py in "${KB4IT_PYTHONS[@]}"; do
    echo ">>> Wheels for Python ${py} on ${MACHINE}"
    "${PIP[@]}" download --quiet --disable-pip-version-check \
        --requirement "${REPO_ROOT}/requirements.txt" \
        --only-binary=:all: --implementation cp --python-version "${py}" \
        --platform "manylinux_2_28_${MACHINE}" --platform "manylinux_2_17_${MACHINE}" \
        --platform "manylinux2014_${MACHINE}" \
        --dest "${DEST}"
done

echo ""
echo "$(find "${DEST}" -name '*.whl' | wc -l | tr -d ' ') wheels in ${DEST} ($(du -sh "${DEST}" | cut -f1))"

#!/usr/bin/env bash
# Build the KB4IT container image from the release wheel.
#
# Env overrides:
#   IMAGE_NAME       image name/tag prefix   (default: kb4it)
#   IMAGE_REGISTRY   remote registry         (default: empty, local only)
#   PYTHON_VERSION   base image python       (default: 3.13)
#
# Tags produced:
#   <name>:<version>        e.g. kb4it:0.9.0
#   <name>:latest
#
# The build context is dist/image/, which holds only the wheel.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"
cd "${REPO_ROOT}"

IMAGE_NAME="${IMAGE_NAME:-kb4it}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-}"
PYTHON_VERSION="${PYTHON_VERSION:-3.13}"

# Docker tags cannot contain '+', replace with '-'
DOCKER_TAG="${KB4IT_VERSION//+/-}"
REVISION="$(git rev-parse HEAD 2>/dev/null || true)"

PREFIX=""
if [[ -n "${IMAGE_REGISTRY}" ]]; then
    PREFIX="${IMAGE_REGISTRY}/"
fi

if command -v docker >/dev/null 2>&1; then
    RUNTIME="docker"
elif command -v podman >/dev/null 2>&1; then
    RUNTIME="podman"
else
    echo "Neither docker nor podman is installed."
    exit 1
fi

echo ">>> Preparing the build context"
ensure_wheel
CONTEXT="${OUT_DIR}/image"
rm -rf "${CONTEXT}"
mkdir -p "${CONTEXT}"
cp "$(wheel_path)" "${CONTEXT}/"

echo ">>> Building ${PREFIX}${IMAGE_NAME}:${DOCKER_TAG} with ${RUNTIME}"
"${RUNTIME}" build \
    --file "${SCRIPT_DIR}/Dockerfile" \
    --build-arg "PYTHON_VERSION=${PYTHON_VERSION}" \
    --build-arg "KB4IT_VERSION=${KB4IT_VERSION}" \
    --build-arg "KB4IT_REVISION=${REVISION}" \
    --build-arg "KB4IT_DESCRIPTION=${KB4IT_DESCRIPTION}" \
    --tag "${PREFIX}${IMAGE_NAME}:${DOCKER_TAG}" \
    --tag "${PREFIX}${IMAGE_NAME}:latest" \
    "${CONTEXT}"

echo ""
echo "Built tags:"
echo "  ${PREFIX}${IMAGE_NAME}:${DOCKER_TAG}"
echo "  ${PREFIX}${IMAGE_NAME}:latest"
echo ""
echo "Run example, from the folder of a knowledge base:"
echo "  ${RUNTIME} run --rm -v \"\$PWD:/work\" --user \"\$(id -u):\$(id -g)\" \\"
echo "    ${PREFIX}${IMAGE_NAME}:latest build config/repo.json"

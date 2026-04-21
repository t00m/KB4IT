#!/usr/bin/env bash
# Build the KB4IT Docker image.
#
# Env overrides:
#   IMAGE_NAME   image name/tag prefix     (default: kb4it)
#   IMAGE_REGISTRY   remote registry       (default: empty, local only)
#   PYTHON_VERSION   base image python     (default: 3.12)
#
# Tags produced:
#   <name>:<version>        e.g. kb4it:0.7.31
#   <name>:latest
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

IMAGE_NAME="${IMAGE_NAME:-kb4it}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-}"
PYTHON_VERSION="${PYTHON_VERSION:-3.12}"

VERSION="$(cat kb4it/VERSION)"
# Docker tags cannot contain '+', replace with '-'
DOCKER_TAG="${VERSION//+/-}"

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

echo ">>> Building ${PREFIX}${IMAGE_NAME}:${DOCKER_TAG} with ${RUNTIME}"
"${RUNTIME}" build \
    --file "${SCRIPT_DIR}/Dockerfile" \
    --build-arg "PYTHON_VERSION=${PYTHON_VERSION}" \
    --tag "${PREFIX}${IMAGE_NAME}:${DOCKER_TAG}" \
    --tag "${PREFIX}${IMAGE_NAME}:latest" \
    "${REPO_ROOT}"

echo ""
echo "Built tags:"
echo "  ${PREFIX}${IMAGE_NAME}:${DOCKER_TAG}"
echo "  ${PREFIX}${IMAGE_NAME}:latest"
echo ""
echo "Run example:"
echo "  ${RUNTIME} run --rm \\"
echo "    -v \"\$(pwd)/myrepo:/work\" \\"
echo "    -v \"\$(pwd)/out:/out\" \\"
echo "    ${PREFIX}${IMAGE_NAME}:latest build /work/config/repo.json"

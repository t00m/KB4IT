#!/usr/bin/env bash
# Smoke test of a KB4IT container image.
#
# Usage: smoke.sh [IMAGE]      (default: kb4it:latest)
#
# Checks that the image prints the version of kb4it/VERSION, creates and builds the
# techdoc sample in a mounted folder as the calling user (and the files belong to
# that user), and serves the site over HTTP. Writes the image size to the GitHub job
# summary when it runs in GitHub Actions.
#
# Env: RUNTIME (docker or podman, default: whichever is installed),
#      KB4IT_SMOKE_USER (UID:GID to run as, default: the calling user),
#      KB4IT_SMOKE_PORT (host port for the serve check, default: 18642).
set -euo pipefail

# shellcheck source=../lib/common.sh
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"

IMAGE="${1:-kb4it:latest}"
RUNTIME="${RUNTIME:-$(command -v docker >/dev/null 2>&1 && echo docker || echo podman)}"
RUN_USER="${KB4IT_SMOKE_USER:-$(id -u):$(id -g)}"
PORT="${KB4IT_SMOKE_PORT:-18642}"
# SELinux hosts (Fedora, RHEL) need the :Z label on bind mounts with podman.
LABEL=""
if [[ "${RUNTIME}" == "podman" ]]; then
    LABEL=":Z"
fi

WORK="$(mktemp -d)"
chmod 0777 "${WORK}"
CONTAINER="kb4it-smoke-$$"
cleanup() {
    "${RUNTIME}" rm -f "${CONTAINER}" >/dev/null 2>&1 || true
    rm -rf "${WORK}" 2>/dev/null || "${RUNTIME}" run --rm -v "${WORK}:/work${LABEL}" --user 0 --entrypoint rm "${IMAGE}" -rf /work/kb || true
}
trap cleanup EXIT

run() {
    "${RUNTIME}" run --rm --user "${RUN_USER}" -v "${WORK}:/work${LABEL}" "${IMAGE}" "$@"
}

echo ">>> Version"
VERSION_OUT="$("${RUNTIME}" run --rm "${IMAGE}" --version)"
echo "${VERSION_OUT}"
if [[ "${VERSION_OUT}" != *"${KB4IT_VERSION}"* ]]; then
    echo "Expected version ${KB4IT_VERSION}" >&2
    exit 1
fi

echo ">>> Create and build the techdoc sample as ${RUN_USER}"
run create techdoc kb >/dev/null 2>&1
run build kb/config/repo.json >"${WORK}/build.log" 2>&1 || { tail -n 20 "${WORK}/build.log"; exit 1; }
test -f "${WORK}/kb/target/index.html"
OWNER="$(stat -c '%u' "${WORK}/kb/target/index.html")"
if [[ "${OWNER}" != "${RUN_USER%%:*}" ]]; then
    echo "index.html belongs to UID ${OWNER}, expected ${RUN_USER%%:*}" >&2
    exit 1
fi
echo "build: ok, files owned by UID ${OWNER}"

echo ">>> Serve"
"${RUNTIME}" run -d --name "${CONTAINER}" --user "${RUN_USER}" -p "127.0.0.1:${PORT}:8642" \
    -v "${WORK}:/work${LABEL}" "${IMAGE}" serve kb/config/repo.json --host 0.0.0.0 --no-watch >/dev/null
for _ in $(seq 1 60); do
    if curl -fsS "http://127.0.0.1:${PORT}/index.html" -o /dev/null 2>/dev/null; then
        echo "serve: ok"
        break
    fi
    sleep 1
done
if ! curl -fsS "http://127.0.0.1:${PORT}/index.html" -o /dev/null; then
    "${RUNTIME}" logs "${CONTAINER}" | tail -n 20
    exit 1
fi

SIZE="$("${RUNTIME}" image inspect "${IMAGE}" --format '{{.Size}}')"
echo ">>> Image size: $(( SIZE / 1024 / 1024 )) MB"
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    echo "Image \`${IMAGE}\`: $(( SIZE / 1024 / 1024 )) MB uncompressed; version, build and serve checks passed." >> "${GITHUB_STEP_SUMMARY}"
fi
echo "All container checks passed."

# shellcheck shell=bash
# shellcheck disable=SC2034  # the variables are read by the scripts that source this file
# Shared settings of the distribution scripts. Source it from a script; do not run it.
#
# Sets REPO_ROOT, DIST_DIR (scripts/distribution), OUT_DIR (<repo>/dist, or KB4IT_DIST_OUT),
# KB4IT_VERSION, the package texts, and the Python versions the Linux packages carry wheels for.

DIST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${DIST_DIR}/../.." && pwd)"
OUT_DIR="${KB4IT_DIST_OUT:-${REPO_ROOT}/dist}"
KB4IT_VERSION="$(tr -d '[:space:]' < "${REPO_ROOT}/kb4it/VERSION")"

# One text for the .deb, the .rpm and the container image.
KB4IT_SUMMARY="Static website generator for Markdown knowledge bases"
KB4IT_DESCRIPTION="KB4IT turns a folder of Markdown files with YAML frontmatter into a static website you can browse by any property. Themes: techdoc, blog, bookshelf, apphelp."

# Python versions the .deb and .rpm ship dependency wheels for.
KB4IT_PYTHONS=(3.11 3.12 3.13)

# Path of the wheel for the current version (it may not exist yet).
wheel_path() {
    echo "${OUT_DIR}/kb4it-${KB4IT_VERSION}-py3-none-any.whl"
}

# Build the wheel and sdist only when dist/ has no wheel for the current version.
ensure_wheel() {
    if [[ ! -f "$(wheel_path)" ]]; then
        "${DIST_DIR}/build/build_python.sh"
    fi
}

#!/usr/bin/env bash
# Steps of the KB4IT GitHub Action (action.yml at the repository root).
#
# Usage: run.sh install|verify|build
#
# Reads the action inputs from the environment: KB4IT_CONFIG, KB4IT_VERSION,
# KB4IT_PYTHON, KB4IT_EXTRAS, KB4IT_FORCE and ACTION_PATH (the action's own
# checkout). Writes outputs to $GITHUB_OUTPUT and the job summary to
# $GITHUB_STEP_SUMMARY. Runs in bash on Linux, macOS and Windows runners.
set -euo pipefail

kb4it() {
    "$(uv tool dir --bin)/kb4it" "$@"
}

install() {
    local spec
    if [[ -n "${KB4IT_VERSION:-}" ]]; then
        spec="KB4IT==${KB4IT_VERSION}"
    else
        # The KB4IT of the action's own commit: @v1.2.3 means KB4IT 1.2.3.
        spec="${ACTION_PATH}"
    fi
    local with=()
    if [[ "${KB4IT_EXTRAS:-false}" == "true" ]]; then
        with=(--with "pymdown-extensions>=10.0" --with "nh3>=0.3.0")
    fi
    echo "Installing ${spec} with Python ${KB4IT_PYTHON}"
    # macOS bash 3.2 treats an empty "${with[@]}" as unbound under set -u.
    uv tool install --force --python "${KB4IT_PYTHON}" ${with[@]+"${with[@]}"} "${spec}"
    local version
    version="$(kb4it --version | awk '{print $2}')"
    echo "version=${version}" >> "${GITHUB_OUTPUT}"
    echo "KB4IT ${version} installed"
}

verify() {
    kb4it verify "${KB4IT_CONFIG}"
}

# Absolute target folder, resolved like KB4IT does: relative to the repository
# root (the parent of the folder holding repo.json), with ~ and $VARS expanded.
target_of() {
    uv run --no-project --python "${KB4IT_PYTHON}" python -c '
import json, os, sys
config = os.path.abspath(sys.argv[1])
root = os.path.dirname(os.path.dirname(config))
with open(config, encoding="utf-8-sig") as fh:
    raw = json.load(fh)["target"]
path = os.path.expanduser(os.path.expandvars(raw))
if not os.path.isabs(path):
    path = os.path.join(root, path)
print(os.path.realpath(path))
' "$1"
}

build() {
    local args=(build "${KB4IT_CONFIG}")
    if [[ "${KB4IT_FORCE:-false}" == "true" ]]; then
        args+=(--force)
    fi
    local log="${RUNNER_TEMP:-/tmp}/kb4it-build.log"
    kb4it "${args[@]}" 2>&1 | tee "${log}"
    local target summary
    target="$(target_of "${KB4IT_CONFIG}")"
    echo "target=${target}" >> "${GITHUB_OUTPUT}"
    summary="$(grep -o '\[WORKFLOW\] SUMMARY.*' "${log}" | tail -n 1 || true)"
    {
        echo "### KB4IT build"
        echo ""
        echo "| | |"
        echo "|---|---|"
        echo "| KB4IT | $(kb4it --version | awk '{print $2}') |"
        for key in docs_total compiled skipped invalid failed; do
            echo "| ${key} | $(grep -o " ${key}=[0-9]*" <<<"${summary}" | cut -d= -f2) |"
        done
        echo "| target | \`${target}\` |"
    } >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
}

case "${1:-}" in
    install) install ;;
    verify) verify ;;
    build) build ;;
    *) echo "Usage: $(basename "$0") install|verify|build" >&2; exit 1 ;;
esac

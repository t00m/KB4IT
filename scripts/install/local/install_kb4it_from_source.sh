#!/usr/bin/env bash
# Install KB4IT from this checkout for the current user, the way a release is built.
#
# Builds the wheel with scripts/distribution/build/build_python.sh (offline help and
# build stamp included), checks it, installs the wheel file (never the folder) and
# proves that the kb4it on PATH is the one just built. No root/admin privileges needed.
#
# Usage: install_kb4it_from_source.sh [options]
#   --method auto|uv|pipx|venv  how to install (default auto: uv, then pipx, then venv)
#   --python PATH               Python 3.11 or newer to use (default: newest python3.X on PATH)
#   --allow-dirty               build even with uncommitted changes or untracked files under kb4it/
#   --extras                    also install the optional extras (PyMdown Extensions, nh3)
#   --wheel FILE                install this wheel instead of building one
#
# venv method: the virtual environment is ${KB4IT_VENV:-~/.local/share/kb4it/venv}
# and ~/.local/bin/kb4it links to it. It only needs Python 3.11 or newer.
#
# Exit codes: 0 installed and verified, 1 failed, 2 installed but another kb4it
# comes first on PATH.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../../.."

METHOD="auto"
PYTHON_ARG=""
ALLOW_DIRTY=0
EXTRAS=0
WHEEL=""

die() { echo "ERROR: $*" >&2; exit 1; }

usage() { sed -n '8,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --method) [[ $# -ge 2 ]] || die "--method needs a value"; METHOD="$2"; shift 2 ;;
        --python) [[ $# -ge 2 ]] || die "--python needs a value"; PYTHON_ARG="$2"; shift 2 ;;
        --allow-dirty) ALLOW_DIRTY=1; shift ;;
        --extras) EXTRAS=1; shift ;;
        --wheel) [[ $# -ge 2 ]] || die "--wheel needs a value"; WHEEL="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) usage >&2; die "unknown option: $1" ;;
    esac
done
case "$METHOD" in auto|uv|pipx|venv) ;; *) die "--method must be auto, uv, pipx or venv, not '$METHOD'" ;; esac

echo "KB4IT installer"
echo "==============="
echo ""

# ── Python (3.11 or newer; never an older system python3) ─────────────────────
python_ok() {
    "$1" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null
}

find_python() {
    local candidate
    if [[ -n "$PYTHON_ARG" ]]; then
        python_ok "$PYTHON_ARG" && { command -v "$PYTHON_ARG"; return 0; }
        return 1
    fi
    for candidate in python3.14 python3.13 python3.12 python3.11 python3; do
        if command -v "$candidate" &>/dev/null && python_ok "$candidate"; then
            command -v "$candidate"
            return 0
        fi
    done
    return 1
}

python_hint() {
    if [[ -n "$PYTHON_ARG" ]]; then
        echo "$PYTHON_ARG is not Python 3.11 or newer."
    elif [[ -f /etc/redhat-release ]]; then
        echo "Install one with: sudo dnf install python3.11   (RHEL 8 and 9 keep their python3 next to it)"
    elif [[ -f /etc/debian_version ]]; then
        echo "Install one with: sudo apt install python3 python3-venv   (Debian 12, Ubuntu 24.04 or newer)"
    else
        echo "Install Python 3.11 or newer, or install uv, which brings its own Python."
    fi
}

PYTHON=""
if PYTHON="$(find_python)"; then
    echo "Python:    $PYTHON ($("$PYTHON" -c 'import platform; print(platform.python_version())'))"
fi

if [[ "$METHOD" == "auto" ]]; then
    if command -v uv &>/dev/null; then METHOD="uv"
    elif command -v pipx &>/dev/null; then METHOD="pipx"
    else METHOD="venv"
    fi
fi
case "$METHOD" in
    uv) command -v uv &>/dev/null || die "uv not found (https://docs.astral.sh/uv/)" ;;
    pipx) command -v pipx &>/dev/null || die "pipx not found" ;;
esac
if [[ "$METHOD" != "uv" && -z "$PYTHON" ]]; then
    die "the $METHOD method needs Python 3.11 or newer and none was found. $(python_hint)"
fi
echo "Method:    $METHOD"

# Any Python reads the wheel and the stamp: the chosen one, else uv's, else python3.
run_python() {
    if [[ -n "$PYTHON" ]]; then "$PYTHON" "$@"
    elif command -v uv &>/dev/null; then uv run --no-project --python ">=3.11" python "$@"
    else python3 "$@"
    fi
}

# ── Build the wheel ───────────────────────────────────────────────────────────
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [[ -z "$WHEEL" ]]; then
    echo ""
    echo "Checking the working tree"
    echo "-------------------------"
    if command -v git &>/dev/null && git rev-parse --is-inside-work-tree &>/dev/null; then
        changes="$(git status --porcelain --untracked-files=no)"
        untracked="$(git ls-files --others --exclude-standard -- kb4it)"
        if [[ -n "$changes" || -n "$untracked" ]]; then
            [[ -n "$changes" ]] && { echo "Uncommitted changes:"; echo "$changes" | sed 's/^/  /'; }
            [[ -n "$untracked" ]] && { echo "Untracked files that would be packaged:"; echo "$untracked" | sed 's/^/  /'; }
            if [[ "$ALLOW_DIRTY" == 0 ]]; then
                die "commit or stash them first, or pass --allow-dirty (the build is then marked .dirty)"
            fi
            echo "Building anyway (--allow-dirty)."
        else
            echo "Clean: commit $(git rev-parse --short HEAD)"
        fi
    else
        echo "Not a git checkout: kb4it --version will not name a commit."
    fi

    echo ""
    echo "Building the wheel"
    echo "------------------"
    export KB4IT_DIST_OUT="$WORK/dist"
    if ! command -v uv &>/dev/null; then
        # Without uv the build needs a Python with the build module and KB4IT's extras (offline help).
        echo "Preparing a build environment with $PYTHON"
        "$PYTHON" -m venv "$WORK/buildenv"
        "$WORK/buildenv/bin/python" -m pip install --quiet --upgrade pip
        "$WORK/buildenv/bin/python" -m pip install --quiet build -r requirements.txt pymdown-extensions nh3 pygments
        export KB4IT_PYTHON="$WORK/buildenv/bin/python"
    fi
    scripts/distribution/build/build_python.sh
    WHEEL="$(find "$KB4IT_DIST_OUT" -maxdepth 1 -name 'kb4it-*.whl' | head -n 1)"
    [[ -n "$WHEEL" ]] || die "no wheel was built in $KB4IT_DIST_OUT"
    if command -v git &>/dev/null && git rev-parse --is-inside-work-tree &>/dev/null; then
        run_python scripts/devel/check_wheel_themes.py "$WHEEL" || die "the wheel is incomplete"
    fi
fi
[[ -f "$WHEEL" ]] || die "wheel not found: $WHEEL"
WHEEL="$(cd "$(dirname "$WHEEL")" && pwd)/$(basename "$WHEEL")"

EXPECTED="$(run_python - "$WHEEL" <<'PY'
import json, sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as wheel:
    try:
        print(json.loads(wheel.read("kb4it/BUILD.json"))["build_version"])
    except KeyError:
        print("")
PY
)"
echo ""
echo "Wheel:     $WHEEL"
echo "Build:     ${EXPECTED:-no build stamp}"

# ── Install ───────────────────────────────────────────────────────────────────
echo ""
echo "Installing KB4IT ($METHOD)"
echo "------------------"
SPEC="$WHEEL"
[[ "$EXTRAS" == 1 ]] && SPEC="kb4it[extras] @ file://$WHEEL"

VENV="${KB4IT_VENV:-$HOME/.local/share/kb4it/venv}"
LINK_DIR="$HOME/.local/bin"

case "$METHOD" in
    uv)
        args=(tool install "$SPEC" --force --reinstall)
        [[ -n "$PYTHON_ARG" ]] && args+=(--python "$PYTHON")
        uv "${args[@]}"
        BIN="$(uv tool dir --bin 2>/dev/null || echo "$LINK_DIR")/kb4it"
        ;;
    pipx)
        pipx install --python "$PYTHON" --force "$SPEC"
        BIN="$(pipx environment --value PIPX_BIN_DIR 2>/dev/null || echo "$LINK_DIR")/kb4it"
        ;;
    venv)
        want="$("$PYTHON" -c 'import sys; print(sys.version_info[:2])')"
        if [[ -x "$VENV/bin/python" ]]; then
            have="$("$VENV/bin/python" -c 'import sys; print(sys.version_info[:2])' 2>/dev/null || true)"
            if [[ "$have" != "$want" ]]; then
                echo "Recreating $VENV: it runs Python ${have:-unknown}, not $want"
                rm -rf "$VENV"
            fi
        fi
        [[ -x "$VENV/bin/python" ]] || "$PYTHON" -m venv "$VENV"
        "$VENV/bin/python" -m pip install --quiet --upgrade pip
        "$VENV/bin/python" -m pip install --quiet --upgrade "$SPEC"
        "$VENV/bin/python" -m pip install --quiet --force-reinstall --no-deps "$WHEEL"
        mkdir -p "$LINK_DIR"
        if [[ -e "$LINK_DIR/kb4it" && ! -L "$LINK_DIR/kb4it" ]]; then
            die "$LINK_DIR/kb4it exists and is not a link; remove the other installation first (scripts/uninstall/local/uninstall.sh)"
        fi
        ln -sfn "$VENV/bin/kb4it" "$LINK_DIR/kb4it"
        echo "Linked $LINK_DIR/kb4it -> $VENV/bin/kb4it"
        BIN="$VENV/bin/kb4it"
        ;;
esac

# ── Verify ────────────────────────────────────────────────────────────────────
echo ""
echo "Verifying"
echo "---------"
[[ -x "$BIN" ]] || die "the installed command is not at $BIN"
REPORTED="$("$BIN" --version | head -n 1)"
echo "Installed: $REPORTED ($BIN)"
if [[ -n "$EXPECTED" && "$REPORTED" != "KB4IT $EXPECTED" ]]; then
    die "the installed KB4IT reports '$REPORTED', the wheel is 'KB4IT $EXPECTED'"
fi
"$BIN" doctor || die "kb4it doctor found problems in the installation"

# Without a working Python, keep the path as given, so two different paths never compare equal.
resolve() {
    local real
    real="$(run_python -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1" 2>/dev/null || true)"
    echo "${real:-$1}"
}
FIRST="$(command -v kb4it || true)"
echo ""
if [[ -z "$FIRST" ]]; then
    on_path_dir="$(dirname "$BIN")"
    [[ "$METHOD" == "venv" ]] && on_path_dir="$LINK_DIR"
    echo "kb4it is not on PATH yet. Add its folder, for example in ~/.bashrc:"
    echo "  export PATH=\"$on_path_dir:\$PATH\""
elif [[ "$(resolve "$FIRST")" != "$(resolve "$BIN")" ]]; then
    echo "WARNING: another kb4it comes first on PATH:"
    type -a kb4it | sed 's/^/  /'
    echo "Remove it (scripts/uninstall/local/uninstall.sh removes uv, pipx, pip and venv installs)"
    echo "or put the folder of $BIN first on PATH."
    exit 2
else
    echo "kb4it on PATH is the new installation: $FIRST"
fi
echo ""
echo "Done. Sites built with an older KB4IT compile every page once on their next build."

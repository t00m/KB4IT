#!/usr/bin/env bash
# Install KB4IT from this checkout into an isolated tool environment.
# Uses uv if available (fastest), then reuses the existing pipx venv if
# present (fast), and falls back to a full pipx install (slowest).
#
# Requirements: uv, or pipx with Python 3.11 or newer. uv needs no system
# Python: it downloads one when needed. No root/admin privileges needed.

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../../.."

# ── Locate installer (uv preferred, pipx fallback) ────────────────────────────
if command -v uv &>/dev/null; then
    INSTALLER="uv"
    echo "Installer: uv $(uv --version)"
elif command -v pipx &>/dev/null; then
    INSTALLER="pipx"
    echo "Installer: pipx $(pipx --version)"
else
    echo "ERROR: Neither uv nor pipx found. Install one:"
    echo "  uv:   curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  pipx: python3 -m pip install --user pipx"
    exit 1
fi

# ── Locate Python for pipx (3.11 or newer) ────────────────────────────────────
python_ok() {
    "$1" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null
}

find_python() {
    local candidate
    # Newest versioned interpreter in /usr/bin first, then python3 on PATH.
    for candidate in $(find /usr/bin -maxdepth 1 -name 'python3.[0-9]*' 2>/dev/null \
                       | grep -E '/python3\.[0-9]+$' | sort -V -r) python3; do
        if command -v "$candidate" &>/dev/null && python_ok "$candidate"; then
            command -v "$candidate"
            return 0
        fi
    done
    return 1
}

if [[ "$INSTALLER" == "pipx" ]]; then
    if ! PYTHON="$(find_python)"; then
        echo "ERROR: pipx needs Python 3.11 or newer; none found in /usr/bin or on PATH."
        exit 1
    fi
    echo "Python: $PYTHON"
fi

echo ""
echo "KB4IT installer"
echo "==============="
echo "Installing KB4IT from sources (no root/admin privileges needed)"
echo ""

# ── Clean leftover build artifacts ────────────────────────────────────────────
echo "Cleaning build artifacts"
echo "------------------------"
rm -rf build/ KB4IT.egg-info/
echo "Deleted build/ KB4IT.egg-info/"
echo ""

# ── Install ───────────────────────────────────────────────────────────────────
echo "Installing KB4IT"
echo "----------------"

PIPX_VENV="$HOME/.local/share/pipx/venvs/kb4it"

if [[ "$INSTALLER" == "uv" ]]; then
    # uv resolves and installs ~50× faster than pip
    uv tool install . --force

elif [[ -d "$PIPX_VENV" ]]; then
    # Venv already exists: reinstall only the kb4it package, keeping all
    # cached dependencies - avoids full venv recreation (~5-10× faster).
    echo "(Reusing existing venv - reinstalling package only)"
    "$PIPX_VENV/bin/python" -m pip install . --quiet

else
    # First-time install: full pipx install
    pipx install --python "$PYTHON" . --force
fi

echo ""
echo "Installation finished"
echo "---------------------"
echo ""

# ── Verify ────────────────────────────────────────────────────────────────────
echo "Installed version"
echo "-----------------"
if command -v kb4it &>/dev/null; then
    kb4it --version
else
    "$HOME/.local/bin/kb4it" --version
fi

#!/usr/bin/env bash
# Install KB4IT from source into an isolated tool environment.
# Uses uv if available (fastest), then reuses the existing pipx venv if
# present (fast), and falls back to a full pipx install (slowest).
#
# Dependencies: asciidoctor coderay ruby-coderay python3-setuptools

set -euo pipefail

# ── Locate Python ─────────────────────────────────────────────────────────────
latest_python=$(ls /usr/bin/python3.* 2>/dev/null | sort -V | tail -n 1)
if [[ -z "$latest_python" ]]; then
    echo "ERROR: No Python 3 installation found in /usr/bin."
    exit 1
fi
echo "Python: $latest_python"

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
    echo "  pipx: pip install --user pipx"
    exit 1
fi

echo ""
echo "KB4IT installer"
echo "==============="
echo "Installing KB4IT from sources (no root/admin privileges needed)"
echo ""

# ── Clean leftover build artifacts ────────────────────────────────────────────
echo "Cleaning build artifacts"
echo "------------------------"
rm -rf build/ dist/ KB4IT.egg-info/
echo "Deleted build/ dist/ KB4IT.egg-info/"
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
    pipx install . --force
fi

echo ""
echo "Installation finished"
echo "---------------------"
echo ""

# ── Verify ────────────────────────────────────────────────────────────────────
echo "Installed version"
echo "-----------------"
"$HOME/.local/bin/kb4it" --version

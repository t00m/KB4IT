#!/usr/bin/env bash
# Uninstall KB4IT from user space: removes it from uv, pipx and pip --user,
# whichever has it. No root/admin privileges needed.
#
# Usage: uninstall.sh [--purge]
#   --purge   also delete the per-user folder (~/.kb4it, or $KB4IT_HOME) after asking:
#             the list of projects, user themes and logs. Your knowledge bases are
#             never touched.
#
# The .deb and .rpm packages are removed with the system package manager instead:
#   sudo apt remove kb4it      or      sudo dnf remove kb4it
set -euo pipefail

PURGE=0
case "${1:-}" in
    "") ;;
    --purge) PURGE=1 ;;
    *) echo "Usage: $(basename "$0") [--purge]" >&2; exit 1 ;;
esac

echo "KB4IT uninstaller"
echo "================="
echo ""

FOUND=0

if command -v uv &>/dev/null && uv tool list 2>/dev/null | grep -qi '^kb4it '; then
    echo "Removing KB4IT installed with uv"
    uv tool uninstall kb4it
    FOUND=1
fi

if command -v pipx &>/dev/null && pipx list --short 2>/dev/null | grep -qi '^kb4it '; then
    echo "Removing KB4IT installed with pipx"
    pipx uninstall kb4it
    FOUND=1
fi

if command -v python3 &>/dev/null && python3 -m pip show kb4it &>/dev/null; then
    echo "Removing KB4IT installed with pip"
    if ! python3 -m pip uninstall -y kb4it; then
        echo ""
        echo "pip could not remove it. If your system Python is managed by the"
        echo "distribution (PEP 668), remove it with the command you used to install it,"
        echo "for example: python3 -m pip uninstall --user --break-system-packages kb4it"
        exit 1
    fi
    FOUND=1
fi

if [[ "$FOUND" == 0 ]]; then
    echo "KB4IT is not installed with uv, pipx or pip."
fi

if [[ "$PURGE" == 1 ]]; then
    DATA="${KB4IT_HOME:-$HOME/.kb4it}"
    if [[ -d "$DATA" ]]; then
        echo ""
        read -r -p "Delete $DATA (projects list, user themes, logs)? [y/N] " answer
        if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
            rm -rf "$DATA"
            echo "Deleted $DATA"
        else
            echo "Kept $DATA"
        fi
    fi
fi

echo ""
echo "Uninstallation finished"

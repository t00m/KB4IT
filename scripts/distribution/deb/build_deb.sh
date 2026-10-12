#!/usr/bin/env bash
# Build a Debian package (.deb) for KB4IT.
#
# Usage: build_deb.sh [ARCH]      ARCH: amd64 (default on x86_64) | arm64
#
# The package carries the KB4IT wheel and the wheels of its dependencies for
# Python 3.11 to 3.14 (lib/common.sh). postinst installs them into
# /opt/kb4it/venv without network access and links /usr/bin/kb4it. This keeps
# KB4IT isolated from the system Python site-packages (same spirit as pipx).
#
# Runtime dependencies (declared in the .deb control file):
#   python3 (>= 3.11), python3-venv
#
# Output: dist/kb4it_<version>_<arch>.deb
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
source "${SCRIPT_DIR}/../lib/common.sh"
cd "${REPO_ROOT}"

if ! ARCH="$(arch_debian "${1:-$(uname -m)}")"; then
    echo "Usage: $(basename "$0") [amd64|arm64]" >&2
    exit 1
fi
# Debian versions cannot contain '+', replace with '~' which sorts correctly.
DEB_VERSION="$(tr '+' '~' <<<"${KB4IT_VERSION}")"
PKG_NAME="kb4it"
BUILD_DIR="${OUT_DIR}/deb_build"
STAGE_DIR="${BUILD_DIR}/${PKG_NAME}_${DEB_VERSION}_${ARCH}"
DEB_OUT="${OUT_DIR}/${PKG_NAME}_${DEB_VERSION}_${ARCH}.deb"

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "dpkg-deb not found. Install dpkg (Debian/Ubuntu) or equivalent."
    exit 1
fi

echo ">>> Cleaning build dir"
rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}/DEBIAN" \
         "${STAGE_DIR}/opt/${PKG_NAME}/wheels" \
         "${STAGE_DIR}/usr/share/doc/${PKG_NAME}"

echo ">>> Staging the KB4IT wheel and the dependency wheels for ${ARCH}"
ensure_wheel
cp "$(wheel_path)" "${STAGE_DIR}/opt/${PKG_NAME}/wheels/"
cp "$(ensure_dep_wheels "${ARCH}")"/*.whl "${STAGE_DIR}/opt/${PKG_NAME}/wheels/"

echo ">>> Writing control file"
{
    cat <<EOF
Package: ${PKG_NAME}
Version: ${DEB_VERSION}
Section: doc
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.11), python3-venv
Maintainer: Tomás Vírseda <tomasvirseda@gmail.com>
Homepage: https://github.com/t00m/KB4IT
Description: ${KB4IT_SUMMARY}
EOF
    # Extended description: continuation lines start with one space.
    fold -s -w 72 <<<"${KB4IT_DESCRIPTION}" | sed -e 's/ *$//' -e 's/^/ /'
} > "${STAGE_DIR}/DEBIAN/control"

echo ">>> Writing postinst (creates the venv offline, links /usr/bin/kb4it)"
cat > "${STAGE_DIR}/DEBIAN/postinst" <<EOF
#!/bin/sh
set -e
[ "\$1" = "configure" ] || exit 0
VENV_DIR=/opt/${PKG_NAME}/venv
WHEELS=/opt/${PKG_NAME}/wheels
SUPPORTED="${KB4IT_PYTHONS[*]}"
PY_VERSION=\$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
case " \$SUPPORTED " in
    *" \$PY_VERSION "*) ;;
    *) echo "kb4it: this package has wheels for Python \$SUPPORTED; python3 is \$PY_VERSION" >&2; exit 1 ;;
esac
rm -rf "\$VENV_DIR"
python3 -m venv "\$VENV_DIR"
"\$VENV_DIR/bin/python" -m pip install --quiet --disable-pip-version-check --no-cache-dir \\
    --no-index --find-links "\$WHEELS" "${PKG_NAME}==${KB4IT_VERSION}"
ln -sf "\$VENV_DIR/bin/kb4it" /usr/bin/kb4it
EOF
chmod 0755 "${STAGE_DIR}/DEBIAN/postinst"

echo ">>> Writing prerm (removes the symlink and the venv)"
# Before dpkg removes the package files, so /opt/kb4it is empty and goes too.
cat > "${STAGE_DIR}/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
rm -f /usr/bin/kb4it
if [ "$1" = "remove" ]; then
    rm -rf /opt/kb4it/venv
fi
EOF
chmod 0755 "${STAGE_DIR}/DEBIAN/prerm"

echo ">>> Copying docs"
cp LICENSE "${STAGE_DIR}/usr/share/doc/${PKG_NAME}/copyright"
cp README.md CHANGELOG.md AUTHORS THANKS "${STAGE_DIR}/usr/share/doc/${PKG_NAME}/"
gzip -n -9 "${STAGE_DIR}/usr/share/doc/${PKG_NAME}/CHANGELOG.md"

echo ">>> Building .deb"
dpkg-deb --root-owner-group --build "${STAGE_DIR}" "${DEB_OUT}"

echo ""
echo "Built: ${DEB_OUT} ($(du -h "${DEB_OUT}" | cut -f1))"
echo ""
echo "Install with:"
echo "  sudo apt install ${DEB_OUT}"

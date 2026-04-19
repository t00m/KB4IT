#!/usr/bin/env bash
# Build a Debian package (.deb) for KB4IT.
#
# Strategy: build a wheel first, then repackage it as a .deb that installs
# into /opt/kb4it/venv with a wrapper symlink in /usr/bin/kb4it. This keeps
# KB4IT isolated from the system Python site-packages (same spirit as pipx).
#
# Runtime dependencies (declared in the .deb control file):
#   python3 (>= 3.11), python3-venv, asciidoctor
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "${REPO_ROOT}"

VERSION="$(cat kb4it/VERSION)"
# Debian versions cannot contain '+', replace with '~' which sorts correctly.
DEB_VERSION="${VERSION//+/~}"
ARCH="all"
PKG_NAME="kb4it"
BUILD_DIR="${REPO_ROOT}/dist/deb_build"
STAGE_DIR="${BUILD_DIR}/${PKG_NAME}_${DEB_VERSION}_${ARCH}"
DEB_OUT="${REPO_ROOT}/dist/${PKG_NAME}_${DEB_VERSION}_${ARCH}.deb"

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "dpkg-deb not found. Install dpkg (Debian/Ubuntu) or equivalent."
    exit 1
fi

echo ">>> Cleaning build dir"
rm -rf "${BUILD_DIR}"
mkdir -p "${STAGE_DIR}/DEBIAN" \
         "${STAGE_DIR}/opt/${PKG_NAME}" \
         "${STAGE_DIR}/usr/bin" \
         "${STAGE_DIR}/usr/share/doc/${PKG_NAME}"

echo ">>> Ensuring a wheel exists"
if ! ls dist/*.whl >/dev/null 2>&1; then
    "${SCRIPT_DIR}/../build/build_python.sh"
fi
WHEEL="$(ls -1t dist/*.whl | head -n 1)"
echo "    using wheel: ${WHEEL}"

echo ">>> Staging wheel for postinst install"
mkdir -p "${STAGE_DIR}/opt/${PKG_NAME}/wheel"
cp "${WHEEL}" "${STAGE_DIR}/opt/${PKG_NAME}/wheel/"

echo ">>> Writing control file"
cat > "${STAGE_DIR}/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${DEB_VERSION}
Section: doc
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.11), python3-venv, asciidoctor
Maintainer: Tomás Vírseda <tomasvirseda@gmail.com>
Homepage: https://github.com/t00m/KB4IT
Description: Static website generator for technical documentation
 KB4IT converts AsciiDoc sources into a static website using Mako
 templates. Supports multiple themes (techdoc, book, blog) and
 incremental compilation via file hashing.
EOF

echo ">>> Writing postinst (creates venv, installs wheel, creates symlink)"
cat > "${STAGE_DIR}/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
VENV_DIR=/opt/kb4it/venv
WHEEL=$(ls /opt/kb4it/wheel/*.whl | head -n 1)
python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/pip" install --quiet --upgrade pip
"${VENV_DIR}/bin/pip" install --quiet "${WHEEL}"
ln -sf "${VENV_DIR}/bin/kb4it" /usr/bin/kb4it
EOF
chmod 0755 "${STAGE_DIR}/DEBIAN/postinst"

echo ">>> Writing prerm (removes symlink) and postrm (removes venv)"
cat > "${STAGE_DIR}/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
rm -f /usr/bin/kb4it
EOF
chmod 0755 "${STAGE_DIR}/DEBIAN/prerm"

cat > "${STAGE_DIR}/DEBIAN/postrm" <<'EOF'
#!/bin/sh
set -e
if [ "$1" = "purge" ] || [ "$1" = "remove" ]; then
    rm -rf /opt/kb4it/venv
fi
EOF
chmod 0755 "${STAGE_DIR}/DEBIAN/postrm"

echo ">>> Copying docs"
cp LICENSE "${STAGE_DIR}/usr/share/doc/${PKG_NAME}/copyright"
cp README.rst Changelog AUTHORS THANKS "${STAGE_DIR}/usr/share/doc/${PKG_NAME}/" 2>/dev/null || true
gzip -n -9 "${STAGE_DIR}/usr/share/doc/${PKG_NAME}/Changelog" 2>/dev/null || true

echo ">>> Building .deb"
dpkg-deb --root-owner-group --build "${STAGE_DIR}" "${DEB_OUT}"

echo ""
echo "Built: ${DEB_OUT}"
echo ""
echo "Install with:"
echo "  sudo dpkg -i ${DEB_OUT} || sudo apt-get install -f -y"

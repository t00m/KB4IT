#!/usr/bin/env bash
# Install KB4IT locally
rm -rf builddir
meson builddir --prefix=~/.local
meson setup builddir --prefix=~/.local --reconfigure
ninja -C builddir install

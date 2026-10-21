#!/usr/bin/env bash
# Download the pinned Mermaid and KaTeX builds into kb4it/resources/render.
# Usage: [MERMAID_VERSION=x.y.z] [KATEX_VERSION=x.y.z] scripts/devel/fetch_render_assets.sh
# Versions not given are read from the VERSIONS file next to the assets.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="$ROOT/kb4it/resources/render"
MERMAID_VERSION="${MERMAID_VERSION:-$(awk '$1 == "mermaid" {print $2}' "$DEST/VERSIONS")}"
KATEX_VERSION="${KATEX_VERSION:-$(awk '$1 == "katex" {print $2}' "$DEST/VERSIONS")}"
CDN="https://cdn.jsdelivr.net/npm"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$DEST/mermaid" "$DEST/katex/fonts"

curl -fsSL "$CDN/mermaid@$MERMAID_VERSION/dist/mermaid.min.js" -o "$DEST/mermaid/mermaid.min.js"
curl -fsSL "$CDN/mermaid@$MERMAID_VERSION/LICENSE" -o "$DEST/mermaid/LICENSE"

curl -fsSL "$CDN/katex@$KATEX_VERSION/dist/katex.min.js" -o "$DEST/katex/katex.min.js"
curl -fsSL "$CDN/katex@$KATEX_VERSION/dist/katex.min.css" -o "$DEST/katex/katex.min.css"
curl -fsSL "$CDN/katex@$KATEX_VERSION/LICENSE" -o "$DEST/katex/LICENSE"

# Every font the stylesheet references, so no url() points to a missing file.
grep -o 'fonts/[A-Za-z0-9_-]*\.[a-z0-9]*' "$DEST/katex/katex.min.css" | sort -u > "$WORK/fonts.txt"
while read -r font; do
    curl -fsSL "$CDN/katex@$KATEX_VERSION/dist/$font" -o "$DEST/katex/$font"
done < "$WORK/fonts.txt"

printf 'mermaid %s\nkatex %s\n' "$MERMAID_VERSION" "$KATEX_VERSION" > "$DEST/VERSIONS"

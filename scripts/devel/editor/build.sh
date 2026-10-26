#!/usr/bin/env bash
# Build the CodeMirror 6 bundle of the techdoc Add page into kb4it/resources/editor.
# Usage: scripts/devel/editor/build.sh
# Needs node and npm. Users and CI never run it; the generated files are committed.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$(cd "$HERE/../../.." && pwd)/kb4it/resources/editor"
MAX_BYTES=$((700 * 1024))

mkdir -p "$DEST"
cd "$HERE"
npm ci

npx esbuild entry.js --bundle --minify --format=iife --global-name=KB4ITEditor \
    --legal-comments=eof --metafile=meta.json --outfile="$DEST/codemirror.min.js"

# Notices and versions come from the packages esbuild put in the bundle.
node -e '
const fs = require("fs");
const path = require("path");
const dest = process.argv[1];
const meta = JSON.parse(fs.readFileSync("meta.json", "utf8"));
const root = path.resolve("node_modules");
const dirs = new Set();
for (const input of Object.keys(meta.inputs)) {
    const abs = path.resolve(input);
    if (!abs.startsWith(root + path.sep)) continue;
    const parts = path.relative(root, abs).split(path.sep);
    dirs.add(parts[0].startsWith("@") ? parts.slice(0, 2).join("/") : parts[0]);
}
const rows = [...dirs].sort().map((name) => {
    const dir = path.join(root, name);
    const version = JSON.parse(fs.readFileSync(path.join(dir, "package.json"), "utf8")).version;
    const file = fs.readdirSync(dir).find((f) => /^licen[sc]e(\.md|\.txt)?$/i.test(f));
    const text = file ? fs.readFileSync(path.join(dir, file), "utf8").trim() : "(no licence file in the package)";
    return { name, version, text };
});
const esbuild = JSON.parse(fs.readFileSync(path.join(root, "esbuild", "package.json"), "utf8")).version;
const notices = rows.map((r) => `${r.name} ${r.version}\n${"-".repeat(40)}\n${r.text}\n`).join("\n");
fs.writeFileSync(path.join(dest, "THIRD-PARTY-NOTICES.txt"),
    "Licences of the packages bundled in codemirror.min.js.\n\n" + notices);
const versions = rows.map((r) => `${r.name} ${r.version}`);
versions.push(`esbuild ${esbuild}`);
fs.writeFileSync(path.join(dest, "VERSIONS"), versions.join("\n") + "\n");
' "$DEST"

cp node_modules/@codemirror/view/LICENSE "$DEST/LICENSE"
rm -f meta.json

SIZE=$(wc -c < "$DEST/codemirror.min.js")
echo "codemirror.min.js: $SIZE bytes (limit $MAX_BYTES)"
if [ "$SIZE" -gt "$MAX_BYTES" ]; then
    echo "Bundle is over the size limit" >&2
    exit 1
fi

"""ED-01 and ED-03: the vendored CodeMirror bundle, its notices and the credits."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDITOR = ROOT / "kb4it" / "resources" / "editor"
EDITOR_FILES = ["codemirror.min.js", "kb4it-frontmatter.js", "LICENSE", "THIRD-PARTY-NOTICES.txt", "VERSIONS"]


def _versions():
    lines = (EDITOR / "VERSIONS").read_text(encoding="utf-8").splitlines()
    return [line.split()[0] for line in lines if line.strip()]


def test_editor_files_in_package():
    for name in EDITOR_FILES:
        assert (EDITOR / name).is_file(), name


def test_versions_name_codemirror_and_esbuild():
    packages = _versions()
    assert "@codemirror/view" in packages
    assert "esbuild" in packages


def test_notices_cover_every_bundled_package():
    notices = (EDITOR / "THIRD-PARTY-NOTICES.txt").read_text(encoding="utf-8")
    for package in _versions():
        if package != "esbuild":
            assert package in notices, package


def test_editor_assets_are_offline():
    files = list(EDITOR.glob("*.js")) + list(EDITOR.glob("*.css"))
    assert files
    for path in files:
        text = path.read_text(encoding="utf-8")
        urls = [u for u in re.findall(r"https?://[^\s\"'<>)]+", text) if not u.startswith("http://www.w3.org/")]
        assert urls == [], (path.name, urls)


def test_bundle_under_budget():
    assert (EDITOR / "codemirror.min.js").stat().st_size < 700 * 1024


def test_thanks_credits_codemirror():
    thanks = (ROOT / "THANKS").read_text(encoding="utf-8")
    assert "* CodeMirror (https://codemirror.net, MIT): source editor of the techdoc Add page" in thanks


def test_techdoc_requires_0_10():
    theme = json.loads((ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "theme.json").read_text(encoding="utf-8"))
    assert theme["kb4it"] == ">=0.10.0"

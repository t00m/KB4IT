"""Every version KB4IT reports comes from kb4it/VERSION; no code, config or doc names an old one (VER-01)."""

import re

import pytest

from kb4it.core.env import ENV
from tests.helpers import ROOT, run_kb4it, write_repo

VERSION = (ROOT / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()

SCANNED = ("kb4it", "scripts", "help", ".github", "tests", "action.yml", "pyproject.toml")
TEXT_SUFFIXES = {".py", ".sh", ".cmd", ".ps1", ".tpl", ".json", ".yml", ".yaml", ".md", ".toml", ".cfg", ".csv", ".txt"}
SKIPPED_PARTS = {"framework", "images", "__pycache__", "var", "node_modules"}  # var: generated build state

# A hand-written 0.x version: KB4IT next to it, a version key, or a release named after "in", "since", "until" or "from".
PATTERNS = [
    re.compile(r"kb4it[\s:=<>!~v-]*v?0\.\d+", re.IGNORECASE),
    re.compile(r"\bversion\"?\s*[:=;]\s*\"?v?0\.\d+", re.IGNORECASE),
    re.compile(r"\b(?:in|since|until|from)\s+v?0\.\d+", re.IGNORECASE),
    re.compile(r"(?<![\w.<>=!~])v?0\.\d+\.\d+(?![\w.])"),  # not after an operator: that is a floor
]

# Compatibility floors ("kb4it": ">=0.9.0") name the oldest KB4IT a theme works with. They are facts, not the version.
FLOOR = re.compile(r'"kb4it"\s*:\s*"[<>=!~]')

# Files that keep a version on purpose. Each reason says why.
ALLOWED = {
    "pyproject.toml": "release.sh writes it from kb4it/VERSION; test_pyproject_matches_version checks it",
    "scripts/devel/editor/package.json": "pinned versions of the npm packages of the editor bundle",
    "scripts/devel/editor/package-lock.json": "pinned versions of the npm packages of the editor bundle",
    "kb4it/resources/editor/THIRD-PARTY-NOTICES.txt": "generated list of bundled third-party packages and versions",
    "tests/apphelp/test_versions.py": "fixtures for the apphelp version folders, not KB4IT's version",
    "tests/apphelp/test_config.py": "an apphelp repo.json fixture with its own version",
    "tests/core/test_version.py": "parser cases for version strings",
    "tests/core/test_changelog_tool.py": "fixture releases for the changelog tool",
    "tests/core/test_owned_pages.py": "a file as written by an older KB4IT, read for compatibility",
    "tests/fixtures/themes/mini/theme.json": "a fixture theme with its own version",
    "tests/packaging/test_install_scripts.py": "fake output of pipx",
    "tests/packaging/test_scripts.py": "fake wheel name",
}

# Sample documentation of a made-up app: its versions belong to that app.
SAMPLE_APP = ("kb4it/resources/themes/apphelp/apps/default/source/", "kb4it/resources/themes/apphelp/apps/default/config/")


def _text_files():
    for name in SCANNED:
        path = ROOT / name
        files = [path] if path.is_file() else path.rglob("*")
        for file in files:
            parts = set(file.relative_to(ROOT).parts)
            if file.is_file() and file.suffix in TEXT_SUFFIXES and not parts & SKIPPED_PARTS:
                yield file


def test_no_old_kb4it_version_in_code_or_docs():
    hits = []
    for file in _text_files():
        rel = file.relative_to(ROOT).as_posix()
        if rel in ALLOWED or rel.startswith(SAMPLE_APP):
            continue
        for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), start=1):
            if FLOOR.search(line):
                continue
            if any(pattern.search(line) for pattern in PATTERNS):
                hits.append(f"{rel}:{number}: {line.strip()[:90]}")
    assert hits == []


def test_pyproject_matches_version():
    assert f'version = "{VERSION}"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")


def test_running_kb4it_reports_the_version_file():
    assert ENV["APP"]["version"] == VERSION


@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf", "apphelp"])
def test_every_theme_loads_with_the_kb4it_version(tmp_path, home, theme):
    cfg = write_repo(tmp_path / "repo", theme, {})
    result = run_kb4it("-L", "DEBUG", "build", cfg, cwd=tmp_path, home=home)
    loaded = [line for line in result.stdout.splitlines() if "THEME_CONF" in line]
    assert loaded, result.stdout
    assert all(f"version={VERSION}" in line for line in loaded), loaded

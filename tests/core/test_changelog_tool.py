import importlib.util

import pytest

from tests.helpers import ROOT

spec = importlib.util.spec_from_file_location("changelog_tool", ROOT / "scripts" / "devel" / "changelog.py")
changelog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changelog)

TEXT = """# Changelog

---

## [Unreleased]

### Fixed

- Pages without a date are kept. They come last.
- `verify` exits 1: it can gate CI.

### Added

- A switch.

---

## [0.7.9] - 2026-10-01

### Added

- Old entry.
"""


def test_has_unreleased():
    assert changelog.has_unreleased(TEXT)
    assert not changelog.has_unreleased(TEXT.replace("- Pages", "Pages").replace("- `verify`", "x").replace("- A switch.", ""))


def test_release_dates_the_section_and_opens_a_new_one():
    out = changelog.release(TEXT, "0.7.10", "2026-10-03")
    assert "## [Unreleased]\n\n---\n\n## [0.7.10] - 2026-10-03\n\n### Fixed" in out
    assert changelog.body(out, "Unreleased") == ""
    assert "Pages without a date are kept" in changelog.body(out, "0.7.10")


def test_release_twice_changes_nothing():
    once = changelog.release(TEXT, "0.7.10", "2026-10-03")
    assert changelog.release(once, "0.7.10", "2026-10-04") == once


def test_release_refuses_an_empty_unreleased():
    empty = changelog.release(TEXT, "0.7.10", "2026-10-03")
    with pytest.raises(SystemExit):
        changelog.release(empty, "0.7.11", "2026-10-04")


def test_notes_draft():
    out = changelog.notes(changelog.release(TEXT, "0.7.10", "2026-10-03"), "0.7.10")
    assert out.startswith("# KB4IT 0.7.10\n\nTODO:")
    assert "- Pages without a date are kept\n- `verify` exits 1\n- A switch\n" in out
    assert "Old entry" not in out

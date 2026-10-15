"""scripts/devel/theme_snapshot.py --content: stable, normalised page copies for before/after diffs."""

import importlib.util

from tests.helpers import ROOT

spec = importlib.util.spec_from_file_location("theme_snapshot", ROOT / "scripts" / "devel" / "theme_snapshot.py")
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


def test_normalise_hides_build_dates_times_and_version():
    version = (ROOT / "kb4it" / "VERSION").read_text(encoding="utf-8").strip()
    text = f"Built 2026-10-15 09:41:07 by KB4IT {version} on Oct 15, 2026 at 10:00:01"
    out = snapshot.normalise(text)
    assert version not in out and "09:41" not in out and "10:00:01" not in out
    assert "<VERSION>" in out and "<DATETIME>" in out


def test_normalise_keeps_document_dates():
    assert snapshot.normalise("Date: 2026-10-14") == "Date: 2026-10-14"


def test_fixtures_exist():
    names = {p.name for p in snapshot.FIXTURES.glob("*.md")}
    assert {"rich.md", "hostile.md"} <= names

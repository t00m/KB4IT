"""techdoc: a document date links to its events day page only when that page is built."""

from tests.core.test_highlight import _app_conf
from tests.helpers import page, run_kb4it, write_repo

EVENT_DAY = "20260110"
OTHER_DAY = "20250305"
DOCS = {
    "change.md": page("A change", "Text.", Category="Record", WorkType="Change", Date="2026-01-10 10:00", Tag="x"),
    "note.md": page("A template", "Text.", Category="Template", WorkType="Knowledge", Date="2025-03-05", Tag="x"),
}


def _build(tmp_path, home, docs=DOCS):
    cfg = write_repo(tmp_path / "repo", "techdoc", docs, **_app_conf("techdoc"))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return cfg, tmp_path / "repo" / "target", result.stdout


def test_non_event_date_is_not_a_link(tmp_path, home):
    _cfg, target, log = _build(tmp_path, home)
    assert not (target / f"events_{OTHER_DAY}.html").exists()
    for path in target.glob("*.html"):
        assert f'href="events_{OTHER_DAY}.html"' not in path.read_text(encoding="utf-8"), path.name
    assert not [line for line in log.splitlines() if "ANCHOR_MISSING" in line and "to=events_" in line]


def test_event_date_still_links_its_day_page(tmp_path, home):
    _cfg, target, _log = _build(tmp_path, home)
    assert (target / f"events_{EVENT_DAY}.html").is_file()
    assert f'href="events_{EVENT_DAY}.html"' in (target / "change.html").read_text(encoding="utf-8")
    assert f'href="events_{EVENT_DAY}.html"' in (target / "all.html").read_text(encoding="utf-8")


def _links_to(target, day):
    return sorted(p.name for p in target.glob("*.html") if f'href="events_{day}.html"' in p.read_text(encoding="utf-8"))


def test_cached_pages_follow_a_document_that_stops_and_starts_being_an_event(tmp_path, home):
    cfg, target, _log = _build(tmp_path, home)
    assert {"all.html", "change.html", "Tag_x.html"} <= set(_links_to(target, EVENT_DAY))
    source = tmp_path / "repo" / "source" / "change.md"
    as_template = page("A change", "Text.", Category="Template", WorkType="Knowledge", Date="2026-01-10 10:00", Tag="x")
    source.write_text(as_template, encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert _links_to(target, EVENT_DAY) == [], "no cached page keeps a link to the removed day page"
    assert not [line for line in result.stdout.splitlines() if "ANCHOR_MISSING" in line and "to=events_" in line]
    source.write_text(DOCS["change.md"], encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert {"all.html", "change.html", "Tag_x.html"} <= set(_links_to(target, EVENT_DAY))
    assert (target / f"events_{EVENT_DAY}.html").is_file()

"""techdoc theme: events, landing page panels, metadata pages and the admin backups."""

# ruff: noqa: DTZ005  # KB4IT works with naive local datetimes

import json
import re
import shutil
import zipfile
from datetime import datetime, timedelta

import pytest

from tests.helpers import page, run_kb4it

TODAY = datetime.now()


def day(offset):
    return (TODAY + timedelta(days=offset)).strftime("%Y-%m-%d")


PAGES = {
    "change.md": page("Upcoming change", Date=day(3), Category="Change", Priority="High", Status="Open",
                      Scope="Infrastructure"),
    "incident.md": page("Recent incident", Date=day(-5), Category="Incident", Priority="Critical",
                        Status="Open"),
    "meeting.md": page("Old meeting", Date="2025-01-15", Category="Meeting", Team="Linux"),
    "monitor.md": page("Check backups", "## Steps\n\nRun it.\n\n### Detail\n\nMore.", Date=day(-40),
                       Category="Procedure", Topic="Monitoring", Periodicity="Daily", DocType="How-to guide"),
    "undated.md": page("Undated note", Category="Note", Tag="misc"),
}


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc")
    home = base / "home"
    home.mkdir()
    result = run_kb4it("create", "techdoc", "repo", cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    repo = base / "repo"
    cfg = repo / "config" / "repo.json"
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["admin"] = True
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    for name, text in PAGES.items():
        (repo / "source" / name).write_text(text, encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return {"base": base, "home": home, "repo": repo, "cfg": cfg, "target": repo / "target", "log": result.stdout}


def read(site, name):
    return (site["target"] / name).read_text(encoding="utf-8")


def test_build_is_clean(site):
    assert "ERROR |" not in site["log"]
    assert "WARNING |" not in site["log"].replace("THEME_REQUIREMENT_MISSING", "")


def test_every_document_has_a_page(site):
    for name in PAGES:
        assert (site["target"] / name.replace(".md", ".html")).exists()


def test_events_page_lists_dated_events(site):
    html = read(site, "events.html")
    assert str(TODAY.year) in html and "2025" in html
    assert "change.html" in html and "meeting.html" in html
    assert "undated.html" not in html


def test_landing_page_panels(site):
    html = read(site, "index.html")
    assert "change.html" in html      # upcoming events and open items
    assert "incident.html" in html    # recent events and open items
    assert "Periodicity_Daily.html" in html
    assert "Check backups" in html


def test_landing_page_order(site):
    html = read(site, "index.html")
    marks = ["kb-hero-bar", "kb-diataxis-card", "Open items"]
    assert [html.index(m) for m in marks] == sorted(html.index(m) for m in marks)


def test_landing_page_sections_fold_except_counts_and_doctypes(site):
    html = read(site, "index.html")
    folding = re.findall(r'<details class="kb-section kb-collapsible" data-kb-section="([\w-]+)" open>', html)
    assert folding == ["open-items", "changes-incidents", "upcoming-events", "monitoring", "recent-events"]
    assert html.count("<details") == html.count("</details>")
    head = html[:html.index("<details")]
    assert "kb-hero-bar" in head and "kb-diataxis-card" in head


def test_metadata_pages(site):
    assert "monitor.html" in read(site, "Periodicity_Daily.html")
    assert "change.html" in read(site, "Priority_High.html")
    for name in ("Category.html", "Status.html", "stats.html", "properties.html", "all.html", "bookmarks.html"):
        assert (site["target"] / name).exists(), name


def test_document_page_has_toc_and_properties(site):
    html = read(site, "monitor.html")
    assert "Steps" in html and "Detail" in html
    assert "Periodicity_Daily.html" in html


def test_admin_backups(site):
    admin = site["target"] / "admin"
    assert (admin / "index.html").exists()
    with zipfile.ZipFile(admin / "kb4it_sources.zip") as zf:
        names = {n.rsplit("/", 1)[-1] for n in zf.namelist()}
    assert set(PAGES) <= names
    with zipfile.ZipFile(admin / "kb4it_site.zip") as zf:
        names = zf.namelist()
    assert "index.html" in names
    assert not any(n.startswith("admin/") for n in names)
    assert "../" in (admin / "index.html").read_text(encoding="utf-8")


def test_admin_backups_follow_changes(site, tmp_path):
    # Own copy: the title change would rename the zips the other tests read.
    repo = tmp_path / "repo"
    shutil.copytree(site["repo"], repo)
    cfg = repo / "config" / "repo.json"
    admin = repo / "target" / "admin"
    before = (admin / "kb4it_site.zip").stat().st_mtime_ns
    result = run_kb4it("build", cfg, cwd=tmp_path, home=site["home"])
    assert result.returncode == 0, result.stdout
    assert (admin / "kb4it_site.zip").stat().st_mtime_ns == before
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["title"] = "Ops Notes"
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=site["home"])
    assert result.returncode == 0, result.stdout
    assert sorted(p.name for p in admin.glob("*.zip")) == ["ops-notes_site.zip", "ops-notes_sources.zip"]

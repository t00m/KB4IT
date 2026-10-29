"""techdoc theme: events, landing page panels, metadata pages and the admin backups."""

# ruff: noqa: DTZ005  # KB4IT works with naive local datetimes

import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timedelta

import pytest

from tests.helpers import ROOT, page, run_kb4it
from tests.themes.test_techdoc_add import build_techdoc

TODAY = datetime.now()


def day(offset):
    return (TODAY + timedelta(days=offset)).strftime("%Y-%m-%d")


PAGES = {
    "change.md": page("Upcoming change", Date=day(3), Category="Change", Priority="High", Status="Open",
                      Scope="Infrastructure"),
    "change2.md": page("Migrated change", Date=day(2), Category="Record", WorkType="Change", Status="Open",
                       Priority="Low"),
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
    for sample in (repo / "source").glob("*.md"):
        sample.unlink()  # the site holds only PAGES; the samples are tested in test_create_samples.py
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


def test_alert_bar_and_open_items_read_worktype_with_legacy_fallback(site):
    html = read(site, "index.html")
    bar = html[html.index("CHANGES PANEL :: START"):html.index("CHANGES PANEL :: END")]
    assert bar.count('href="change2.html"') == 1 and bar.count('href="change.html"') == 1
    assert bar.index('href="change.html"') < bar.index('href="change2.html"')  # newest Date first: day(3) before day(2)
    assert 'href="WorkType_Change.html">Changes</a>' in html
    assert 'href="Category_Incident.html">Incidents</a>' in html   # only legacy incidents in this site


def test_events_page_uses_worktype(site):
    assert "change2.html" in read(site, "events.html")


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
    assert folding == ["work"]
    assert html.count("<details") == html.count("</details>")
    head = html[:html.index("<details")]
    assert "kb-hero-bar" in head and "kb-diataxis-card" in head


def test_landing_page_labels_are_all_badges(site):
    """Every coloured label on the dashboard is a kb-badge, so they all get one width."""
    html = read(site, "index.html")
    labels = re.findall(r'<a class="uk-label([^"]*)"', html)
    assert labels and all(" kb-badge " in f"{c} " for c in labels), labels
    assert 'style="color: white;"' not in html


def test_metadata_pages(site):
    assert "monitor.html" in read(site, "Periodicity_Daily.html")
    assert "change.html" in read(site, "Priority_High.html")
    for name in ("Category.html", "Status.html", "stats.html", "properties.html", "all.html", "bookmarks.html"):
        assert (site["target"] / name).exists(), name


def test_properties_page_is_a_leader_list_of_the_properties(site):
    html = read(site, "properties.html")
    assert 'class="kb-props"' in html and "kb-cloud" not in html and "data-uk-modal" not in html.split("PROPERTIES :: START")[1]
    row = re.search(r'<a class="kb-props-key" href="Priority.html">Priority</a>\s*</div>\s*'
                    r'<div class="kb-props-count">([^<]*)<span class="kb-meta-sep">', html)
    assert row and row.group(1).split() == ["3", "values"]


def test_property_page_has_cloud_and_table_but_no_leader(site):
    html = read(site, "Priority.html")
    tabs = re.findall(r'<li><a href="#">([^<]+)</a></li>', html)
    assert tabs == ["Cloud", "Table"]
    assert "data-uk-leader" not in html


def test_stats_page(site):
    """Totals, activity and property coverage; Summary is not counted."""
    html = read(site, "stats.html")
    for anchor in ("stats-activity", "stats-coverage", "stats-health", "stats-links"):
        assert f'id="{anchor}"' in html, anchor  # every section is a card
    assert 'id="stats-coverage-details"' in html  # its details open in a modal
    assert 'href="Periodicity.html"' in html and 'href="Summary.html"' not in html


def test_document_page_has_toc_and_properties(site):
    html = read(site, "monitor.html")
    assert "Steps" in html and "Detail" in html
    assert "Periodicity_Daily.html" in html


def test_document_page_folds_sections_and_has_no_properties_section(site):
    html = read(site, "monitor.html")
    assert "Document Properties" not in html  # the properties are in the info card, not a body section
    assert 'id="kb-info-card"' in html and 'id="modal-metadata"' not in html
    # Every section starts folded except the first top-level one and the sections inside it.
    assert "if (s !== first && !first.contains(s)) s.classList.add('kb-closed');" in html
    assert 'id="kb-toc-inline" open' in html


def test_print_hides_tooltips_and_uses_sans_serif(site):
    css = (site["target"] / "resources/themes/techdoc/framework/kb4it/css/print.css").read_text(encoding="utf-8")
    hidden = css[:css.index("display: none !important;")]
    assert ".uk-tooltip," in hidden and ".uk-navbar-dropdown," in hidden
    assert "Georgia" not in css and "sans-serif" in css
    assert "attr(href)" not in css  # links print as text only


def test_print_footer_has_title_and_page_numbers(site, tmp_path):
    css = (site["target"] / "resources/themes/techdoc/framework/kb4it/css/print.css").read_text(encoding="utf-8")
    assert 'content: counter(page) "/" counter(pages);' in css
    assert '@page { @bottom-left { content: "Check backups"; } }' in read(site, "monitor.html")
    home = tmp_path / "home"
    home.mkdir()
    target = build_techdoc(tmp_path, home, {"x.md": page('Use "q" \\ and </style><b>', Category="Note")})
    html = (target / "x.html").read_text(encoding="utf-8")
    assert '@page { @bottom-left { content: "Use \\"q\\" \\\\ and \\3c /style>\\3c b>"; } }' in html


def test_datatable_labels_are_badges(site):
    labels = re.findall(r'class="uk-label([^"]*kb-dt-label[^"]*)"', read(site, "all.html"))
    assert labels and all(" kb-badge " in f"{c} " for c in labels), labels


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


SKELETONS = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "templates" / "skeletons"


@pytest.mark.parametrize("name,category,worktype", [("CHANGE", "Record", "Change"), ("INCIDENT", "Record", "Incident"),
                                                     ("TASK", "Record", "Task"), ("MEETING", "Minutes", "Meeting")])
def test_record_skeletons_use_worktype(name, category, worktype):
    text = (SKELETONS / f"{name}-SKELETON.md").read_text(encoding="utf-8")
    assert f"\nCategory: {category}\n" in text and f"\nWorkType: {worktype}\n" in text


@pytest.mark.parametrize("name", ["NOTE", "POST", "PROCEDURE", "REPORT"])
def test_knowledge_skeletons_use_worktype_knowledge(name):
    text = (SKELETONS / f"{name}-SKELETON.md").read_text(encoding="utf-8")
    assert "\nWorkType: Knowledge\n" in text


@pytest.mark.parametrize("path", sorted(SKELETONS.glob("*-SKELETON.md")), ids=lambda p: p.name)
def test_skeleton_keys_are_alphabetical_without_version(path):
    keys = [line.split(":")[0] for line in path.read_text(encoding="utf-8").split("---")[1].splitlines() if line]
    assert keys == sorted(keys) and "Version" not in keys


def test_worktype_knowledge_is_not_a_record():
    sys.path.insert(0, str(ROOT / "kb4it/resources/themes/techdoc/logic"))
    import techdoc_records as records

    class Db:
        def __init__(self, meta):
            self.meta = meta

        def get_values(self, doc_id, key):
            return self.meta.get(key, [''])

    assert records.work_type(Db({"WorkType": ["Knowledge"], "Category": ["Procedure"]}), "a.md") == ""
    assert records.event_type(Db({"WorkType": ["Knowledge"], "Category": ["Procedure"]}), "a.md") == "Procedure"
    assert records.work_type(Db({"WorkType": ["Incident"], "Category": ["Record"]}), "a.md") == "Incident"
    assert records.work_type(Db({"Category": ["Change"]}), "a.md") == "Change"


def test_apps_list_worktype_after_category():
    for app in ("default", "sapbasis"):
        conf = json.loads((ROOT / "kb4it/resources/themes/techdoc/apps" / app / "config/repo.json").read_text(encoding="utf-8"))
        for key in ("datatable", "menu"):
            assert conf[key].index("WorkType") == conf[key].index("Category") + 1


def test_datatable_header_scrolls_with_the_body(site):
    # With scrollY the header is a separate table; only scrollX makes it follow a horizontal scroll.
    html = read(site, "all.html")
    setup = html[html.index("DATATABLES SETUP :: START"):html.index("DATATABLES SETUP :: END")]
    assert re.search(r"scrollY:[^\n]*\n", setup) and re.search(r"scrollX:\s*true", setup)


def test_datatable_title_cell_can_shrink_to_fit(site):
    html = read(site, "all.html")
    assert '<td class="uk-text-small kb-dt-title">' in html
    assert '<td class="uk-text-left kb-dt-date">' in html
    assert ".kb-dt-title" in (site["target"] / "resources/themes/techdoc/framework/kb4it/css/screen.css").read_text(encoding="utf-8")


def _headers(html):
    return re.findall(r'<span class="uk-text-secondary">([^<]+)</span>', html[html.index("<thead>"):html.index("</thead>")])


def test_document_tables_hide_columns_empty_in_every_row(site):
    # Category_Note lists only undated.md: no WorkType, Priority, Status or Scope; Date and Title always stay.
    assert _headers(read(site, "Category_Note.html")) == ["Date", "Title", "Category"]
    assert "WorkType" in _headers(read(site, "Category_Record.html"))


def test_open_items_and_activity_are_two_tabs_of_one_card(site):
    html = read(site, "index.html")
    card = html[html.index("WORK :: START"):html.index("WORK :: END")]
    tabs = re.findall(r'<ul class="kb-work-tabs".*?</ul>', card, re.S)[0]
    assert re.findall(r'<li data-kb-tab="([\w-]+)">', tabs) == ["open-items", "activity"]
    assert card.index("OPEN ITEMS :: START") < card.index("ACTIVITY :: START")
    assert 'data-kb-remember="kb-work-tab"' in card     # the last tab is remembered


def test_activity_card_has_a_tab_per_kind_of_activity(site):
    html = read(site, "index.html")
    card = html[html.index("ACTIVITY :: START"):html.index("ACTIVITY :: END")]
    tabs = re.findall(r'<li data-kb-tab="(\w+)"><a href="#">', card)
    assert tabs == ["changes", "incidents", "events", "monitoring"]
    for gone in ("changes-incidents", "upcoming-events", "recent-events", 'data-kb-section="monitoring"'):
        assert gone not in html
    assert "kb-activity-tab" in html                 # the last tab is remembered

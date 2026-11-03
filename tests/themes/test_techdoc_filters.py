"""techdoc techdoc_filters.py: the filter bar of the document tables on all, bookmarks and value pages."""

import importlib.util
import json
import re

import pytest

from tests.helpers import ROOT, page
from tests.themes.test_techdoc_add import build_techdoc

LOGIC = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic"
spec = importlib.util.spec_from_file_location("techdoc_filters", LOGIC / "techdoc_filters.py")
filters = importlib.util.module_from_spec(spec)
spec.loader.exec_module(filters)


espec = importlib.util.spec_from_file_location("techdoc_events", LOGIC / "techdoc_events.py")
events = importlib.util.module_from_spec(espec)
espec.loader.exec_module(events)


def test_event_days_map_each_document_to_its_day():
    assert events.event_days({2026: {3: {4: ["a.md", "b.md"]}, 11: {30: ["c.md"]}}}) == {
        "a.md": "2026-03-04", "b.md": "2026-03-04", "c.md": "2026-11-30"}


def test_calendar_json_counts_events_per_day_and_is_safe_in_a_script():
    text = events.calendar_json({"a.md": "2026-03-04", "b.md": "2026-03-04", "c.md": "2025-01-01"})
    assert json.loads(text) == {"days": {"2025-01-01": 1, "2026-03-04": 2}}


def values_from(table):
    return lambda doc, key: table.get(doc, {}).get(key, [])


def test_groups_count_values_and_sort_by_count_then_name():
    docs = {
        "a": {"Status": ["Open"], "Priority": ["High"]},
        "b": {"Status": ["Open"], "Priority": ["Low"]},
        "c": {"Status": ["Completed"], "Priority": ["High"]},
        "d": {"Status": ["Draft", "Open"]},
    }
    groups = filters.facet_groups(list(docs), values_from(docs), ("Status", "Priority"))
    status, priority = groups
    assert status["key"] == "Status" and status["slug"] == "status"
    assert [(v["name"], v["count"]) for v in status["values"]] == [("Open", 3), ("Completed", 1), ("Draft", 1)]
    assert [(v["name"], v["count"]) for v in priority["values"]] == [("High", 2), ("Low", 1)]


def test_groups_leave_out_keys_that_do_not_split_the_documents():
    docs = {"a": {"Status": ["Open"], "Topic": ["Backup"]}, "b": {"Status": ["Open"]}}
    groups = filters.facet_groups(list(docs), values_from(docs), ("Status", "Topic", "Priority"))
    # Status: same value everywhere; Priority: no values; Topic: one value, but not on every document.
    assert [g["key"] for g in groups] == ["Topic"]


def test_row_attributes_are_slugs_and_escaped():
    docs = {"a": {"DocType": ["How-to guide"], "Status": ["Open", "Draft"], "Topic": ['x"y']}}
    attrs = filters.facet_attrs(values_from(docs), "a", ("DocType", "Status", "Topic", "Priority"))
    assert attrs == 'data-kb-f-doctype="how-to-guide" data-kb-f-status="draft open" data-kb-f-topic="x-y"'
    assert 'x"y' not in attrs
    assert filters.facet_attrs(values_from(docs), "b") == ""


STATUSES = ["Open", "Open", "Open", "Completed", "Completed", "Draft", "Open", "Completed", "Planned", "Open",
            "Open"]
DOCS = {
    f"doc{i:02d}.md": page(f"Document {i}", Date=f"2026-01-{i + 1:02d}", Category="Record", WorkType="Change",
                           Status=status, Priority="High" if i % 2 else "Low", Topic="Backup",
                           Bookmark="Yes" if i < 3 else "No")
    for i, status in enumerate(STATUSES)
}


@pytest.fixture(scope="module")
def target(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-filters")
    home = base / "home"
    home.mkdir()
    return build_techdoc(base, home, DOCS)


def read(target, name):
    return (target / name).read_text(encoding="utf-8")


def bar(html):
    start = html.index("<!-- DOCUMENT FILTER :: START -->")
    return html[start:html.index("<!-- DOCUMENT FILTER :: END -->", start)]


def test_all_documents_page_has_the_bar_hidden_with_counts(target):
    html = read(target, "all.html")
    facets = bar(html)
    assert 'data-kb-table="kb4it-datatable"' in facets and " hidden>" in facets
    keys = re.findall(r'data-kb-key="([a-z]+)"', facets)
    assert keys == ["status", "priority"]  # WorkType, Category and Topic are the same on every document
    status = facets[facets.index('data-kb-key="status"'):facets.index('data-kb-key="priority"')]
    values = re.findall(r'data-kb-value="([a-z-]*)">([^<]+?) ?<span class="kb-dt-facet-n">(\d+)', status)
    assert values == [("open", "Open", "6"), ("completed", "Completed", "3"), ("draft", "Draft", "1"),
                      ("planned", "Planned", "1")]
    assert 'data-kb-value="">All</a>' in status


def test_rows_carry_their_values_in_the_title_cell(target):
    html = read(target, "all.html")
    assert html.count('data-kb-f-status="') == len(DOCS)
    assert re.search(r'<td class="[^"]*kb-dt-title" data-kb-f-worktype="change" data-kb-f-category="record" '
                     r'data-kb-f-topic="backup" data-kb-f-status="[a-z]+" data-kb-f-priority="(high|low)">', html)


def test_value_page_has_the_bar_without_its_own_property(target):
    html = read(target, "Topic_Backup.html")
    keys = re.findall(r'data-kb-key="([a-z]+)"', bar(html))
    assert keys == ["status", "priority"]


def test_small_tables_have_no_bar(target):
    assert "DOCUMENT FILTER" not in read(target, "Status_Completed.html")  # three rows
    assert "DOCUMENT FILTER" not in read(target, "bookmarks.html")  # three rows
    assert "data-kb-f-" not in read(target, "bookmarks.html")


def test_year_and_month_archive_pages_have_the_bar(target):
    for name in ("events_2026.html", "events_202601.html"):
        keys = re.findall(r'data-kb-key="([a-z]+)"', bar(read(target, name)))
        assert keys == ["status", "priority"], name


def test_day_archive_and_document_pages_have_no_bar(target):
    assert "DOCUMENT FILTER" not in read(target, "events_20260102.html")  # one row
    doc = read(target, "doc01.html")
    assert "DOCUMENT FILTER" not in doc and "data-kb-f-" not in doc


def test_events_page_has_one_table_with_the_bar_and_event_days(target):
    html = read(target, "events.html")
    assert html.count('class="kb4it-datatable') == 1
    assert 'data-kb-table="kb4it-events-table"' in bar(html)
    assert html.count('data-kb-date="2026-01-') == len(DOCS)
    assert 'data-kb-date="2026-01-02"' in html  # doc01 is dated 2026-01-02
    assert 'data-kb-events data-kb-table="kb4it-events-table"' in html
    assert "framework/kb4it/js/events.js" in html
    assert "kb4it-events-year-select" not in html and "kb-evcal-grid" not in html


def test_events_page_has_the_calendar_data(target):
    html = read(target, "events.html")
    start = html.index('<script type="application/json" id="kb-events-data">') + len(
        '<script type="application/json" id="kb-events-data">')
    data = json.loads(html[start:html.index("</script>", start)])
    assert data == {"days": {f"2026-01-{i + 1:02d}": 1 for i in range(len(DOCS))}}


def test_scripts_are_deployed_and_loaded(target):
    assert "framework/kb4it/js/datatable-filter.js" in read(target, "all.html")
    js = target / "resources" / "themes" / "techdoc" / "framework" / "kb4it" / "js"
    assert (js / "datatable-filter.js").exists() and (js / "events.js").exists()

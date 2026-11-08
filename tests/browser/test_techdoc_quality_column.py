"""techdoc Quality column: the tier is the tooltip of the meter, and the table search still finds it."""

import pytest

from tests.helpers import page, run_kb4it, write_repo
from tests.themes.test_techdoc_add import _app_conf

pytestmark = pytest.mark.browser

LONG = "\n\n".join(f"## Part {i}\n\n" + "Words that make the body long enough. " * 12 for i in range(1, 5))
DOCS = {
    "stub-a.md": page("Stub A", "Short.", Category="Note", Date="2026-01-01", Tag="x"),
    "stub-b.md": page("Stub B", "Short too.", Category="Note", Date="2026-01-02", Tag="x"),
    "rich.md": page("Rich", LONG, Category="Note", DocType="Explanation", Date="2026-01-03", Tag="x",
                    Author="Ana", Product="ADS", Scope="Ops", Status="Released", Topic="Backup", WorkType="Knowledge",
                    Summary="A full note."),
}


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-quality-column")
    home = base / "home"
    home.mkdir()
    conf = _app_conf("techdoc")
    conf["datatable"] = ["Date", "Title", "Quality"]
    cfg = write_repo(base, "techdoc", DOCS, **conf)
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return base / "target"


@pytest.fixture
def all_page(browser, site):
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    context.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file://") else r.abort())
    pg = context.new_page()
    pg.set_default_timeout(10000)
    pg.goto((site / "all.html").as_uri())
    pg.wait_for_selector(".dataTables_filter input")
    yield pg
    context.close()


def test_tier_is_a_tooltip_not_text(all_page):
    meters = all_page.locator("#kb4it-datatable tbody .kb-q-meter")
    assert meters.count() == len(DOCS)
    cells = all_page.locator("#kb4it-datatable tbody td[data-search]")
    assert all(t.strip() == "" for t in cells.all_inner_texts()), "no tier word is printed in the column"
    meters.first.hover()
    tooltip = all_page.locator(".uk-tooltip.uk-active")
    tooltip.wait_for()
    tier = cells.first.get_attribute("data-search")
    assert tooltip.inner_text().startswith(f"{tier}, score ")


def test_table_search_finds_rows_by_tier(all_page):
    tiers = all_page.locator("#kb4it-datatable tbody td[data-search]").evaluate_all(
        "cells => cells.map(c => c.dataset.search)")
    assert sorted(set(tiers)) == ["Complete", "Stub"], tiers
    for tier in ("Stub", "Complete"):
        all_page.fill(".dataTables_filter input", tier)
        all_page.wait_for_function(f"document.querySelectorAll('#kb4it-datatable tbody tr').length === {tiers.count(tier)}")
        assert all_page.locator("#kb4it-datatable tbody tr").count() == tiers.count(tier)

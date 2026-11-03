"""The techdoc events page: a calendar panel beside one events table; the panel filters the table."""

from datetime import datetime

import pytest

from tests.helpers import page as md_page
from tests.themes.test_techdoc_add import build_techdoc

pytestmark = pytest.mark.browser

THIS_YEAR = datetime.now().year  # noqa: DTZ005  # KB4IT works with naive local datetimes
DOCS = {
    "a.md": md_page("March change", Date=f"{THIS_YEAR}-03-04", Category="Record", WorkType="Change", Status="Open"),
    "b.md": md_page("March incident", Date=f"{THIS_YEAR}-03-17", Category="Record", WorkType="Incident",
                    Status="Completed"),
    "c.md": md_page("May change", Date=f"{THIS_YEAR}-05-02", Category="Record", WorkType="Change",
                    Status="Completed"),
    "d.md": md_page("Old change", Date="2020-06-10", Category="Record", WorkType="Change", Status="Completed"),
}


@pytest.fixture(scope="module")
def events_site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-events-browser")
    home = base / "home"
    home.mkdir()
    return build_techdoc(base, home, DOCS)


@pytest.fixture
def events(browser, events_site):
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    context.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file://") else r.abort())
    page = context.new_page()
    page.set_default_timeout(10000)
    page.goto((events_site / "events.html").as_uri())
    page.wait_for_selector(".kb-dt-chips .kb-dt-chip")
    yield page
    context.close()


def rows(page):
    return page.locator("#kb4it-events-table tbody tr").count()


def test_opens_on_this_year(events):
    assert events.evaluate("location.hash") == f"#{THIS_YEAR}"
    assert events.inner_text(".kb-ev-year-name") == str(THIS_YEAR)
    assert rows(events) == 3
    assert events.inner_text(".kb-dt-chips .kb-dt-chip").startswith(str(THIS_YEAR))


def test_month_bar_and_day_filter_the_table(events):
    events.locator(".kb-ev-strip .kb-ev-bar").nth(2).click()  # March
    assert events.evaluate("location.hash") == f"#{THIS_YEAR}-03"
    assert rows(events) == 2
    events.click(".kb-ev-day.kb-ev-has >> text='17'")
    assert events.evaluate("location.hash") == f"#{THIS_YEAR}-03-17"
    assert rows(events) == 1
    assert "March incident" in events.inner_text("#kb4it-events-table tbody")
    assert events.get_attribute(".kb-ev-archive", "href") == f"events_{THIS_YEAR}0317.html"
    events.go_back()
    assert events.evaluate("location.hash") == f"#{THIS_YEAR}-03"
    assert rows(events) == 2


def test_year_list_and_chip_reset(events):
    events.click(".kb-ev-year-label")
    events.click(".kb-ev-years-item >> text='2020'")
    assert rows(events) == 1
    events.click(".kb-dt-chips .kb-dt-chip")
    assert events.evaluate("location.hash") == "#all"
    assert events.inner_text(".kb-ev-year-name") == "All years"
    assert rows(events) == 4


def test_address_opens_a_day_and_works_with_the_filter_bar(events, events_site):
    events.goto((events_site / "events.html").as_uri() + f"#{THIS_YEAR}-05")
    events.wait_for_selector(".kb-dt-chips .kb-dt-chip")
    assert rows(events) == 1
    events.click(".kb-ev-year-label")
    events.click(".kb-ev-years-item >> nth=0")  # All years
    events.click(".kb-dt-facets-toggle")
    events.click('[data-kb-key="worktype"] a[data-kb-value="change"]')
    assert rows(events) == 3
    status = events.locator('[data-kb-key="status"] a[data-kb-value="completed"] .kb-dt-facet-n')
    assert status.inner_text() == "2"  # live count: changes only

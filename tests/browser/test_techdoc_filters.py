"""The techdoc filter bar of the document tables: a Filter button after the search box opens pills per property."""

import pytest

from tests.themes.test_techdoc_add import build_techdoc
from tests.themes.test_techdoc_filters import DOCS

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def filter_site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-filter-browser")
    home = base / "home"
    home.mkdir()
    return build_techdoc(base, home, DOCS)


@pytest.fixture
def all_page(browser, filter_site):
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    context.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file://") else r.abort())
    page = context.new_page()
    page.set_default_timeout(10000)
    page.goto((filter_site / "all.html").as_uri())
    page.wait_for_selector(".kb-dt-facets-toggle")
    yield page
    context.close()


def rows(page):
    return page.locator("#kb4it-datatable tbody tr").count()


def pill(key, value):
    return f'[data-kb-key="{key}"] a[data-kb-value="{value}"]'


def test_bar_is_folded_below_the_search_box(all_page):
    assert all_page.locator(".dataTables_filter .kb-dt-facets-toggle").count() == 1
    assert all_page.is_hidden(".kb-dt-facets")
    all_page.click(".kb-dt-facets-toggle")
    assert all_page.is_visible(".kb-dt-facets")
    assert all_page.get_attribute(".kb-dt-facets-toggle", "aria-expanded") == "true"
    above = all_page.eval_on_selector(".dataTables_filter", "e => e.getBoundingClientRect().bottom")
    assert all_page.eval_on_selector(".kb-dt-facets", "e => e.getBoundingClientRect().top") >= above


def test_values_of_one_property_add_up_and_properties_narrow(all_page):
    all_page.click(".kb-dt-facets-toggle")
    assert rows(all_page) == 11
    all_page.click(pill("status", "open"))
    assert rows(all_page) == 6
    assert "filtered from 11" in all_page.inner_text(".dataTables_info")
    all_page.click(pill("status", "draft"))
    assert rows(all_page) == 7
    all_page.click(pill("priority", "high"))
    assert rows(all_page) == 3
    assert all_page.inner_text(".kb-dt-facets-count") == "3"
    all_page.click(pill("status", "draft"))  # a second click takes the value out again
    assert rows(all_page) == 2


def test_all_and_clear_reset_the_filters(all_page):
    all_page.click(".kb-dt-facets-toggle")
    all_page.click(pill("status", "open"))
    all_page.click(pill("priority", "low"))
    all_page.click(pill("status", ""))
    assert rows(all_page) == 6
    assert all_page.get_attribute(pill("status", ""), "aria-pressed") == "true"
    all_page.click(".kb-dt-facets-clear")
    assert rows(all_page) == 11
    assert all_page.is_hidden(".kb-dt-facets-clear")
    assert all_page.inner_text(".kb-dt-facets-count") == ""


def test_search_box_works_together_with_the_filters(all_page):
    all_page.click(".kb-dt-facets-toggle")
    all_page.click(pill("status", "completed"))
    all_page.fill(".dataTables_filter input", "Document 3")
    all_page.wait_for_function("document.querySelectorAll('#kb4it-datatable tbody tr').length === 1")
    assert "Document 3" in all_page.inner_text("#kb4it-datatable tbody")


def test_quality_lists_are_filtered(browser, filter_site):
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    context.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file://") else r.abort())
    page = context.new_page()
    page.goto((filter_site / "quality.html").as_uri())
    page.wait_for_selector(".kb-dt-list-tools .kb-dt-facets-toggle")
    visible = "document.querySelectorAll('#kb-quality-lists [data-kb-item]:not([hidden])').length"
    total = page.evaluate(visible)
    page.click(".kb-dt-facets-toggle")
    page.click(pill("status", "completed"))
    assert 0 < page.evaluate(visible) < total
    assert page.inner_text(".kb-dt-chips .kb-dt-chip").startswith("Status: Completed")
    page.click(".kb-dt-facets-clear")
    assert page.evaluate(visible) == total
    context.close()

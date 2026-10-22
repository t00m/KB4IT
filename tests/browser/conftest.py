"""Browser tests of the techdoc Add page (ED-12): Playwright and Chromium, skipped when missing.

KB4IT_BROWSER_TESTS=required (the CI browser job) turns a missing Chromium into a failure.
"""

import os

import pytest

from tests.themes.test_techdoc_add import ADD_DOCS, build_techdoc


@pytest.fixture(scope="session")
def site(tmp_path_factory):
    """A techdoc build with two Notes, a Procedure tagged "sap, linux" and a "x<b>y</b>" tag."""
    base = tmp_path_factory.mktemp("browser-site")
    home = base / "home"
    home.mkdir()
    return build_techdoc(base, home, ADD_DOCS)


@pytest.fixture(scope="session")
def browser():
    # Inside the fixture: a module-level importorskip in a conftest stops pytest when
    # tests/browser is given on the command line.
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as pw:
        try:
            chromium = pw.chromium.launch()
        except Exception as exc:  # noqa: BLE001  # no browser installed: skip, do not fail
            if os.environ.get("KB4IT_BROWSER_TESTS") == "required":
                raise
            pytest.skip(f"Chromium not available: {exc}")
        yield chromium
        chromium.close()


@pytest.fixture
def add_page(browser, site):
    """add.html opened from file://, with every other request aborted and recorded in page.aborted."""
    context = browser.new_context()
    aborted = []

    def route(r):
        if r.request.url.startswith("file://"):
            r.continue_()
        else:
            aborted.append(r.request.url)
            r.abort()

    context.route("**/*", route)
    page = context.new_page()
    page.aborted = aborted
    page.set_default_timeout(10000)
    page.goto((site / "add.html").as_uri())
    page.wait_for_function("!!(window.KB4ITEditor && window.KB4ITEditor.open)")
    yield page
    context.close()


def editor_text(page, cat):
    return page.evaluate("c => KB4ITEditor.text(c)", cat)

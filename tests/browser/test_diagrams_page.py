"""The techdoc Diagrams page in a browser: nothing drawn at first, the chosen diagrams drawn, broken ones reported."""

import pytest

from tests.helpers import page as md_page
from tests.themes.test_techdoc_add import build_techdoc

pytestmark = pytest.mark.browser

FENCE = "`" * 3
GOOD = f"## Flow\n\n{FENCE}mermaid\nflowchart LR\n  A[Alert] -. replication .-> B[Restart]\n{FENCE}\n"
BROKEN = f"## Broken\n\n{FENCE}mermaid\nflowchart LR\n  A[Alert -->\n{FENCE}\n"


@pytest.fixture(scope="module")
def diagrams_site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-diagrams-page")
    home = base / "home"
    home.mkdir()
    docs = {
        "good.md": md_page("Good", body=GOOD, Category="Note", Date="2026-11-01"),
        "broken.md": md_page("Broken", body=BROKEN, Category="Procedure", Date="2026-10-01"),
    }
    return build_techdoc(base, home, docs)


@pytest.fixture
def dia_page(browser, diagrams_site):
    context = browser.new_context(viewport={"width": 1200, "height": 900})
    context.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file://") else r.abort())
    page = context.new_page()
    page.set_default_timeout(10000)
    page.errors = []
    page.on("pageerror", lambda error: page.errors.append(str(error)))
    page.goto((diagrams_site / "diagrams.html").as_uri())
    page.wait_for_function("!!window.mermaid")
    yield page
    context.close()


def test_nothing_is_drawn_until_a_filter_matches(dia_page):
    dia_page.wait_for_timeout(300)
    assert dia_page.evaluate("document.getElementById('kb-gal-grid').hidden")
    assert dia_page.locator("#kb-gal-grid img").count() == 0
    assert dia_page.evaluate("document.querySelectorAll('svg[id^=\"kb-dia-\"]').length") == 0
    assert not dia_page.errors


def test_chosen_diagrams_are_drawn_and_broken_ones_reported(dia_page):
    dia_page.fill("#kb-gal-text", "a")  # matches both: words of the diagram text count
    dia_page.wait_for_function("document.querySelector('#kb-gal-grid img') && document.querySelector('#kb-gal-grid img').complete")
    image = dia_page.locator("#kb-gal-grid img")
    assert image.count() == 1
    assert image.evaluate("i => i.naturalWidth > 0 && i.src.startsWith('blob:')")
    assert "Mermaid could not draw this diagram" in dia_page.inner_text(".kb-gal-dia-error")
    assert dia_page.inner_text("#kb-gal-status") == "2 diagrams in 2 documents."
    link = dia_page.locator(".kb-gal-cap a").first
    assert link.get_attribute("href") == "good.html#flow"
    assert not dia_page.errors


def test_a_drawn_diagram_opens_in_the_lightbox(dia_page):
    dia_page.goto(dia_page.url.split("#")[0] + "#Category=Note")
    dia_page.reload()
    dia_page.wait_for_selector("#kb-gal-grid img")
    dia_page.click("#kb-gal-grid a.kb-gal-zoom")
    dia_page.wait_for_selector(".uk-lightbox img[src^='blob:']", state="visible")
    assert "good.html#flow" in dia_page.inner_html(".uk-lightbox")

"""The techdoc top bar: a long title is cut, never drawn over the search icon; search opens in a dialog."""

import pytest

from kb4it.core.notice import HELP_ONLINE_URL
from tests.browser.test_add_editor import open_cat
from tests.helpers import page as md_page
from tests.themes.test_techdoc_add import build_techdoc

pytestmark = pytest.mark.browser

TOC_BODY = "\n\n".join(f"## Part {n} of a long procedure with many steps\n\nText.\n\n### Detail {n}\n\nMore." for n in range(1, 4))
LONG = "A very long document title that would never fit in the top bar next to the logo menu and the search icon"


@pytest.fixture(scope="module")
def navbar_site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-navbar")
    home = base / "home"
    home.mkdir()
    docs = {
        "long.md": md_page(LONG, Category="Note", Date="2026-10-01"),
        "zebra.md": md_page("Zebra", Category="Note", Date="2026-10-02"),
        "toc.md": md_page("Sections", body=TOC_BODY, Category="Note", Date="2026-10-03"),
    }
    return build_techdoc(base, home, docs)


@pytest.fixture
def nav_page(browser, navbar_site):
    context = browser.new_context(viewport={"width": 1024, "height": 700})
    context.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file://") else r.abort())
    page = context.new_page()
    page.set_default_timeout(10000)
    page.goto((navbar_site / "long.html").as_uri())
    page.wait_for_function("!!window.KB4IT_INDEX")
    yield page
    context.close()


def _box(page, selector):
    return page.eval_on_selector(selector, "e => { const r = e.getBoundingClientRect(); return [r.left, r.right]; }")


def test_long_title_is_cut_before_the_search_icon(nav_page):
    nav_page.set_viewport_size({"width": 700, "height": 700})
    title = "#kb4it-page-title"
    assert nav_page.eval_on_selector(title, "e => e.scrollWidth > e.clientWidth"), "the title is not cut"
    assert _box(nav_page, title)[1] <= _box(nav_page, 'a[href="#kb4it-search-modal"]')[0]
    assert _box(nav_page, title)[0] >= _box(nav_page, "#kb4it-menu .uk-navbar-left")[1]
    assert nav_page.get_attribute(".kb4it-navbar-title a", "title") == LONG


@pytest.mark.parametrize("keys", ["/", "Control+k"])
def test_shortcut_opens_search_dialog_with_results(nav_page, keys):
    assert not nav_page.is_visible("#kb4it-search-input")
    nav_page.keyboard.press(keys)
    nav_page.wait_for_function("document.activeElement.id === 'kb4it-search-input'")
    nav_page.keyboard.type("zebra")
    nav_page.wait_for_selector('#kb4it-search-dropdown a[href="zebra.html"]', state="visible")


def test_icon_opens_search_dialog(nav_page):
    nav_page.click('a[href="#kb4it-search-modal"]')
    nav_page.wait_for_function("document.activeElement.id === 'kb4it-search-input'")


def test_slash_typed_in_the_search_box_stays_text(nav_page):
    nav_page.keyboard.press("/")
    nav_page.wait_for_function("document.activeElement.id === 'kb4it-search-input'")
    nav_page.keyboard.type("a/b")
    assert nav_page.input_value("#kb4it-search-input") == "a/b"


def test_title_with_markup_is_escaped_once(browser, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    target = build_techdoc(tmp_path, home, {"x.md": md_page('Use <b> & "quotes"', Category="Note")})
    page = browser.new_page()
    page.goto((target / "x.html").as_uri())
    assert page.get_attribute(".kb4it-navbar-title a", "title") == 'Use <b> & "quotes"'
    assert page.text_content("#kb4it-page-title") == 'Use <b> & "quotes"'
    page.close()


def test_shortcuts_do_nothing_in_the_add_page_editor(add_page):
    open_cat(add_page, "note")
    add_page.click("#kb-editor-note .cm-content")
    add_page.keyboard.press("/")
    add_page.keyboard.press("Control+k")
    assert not add_page.is_visible("#kb4it-search-input")


def test_help_and_about_are_in_the_logo_menu(nav_page):
    menu = "#kb4it-menu .uk-navbar-left .uk-navbar-dropdown"
    for href in ("about_app.html", "about_kb4it.html"):
        assert nav_page.query_selector(f'{menu} a[href="{href}"]'), href
    # Help is the KB4IT help site, opened in a new window.
    assert nav_page.query_selector(f'{menu} a[href="{HELP_ONLINE_URL}"][target="_blank"][rel="noopener"]')
    assert not nav_page.query_selector('#kb4it-menu .uk-navbar-right a[href="help.html"]')


def _goto(page, doc):
    page.goto(page.url.rsplit("/", 1)[0] + "/" + doc)


def _open_title_menu(page, doc):
    _goto(page, doc)
    # UIkit 3.22+ ignores the first hover of a navbar when the pointer already sits on it
    # at load, and Playwright starts the pointer at (0, 0). Come in from the page instead.
    page.mouse.move(600, 600)
    page.hover(".kb4it-navbar-title a")
    page.wait_for_selector(".kb4it-title-menu", state="visible")


def test_page_actions_are_one_row_under_the_title_in_the_top_bar(nav_page):
    assert not nav_page.query_selector("#kb4it-menu .uk-navbar-left .kb4it-page-action")
    assert not nav_page.query_selector(".kb4it-title-menu .kb4it-page-action")
    _goto(nav_page, "toc.html")
    # Visible without hovering the title.
    assert nav_page.is_visible(".kb4it-page-action")
    tops = nav_page.eval_on_selector_all(".kb4it-page-action", "els => els.map(e => Math.round(e.getBoundingClientRect().top))")
    # Edit in the editor (on by default), properties, quality, source and print; edit in git only with git settings.
    assert len(tops) == 5 and len(set(tops)) == 1, tops
    title_bottom = nav_page.eval_on_selector("#kb4it-page-title", "e => e.getBoundingClientRect().bottom")
    bar_bottom = nav_page.eval_on_selector("#kb4it-menu nav", "e => e.getBoundingClientRect().bottom")
    assert title_bottom <= tops[0] and tops[0] + 28 <= bar_bottom


def test_source_action_opens_its_dialog_from_the_top_bar(nav_page):
    _goto(nav_page, "toc.html")
    nav_page.click('.kb4it-page-action[href="#modal-full-source"]')
    nav_page.wait_for_selector("#modal-full-source.uk-open", state="visible")


def test_properties_action_opens_the_details_tab_from_the_top_bar(nav_page):
    _goto(nav_page, "toc.html")
    nav_page.click('.kb4it-page-action[href="#kb-info-details"]')
    nav_page.wait_for_selector("#kb-info-card.kb-open #kb-info-details", state="visible")


def test_title_menu_is_wide_and_nests_the_contents(nav_page):
    _open_title_menu(nav_page, "toc.html")
    assert nav_page.eval_on_selector(".kb4it-title-menu", "e => e.getBoundingClientRect().width") >= 600
    # The menu opens below the whole bar, so it never covers the page actions.
    menu_top = nav_page.eval_on_selector(".kb4it-title-menu", "e => e.getBoundingClientRect().top")
    assert menu_top >= nav_page.eval_on_selector("#kb4it-menu nav", "e => e.getBoundingClientRect().bottom")
    top = nav_page.eval_on_selector('.kb4it-title-toc a[href="#part-1-of-a-long-procedure-with-many-steps"]', "e => e.getBoundingClientRect().left")
    sub = nav_page.eval_on_selector('.kb4it-title-toc a[href="#detail-1"]', "e => e.getBoundingClientRect().left")
    assert sub > top
    assert nav_page.eval_on_selector(".kb4it-title-toc a", "e => e.scrollWidth <= e.clientWidth"), "an entry runs over"


def test_reload_is_a_top_bar_button_left_of_search(nav_page):
    assert not nav_page.query_selector('#kb4it-menu .uk-navbar-left a[href="javascript:location.reload();"]')
    hrefs = [a.get_attribute("href") for a in nav_page.query_selector_all("#kb4it-menu .uk-navbar-right a")]
    assert hrefs == ["javascript:location.reload();", "#kb4it-search-modal"]

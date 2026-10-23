"""Browser tests of the techdoc Add page (ED-12): Playwright and Chromium, skipped when missing.

KB4IT_BROWSER_TESTS=required (the CI browser job) turns a missing Chromium into a failure.
"""

import os

import pytest

from tests.core.test_highlight import _app_conf
from tests.helpers import page as md_page
from tests.helpers import run_kb4it, write_repo
from tests.themes.test_techdoc_add import ADD_DOCS, build_techdoc


@pytest.fixture(scope="session")
def site(tmp_path_factory):
    """A techdoc build with two Notes, a Procedure tagged "sap, linux" and a "x<b>y</b>" tag."""
    base = tmp_path_factory.mktemp("browser-site")
    home = base / "home"
    home.mkdir()
    return build_techdoc(base, home, ADD_DOCS)


VOCAB = {"Feature": ["Backup", "Rename"], "Level": ["basic", "advanced"], "Platform": ["Linux", "Windows"]}

# Per theme: the category to open, a property and a value that two documents share.
THEME_CASES = {
    "techdoc": {"cat": "note", "key": "Tag", "value": "sharedtag"},
    "blog": {"cat": "post", "key": "Tag", "value": "sharedtag"},
    "bookshelf": {"cat": "chapter", "key": "Book", "value": "Sharedbook"},
    "apphelp": {"cat": "tutorial", "key": "Feature", "value": "Backup"},
}


def _theme_docs(theme):
    key, value = THEME_CASES[theme]["key"], THEME_CASES[theme]["value"]
    if theme == "apphelp":
        extra = {"DocType": "How-to guide", "Section": "How-to", "Summary": "A summary."}
        return {
            "one.md": md_page("One", Order="10", **{key: value}, **extra),
            "two.md": md_page("Two", Order="20", **{key: value}, **extra),
        }
    extra = {"Category": "Note"} if theme == "techdoc" else {"Category": "Post"} if theme == "blog" else {}
    return {
        "one.md": md_page("One", Date="2026-10-01", **{key: value}, **extra),
        "two.md": md_page("Two", Date="2026-10-02", **{key: value}, **extra),
    }


@pytest.fixture(scope="session")
def theme_site(tmp_path_factory):
    """theme_site(theme): the target folder of a site built with the editor on and two documents sharing a value."""
    built = {}

    def make(theme):
        if theme not in built:
            base = tmp_path_factory.mktemp(f"theme-{theme}")
            home = base / "home"
            home.mkdir()
            conf = {**_app_conf(theme), "editor": True}
            if theme == "apphelp":
                conf["apphelp"] = {"strict": True, "vocabulary": VOCAB}
            cfg = write_repo(base, theme, _theme_docs(theme), **conf)
            result = run_kb4it("build", cfg, cwd=base, home=home)
            assert result.returncode == 0, result.stdout
            built[theme] = base / "target"
        return built[theme]

    return make


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


TOAST = "#kb-toasts .kb-toast"


def open_dialog(page, cat):
    """Click Create on the card of a category and wait for the dialog and the editor."""
    page.click(f'[data-kb-open="{cat}"]')
    page.wait_for_selector(f"#kb-editor-{cat} .cm-editor", state="visible")
    page.wait_for_function("c => document.getElementById('modal-add-' + c).open", arg=cat)


def dialog_open(page, cat):
    return page.evaluate("c => document.getElementById('modal-add-' + c).open", arg=cat)


def close_dialog(page, cat):
    """Close the dialog with its Close button, accepting the unsaved-changes prompt."""
    accept = lambda dialog: dialog.accept()  # noqa: E731
    page.on("dialog", accept)
    try:
        page.click(f'[data-kb-close="{cat}"]')
        page.wait_for_function("c => !document.getElementById('modal-add-' + c).open", arg=cat)
    finally:
        page.remove_listener("dialog", accept)

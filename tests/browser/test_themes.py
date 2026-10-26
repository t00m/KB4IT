"""ET-11: the shared subset of the editor browser tests, on every bundled theme."""

import pytest

from tests.browser.conftest import (
    THEME_CASES,
    TOAST,
    close_dialog,
    dialog_open,
    editor_text,
    open_dialog,
)

pytestmark = pytest.mark.browser

THEMES = list(THEME_CASES)

CLIPBOARD = "Object.defineProperty(navigator, 'clipboard', {value: {writeText: async () => {}}});"
NO_PICKER = "delete window.showSaveFilePicker;"

CONTRAST = """() => {
  const el = document.querySelector('#kb-toasts .kb-toast');
  const parse = (c) => c.match(/[\\d.]+/g).map(Number);
  const lum = ([r, g, b]) => {
    const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const style = getComputedStyle(el);
  const fg = parse(style.color);
  let bg = null;
  for (let n = el; n; n = n.parentElement) {
    const c = parse(getComputedStyle(n).backgroundColor);
    if (c.length < 4 || c[3] > 0) { bg = c; break; }
  }
  const a = lum(fg), b = lum(bg);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}"""


@pytest.fixture
def theme_page(browser, theme_site):
    """theme_page(theme, script=""): add.html of the theme's site, only file:// requests allowed."""
    contexts = []

    def make(theme, script=""):
        context = browser.new_context(accept_downloads=True)
        if script:
            context.add_init_script(script)
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
        page.goto((theme_site(theme) / "add.html").as_uri())
        page.wait_for_function("!!(window.KB4ITEditor && window.KB4ITEditor.open)")
        contexts.append(context)
        return page

    yield make
    for context in contexts:
        context.close()


def set_doc(page, cat, text, anchor=None):
    page.evaluate(
        "([c, t, a]) => { const v = KB4ITEditor.views[c];"
        " v.dispatch({changes: {from: 0, to: v.state.doc.length, insert: t}, selection: {anchor: a}}); v.focus(); }",
        [cat, text, len(text) if anchor is None else anchor],
    )


def row(cat, key):
    return f'#kb-props-{cat} .kb-prop-row[data-key="{key}"]'


@pytest.mark.parametrize("theme", THEMES)
def test_open_and_type(theme_page, theme):
    cat = THEME_CASES[theme]["cat"]
    page = theme_page(theme)
    open_dialog(page, cat)
    assert editor_text(page, cat).startswith("---\n")
    skeleton = editor_text(page, cat)
    page.click(f"#kb-editor-{cat} .cm-content")
    page.keyboard.press("Control+End")
    page.keyboard.type("Hello")
    assert editor_text(page, cat) == skeleton + "Hello"


@pytest.mark.parametrize("theme", THEMES)
def test_completion_offers_repo_value(theme_page, theme):
    case = THEME_CASES[theme]
    page = theme_page(theme)
    open_dialog(page, case["cat"])
    set_doc(page, case["cat"], f"---\n{case['key']}: \n---\n\n# T\n", len(f"---\n{case['key']}: "))
    page.keyboard.type(case["value"][:2])
    page.wait_for_selector(".cm-tooltip-autocomplete")
    assert case["value"] in page.inner_text(".cm-tooltip-autocomplete")


@pytest.mark.parametrize("theme", THEMES)
def test_properties_form_edits_text(theme_page, theme):
    case = THEME_CASES[theme]
    cat, key = case["cat"], case["key"]
    page = theme_page(theme)
    open_dialog(page, cat)
    set_doc(page, cat, "---\nAuthor: me\n---\n\n# T\n")
    page.evaluate("c => KB4ITEditor.renderPane(c)", cat)
    if not page.locator(row(cat, key)).count():
        page.select_option(f"#kb-props-{cat} .kb-add-prop", value=key)
    page.fill(row(cat, key) + " .kb-value-input", "formvalue")
    page.press(row(cat, key) + " .kb-value-input", "Enter")
    assert f"{key}: formvalue" in editor_text(page, cat).split("\n")


@pytest.mark.parametrize("theme", THEMES)
def test_save_downloads_file(theme_page, theme, tmp_path):
    cat = THEME_CASES[theme]["cat"]
    page = theme_page(theme, NO_PICKER)
    open_dialog(page, cat)
    set_doc(page, cat, "---\nAuthor: me\n---\n# Theme Doc\n\nbody")
    with page.expect_download() as info:
        page.click(f"#kb-save-{cat}")
    assert info.value.suggested_filename == "theme-doc.md"
    target = tmp_path / "out.md"
    info.value.save_as(target)
    assert target.read_bytes() == b"---\nAuthor: me\n---\n# Theme Doc\n\nbody\n"
    assert page.evaluate("c => KB4ITEditor.dirty(c)", cat) is False


@pytest.mark.parametrize("theme", THEMES)
def test_copy_toast(theme_page, theme):
    cat = THEME_CASES[theme]["cat"]
    page = theme_page(theme, CLIPBOARD)
    open_dialog(page, cat)
    page.click(f'[data-kb-copy="{cat}"]')
    page.wait_for_selector(TOAST)
    assert "Copied to clipboard" in page.text_content(TOAST)
    assert "kb-toast-success" in page.get_attribute(TOAST, "class")


@pytest.mark.parametrize("theme", THEMES)
def test_close_prompt(theme_page, theme):
    cat = THEME_CASES[theme]["cat"]
    page = theme_page(theme)
    open_dialog(page, cat)
    page.click(f"#kb-editor-{cat} .cm-content")
    page.keyboard.press("Control+End")
    page.keyboard.type("x")
    messages = []

    def dismiss(dialog):
        messages.append(dialog.message)
        dialog.dismiss()

    page.once("dialog", dismiss)
    page.click(f'[data-kb-close="{cat}"]')
    page.wait_for_timeout(500)
    assert messages == ["You have unsaved changes. Close and lose them?"]
    assert dialog_open(page, cat)
    close_dialog(page, cat)
    assert not dialog_open(page, cat)


@pytest.mark.parametrize("theme", THEMES)
def test_no_network_request(theme_page, theme):
    page = theme_page(theme)
    # The theme's own page may load web fonts; the editor must add no request of its own.
    page.aborted.clear()
    open_dialog(page, THEME_CASES[theme]["cat"])
    assert page.aborted == []


@pytest.mark.parametrize("theme", THEMES)
def test_dark_page_all_themes(theme_page, theme):
    cat = THEME_CASES[theme]["cat"]
    page = theme_page(theme, CLIPBOARD)
    page.evaluate("document.documentElement.style.background = '#111'; document.body.style.background = '#111'")
    open_dialog(page, cat)
    assert page.evaluate("c => document.getElementById('modal-add-' + c).classList.contains('kb-dialog-dark')", cat)
    page.click(f'[data-kb-copy="{cat}"]')
    page.wait_for_selector(TOAST)
    assert page.evaluate(CONTRAST) >= 4.5

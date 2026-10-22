"""ED-04: CodeMirror on the techdoc Add page, driven in Chromium."""

from datetime import date

import pytest

from tests.browser.conftest import editor_text

pytestmark = pytest.mark.browser

CATEGORIES = ["change", "incident", "meeting", "note", "post", "procedure", "report", "task"]


def open_cat(page, cat):
    page.click(f"button[onclick=\"kbAddOpen('{cat}')\"]")
    page.wait_for_selector(f"#kb-editor-{cat} .cm-editor", state="visible")
    page.wait_for_selector(f"#modal-add-{cat}.uk-open")


def close_cat(page, cat):
    page.evaluate("c => UIkit.modal('#modal-add-' + c).hide()", cat)
    page.wait_for_selector(f"#modal-add-{cat}", state="hidden")


def type_at_end(page, cat, text):
    page.click(f"#kb-editor-{cat} .cm-content")
    page.keyboard.press("Control+End")
    page.keyboard.type(text)


def test_no_network_requests(add_page):
    open_cat(add_page, "note")
    assert add_page.aborted == []


@pytest.mark.parametrize("cat", CATEGORIES)
def test_open_each_category(add_page, cat):
    open_cat(add_page, cat)
    text = editor_text(add_page, cat)
    assert text.startswith("---\n")
    assert f"Date: {date.today().isoformat()}" in text  # noqa: DTZ011  # local date, as the page
    assert f"# {cat.capitalize()} title" in text


def test_type_and_undo(add_page):
    open_cat(add_page, "note")
    skeleton = editor_text(add_page, "note")
    type_at_end(add_page, "note", "Hello")
    assert editor_text(add_page, "note").endswith("Hello")
    add_page.keyboard.press("Control+z")
    assert editor_text(add_page, "note") == skeleton


def test_tab_inserts_four_spaces(add_page):
    open_cat(add_page, "note")
    skeleton = editor_text(add_page, "note")
    type_at_end(add_page, "note", "x")
    add_page.keyboard.press("Tab")
    assert editor_text(add_page, "note") == skeleton + "x    "


def test_enter_continues_list(add_page):
    open_cat(add_page, "note")
    type_at_end(add_page, "note", "\n- a")
    add_page.keyboard.press("Enter")
    assert editor_text(add_page, "note").endswith("\n- a\n- ")


def test_reopen_keeps_edits_on_cancel(add_page):
    open_cat(add_page, "note")
    skeleton = editor_text(add_page, "note")
    type_at_end(add_page, "note", "Hello")
    close_cat(add_page, "note")

    messages = []

    def dismiss(dialog):
        messages.append(dialog.message)
        dialog.dismiss()

    add_page.once("dialog", dismiss)
    open_cat(add_page, "note")
    assert messages == ["Discard your changes and start again?"]
    assert editor_text(add_page, "note") == skeleton + "Hello"
    add_page.click("#kb-editor-note .cm-content")
    add_page.keyboard.press("Control+z")
    assert editor_text(add_page, "note") == skeleton

    type_at_end(add_page, "note", "Again")
    close_cat(add_page, "note")
    add_page.once("dialog", lambda d: d.accept())
    open_cat(add_page, "note")
    assert editor_text(add_page, "note") == skeleton


def test_dark_background_switches_theme(add_page):
    add_page.evaluate("document.body.style.background = '#111'")
    open_cat(add_page, "note")
    assert add_page.evaluate("document.querySelector('#kb-editor-note .cm-editor').classList.contains('kb4it-cm-dark')")


def test_light_background_keeps_light_theme(add_page):
    open_cat(add_page, "note")
    assert not add_page.evaluate(
        "document.querySelector('#kb-editor-note .cm-editor').classList.contains('kb4it-cm-dark')")


def test_escape_then_tab_leaves_editor(add_page):
    open_cat(add_page, "note")
    skeleton = editor_text(add_page, "note")
    add_page.click("#kb-editor-note .cm-content")
    add_page.keyboard.press("Escape")
    add_page.keyboard.press("Tab")
    assert editor_text(add_page, "note") == skeleton
    assert not add_page.evaluate("document.querySelector('#kb-editor-note .cm-editor').contains(document.activeElement)")
    # Escape inside the editor does not close the modal.
    assert add_page.evaluate("document.getElementById('modal-add-note').classList.contains('uk-open')")

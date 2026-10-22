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


# ---- ED-05 completion, ED-06 lint, Tab indentation ----

SET_DOC = """([cat, text, anchor]) => {
    const v = KB4ITEditor.views[cat];
    v.dispatch({changes: {from: 0, to: v.state.doc.length, insert: text}, selection: {anchor: anchor}});
    v.focus();
}"""

DIAG = "c => KB4ITEditor.diagnostics(c)"


def set_doc(page, cat, text, anchor=None):
    page.evaluate(SET_DOC, [cat, text, len(text) if anchor is None else anchor])


def reasons(page, cat):
    return [d["reason"] for d in page.evaluate(DIAG, cat)]


def test_complete_property_then_value(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", "---\n\n---\n\n# T\n", 4)
    add_page.keyboard.type("Cat")
    add_page.wait_for_selector(".cm-tooltip-autocomplete")
    add_page.keyboard.press("Enter")
    assert editor_text(add_page, "note").startswith("---\nCategory: \n")
    add_page.keyboard.type("N")
    add_page.wait_for_selector(".cm-tooltip-autocomplete")
    add_page.keyboard.press("Enter")
    assert editor_text(add_page, "note").startswith("---\nCategory: Note\n")


def test_free_values_allowed(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", "---\n\n---\n\n# T\n", 4)
    add_page.keyboard.type("Category: Brandnew")
    add_page.keyboard.press("Escape")
    assert editor_text(add_page, "note").startswith("---\nCategory: Brandnew\n")
    diags = add_page.evaluate(DIAG, "note")
    assert {"reason": "new_value", "severity": "info"} in [
        {"reason": d["reason"], "severity": d["severity"]} for d in diags]


def test_missing_h1_then_fixed(add_page):
    open_cat(add_page, "note")
    assert "missing_h1_title" not in reasons(add_page, "note")
    set_doc(add_page, "note", "---\nCategory: Note\n---\n\ntext\n")
    assert "missing_h1_title" in reasons(add_page, "note")
    add_page.keyboard.press("Control+End")
    add_page.keyboard.type("# T")
    assert "missing_h1_title" not in reasons(add_page, "note")


def test_yaml_syntax_error(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", "---\nTag: [a\n---\n\n# T\n")
    assert "yaml_error" in reasons(add_page, "note")


def test_yaml_tree_error_without_duplicates(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", "---\nCategory: Note\n  : : [\n---\n\n# T\n")
    assert reasons(add_page, "note").count("yaml_error") >= 1
    set_doc(add_page, "note", "---\nTag: [a\n---\n\n# T\n")
    assert reasons(add_page, "note").count("yaml_error") == 1


def test_lint_gutter_and_underline_render(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", "---\nTag: [a\n---\n\n# T\n")
    add_page.wait_for_selector("#kb-editor-note .cm-lint-marker-error")
    add_page.wait_for_selector("#kb-editor-note .cm-lintRange-error")


def test_flow_list_completion_quotes_question_mark(add_page):
    open_cat(add_page, "note")
    keys = add_page.evaluate("KB4ITEditor.keys()")
    keys["Tag"] = keys.get("Tag", []) + [{"v": "Why?", "c": 9}]
    add_page.evaluate("k => { Object.assign(KB4ITEditor.keys(), k); }", keys)
    set_doc(add_page, "note", "---\nTag: [a, ]\n---\n\n# T\n", len("---\nTag: [a, "))
    add_page.keyboard.type("Wh")
    add_page.wait_for_selector(".cm-tooltip-autocomplete")
    add_page.keyboard.press("Enter")
    assert editor_text(add_page, "note").startswith('---\nTag: [a, "Why?"]\n')


def test_tab_indents_selected_lines(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", "---\nA: b\n---\n\n# T\n\nx\ny\n", len("---\nA: b\n---\n\n# T\n\n"))
    add_page.evaluate("""() => {
        const v = KB4ITEditor.views.note;
        v.dispatch({selection: {anchor: v.state.doc.length - 4, head: v.state.doc.length - 1}});
    }""")
    add_page.keyboard.press("Tab")
    assert editor_text(add_page, "note").endswith("\n    x\n    y\n")
    add_page.keyboard.press("Shift+Tab")
    assert editor_text(add_page, "note").endswith("\n\nx\ny\n")


@pytest.mark.parametrize("cat", CATEGORIES)
def test_skeletons_have_no_errors(add_page, cat):
    open_cat(add_page, cat)
    assert [d for d in add_page.evaluate(DIAG, cat) if d["severity"] == "error"] == []


def test_nested_yaml_error_comes_from_the_tree(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", "---\nA:\n  - b\n c: 1\n---\n\n# T\n")
    assert reasons(add_page, "note").count("yaml_error") == 1


# ---- ED-07 Properties pane ----

PANE = "#kb-props-note"
FM_END = "\n---\n"


def row(cat, key):
    return f'#kb-props-{cat} .kb-prop-row[data-key="{key}"]'


def add_prop(page, cat, name):
    page.select_option(f"#kb-props-{cat} .kb-add-prop", value=name)


def ensure_prop(page, cat, name):
    if not page.locator(row(cat, name)).count():
        add_prop(page, cat, name)


def lines(page, cat):
    return editor_text(page, cat).split("\n")


def test_add_value_from_form(add_page):
    open_cat(add_page, "note")
    ensure_prop(add_page, "note", "Tag")
    add_page.fill(row("note", "Tag") + " .kb-value-input", "sap")
    add_page.press(row("note", "Tag") + " .kb-value-input", "Enter")
    assert "Tag: sap" in lines(add_page, "note")
    assert add_page.locator(row("note", "Tag") + ' .kb-chip[data-value="sap"]').count() == 1


def test_remove_chip_changes_text(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", "---\nCategory: Note\nTag: sap, linux\n---\n\n# T\n")
    add_page.evaluate("c => KB4ITEditor.renderPane(c)", "note")
    add_page.click(row("note", "Tag") + ' .kb-chip[data-value="linux"] .kb-chip-remove')
    assert "Tag: sap" in lines(add_page, "note")
    assert "Tag: sap, linux" not in lines(add_page, "note")
    add_page.click("#kb-editor-note .cm-content")
    add_page.keyboard.press("Control+z")
    assert "Tag: sap, linux" in lines(add_page, "note")


def test_remove_property(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", "---\nCategory: Note\nTag: sap\n---\n\n# T\n")
    add_page.evaluate("c => KB4ITEditor.renderPane(c)", "note")
    add_page.click(row("note", "Tag") + " .kb-prop-remove")
    assert editor_text(add_page, "note") == "---\nCategory: Note\n---\n\n# T\n"


def test_comma_refused(add_page):
    open_cat(add_page, "note")
    ensure_prop(add_page, "note", "Tag")
    box = row("note", "Tag") + " .kb-value-input"
    add_page.fill(box, "a,b")
    msg = "A value cannot contain a comma: KB4IT splits values on commas."
    assert add_page.inner_text(row("note", "Tag") + " .kb-prop-msg") == msg
    add_page.press(box, "Enter")
    assert add_page.locator(row("note", "Tag") + " .kb-chip").count() == 0
    assert "Tag: a,b" not in editor_text(add_page, "note")


def test_new_property_name_checked(add_page):
    open_cat(add_page, "note")
    add_prop(add_page, "note", "__new__")
    add_page.fill("#kb-props-note .kb-new-prop-name", "???")
    add_page.click("#kb-props-note .kb-new-prop-add")
    assert "???" not in editor_text(add_page, "note")
    add_page.fill("#kb-props-note .kb-new-prop-name", "Owner")
    add_page.click("#kb-props-note .kb-new-prop-add")
    text = editor_text(add_page, "note")
    assert "Owner:\n---\n" in text
    assert add_page.locator(row("note", "Owner")).count() == 1


def test_complex_property_read_only(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", "---\nTags:\n  - a\n---\n\n# T\n")
    add_page.evaluate("c => KB4ITEditor.renderPane(c)", "note")
    cell = row("note", "Tags") + " .kb-prop-complex"
    assert "Edit this property in the text" in add_page.inner_text(cell)
    assert add_page.locator(row("note", "Tags") + " input").count() == 0


def test_cloud_click_adds_value(add_page):
    open_cat(add_page, "note")
    add_page.click(row("note", "Category") + " .kb-cloud-toggle")
    add_page.click(row("note", "Category") + ' .kb-wcloud-word[data-value="Procedure"]')
    assert "Category: Note, Procedure" in lines(add_page, "note")


def test_hostile_values_stay_text(add_page):
    open_cat(add_page, "note")
    ensure_prop(add_page, "note", "Tag")
    box = row("note", "Tag") + " .kb-value-input"
    add_page.fill(box, "x<")
    add_page.wait_for_selector(row("note", "Tag") + ' .kb-suggest-item[data-value="x<b>y</b>"]')
    assert "x<b>y</b>" in add_page.inner_text(row("note", "Tag") + " .kb-suggest")
    add_page.click(row("note", "Tag") + " .kb-cloud-toggle")
    assert "x<b>y</b>" in add_page.inner_text(row("note", "Tag") + " .kb-wcloud")
    add_page.press(box, "ArrowDown")
    add_page.press(box, "Enter")
    assert add_page.locator(row("note", "Tag") + ' .kb-chip[data-value="x<b>y</b>"]').count() == 1
    assert "x<b>y</b>" in add_page.inner_text(row("note", "Tag") + " .kb-chips")
    assert add_page.locator("#modal-add-note b").count() == 0


def test_undo_after_form_edit(add_page):
    open_cat(add_page, "note")
    skeleton = editor_text(add_page, "note")
    add_prop(add_page, "note", "__new__")
    add_page.fill("#kb-props-note .kb-new-prop-name", "Owner")
    add_page.click("#kb-props-note .kb-new-prop-add")
    assert editor_text(add_page, "note") != skeleton
    add_page.click("#kb-editor-note .cm-content")
    add_page.keyboard.press("Control+z")
    assert editor_text(add_page, "note") == skeleton


DUP = "---\nCategory: Note\nTag: a\nTag: b\n---\n\n# T\n"


def load_dup(page):
    open_cat(page, "note")
    set_doc(page, "note", DUP)
    page.evaluate("c => KB4ITEditor.renderPane(c)", "note")


def test_duplicate_key_add_value_edits_last(add_page):
    load_dup(add_page)
    add_page.fill(row("note", "Tag") + " .kb-value-input", "c")
    add_page.press(row("note", "Tag") + " .kb-value-input", "Enter")
    assert editor_text(add_page, "note") == DUP.replace("Tag: b", "Tag: b, c")
    assert add_page.locator(row("note", "Tag") + ' .kb-chip[data-value="c"]').count() == 1


def test_duplicate_key_remove_chip_edits_last(add_page):
    load_dup(add_page)
    add_page.click(row("note", "Tag") + ' .kb-chip[data-value="b"] .kb-chip-remove')
    assert editor_text(add_page, "note") == DUP.replace("Tag: b", "Tag:")
    assert add_page.locator(row("note", "Tag") + " .kb-chip").count() == 0


def test_duplicate_key_remove_property_edits_last(add_page):
    load_dup(add_page)
    add_page.click(row("note", "Tag") + " .kb-prop-remove")
    assert editor_text(add_page, "note") == DUP.replace("Tag: b\n", "")
    assert add_page.locator(row("note", "Tag") + ' .kb-chip[data-value="a"]').count() == 1


def test_escape_in_value_input_closes_modal_only_without_list(add_page):
    open_cat(add_page, "note")
    box = row("note", "Tag") + " .kb-value-input"
    add_page.focus(box)
    add_page.wait_for_selector(row("note", "Tag") + " .kb-suggest-item")
    add_page.press(box, "Escape")
    assert add_page.evaluate("document.getElementById('modal-add-note').classList.contains('uk-open')")
    add_page.press(box, "Escape")
    add_page.wait_for_selector("#modal-add-note", state="hidden")


def test_pane_follows_dark_page(add_page):
    add_page.evaluate("document.body.style.background = '#111'")
    open_cat(add_page, "note")
    assert add_page.evaluate("document.querySelector('#modal-add-note .kb-pane-right').classList.contains('kb-props-dark')")

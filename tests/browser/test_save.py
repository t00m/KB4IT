"""ED-10: Save, download, copy and the unsaved-changes prompts of the Add page editor."""

import pytest

from tests.browser.conftest import TOAST, dialog_open, editor_text
from tests.browser.test_add_editor import close_cat, open_cat

pytestmark = pytest.mark.browser

NO_PICKER = "delete window.showSaveFilePicker;"

PICKER_STUB = """
window.__calls = [];
window.__written = [];
window.showSaveFilePicker = async (options) => {
  window.__calls.push(options);
  if (window.__reject) { throw new DOMException('cancelled', 'AbortError'); }
  return {
    name: options.suggestedName,
    createWritable: async () => ({
      write: async (t) => { window.__written.push(t); },
      close: async () => {},
    }),
  };
};
"""



@pytest.fixture
def make_page(browser, site):
    contexts = []

    def make(script):
        context = browser.new_context(accept_downloads=True)
        context.add_init_script(script)
        context.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file://") else r.abort())
        page = context.new_page()
        page.set_default_timeout(10000)
        page.goto((site / "add.html").as_uri())
        page.wait_for_function("!!(window.KB4ITEditor && window.KB4ITEditor.open)")
        contexts.append(context)
        return page

    yield make
    for context in contexts:
        context.close()


def set_text(page, cat, text):
    page.evaluate(
        "([c, t]) => { const v = KB4ITEditor.views[c]; v.dispatch({changes: {from: 0, to: v.state.doc.length, insert: t}}); }",
        [cat, text],
    )


def label(page):
    return page.text_content("#kb-save-note").strip()


def test_download_path(make_page, tmp_path):
    page = make_page(NO_PICKER)
    open_cat(page, "note")
    set_text(page, "note", "---\nCategory: Note\n---\n# Hello World é\n\nbody")
    with page.expect_download() as info:
        page.click("#kb-save-note")
    download = info.value
    assert download.suggested_filename.endswith(".md")
    target = tmp_path / "out.md"
    download.save_as(target)
    assert target.read_bytes() == "---\nCategory: Note\n---\n# Hello World é\n\nbody\n".encode("utf-8")
    assert page.evaluate("KB4ITEditor.dirty('note')") is False


def test_download_name_is_slug(make_page):
    page = make_page(NO_PICKER)
    open_cat(page, "note")
    set_text(page, "note", "---\nCategory: Note\n---\n# My First Note\n")
    with page.expect_download() as info:
        page.click("#kb-save-note")
    assert info.value.suggested_filename == "my-first-note.md"


def test_save_writes_lf(make_page, tmp_path):
    page = make_page(NO_PICKER)
    open_cat(page, "note")
    set_text(page, "note", "---\r\nCategory: Note\r\n---\r\n# T\r\n\r\nbody\r\n")
    with page.expect_download() as info:
        page.click("#kb-save-note")
    target = tmp_path / "lf.md"
    info.value.save_as(target)
    data = target.read_bytes()
    assert b"\r" not in data
    assert data == b"---\nCategory: Note\n---\n# T\n\nbody\n"


def test_save_picker_stub(make_page):
    page = make_page(PICKER_STUB)
    open_cat(page, "note")
    set_text(page, "note", "---\nCategory: Note\n---\n# Picker Doc\n\nbody")
    assert label(page) == "Save"
    page.click("#kb-save-note")
    page.wait_for_function("window.__written.length === 1")
    options = page.evaluate("window.__calls[0]")
    assert options["suggestedName"] == "picker-doc.md"
    assert options["id"] == "kb4it-source"
    assert options["types"][0]["accept"] == {"text/markdown": [".md"]}
    assert page.evaluate("window.__written[0]") == "---\nCategory: Note\n---\n# Picker Doc\n\nbody\n"
    assert label(page) == "Save (picker-doc.md)"
    assert page.evaluate("KB4ITEditor.dirty('note')") is False
    set_text(page, "note", "---\nCategory: Note\n---\n# Picker Doc\n\nmore")
    page.click("#kb-save-note")
    page.wait_for_function("window.__written.length === 2")
    assert page.evaluate("window.__calls.length") == 1


def test_discard_drops_handle(make_page):
    page = make_page(PICKER_STUB)
    open_cat(page, "note")
    page.click("#kb-save-note")
    page.wait_for_function("window.__written.length === 1")
    assert label(page).startswith("Save (")
    set_text(page, "note", "---\nCategory: Note\n---\n# Other\n")
    close_cat(page, "note")
    page.once("dialog", lambda d: d.accept())  # the discard prompt
    page.click('[data-kb-open="note"]')
    page.wait_for_function("document.getElementById('modal-add-note').open")
    assert label(page) == "Save"


def test_picker_cancel_offers_download(make_page, tmp_path):
    page = make_page(PICKER_STUB + "window.__reject = true;")
    open_cat(page, "note")
    messages = []

    def accept(dialog):
        messages.append(dialog.message)
        dialog.accept()

    page.once("dialog", accept)
    with page.expect_download() as info:
        page.click("#kb-save-note")
    assert info.value.suggested_filename.endswith(".md")
    assert len(messages) == 1


def test_picker_cancel_declined_saves_nothing(make_page):
    page = make_page(PICKER_STUB + "window.__reject = true;")
    open_cat(page, "note")
    set_text(page, "note", editor_text(page, "note") + "x")
    page.once("dialog", lambda d: d.dismiss())
    result = page.evaluate("KB4ITEditor.save('note')")
    assert result == "cancelled"
    assert page.evaluate("KB4ITEditor.dirty('note')") is True


@pytest.mark.parametrize(
    "text,message",
    [
        ("---\nCategory: Note\n---\nno heading\n", "This document has 1 error and will not build. Save anyway?"),
        ("---\nCategory: Note\n'/': x\n---\nno heading\n", "This document has 2 errors and will not build. Save anyway?"),
    ],
)
def test_errors_confirm(make_page, text, message):
    page = make_page(NO_PICKER)
    open_cat(page, "note")
    set_text(page, "note", text)
    messages = []

    def dismiss(dialog):
        messages.append(dialog.message)
        dialog.dismiss()

    page.once("dialog", dismiss)
    assert page.evaluate("KB4ITEditor.save('note')") == "cancelled"
    assert messages == [message]


def test_errors_confirm_accepted_saves(make_page):
    page = make_page(NO_PICKER)
    open_cat(page, "note")
    set_text(page, "note", "---\nCategory: Note\n---\nno heading\n")
    page.once("dialog", lambda d: d.accept())
    with page.expect_download():
        page.click("#kb-save-note")


def test_unsaved_changes_prompt(make_page):
    page = make_page(NO_PICKER)
    open_cat(page, "note")
    set_text(page, "note", "---\nCategory: Note\n---\n# Changed\n")
    messages = []

    def dismiss(dialog):
        messages.append(dialog.message)
        dialog.dismiss()

    page.once("dialog", dismiss)
    page.click('[data-kb-close="note"]')
    page.wait_for_timeout(500)
    assert len(messages) == 1
    assert dialog_open(page, "note")
    # a save marks clean: closing does not ask
    with page.expect_download():
        page.click("#kb-save-note")
    page.once("dialog", lambda d: messages.append("unexpected"))
    page.click('[data-kb-close="note"]')
    page.wait_for_function("!document.getElementById('modal-add-note').open")
    assert len(messages) == 1


def test_close_button_asks_and_accepts(make_page):
    page = make_page(NO_PICKER)
    open_cat(page, "note")
    set_text(page, "note", "---\nCategory: Note\n---\n# Changed\n")
    page.once("dialog", lambda d: d.accept())
    page.click('[data-kb-close="note"]')
    page.wait_for_function("!document.getElementById('modal-add-note').open")


def test_beforeunload_while_dirty(make_page):
    page = make_page(NO_PICKER)
    probe = "() => { const e = new Event('beforeunload', {cancelable: true}); window.dispatchEvent(e); return e.defaultPrevented; }"
    assert page.evaluate(probe) is False
    open_cat(page, "note")
    assert page.evaluate(probe) is False
    set_text(page, "note", "---\nCategory: Note\n---\n# Changed\n")
    assert page.evaluate(probe) is True
    with page.expect_download():
        page.click("#kb-save-note")
    assert page.evaluate(probe) is False


def test_copy_writes_normalised_text(make_page):
    page = make_page(
        NO_PICKER + "window.__copied = [];"
        "Object.defineProperty(navigator, 'clipboard', {value: {writeText: async (t) => { window.__copied.push(t); }}});"
    )
    open_cat(page, "note")
    set_text(page, "note", "---\r\nCategory: Note\r\n---\r\n# T\r\n")
    page.click('[data-kb-copy="note"]')
    page.wait_for_function("window.__copied.length === 1")
    assert page.evaluate("window.__copied[0]") == "---\nCategory: Note\n---\n# T\n"


def test_page_note_rewritten(make_page):
    page = make_page(NO_PICKER)
    note = page.text_content(".kb-add-note")
    assert "cannot create files for you" not in note
    flat = " ".join(note.split())
    assert "saves or downloads" in flat
    assert "source" in flat and "rebuild" in flat


FAIL_STUB = """
window.__written = [];
window.__aborted = 0;
window.__mode = 'create';
window.__fail = 'create';
window.showSaveFilePicker = async (options) => ({
  name: options.suggestedName,
  createWritable: async () => {
    if (window.__fail === 'create') { throw new DOMException('denied', 'NotAllowedError'); }
    return {
      write: async (t) => {
        if (window.__fail === 'write') { throw new DOMException('disk', 'NotReadableError'); }
        window.__written.push(t);
      },
      close: async () => {},
      abort: async () => { window.__aborted += 1; },
    };
  },
});
"""

NOTIFY = TOAST


@pytest.mark.parametrize("mode", ["create", "write"])
def test_write_failure_first_save(make_page, tmp_path, mode):
    page = make_page(FAIL_STUB + f"window.__fail = '{mode}';")
    open_cat(page, "note")
    set_text(page, "note", "---\r\nCategory: Note\r\n---\r\n# F\r\n")
    messages = []

    def dismiss(dialog):
        messages.append(dialog.message)
        dialog.dismiss()

    page.once("dialog", dismiss)
    assert page.evaluate("KB4ITEditor.save('note')") == "cancelled"
    assert messages == ["The file was not saved. Download it instead?"]
    page.wait_for_selector(NOTIFY)
    assert "Saving failed" in page.text_content(NOTIFY)
    assert page.evaluate("KB4ITEditor.dirty('note')") is True
    assert label(page) == "Save"
    if mode == "write":
        assert page.evaluate("window.__aborted") == 1
    page.once("dialog", lambda d: d.accept())
    with page.expect_download() as info:
        page.click("#kb-save-note")
    target = tmp_path / "f.md"
    info.value.save_as(target)
    assert target.read_bytes() == b"---\nCategory: Note\n---\n# F\n"
    assert page.evaluate("KB4ITEditor.dirty('note')") is False


@pytest.mark.parametrize("mode", ["create", "write"])
def test_write_failure_kept_handle(make_page, mode):
    page = make_page(FAIL_STUB + "window.__fail = 'none';")
    open_cat(page, "note")
    page.click("#kb-save-note")
    page.wait_for_function("window.__written.length === 1")
    assert label(page).startswith("Save (")
    set_text(page, "note", editor_text(page, "note") + "more")
    page.evaluate(f"window.__fail = '{mode}'")
    messages = []

    def dismiss(dialog):
        messages.append(dialog.message)
        dialog.dismiss()

    page.once("dialog", dismiss)
    assert page.evaluate("KB4ITEditor.save('note')") == "cancelled"
    assert messages == ["The file was not saved. Download it instead?"]
    page.wait_for_selector(NOTIFY)
    assert page.evaluate("KB4ITEditor.dirty('note')") is True
    assert label(page) == "Save"


def test_second_save_while_pending_is_ignored(make_page):
    page = make_page(
        "window.__n = 0; window.showSaveFilePicker = (o) => { window.__n += 1;"
        " return new Promise(r => setTimeout(() => r({name: 'a.md', createWritable: async () => ({"
        "write: async () => {}, close: async () => {}})}), 300)); };"
    )
    open_cat(page, "note")
    result = page.evaluate("Promise.all([KB4ITEditor.save('note'), KB4ITEditor.save('note')])")
    assert result == ["saved", "saved"]
    assert page.evaluate("window.__n") == 1


def test_edit_during_write_stays_dirty(make_page):
    page = make_page(
        "window.showSaveFilePicker = async (o) => ({name: 'a.md', createWritable: async () => ({"
        "write: async () => { const v = KB4ITEditor.views.note;"
        " v.dispatch({changes: {from: v.state.doc.length, insert: 'late'}}); }, close: async () => {}})});"
    )
    open_cat(page, "note")
    assert page.evaluate("KB4ITEditor.save('note')") == "saved"
    assert page.evaluate("KB4ITEditor.dirty('note')") is True

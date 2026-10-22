"""ED-09: the toolbar of the Add page editor, driven in Chromium."""

import pytest

from tests.browser.conftest import editor_text
from tests.browser.test_add_editor import open_cat

pytestmark = pytest.mark.browser

FM = "---\nCategory: Note\n---\n"
HEAD = FM + "# T\n\n"
EMPTY = HEAD  # cursor at the end, on a blank line
WORD = HEAD + "word\n"  # "word" selected
TABLE = "| Column 1 | Column 2 | Column 3 |\n| --- | --- | --- |\n|  |  |  |\n|  |  |  |"
ADMON = '!!! {kind} "Title"\n    {body}'
NOTE_BODY = "Text of the note, indented by four spaces."

# action: (text with an empty selection, selected text then, text with "word" selected, selected text then)
CASES = {
    "bold": ("**text**", "text", "**word**", "word"),
    "italic": ("*text*", "text", "*word*", "word"),
    "code": ("`code`", "code", "`word`", "word"),
    "link": ("[text](url)", "text", "[word](url)", "url"),
    "h2": ("## ", "", "## word", "word"),
    "h3": ("### ", "", "### word", "word"),
    "h4": ("#### ", "", "#### word", "word"),
    "ul": ("- ", "", "- word", "word"),
    "ol": ("1. ", "", "1. word", "word"),
    "task": ("- [ ] ", "", "- [ ] word", "word"),
    "quote": ("> ", "", "> word", "word"),
    "codeblock": ("```\n\n```", "", "```\nword\n```", "word"),
    "hr": ("---\n", "", None, None),
    "table": (TABLE, "", None, None),
    "image": ("![alt](path)", "path", "![word](path)", "path"),
    "note": (ADMON.format(kind="note", body=NOTE_BODY), NOTE_BODY, ADMON.format(kind="note", body="word"), "word"),
    "tip": (ADMON.format(kind="tip", body=NOTE_BODY), NOTE_BODY, ADMON.format(kind="tip", body="word"), "word"),
    "warning": (
        ADMON.format(kind="warning", body=NOTE_BODY), NOTE_BODY, ADMON.format(kind="warning", body="word"), "word",
    ),
    "danger": (
        ADMON.format(kind="danger", body=NOTE_BODY), NOTE_BODY, ADMON.format(kind="danger", body="word"), "word",
    ),
    "mermaid": ("```mermaid\ngraph TD\n    A --> B\n```", "", None, None),
    "math": ("$x$", "x", "$word$", "word"),
    "mathblock": ("$$\nx\n$$", "x", "$$\nword\n$$", "word"),
}
ACTIONS = list(CASES)


def set_doc(page, cat, doc, anchor, head=None):
    page.evaluate(
        """([c, doc, a, h]) => {
            const v = KB4ITEditor.views[c];
            v.dispatch({changes: {from: 0, to: v.state.doc.length, insert: doc}, selection: {anchor: a, head: h}});
            v.focus();
        }""",
        [cat, doc, anchor, anchor if head is None else head],
    )


def selected(page, cat):
    return page.evaluate(
        "c => { const s = KB4ITEditor.views[c].state; const r = s.selection.main; return s.sliceDoc(r.from, r.to); }",
        cat,
    )


def click(page, cat, action):
    page.click(f"#kb-toolbar-{cat} [data-action={action}]")


def test_toolbar_has_every_button(add_page):
    open_cat(add_page, "note")
    found = add_page.eval_on_selector_all(
        "#kb-toolbar-note [data-action]", "els => els.map(e => e.getAttribute('data-action'))"
    )
    assert sorted(found) == sorted(ACTIONS)
    assert sorted(add_page.evaluate("Object.keys(KB4ITEditor.ACTIONS)")) == sorted(ACTIONS)


@pytest.mark.parametrize("action", ACTIONS)
def test_toolbar_action_empty(add_page, action):
    open_cat(add_page, "note")
    set_doc(add_page, "note", EMPTY, len(EMPTY))
    click(add_page, "note", action)
    expected, sel, _, _ = CASES[action]
    assert editor_text(add_page, "note") == EMPTY + expected
    assert selected(add_page, "note") == sel


@pytest.mark.parametrize("action", ACTIONS)
def test_toolbar_action_selection(add_page, action):
    open_cat(add_page, "note")
    set_doc(add_page, "note", WORD, len(HEAD), len(HEAD) + 4)
    click(add_page, "note", action)
    _, _, expected, sel = CASES[action]
    if expected is None:  # block inserts go after the line of the selection
        expected = {"hr": "word\n\n---\n", "table": "word\n\n" + TABLE + "\n",
                    "mermaid": "word\n\n```mermaid\ngraph TD\n    A --> B\n```\n"}[action]
        sel = None
    assert editor_text(add_page, "note") == HEAD + expected + ("" if expected.endswith("\n") else "\n")
    if sel is not None:
        assert selected(add_page, "note") == sel


def test_action_is_one_undo_step(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", WORD, len(HEAD), len(HEAD) + 4)
    click(add_page, "note", "bold")
    assert editor_text(add_page, "note") == HEAD + "**word**\n"
    add_page.keyboard.press("Control+z")
    assert editor_text(add_page, "note") == WORD


def test_multiple_lines_and_selections(add_page):
    open_cat(add_page, "note")
    doc = HEAD + "a\nb\n"
    set_doc(add_page, "note", doc, len(HEAD), len(doc) - 1)
    click(add_page, "note", "ol")
    assert editor_text(add_page, "note") == HEAD + "1. a\n2. b\n"
    # Two cursors on the same line prefix it once; two words are both wrapped.
    add_page.evaluate(
        """() => {
            const v = KB4ITEditor.views.note;
            const n = v.state.doc.length - 1;
            v.dispatch({selection: v.state.selection.constructor.create([
                v.state.selection.constructor.range(n - 6, n - 5), v.state.selection.constructor.range(n - 1, n)], 0)});
        }"""
    )
    click(add_page, "note", "bold")
    assert editor_text(add_page, "note") == HEAD + "1. **a**\n2. **b**\n"
    set_doc(add_page, "note", HEAD + "ab\n", len(HEAD))
    add_page.evaluate(
        """() => {
            const v = KB4ITEditor.views.note;
            const S = v.state.selection.constructor;
            const p = v.state.doc.length - 3;
            v.dispatch({selection: S.create([S.cursor(p), S.cursor(p + 1)], 0)});
        }"""
    )
    click(add_page, "note", "h2")
    assert editor_text(add_page, "note") == HEAD + "## ab\n"


@pytest.mark.parametrize(
    ("keys", "expected"),
    [("Control+b", "**word**"), ("Control+i", "*word*"), ("Control+e", "`word`"), ("Control+k", "[word](url)")],
)
def test_shortcuts(add_page, keys, expected):
    open_cat(add_page, "note")
    set_doc(add_page, "note", WORD, len(HEAD), len(HEAD) + 4)
    add_page.keyboard.press(keys)
    assert editor_text(add_page, "note") == HEAD + expected + "\n"


def test_buttons_carry_titles_with_shortcuts(add_page):
    open_cat(add_page, "note")
    title = add_page.get_attribute("#kb-toolbar-note [data-action=bold]", "title")
    assert "Ctrl+B" in title


def test_disabled_in_frontmatter(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", WORD, 6)  # inside "Category: Note"
    add_page.wait_for_selector("#kb-toolbar-note [data-action=bold][disabled]")
    for action in ACTIONS:
        assert add_page.is_disabled(f"#kb-toolbar-note [data-action={action}]")
    add_page.keyboard.press("Control+b")
    add_page.keyboard.press("Control+i")
    assert editor_text(add_page, "note") == WORD
    set_doc(add_page, "note", WORD, len(HEAD))
    add_page.wait_for_selector("#kb-toolbar-note [data-action=bold]:not([disabled])")
    assert not add_page.is_disabled("#kb-toolbar-note [data-action=hr]")


def test_no_network_requests(add_page):
    open_cat(add_page, "note")
    set_doc(add_page, "note", EMPTY, len(EMPTY))
    click(add_page, "note", "bold")
    assert add_page.aborted == []

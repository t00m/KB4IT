"""ED-06 and ED-08: the frontmatter parser, quoting and name rules, run with node."""

import json
from pathlib import Path

import pytest

from tests.js.nodejs import NODE, run_node

pytestmark = pytest.mark.skipif(NODE is None, reason="node not installed")

TABLE = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "editor" / "names.json").read_text(encoding="utf-8")
)


def call(name, *args):
    return run_node([(name, list(args))])[0]


def doc(*lines):
    return "---\n" + "\n".join(lines) + "\n---\n\n# Title\n"


def props(text):
    return {p["key"]: p for p in call("parse", text)["props"]}


def test_js_matches_shared_table():
    calls = [("validFilename", [v]) for v, _ in TABLE["valid_filename"]]
    calls += [("slugify", [v]) for v, _ in TABLE["slugify"]]
    got = run_node(calls)
    expected = [e for _, e in TABLE["valid_filename"]] + [e for _, e in TABLE["slugify"]]
    inputs = [v for v, _ in TABLE["valid_filename"]] + [v for v, _ in TABLE["slugify"]]
    for value, want, have in zip(inputs, expected, got):
        assert have == want, value


LINE_FORMS = [
    ("Key:", []),
    ("Key: a", ["a"]),
    ("Key: a, b", ["a", "b"]),
    ("Key: [a, b]", ["a", "b"]),
    ('Key: "a: b"', ["a: b"]),
    ("Key: 'a: b'", ["a: b"]),
]


@pytest.mark.parametrize("line,values", LINE_FORMS)
def test_parse_line_forms(line, values):
    result = call("parse", doc(line))
    assert result["ok"] is True and result["reason"] is None
    prop = result["props"][0]
    assert prop["key"] == "Key" and prop["values"] == values and prop["complex"] is False


@pytest.mark.parametrize(
    "block",
    ["Tags:\n  - a\n  - b", "Text: |\n  x", "Map:\n  k: v", "Ref: &a x"],
)
def test_parse_complex(block):
    result = call("parse", doc(block, "Next: z"))
    first, second = result["props"]
    assert first["complex"] is True and first["values"] == []
    assert second["key"] == "Next" and second["values"] == ["z"] and second["complex"] is False


def test_complex_range_covers_continuation_lines():
    text = doc("Tags:", "  - a", "  - b", "Next: z")
    first = call("parse", text)["props"][0]
    assert text[first["from"]:first["to"]] == "Tags:\n  - a\n  - b"


def test_blank_and_comment_lines_are_skipped():
    result = call("parse", doc("# note", "", "Key: a"))
    assert [p["key"] for p in result["props"]] == ["Key"]
    assert result["props"][0]["line"] == 3


def test_quoted_comma_splits():
    assert call("parse", doc('Tag: "a, b"'))["props"][0]["values"] == ["a", "b"]


def test_crlf_input():
    lines = ["Key: a, b", "Other: [x, y]", 'Q: "a: b"', "Tags:", "  - a", "Last:"]
    lf = call("parse", doc(*lines))
    crlf = call("parse", doc(*lines).replace("\n", "\r\n"))
    assert [(p["key"], p["values"], p["complex"]) for p in crlf["props"]] == [
        (p["key"], p["values"], p["complex"]) for p in lf["props"]
    ]


@pytest.mark.parametrize(
    "text,reason",
    [
        ("# Title\n", "missing_frontmatter"),
        ("---\nKey: a\n", "missing_frontmatter_close"),
    ],
)
def test_bounds_follow_the_build(text, reason):
    result = call("parse", text)
    assert result["ok"] is False and result["reason"] == reason and result["props"] == []


def test_bom_is_skipped_like_the_build():
    text = "\ufeff---\nKey: a\n---\n\n# T\n"
    result = call("parse", text)
    assert result["ok"] is True and result["props"][0]["values"] == ["a"]
    prop = result["props"][0]
    assert text[prop["from"]:prop["to"]] == "Key: a"
    change = call("setValues", text, "Key", ["b"])
    assert text[:change["from"]] + change["insert"] + text[change["to"]:] == text.replace("Key: a", "Key: b")
    assert call("bounds", "\ufeff# T")["open"] is False


def test_bounds_offsets():
    text = "---\nKey: a\n---\n\n# T\n"
    got = call("bounds", text)
    assert got["open"] is True and got["close"] == text.index("\n---", 3)
    assert text[got["start"]:got["end"]] == "Key: a\n"
    assert call("bounds", "no")["open"] is False


QUOTED = ["[x", "]", "{", "}", "&a", "*a", "!a", "|a", ">a", "'a", '"a', "%a", "@a", "`a", "- a", "a: b",
          "a #b", "true", "False", "yes", "NO", "null", "~", "12", "1.5", "-3"]
PLAIN = ["sap", "a-b", "a#b", "SAP Basis", "2026-10-22"]


@pytest.mark.parametrize("value", QUOTED)
def test_quote_rule_quotes(value):
    want = '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    assert call("quote", value) == want


@pytest.mark.parametrize("value", PLAIN)
def test_quote_rule_keeps(value):
    assert call("quote", value) == value


def test_quote_escapes_backslash_and_quote():
    assert call("quote", '"a\\b') == '"\\"a\\\\b"'


ROUND_TRIP = [
    ["a"], ["a", "b"], [], ["a: b"], ["[x"], ["true", "SAP Basis"], ['q"q'], ["back\\slash"], ["12"], ["- a"], ["a[1]", "b: c"], ["x]", "y"],
]


@pytest.mark.parametrize("line,_values", LINE_FORMS)
@pytest.mark.parametrize("new", ROUND_TRIP)
def test_set_values_round_trip(line, _values, new):
    text = doc("Before: x", line, "After: [y, z]")
    change = call("setValues", text, "Key", new)
    out = text[:change["from"]] + change["insert"] + text[change["to"]:]
    assert props(out)["Key"]["values"] == new
    assert props(out)["Key"]["complex"] is False
    before = [ln for ln in text.split("\n") if ln != line]
    after = [ln for ln in out.split("\n") if not ln.startswith("Key:")]
    assert before == after


def test_set_values_writes_plain_lines():
    text = doc("Key: old")
    assert call("setValues", text, "Key", ["a", "b: c"])["insert"] == 'Key: [a, "b: c"]'
    assert call("setValues", text, "Key", [])["insert"] == "Key:"


def test_set_values_replaces_complex_range():
    text = doc("Tags:", "  - a", "  - b", "Next: z")
    change = call("setValues", text, "Tags", ["a", "b"])
    out = text[:change["from"]] + change["insert"] + text[change["to"]:]
    assert out == doc("Tags: a, b", "Next: z")


def test_set_values_new_key_before_close():
    text = doc("Key: a")
    change = call("setValues", text, "Tag", ["x", "y"])
    assert change["insert"] == "Tag: x, y\n" and change["from"] == change["to"]
    out = text[:change["from"]] + change["insert"] + text[change["to"]:]
    assert out == doc("Key: a", "Tag: x, y")


def test_set_values_new_key_in_empty_frontmatter():
    text = "---\n---\n\n# T\n"
    change = call("setValues", text, "Tag", ["x"])
    assert text[:change["from"]] + change["insert"] + text[change["to"]:] == "---\nTag: x\n---\n\n# T\n"


def test_set_values_remove():
    text = doc("A: 1", "Key: a", "B: 2")
    change = call("setValues", text, "Key", None)
    assert text[:change["from"]] + change["insert"] + text[change["to"]:] == doc("A: 1", "B: 2")


def test_set_values_targets_the_last_duplicate():
    text = doc("Tag: a", "Tag: b")
    change = call("setValues", text, "Tag", ["b", "c"])
    assert text[:change["from"]] + change["insert"] + text[change["to"]:] == doc("Tag: a", "Tag: b, c")
    change = call("setValues", text, "Tag", None)
    assert text[:change["from"]] + change["insert"] + text[change["to"]:] == doc("Tag: a")


def test_set_values_keeps_crlf():
    text = doc("A: 1", "Key: a").replace("\n", "\r\n")
    change = call("setValues", text, "Key", ["b"])
    out = text[:change["from"]] + change["insert"] + text[change["to"]:]
    assert out == doc("A: 1", "Key: b").replace("\n", "\r\n")
    change = call("setValues", text, "New", ["c"])
    assert change["insert"] == "New: c\r\n"


def test_first_heading_skips_code():
    body = "```sh\n# in fence\n```\n\n~~~\n# in tilde\n~~~\n\n    # indented\n\n# Real  \n"
    assert call("firstHeading", body) == {"title": "Real", "line": 10}
    assert call("firstHeading", "text\n") is None
    assert call("firstHeading", "#nospace\n") is None


def test_file_name_fallback():
    assert call("fileName", "---\nA: b\n---\n\n# 日本語\n", "note") == "note.md"
    assert call("fileName", "---\nA: b\n---\n\n# Disk full on SAP\n", "note") == "disk-full-on-sap.md"
    assert call("fileName", "---\nA: b\n---\n\nno heading\n", "note") == "note.md"
    assert call("fileName", "# In a fence-less doc\n", "note") == "in-a-fence-less-doc.md"


def _build_values(raw):
    """What the build makes of `K: <raw>`, or None when the property must be complex."""
    import yaml

    value = yaml.safe_load("K: " + raw)["K"]
    if value is None:
        return []
    if isinstance(value, list):
        return [str(i).strip() for i in value if i is not None]
    if isinstance(value, str) and "," in value:
        return [i.strip() for i in value.split(",")]
    return [str(value).strip()]


SIMPLE_SCALARS = [
    "null", "Null", "NULL", "~", "true", "True", "TRUE", "false", "False", "yes", "Yes", "YES", "no", "No", "NO",
    "on", "On", "ON", "off", "Off", "OFF", "0", "7", "-3", "42", "2026-10-22", "e5", "word", "[null, a]",
    "[true, No, x]", "[~, 5]", "a, b", "1, 2", "[1, 2]",
]
NUMERIC_SCALARS = ["1.50", "1.5", "010", "0x1F", "1e3", ".5", "+1", "1_000", "-0", "0o7", "[1.5, a]", "1:30",
                   ".inf", "2026-10-22 10:00:00"]


@pytest.mark.parametrize("raw", SIMPLE_SCALARS)
def test_plain_scalars_read_like_the_build(raw):
    prop = call("parse", doc("K: " + raw))["props"][0]
    assert prop["complex"] is False
    assert prop["values"] == _build_values(raw)


@pytest.mark.parametrize("raw", NUMERIC_SCALARS)
def test_non_canonical_numbers_are_complex(raw):
    prop = call("parse", doc("K: " + raw))["props"][0]
    assert prop["complex"] is True and prop["values"] == []


@pytest.mark.parametrize("raw,expected", [
    ('"caf\u00e9"', ["caf\u00e9"]),
    ('"caf\\u00e9"', ["caf\u00e9"]),
    ('"a\\u0041"', ["aA"]),
    ('"a\\"b"', ['a"b']),
    ('"a\\\\b"', ["a\\b"]),
    ('"a\\x41"', None),
    ('"a\\/b"', None),
    ('"a\\u00zz"', None),
])
def test_double_quoted_escapes(raw, expected):
    prop = call("parse", doc("K: " + raw))["props"][0]
    if expected is None:
        assert prop["complex"] is True and prop["values"] == []
    else:
        assert prop["complex"] is False and prop["values"] == expected
        assert prop["values"] == _build_values(raw)


KEYS = {
    "Category": [{"v": "Note", "c": 9}, {"v": "Howto", "c": 5}, {"v": "Bad Idea: x", "c": 1}],
    "Tag": [{"v": "a", "c": 4}, {"v": "b", "c": 2}],
    "Title": [{"v": "x", "c": 1}],
}
H1 = "\n# Heading\n"


def lint(text, keys=None):
    return call("lint", text, KEYS if keys is None else keys)


def reasons(text, keys=None):
    return [(d["reason"], d["severity"]) for d in lint(text, keys)]


LINT_CASES = [
    ("# Heading\n", "missing_frontmatter", "error"),
    ("---\nCategory: Note\n# Heading\n", "missing_frontmatter_close", "error"),
    ("---\nCategory: [a\n---" + H1, "yaml_error", "error"),
    ('---\nCategory: "a\n---' + H1, "yaml_error", "error"),
    ("---\nCategory: a: b\n---" + H1, "yaml_error", "error"),
    ("---\nCategory: - a\n---" + H1, "yaml_error", "error"),
    ("---\nCategory: Note\nstray\n---" + H1, "yaml_error", "error"),
    ("---\njust text\n---" + H1, "invalid_frontmatter", "error"),
    ("---\n- a\n---" + H1, "invalid_frontmatter", "error"),
    ("---\nCategory: Note\n---\n\nno heading\n", "missing_h1_title", "error"),
    ("---\nTitle: x\nCategory: Note\n---" + H1, "title_in_frontmatter_ignored", "warning"),
    ("---\n...: x\n---" + H1, "bad_property_name", "error"),
    ("---\nCategory: ...\n---" + H1, "bad_property_value", "error"),
    ("---\nCategory: Note, ???\n---" + H1, "bad_property_value", "error"),
    ("---\nSystem: s4\n---" + H1, "new_property", "info"),
    ("---\nCategory: Brand New\n---" + H1, "new_value", "info"),
    ("---\nTag: a\nTag: b\n---" + H1, "duplicate_property", "warning"),
]


@pytest.mark.parametrize("text,reason,severity", LINT_CASES)
def test_lint_reasons(text, reason, severity):
    assert reasons(text) == [(reason, severity)]


def test_lint_clean_document():
    text = "---\nCategory: Note\nTag: a, b\n---\n\n# Heading\n\ntext\n"
    assert lint(text) == []
    assert lint("---\n# comment\n\nCategory: Howto\nTag: [a, b]\n---" + H1) == []
    assert lint("---\n---" + H1) == []


def test_lint_positions():
    text = "---\nCategory: Note\nSystem: s4\n---\n\n# Heading\n"
    diag = lint(text)[0]
    assert text[diag["from"]:diag["to"]] == "System: s4"
    assert lint("# Heading\n")[0]["from"] == 0 and lint("# Heading\n")[0]["to"] == 0
    dup = lint("---\nTag: a\nTag: b\n---" + H1)[0]
    assert "---\nTag: a\nTag: b\n---"[dup["from"]:dup["to"]] == "Tag: b"


def test_lint_h1_rule_matches_python():
    text = "---\nCategory: Note\n---\n\n```\n# x\n```\n"
    assert reasons(text) == [("missing_h1_title", "error")]
    assert reasons("---\nCategory: Note\n---\n\n    # x\n") == [("missing_h1_title", "error")]


def test_lint_title_key_both_cases():
    for key in ("Title", "title"):
        assert reasons("---\n" + key + ": x\n---" + H1) == [("title_in_frontmatter_ignored", "warning")]


def test_lint_skips_complex_values_and_bom():
    assert lint("---\nTag: 1.50\n---" + H1) == []
    assert lint("\ufeff---\nTag: a\n---" + H1) == []
    assert reasons("\ufeff---\nTag: a\n---\n\nnone\n") == [("missing_h1_title", "error")]


def test_lint_without_known_keys_reports_new():
    assert reasons("---\nTag: a\n---" + H1, {}) == [("new_property", "info")]


def complete(text, pos=None, keys=None):
    return call("complete", text, len(text) if pos is None else pos, KEYS if keys is None else keys)


def test_complete_property_names():
    result = complete("---\nCat")
    assert result["from"] == 4
    options = {o["label"]: o for o in result["options"]}
    assert options["Category"]["insert"] == "Category: "
    assert options["Category"]["detail"] == "3 values"
    assert options["Tag"]["detail"] == "2 values"
    assert "Title" not in options
    present = complete("---\nCategory: Note\nT\n---\n# x\n", 20)
    assert [o["label"] for o in present["options"]] == ["Tag"]


def test_complete_values_by_use():
    result = complete("---\nCategory: ")
    assert [o["label"] for o in result["options"]] == ["Note", "Howto", "Bad Idea: x"]
    assert result["options"][0]["detail"] == "9 documents"
    assert result["options"][2]["insert"] == '"Bad Idea: x"'
    assert result["from"] == len("---\nCategory: ")
    tags = complete("---\nTag: a, ")
    assert [o["label"] for o in tags["options"]] == ["b"]
    assert tags["from"] == len("---\nTag: a, ")
    partial = complete("---\nTag: a, b\n---\n# x\n", len("---\nTag: a, b"))
    assert partial["from"] == len("---\nTag: a, ") and [o["label"] for o in partial["options"]] == ["b"]
    flow = complete("---\nTag: [a, \n---\n# x\n", len("---\nTag: [a, "))
    assert [o["label"] for o in flow["options"]] == ["b"]


def test_complete_outside_frontmatter():
    text = "---\nTag: a\n---\n\n# Heading\nbody\n"
    assert complete(text, len(text) - 2) is None
    assert complete("---\nUnknown: ") is None
    assert complete("# Heading") is None
    assert complete("---\nTag: a\n  indented") is None
    assert complete("---\nTag: a\n---\n", 2) is None


NEEDY_VALUES = [
    "12:30", "0x1F", "0o7", "1_000", ".inf", ".NaN", "#x", "=", "<<", "yes", "No", "null", "~", "1.5", "7",
    "2026-10-22", "2026-1-2", "a #b", "Bad Idea: x", "- x", "@x", "`x", "*x", "&x", "!x", "%x", "? x", "?",
    "[x]", "{x}", "a\tb", "> x", "| x", 'say "hi"', "it's", "tail:", "plain", "two words",
    "a?", "?a", "Why?", "a:b", "a#b", "a[1", "a]b", "a}b", "a{b",
]


def _apply(text, pos, option, result):
    start = option.get("from", result["from"])
    end = option.get("to", pos)
    return text[:start] + option["insert"] + text[end:]


def _doc_values(doc_text):
    import yaml

    fm = doc_text.split("\n---", 1)[0][3:]
    value = yaml.safe_load(fm)["Tag"]
    if value is None:
        return []
    if isinstance(value, list):
        return [str(i).strip() for i in value if i is not None]
    if isinstance(value, str) and "," in value:
        return [i.strip() for i in value.split(",")]
    return [str(value).strip()]


@pytest.mark.parametrize("value", NEEDY_VALUES)
def test_completed_values_read_back_like_the_build(value):
    keys = {"Tag": [{"v": value, "c": 1}, {"v": "a", "c": 0}], "Other": [{"v": value, "c": 1}]}
    tail = "\n---\n\n# H\n"
    first = "---\nTag: "
    result = call("complete", first + tail, len(first), keys)
    option = next(o for o in result["options"] if o["label"] == value)
    assert _doc_values(_apply(first + tail, len(first), option, result)) == [value]
    later = "---\nTag: a, "
    result = call("complete", later + tail, len(later), keys)
    option = next(o for o in result["options"] if o["label"] == value)
    assert _doc_values(_apply(later + tail, len(later), option, result)) == ["a", value]
    middle = "---\nTag: , b"
    result = call("complete", middle + tail, len("---\nTag: "), keys)
    option = next(o for o in result["options"] if o["label"] == value)
    assert _doc_values(_apply(middle + tail, len("---\nTag: "), option, result)) == [value, "b"]
    flow = "---\nTag: [a, "
    result = call("complete", flow + "]" + tail, len(flow), keys)
    option = next(o for o in result["options"] if o["label"] == value)
    assert _doc_values(_apply(flow + "]" + tail, len(flow), option, result)) == ["a", value]


def test_plain_list_is_rewritten_as_flow_list():
    text = "---\nTag: a, \n---\n\n# H\n"
    keys = {"Tag": [{"v": "Bad Idea: x", "c": 1}, {"v": "b", "c": 0}]}
    result = call("complete", text, len("---\nTag: a, "), keys)
    options = {o["label"]: o for o in result["options"]}
    assert options["Bad Idea: x"]["insert"] == '[a, "Bad Idea: x"]'
    assert options["Bad Idea: x"]["from"] == len("---\nTag: ")
    assert options["Bad Idea: x"]["to"] == len("---\nTag: a, ")
    assert "from" not in options["b"]


AGREE_CASES = [
    ("K: a", False), ("K: [a, b]", False), ('K: "a b"', False), ("K: 'a b'", False), ("K:", False),
    ("K: a # note", False), ("K: >", False), ("K: !!str x", False), ("K: &a x", False), ("K: ?a", False),
    ("K: a\n b", False), ("K: a\n - b", False), ("K:\n - a\n - b", False), ('K: "a\\x41"', False),
    ('K: "a\\/b"', False), ('K: "tab\there"', False), ("K: 'a\\q'", False),
    ("K: [a", True), ('K: "a', True), ("K: a: b", True), ("K: - a", True), ("K: *a", True),
    ("K: !t x", True), ("K: %x", True), ("K: ? a", True), ("K: > x", True), ("K: | x", True),
    ('K: "a\\q"', True), ("K: a\tb", True), ("K:\tx", True), ("K: a\n b: c", True), ("K: =", True),
    ("K: <<", True), ("K: @x", True), ("K: [a, b] x", True), ('K: ["a\\q"]', True), ("K: ,a", True),
    ("K: a\nstray", True), ("K: ?", True),
]


@pytest.mark.parametrize("fm,rejected", AGREE_CASES)
def test_lint_agrees_with_the_build(tmp_path, fm, rejected):
    from kb4it.core.documents import get_markdown_attributes

    text = "---\n" + fm + "\n---\n\n# Heading\n"
    path = tmp_path / "doc.md"
    path.write_text(text, encoding="utf-8")
    _keys, ok, _reason = get_markdown_attributes(str(path))
    assert (not ok) is rejected
    has_error = any(d["severity"] == "error" for d in lint(text, {}))
    assert has_error is rejected


def test_lint_repeated_key_checks_only_the_last():
    text = "---\nTag: ...\nTag: a\n---\n\n# Heading\n"
    assert reasons(text) == [("duplicate_property", "warning")]
    text = "---\nTag: Brand\nTag: a\n---\n\n# Heading\n"
    assert reasons(text) == [("duplicate_property", "warning")]
    text = "---\nTag: a\nTag: ...\n---\n\n# Heading\n"
    assert reasons(text) == [("duplicate_property", "warning"), ("bad_property_value", "error")]

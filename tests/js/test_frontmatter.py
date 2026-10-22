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
        ("﻿---\nKey: a\n---\n", "missing_frontmatter"),
    ],
)
def test_bounds_follow_the_build(text, reason):
    result = call("parse", text)
    assert result["ok"] is False and result["reason"] == reason and result["props"] == []


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

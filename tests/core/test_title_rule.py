"""The title is the first level-1 heading outside code blocks (OC-03)."""

import pytest

from kb4it.core.util import (
    first_heading,
    get_hash_from_body,
    get_markdown_attributes,
    strip_first_heading,
)

FENCED = "```bash\n# install the tool\napt install x\n```\n\n# Real title\n\nText.\n"


@pytest.mark.parametrize("body, title", [
    ("# Plain\n\nText.\n", "Plain"),
    (FENCED, "Real title"),
    ("~~~python\n# comment\n~~~\n# Real title\n", "Real title"),
    ("````\n```\n# inside\n```\n````\n# Real title\n", "Real title"),
    ("  ```\n# inside\n  ```\n# Real title\n", "Real title"),
    ("Intro.\n\n    # indented code\n\n# Real title\n", "Real title"),
    ("\t# tab indented code\n# Real title\n", "Real title"),
    ("## Second level\n# Real title\n", "Real title"),
    ("#hashtag\n# Real title\n", "Real title"),
    ("# Title with trailing spaces   \n", "Title with trailing spaces"),
])
def test_first_heading(body, title):
    assert first_heading(body)[0] == title


def test_no_heading_outside_code():
    assert first_heading("```\n# only in code\n```\n") == (None, None)


def test_unclosed_fence_hides_the_rest():
    assert first_heading("```\n# a\n\n# b\n") == (None, None)


def test_strip_removes_only_the_title_line():
    assert strip_first_heading(FENCED) == "```bash\n# install the tool\napt install x\n```\n\n\nText.\n"
    assert strip_first_heading("# T\nBody\n") == "Body\n"
    assert strip_first_heading("No title\n") == "No title\n"


def test_document_title_ignores_code_comments(tmp_path):
    """The audit reproduction of COR-07: the title was "install the tool"."""
    doc = tmp_path / "doc.md"
    doc.write_text("---\nTag: x\n---\n" + FENCED, encoding="utf-8")
    keys, valid, _reason = get_markdown_attributes(str(doc))
    assert valid and keys["Title"] == ["Real title"]


def test_body_hash_ignores_a_title_rename(tmp_path):
    doc = tmp_path / "doc.md"
    doc.write_text("---\nTag: x\n---\n" + FENCED, encoding="utf-8")
    before = get_hash_from_body(str(doc))
    doc.write_text("---\nTag: x\n---\n" + FENCED.replace("Real title", "Renamed"), encoding="utf-8")
    assert get_hash_from_body(str(doc)) == before

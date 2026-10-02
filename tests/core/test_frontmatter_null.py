from kb4it.core.util import get_document_attributes


def test_null_frontmatter_value_is_empty_list(tmp_path):
    doc = tmp_path / "a.md"
    doc.write_text("---\nSummary:\nKind: howto\nKeyword:\n  - one\n  -\n---\n\n# Title\n\nBody\n", encoding="utf-8")
    keys, ok, _reason = get_document_attributes(str(doc))
    assert ok
    assert keys["Summary"] == []
    assert keys["Kind"] == ["howto"]
    assert keys["Keyword"] == ["one"]

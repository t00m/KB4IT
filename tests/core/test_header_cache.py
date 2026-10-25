"""A document is read once per build and its parsed header is reused while its bytes do not change."""

import json

import yaml

from kb4it.core import files
from kb4it.core.documents import get_hash_from_body, get_markdown_attributes, parse_markdown_attributes
from tests.helpers import page, run_kb4it, write_repo

TEXT = "---\nTag: a, b\n---\n\n# Title\n\nBody line.\n\n## Part\n\nMore.\n"


def _variants(tmp_path):
    raw = {
        "lf": TEXT.encode("utf-8"),
        "crlf": TEXT.replace("\n", "\r\n").encode("utf-8"),
        "bom": b"\xef\xbb\xbf" + TEXT.encode("utf-8"),
        "bom_crlf": b"\xef\xbb\xbf" + TEXT.replace("\n", "\r\n").encode("utf-8"),
    }
    paths = {}
    for name, content in raw.items():
        path = tmp_path / f"{name}.md"
        path.write_bytes(content)
        paths[name] = path
    return paths


def test_read_document_normalises_text_and_hashes_the_bytes(tmp_path):
    paths = _variants(tmp_path)
    texts = {}
    hashes = set()
    for name, path in paths.items():
        text, file_hash = files.read_document(str(path))
        texts[name] = text
        hashes.add(file_hash)
    assert set(texts.values()) == {TEXT}
    assert len(hashes) == len(paths)
    assert files.get_hash_from_bytes(paths["lf"].read_bytes()) in hashes


def test_crlf_and_bom_files_parse_like_their_lf_twin(tmp_path):
    paths = _variants(tmp_path)
    reference = parse_markdown_attributes(files.read_document(str(paths["lf"]))[0], "lf.md")
    for name, path in paths.items():
        text, _file_hash = files.read_document(str(path))
        assert parse_markdown_attributes(text, f"{name}.md") == reference
        assert get_hash_from_body(str(path), content=text) == get_hash_from_body(str(paths["lf"]))


def test_parser_reports_an_ignored_frontmatter_title(tmp_path):
    path = tmp_path / "warned.md"
    path.write_text("---\nTitle: Wrong\nTag: x\n---\n\n# Real\n\nText.\n", encoding="utf-8")
    content, _file_hash = files.read_document(str(path))
    keys, valid, reason, warned = parse_markdown_attributes(content, "warned.md")
    assert valid is True and reason == "Success" and warned is True
    assert keys["Title"] == ["Real"]
    assert get_markdown_attributes(str(path)) == (keys, True, "Success")

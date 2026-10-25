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


def _header_actions(repo):
    import re
    text = (repo / "var" / "log" / "kb4it.log").read_text(encoding="utf-8")
    return re.findall(r"\[PROCESSOR\] HEADER_CACHE doc=(\S+) action=(\w+)", text)


def _build(cfg, tmp_path, home):
    result = run_kb4it("-L", "DEBUG", "build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return result


def test_second_build_reuses_every_header(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {
        "a.md": page("A", Tag="x"),
        "b.md": page("B", Tag="y"),
        "c.md": page("C", Tag="z"),
    })
    _build(cfg, tmp_path, home)
    cache = json.loads((repo / "var" / "db" / "kbdict.json").read_text(encoding="utf-8"))
    assert all(len(entry["file_hash"]) == 128 for entry in cache["document"].values())

    result = _build(cfg, tmp_path, home)
    actions = _header_actions(repo)
    assert sorted(name for name, action in actions if action == "reuse") == ["a.md", "b.md", "c.md"]
    assert [name for name, action in actions if action == "parse"] == []
    assert "compiled=0" in result.stdout


def test_editing_one_document_parses_only_that_header(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {
        "a.md": page("A", Tag="x"),
        "b.md": page("B", Tag="y"),
        "c.md": page("C", Tag="z"),
    })
    _build(cfg, tmp_path, home)
    (repo / "source" / "b.md").write_text(page("B", Tag="y", body="Changed."), encoding="utf-8")

    _build(cfg, tmp_path, home)
    actions = _header_actions(repo)
    assert [name for name, action in actions if action == "parse"] == ["b.md"]
    assert sorted(name for name, action in actions if action == "reuse") == ["a.md", "c.md"]


def test_a_frontmatter_title_warns_on_every_build(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {
        "a.md": page("A", Tag="x"),
        "warned.md": page("Real", Title="Wrong", Tag="x"),
    })
    _build(cfg, tmp_path, home)
    cache = json.loads((repo / "var" / "db" / "kbdict.json").read_text(encoding="utf-8"))
    assert cache["document"]["warned.md"]["warned"] is True

    _build(cfg, tmp_path, home)
    actions = dict(_header_actions(repo))
    assert actions["warned.md"] == "parse" and actions["a.md"] == "reuse"
    log = (repo / "var" / "log" / "kb4it.log").read_text(encoding="utf-8")
    assert "DOC_WARN doc=warned.md reason=title_in_frontmatter_ignored" in log


def test_a_yaml_upgrade_drops_the_cache(tmp_path, home):
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "techdoc", {
        "a.md": page("A", Tag="x"),
        "b.md": page("B", Tag="y"),
    })
    _build(cfg, tmp_path, home)
    cache_file = repo / "var" / "db" / "kbdict.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8"))
    assert cache["pyyaml_version"] == yaml.__version__

    cache["pyyaml_version"] = "an-old-yaml"
    cache_file.write_text(json.dumps(cache), encoding="utf-8")
    result = _build(cfg, tmp_path, home)
    assert "KBDICT_PYYAML_MISMATCH stored=an-old-yaml" in result.stdout
    assert f"current={yaml.__version__}" in result.stdout
    assert "compiled=2" in result.stdout
    assert json.loads(cache_file.read_text(encoding="utf-8"))["pyyaml_version"] == yaml.__version__

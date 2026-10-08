"""Sources and settings saved on Windows (CRLF line endings, byte order mark) behave like Linux ones."""

import json

import pytest

from kb4it.core import util
from tests.helpers import page, run_kb4it, write_repo

TEXT = "---\nAuthor: Tomás\nTag: a, b\n---\n\n# Title\n\nBody line.\n\n## Part\n\nMore.\n"
VARIANTS = {
    "lf": TEXT.encode("utf-8"),
    "crlf": TEXT.replace("\n", "\r\n").encode("utf-8"),
    "bom": b"\xef\xbb\xbf" + TEXT.encode("utf-8"),
    "bom_crlf": b"\xef\xbb\xbf" + TEXT.replace("\n", "\r\n").encode("utf-8"),
}


@pytest.mark.parametrize("variant", sorted(VARIANTS))
def test_same_metadata_and_hash(tmp_path, variant):
    reference = tmp_path / "lf.md"
    reference.write_bytes(VARIANTS["lf"])
    other = tmp_path / f"{variant}.md"
    other.write_bytes(VARIANTS[variant])
    assert util.get_document_attributes(str(other)) == util.get_document_attributes(str(reference))
    assert util.get_hash_from_body(str(other)) == util.get_hash_from_body(str(reference))


def test_json_with_byte_order_mark(tmp_path):
    path = tmp_path / "repo.json"
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps({"title": "T"}).encode("utf-8"))
    assert util.json_load(str(path)) == {"title": "T"}


def test_windows_saved_files_build(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"ok.md": page("Ok", Tag="y")})
    (tmp_path / "repo" / "source" / "win.md").write_bytes(VARIANTS["bom_crlf"])
    cfg.write_bytes(b"\xef\xbb\xbf" + cfg.read_bytes().replace(b"\n", b"\r\n"))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "repo" / "target" / "win.html").read_text(encoding="utf-8")
    assert "Body line." in html
    assert "\r" not in html.split("Body line.")[0][-200:]

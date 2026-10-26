"""ET-10: the Add page of the apphelp theme."""

import json
import re
from pathlib import Path

import pytest

from tests.helpers import page, run_kb4it, write_repo

SKELETONS = Path(__file__).resolve().parents[2] / "kb4it" / "resources" / "themes" / "apphelp" / "templates" / "skeletons"
VOCAB = {"Feature": ["Backup", "Rename"], "Level": ["basic", "advanced"], "Platform": ["Linux", "Windows"]}
DOCS = {"backup.md": page("Back up", DocType="How-to guide", Section="How-to", Order="10",
                          Summary="A summary.", Feature="Backup")}


def build(tmp_path, home, command="build", apphelp=None, **conf):
    repo = tmp_path / "repo"
    block = {"strict": True, "vocabulary": VOCAB}
    block.update(apphelp or {})
    cfg = write_repo(repo, "apphelp", DOCS, publish_sources=False, apphelp=block, **conf)
    return repo, run_kb4it(command, cfg, cwd=repo, home=home)


def keys_of(html):
    match = re.search(r'<script id="kb-add-keys" type="application/json">(.*?)</script>', html, re.S)
    return json.loads(match.group(1))


def test_apphelp_add_page(tmp_path, home):
    repo, result = build(tmp_path, home, editor=True)
    assert result.returncode == 0, result.stdout
    html = (repo / "target" / "add.html").read_text(encoding="utf-8")
    assert "ah-sidebar" in html
    assert "<title>Add a page | Test</title>" in html
    for cat in ("tutorial", "howto", "reference", "explanation"):
        assert f'id="modal-add-{cat}"' in html
    assert "[BUILDER] ADD_PAGE enabled=True skeletons=theme categories=4" in result.stdout
    assert (repo / "target" / "resources" / "editor" / "kb4it-editor.js").exists()


def test_apphelp_sidebar_link(tmp_path, home):
    repo, result = build(tmp_path, home, editor=True)
    assert result.returncode == 0, result.stdout
    html = (repo / "target" / "backup.html").read_text(encoding="utf-8")
    assert re.search(r'<a [^>]*href="add.html"[^>]*>Add a page</a>', html)


def test_apphelp_sidebar_link_label(tmp_path, home):
    repo, result = build(tmp_path, home, editor=True, apphelp={"labels": {"add": "Nueva página"}})
    assert result.returncode == 0, result.stdout
    html = (repo / "target" / "backup.html").read_text(encoding="utf-8")
    assert re.search(r'<a [^>]*href="add.html"[^>]*>Nueva página</a>', html)


def test_apphelp_off_by_default(tmp_path, home):
    repo, result = build(tmp_path, home)
    assert result.returncode == 0, result.stdout
    assert not (repo / "target" / "add.html").exists()
    assert 'href="add.html"' not in (repo / "target" / "backup.html").read_text(encoding="utf-8")
    assert "[BUILDER] ADD_PAGE enabled=False" in result.stdout


def test_apphelp_stale_page_removed(tmp_path, home):
    repo, _ = build(tmp_path, home, editor=True)
    assert (repo / "target" / "add.html").exists()
    repo, result = build(tmp_path, home, editor=False)
    assert result.returncode == 0, result.stdout
    assert not (repo / "target" / "add.html").exists()


@pytest.mark.parametrize("name,doctype", [("TUTORIAL", "Tutorial"), ("HOWTO", "How-to guide"),
                                          ("REFERENCE", "Reference"), ("EXPLANATION", "Explanation")])
def test_apphelp_skeletons_pass_verify(tmp_path, home, name, doctype):
    text = (SKELETONS / f"{name}-SKELETON.md").read_text(encoding="utf-8")
    assert f"DocType: {doctype}\n" in text
    for key, value in (("Section", "How-to"), ("Order", "100"), ("Summary", "A new page."),
                       ("Feature", "Rename"), ("Level", "basic")):
        text = re.sub(rf"^{key}:.*$", f"{key}: {value}", text, count=1, flags=re.M)
    repo = tmp_path / "repo"
    docs = dict(DOCS)
    docs["new.md"] = text
    cfg = write_repo(repo, "apphelp", docs, apphelp={"strict": True, "vocabulary": VOCAB})
    result = run_kb4it("verify", cfg, cwd=repo, home=home)
    assert result.returncode == 0, result.stdout
    assert "META_" not in result.stdout and "DOCTYPE_" not in result.stdout


def test_apphelp_editor_keys(tmp_path, home):
    repo, result = build(tmp_path, home, editor=True)
    assert result.returncode == 0, result.stdout
    keys = keys_of((repo / "target" / "add.html").read_text(encoding="utf-8"))
    counts = {key: {item["v"]: item["c"] for item in items} for key, items in keys.items()}
    assert counts["Feature"] == {"Backup": 1, "Rename": 0}
    assert counts["Level"] == {"basic": 0, "advanced": 0}
    assert counts["Platform"] == {"Linux": 0, "Windows": 0}
    assert counts["DocType"] == {"Tutorial": 0, "How-to guide": 1, "Reference": 0, "Explanation": 0}
    assert counts["Layout"] == {"faq": 0, "tips": 0, "troubleshooting": 0}


def test_apphelp_versions_add_page(tmp_path, home):
    repo, result = build(tmp_path, home, editor=True, version="1.0", apphelp={"versions": {"enabled": True}})
    assert result.returncode == 0, result.stdout
    assert (repo / "target" / "1.0" / "add.html").exists()
    assert (repo / "target" / "1.0" / "resources" / "editor" / "kb4it-editor.js").exists()


def test_apphelp_source_add_md_is_reserved(tmp_path, home):
    repo = tmp_path / "repo"
    docs = dict(DOCS)
    docs["add.md"] = page("Mine", DocType="How-to guide", Section="How-to", Order="1",
                          Summary="S.", Feature="Backup")
    cfg = write_repo(repo, "apphelp", docs, editor=True, apphelp={"strict": False, "vocabulary": VOCAB})
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert "DOC_NAME_RESERVED doc=add.md" in result.stdout
    assert 'id="modal-add-howto"' in (repo / "target" / "add.html").read_text(encoding="utf-8")
    verify = run_kb4it("verify", cfg, cwd=repo, home=home)
    assert "add.md" in verify.stdout and "reserved_name" in verify.stdout

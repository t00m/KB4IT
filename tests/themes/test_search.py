"""Full-text search in techdoc, blog and bookshelf: index, search page, search box, and search: false."""

import json

import pytest

from tests.helpers import ROOT, page, run_kb4it, write_repo

THEMES = ["techdoc", "blog", "bookshelf"]
BODY = "Intro mentions zebrafish.\n\n## Restore steps\n\nUse the quokka option.\n"


def _conf(theme, **extra):
    path = ROOT / "kb4it" / "resources" / "themes" / theme / "apps" / "default" / "config" / "repo.json"
    conf = json.loads(path.read_text(encoding="utf-8"))
    for key in ("theme", "source", "target", "title"):
        conf.pop(key, None)
    conf.update(extra)
    return conf


def _page(title, body=BODY):
    return page(title, body, Category="Post", Date="2026-10-08", Tag="fish, tools")


def _index(target):
    text = (target / "search-index.js").read_text(encoding="utf-8")
    assert text.startswith("window.KB4IT_INDEX = ")
    return {r["u"]: r for r in json.loads(text.split(" = ", 1)[1].rstrip(";\n"))}


def _build(tmp_path, home, theme, pages, **extra):
    cfg = write_repo(tmp_path / theme, theme, pages, **_conf(theme, **extra))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return cfg, tmp_path / theme / "target", result


@pytest.mark.parametrize("theme", THEMES)
def test_index_page_and_box(tmp_path, home, theme):
    _cfg, target, result = _build(tmp_path, home, theme, {"a.md": _page("Alpha")})
    assert "[SEARCH] INDEX_BUILT pages=1" in result.stdout
    records = _index(target)
    assert list(records) == ["a.html"], "only source documents are indexed"
    alpha = records["a.html"]
    assert alpha["t"] == "Alpha"
    assert alpha["f"] == {"Category": ["Post"], "Tag": ["fish", "tools"]}
    sections = {s[0]: s for s in alpha["x"]}
    assert "zebrafish" in sections[""][2]
    assert sections["restore-steps"][1] == "Restore steps" and "quokka" in sections["restore-steps"][2]
    assert 'id="kb4it-search-page"' in (target / "search.html").read_text(encoding="utf-8")
    assert 'id="kb4it-search-input"' in (target / "a.html").read_text(encoding="utf-8")
    for asset in ("js/kb4it-search.js", "js/kb4it-search-ui.js", "css/kb4it-search.css"):
        assert (target / "resources" / "common" / asset).is_file(), asset


def test_search_false_removes_everything(tmp_path, home):
    cfg, target, _ = _build(tmp_path, home, "techdoc", {"a.md": _page("Alpha")})
    assert (target / "search-index.js").exists()
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["search"] = False
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert not (target / "search-index.js").exists()
    assert not (target / "search.html").exists()
    assert "kb4it-search-input" not in (target / "a.html").read_text(encoding="utf-8")


def test_incremental_build_keeps_unchanged_pages_in_the_index(tmp_path, home):
    cfg, target, _ = _build(tmp_path, home, "techdoc", {"a.md": _page("Alpha"), "b.md": _page("Beta", "Beta text.")})
    (tmp_path / "techdoc" / "source" / "c.md").write_text(_page("Gamma", "Gamma owl text."), encoding="utf-8")
    (tmp_path / "techdoc" / "source" / "b.md").unlink()
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "COMPILED doc=a.md" not in result.stdout, "a.md did not change and is not recompiled"
    records = _index(target)
    assert sorted(records) == ["a.html", "c.html"]
    assert any("zebrafish" in s[2] for s in records["a.html"]["x"])
    assert not (tmp_path / "techdoc" / "var" / "search" / "b.md.json").exists()


def test_engine_finds_a_section_in_the_built_index(tmp_path, home):
    import os
    import shutil
    import subprocess
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    _cfg, target, _ = _build(tmp_path, home, "techdoc", {"a.md": _page("Alpha")})
    script = ("const fs=require('fs'); global.window=global;"
              "eval(fs.readFileSync(process.env.INDEX,'utf8')); eval(fs.readFileSync(process.env.ENGINE,'utf8'));"
              "const e=new window.KB4ITSearch.Engine(window.KB4IT_INDEX);"
              "console.log(JSON.stringify(e.search('quokka',{}).map(r=>r.url)));")
    env = dict(os.environ, INDEX=str(target / "search-index.js"),
               ENGINE=str(target / "resources" / "common" / "js" / "kb4it-search.js"))
    out = subprocess.run([node, "-e", script], env=env, capture_output=True, text=True, encoding="utf-8", check=True)
    assert json.loads(out.stdout) == ["a.html#restore-steps"]


def test_worktype_is_a_facet(tmp_path, home):
    _cfg, target, _ = _build(tmp_path, home, "techdoc", {"c.md": page("Change one", Category="Record", WorkType="Change", Date="2026-10-08")})
    assert _index(target)["c.html"]["f"] == {"Category": ["Record"], "WorkType": ["Change"]}

"""techdoc: the quality tier in the search index and results."""

import json
import os
import shutil
import subprocess

import pytest

from tests.core.test_highlight import _app_conf
from tests.helpers import ROOT, page, run_kb4it, write_repo

PAGE = "## Steps\n\nRun the quokka command.\n"


def _build(tmp_path, home, pages, **extra):
    conf = _app_conf("techdoc")
    conf.update(extra)
    cfg = write_repo(tmp_path / "repo", "techdoc", pages, **conf)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    target = tmp_path / "repo" / "target"
    text = (target / "search-index.js").read_text(encoding="utf-8")
    return target, {r["u"]: r for r in json.loads(text.split(" = ", 1)[1].rstrip(";\n"))}


def test_index_carries_the_score_and_tier(tmp_path, home):
    _target, records = _build(tmp_path, home, {
        "a.md": page("Alpha", PAGE, Category="How-to", DocType="How-to guide", Date="2026-10-01",
                     Author="Tomas", Summary="One", Tag="quokka"),
    })
    quality = records["a.html"]["q"]
    assert isinstance(quality["score"], int) and quality["score"] >= 0
    assert quality["tier"] in ("exemplary", "complete", "basic", "stub", "retired")
    assert quality["label"] in ("Exemplary", "Complete", "Basic", "Stub", "Retired")


def test_quality_off_leaves_the_record_as_before(tmp_path, home):
    _target, records = _build(tmp_path, home, {"a.md": page("Alpha", PAGE, Date="2026-10-01")}, quality=False)
    assert "q" not in records["a.html"]


def test_quality_breaks_a_relevance_tie(tmp_path, home):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    records = [
        {"u": "low.html", "t": "Alpha aaa", "q": {"score": 20, "tier": "stub", "label": "Stub"}},
        {"u": "high.html", "t": "Alpha zzz", "q": {"score": 80, "tier": "exemplary", "label": "Exemplary"}},
    ]
    index = tmp_path / "index.js"
    index.write_text("window.KB4IT_INDEX = " + json.dumps(records) + ";\n", encoding="utf-8")
    engine = ROOT / "kb4it" / "resources" / "common" / "js" / "kb4it-search.js"
    script = ("const fs=require('fs'); global.window=global;"
              "eval(fs.readFileSync(process.env.INDEX,'utf8')); eval(fs.readFileSync(process.env.ENGINE,'utf8'));"
              "const e=new window.KB4ITSearch.Engine(window.KB4IT_INDEX);"
              "console.log(JSON.stringify(e.search('alpha',{}).map(r=>r.url)));")
    env = dict(os.environ, INDEX=str(index), ENGINE=str(engine))
    out = subprocess.run([node, "-e", script], env=env, capture_output=True, text=True, encoding="utf-8", check=True)
    assert json.loads(out.stdout) == ["high.html", "low.html"]


def test_ui_renders_the_same_quality_chip():
    ui = (ROOT / "kb4it" / "resources" / "common" / "js" / "kb4it-search-ui.js").read_text(encoding="utf-8")
    assert '"kb-q-chip kb-q-" +' in ui
    assert "record.q" in ui
    assert "Quality " in ui and " of 100, " in ui


def test_styles_cover_the_chip_in_the_dropdown():
    css = (ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "framework" / "kb4it" / "css" / "screen.css").read_text(encoding="utf-8")
    assert ".kb4it-search-dropdown .kb-q-chip" in css

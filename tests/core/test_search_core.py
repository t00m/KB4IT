"""The shared search code: section extraction, index script, and the engine apphelp copies in."""

import json

from kb4it.core import search
from tests.helpers import ROOT, page, run_kb4it, write_repo

HTML = """<html><body><div id="doc"><p>Intro <b>text</b>.</p>
<h2 id="one">First part</h2><p>Alpha beta.</p><script>skip()</script>
<h3 id="two">Second</h3><p>Gamma.</p></div><p>Outside.</p></body></html>"""


def test_extract_sections():
    assert search.extract_sections(HTML, "doc") == [
        {"id": "", "heading": "", "text": "Intro text ."},
        {"id": "one", "heading": "First part", "text": "Alpha beta."},
        {"id": "two", "heading": "Second", "text": "Gamma."},
    ]
    assert search.extract_sections(HTML, "missing") == []


def test_render_index_js():
    js = search.render_index_js([{"t": "Tomás"}], "MY_INDEX")
    assert js.startswith("window.MY_INDEX = ")
    assert json.loads(js.split(" = ", 1)[1].rstrip(";\n")) == [{"t": "Tomás"}]


def test_apphelp_site_carries_the_shared_engine(tmp_path, home):
    conf = {"apphelp": {"strict": False}}
    cfg = write_repo(tmp_path / "help", "apphelp", {"a.md": page("A", DocType="Reference", Tag="x")}, **conf)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    deployed = tmp_path / "help" / "target" / "resources" / "themes" / "apphelp" / "framework" / "apphelp" / "js"
    engine = (ROOT / "kb4it" / "resources" / "common" / "js" / "kb4it-search.js").read_text(encoding="utf-8")
    assert (deployed / "search.js").read_text(encoding="utf-8") == engine

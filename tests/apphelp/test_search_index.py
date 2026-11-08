import json

from apphelp_meta import Page
from apphelp_search import extract_sections, page_record, render_index_js

HTML = """<html><body><main><h1>Title</h1><div id="ah-article-body">
<p>Intro <b>bold</b> text.</p>
<div class="sect1"><h2 id="one">First <code>part</code></h2><div class="sectionbody"><p>Alpha beta.</p>
<div class="ah-code"><button class="ah-copy" type="button">Copy</button><pre>ls -l</pre></div></div></div>
<details class="ah-faq" id="q1"><summary>Question?</summary><div class="ah-faq-answer"><p>Answer.</p></div></details>
<script>var x = 1;</script>
</div><footer>Footer text</footer></main></body></html>"""


def test_extract_sections():
    sections = extract_sections(HTML)
    assert sections == [
        {"id": "", "heading": "", "text": "Intro bold text."},
        {"id": "one", "heading": "First part", "text": "Alpha beta. ls -l"},
        {"id": "q1", "heading": "Question?", "text": "Answer."},
    ]


def test_extract_without_article():
    assert extract_sections("<html><body><p>x</p></body></html>") == []


def test_record_and_js():
    page = Page(doc_id="a.md", title="A", doctype="howto", section="How-to", order=1, summary="S",
                features=["Backup"], keywords=["copy"], level="basic", tags=["t"])
    record = page_record(page, [{"id": "one", "heading": "H", "text": "body"}])
    assert record == {"u": "a.html", "t": "A", "s": "S", "k": "howto", "c": "How-to",
                      "f": {"DocType": ["howto"], "Feature": ["Backup"], "Level": ["basic"]},
                      "w": ["copy"], "g": ["t"], "x": [["one", "H", "body"]]}
    js = render_index_js([record])
    assert js.startswith("window.APPHELP_INDEX = ") and js.endswith(";\n")
    assert json.loads(js[len("window.APPHELP_INDEX = "):-2]) == [record]


def _apphelp_theme_class():
    import importlib.util
    from tests.helpers import ROOT
    path = ROOT / "kb4it" / "resources" / "themes" / "apphelp" / "logic" / "theme.py"
    spec = importlib.util.spec_from_file_location("apphelp_theme_module_b3", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Theme


def test_apphelp_has_no_private_index_writer():
    from kb4it.services.builder import Builder
    theme = _apphelp_theme_class()
    assert not hasattr(theme, "_write_search_index")
    assert theme.search_record is not Builder.search_record
    assert theme.search_sections is not Builder.search_sections
    assert theme.search_index_var == "APPHELP_INDEX"
    assert theme.search_index_warn_bytes == 2 * 1024 * 1024


def test_apphelp_templates_get_the_apphelp_namespace():
    ctx = {"lang": "en"}
    assert _apphelp_theme_class().template_var(ctx) == {"apphelp": ctx, "ah": ctx}

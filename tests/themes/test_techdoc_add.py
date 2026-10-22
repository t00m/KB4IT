"""ED-04: the techdoc Add page loads the CodeMirror editor instead of a textarea."""

import re
from pathlib import Path

import pytest

from tests.core.test_highlight import _app_conf
from tests.helpers import page, run_kb4it, write_repo

ROOT = Path(__file__).resolve().parents[2]
EDITOR = ROOT / "kb4it" / "resources" / "editor"

# Shared with tests/browser/conftest.py. "x<b>y</b>" is accepted by the build
# (valid_filename leaves "xbyb"), so it reaches keys_json as HTML-looking text.
ADD_DOCS = {
    "note-one.md": page("Note one", Category="Note", Date="2026-10-01"),
    "note-two.md": page("Note two", Category="Note", Date="2026-10-02"),
    "procedure.md": page("A procedure", Category="Procedure", Tag="sap, linux", Date="2026-10-03"),
    "html-tag.md": page("Html tag", Category="Post", Tag="x<b>y</b>", Date="2026-10-04"),
}


def build_techdoc(base, home, docs):
    """Build a techdoc site from docs under base; return the target folder."""
    cfg = write_repo(base, "techdoc", docs, **_app_conf("techdoc"))
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return base / "target"


@pytest.fixture(scope="module")
def add_html(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-add")
    home = base / "home"
    home.mkdir()
    docs = dict(ADD_DOCS)
    docs["hostile.md"] = "---\nCategory: Note\nBad</script>: v\n---\n\n# Hostile\n\nText.\n"
    target = build_techdoc(base, home, docs)
    return (target / "add.html").read_text(encoding="utf-8")


def test_add_page_loads_editor_files_in_order(add_html):
    names = ["codemirror.min.js", "kb4it-frontmatter.js", "kb4it-editor.js"]
    tags = [re.search(r'<script[^>]*src="resources/editor/' + re.escape(n) + r'"[^>]*>', add_html) for n in names]
    assert all(tags), tags
    assert [t.start() for t in tags] == sorted(t.start() for t in tags)
    for tag in tags:
        assert 'type="module"' not in tag.group(0)
    assert '<link rel="stylesheet" href="resources/editor/kb4it-editor.css">' in add_html


def test_editor_hosts_are_divs(add_html):
    assert '<div id="kb-editor-note"' in add_html
    assert '<textarea id="kb-editor-' not in add_html


def test_keys_json_has_no_raw_lt(add_html):
    body = re.search(r'<script id="kb-add-keys" type="application/json">(.*?)</script>', add_html, re.S)
    assert body
    assert "<" not in body.group(1)
    assert "x\\u003cb>y\\u003c/b>" in body.group(1)


def test_hostile_property_names_stay_escaped(add_html):
    # Built or rejected by bad_property_name, no value closes a script element early.
    assert add_html.count("</script>") == len(re.findall(r"<script[\s>]", add_html))


def test_editor_js_never_uses_innerhtml():
    for name in ("kb4it-editor.js", "kb4it-frontmatter.js"):
        text = (EDITOR / name).read_text(encoding="utf-8")
        for word in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
            assert word not in text, (name, word)

"""techdoc: the focus mode switch in the top bar of a document page."""

import pytest

from tests.helpers import ROOT, page
from tests.themes.test_techdoc_add import build_techdoc

THEME = ROOT / "kb4it" / "resources" / "themes" / "techdoc"
FOUR = "## One\n\nA.\n\n## Two\n\nB.\n\n## Three\n\nC.\n\n## Four\n\nD."


@pytest.fixture(scope="module")
def focus_site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-focus")
    home = base / "home"
    home.mkdir()
    return build_techdoc(base, home, {"four.md": page("Four sections", FOUR, Category="Note", Date="2026-10-01")})


def buttons(html):
    return html[html.index("TOP BAR BUTTONS :: START"):html.index("TOP BAR BUTTONS :: END")]


def test_document_has_the_switch_left_of_reload(focus_site):
    right = buttons((focus_site / "four.html").read_text(encoding="utf-8"))
    assert 'data-kb-focus' in right and 'aria-pressed="false"' in right and 'title="Focus mode"' in right
    assert right.index("data-kb-focus") < right.index("Reload page")


def test_system_pages_have_no_switch(focus_site):
    for name in ("index.html", "events.html", "properties.html"):
        assert "data-kb-focus" not in buttons((focus_site / name).read_text(encoding="utf-8")), name


def test_header_strip_and_info_card_share_one_wrapper(focus_site):
    html = (focus_site / "four.html").read_text(encoding="utf-8")
    meta = html[html.index("DOCUMENT META :: START"):html.index("DOCUMENT META :: END")]
    assert '<div class="kb-doc-meta">' in meta and 'id="kb-info-card"' in meta and "kb-doc-strip" in meta


def test_styles_hide_everything_but_the_document():
    css = (THEME / "framework" / "kb4it" / "css" / "screen.css").read_text(encoding="utf-8")
    for selector in (".kb4it-page-actions", ".kb-doc-meta", "#kb-toc-inline", ".kb-toc-sidebar-actions",
                     ".kb-footer", ".kb-totop"):
        assert f".kb-focus {selector}" in css, selector
    assert ".kb-focus .kb-toc-sidebar " not in css and ".kb-focus .kb-toc-sidebar," not in css


def test_script_toggles_the_class_and_restores_the_folds():
    js = (THEME / "framework" / "kb4it" / "js" / "page.js").read_text(encoding="utf-8")
    assert "document.querySelector('[data-kb-focus]')" in js
    assert "root.classList.toggle('kb-focus', on)" in js
    assert "folded.indexOf(s) >= 0" in js

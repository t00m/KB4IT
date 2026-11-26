"""techdoc: the focus mode switch in the top bar of a document page, and "focus_mode" to start it on."""

import json
import re

import pytest

from tests.core.test_highlight import _app_conf
from tests.helpers import ROOT, page, run_kb4it, write_repo
from tests.themes.test_techdoc_add import build_techdoc

THEME = ROOT / "kb4it" / "resources" / "themes" / "techdoc"
FOUR = "## One\n\nA.\n\n## Two\n\nB.\n\n## Three\n\nC.\n\n## Four\n\nD."
DOCS = {"four.md": page("Four sections", FOUR, Category="Note", Date="2026-10-01")}


@pytest.fixture(scope="module")
def focus_site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-focus")
    home = base / "home"
    home.mkdir()
    return build_techdoc(base, home, DOCS)


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


def html_tag(html):
    return re.search(r"<html\b[^>]*>", html).group(0)


def build_with(tmp_path, home, **conf):
    cfg = write_repo(tmp_path / "repo", "techdoc", DOCS, **{**_app_conf("techdoc"), **conf})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert "THEME_SETTING_UNKNOWN" not in result.stdout
    return tmp_path / "repo" / "target"


def test_focus_mode_is_off_by_default(focus_site):
    html = (focus_site / "four.html").read_text(encoding="utf-8")
    assert "kb-focus" not in html_tag(html)
    assert 'aria-pressed="false"' in buttons(html)


def test_repo_json_focus_mode_starts_documents_in_focus(tmp_path, home):
    target = build_with(tmp_path, home, focus_mode=True)
    html = (target / "four.html").read_text(encoding="utf-8")
    assert 'class="kb-focus"' in html_tag(html)
    assert 'aria-pressed="true"' in buttons(html) and 'title="Leave focus mode"' in buttons(html)
    # System pages have no document to focus on.
    assert "kb-focus" not in html_tag((target / "index.html").read_text(encoding="utf-8"))


def test_techdoc_block_sets_focus_mode(tmp_path, home):
    target = build_with(tmp_path, home, techdoc={"focus_mode": True})
    assert 'class="kb-focus"' in html_tag((target / "four.html").read_text(encoding="utf-8"))


def test_top_level_focus_mode_wins_over_the_techdoc_block(tmp_path, home):
    target = build_with(tmp_path, home, focus_mode=False, techdoc={"focus_mode": True})
    assert "kb-focus" not in html_tag((target / "four.html").read_text(encoding="utf-8"))


def test_theme_default_is_off():
    conf = json.loads((THEME / "theme.json").read_text(encoding="utf-8"))
    assert conf["focus_mode"] is False


def test_script_starts_in_focus_when_the_page_asks():
    js = (THEME / "framework" / "kb4it" / "js" / "page.js").read_text(encoding="utf-8")
    assert "if (root.classList.contains('kb-focus')) {\n        setFocus(true);" in js


@pytest.mark.parametrize("app", ["default", "sapbasis"])
def test_sample_apps_turn_focus_mode_on(app):
    conf = json.loads((THEME / "apps" / app / "config" / "repo.json").read_text(encoding="utf-8"))
    assert conf["focus_mode"] is True


def test_a_new_repository_opens_documents_in_focus(tmp_path, home):
    assert run_kb4it("create", "techdoc", "repo", cwd=tmp_path, home=home).returncode == 0
    cfg = tmp_path / "repo" / "config" / "repo.json"
    assert json.loads(cfg.read_text(encoding="utf-8"))["focus_mode"] is True
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    target = tmp_path / "repo" / "target"
    doc = next(p for p in target.glob("*.html") if 'data-kb-focus' in p.read_text(encoding="utf-8"))
    assert "kb-focus" in html_tag(doc.read_text(encoding="utf-8")).split("class=")[1]

"""techdoc: the optional sticky table of contents."""

import json
import shutil

from tests.core.test_highlight import _app_conf
from tests.helpers import ROOT, page, run_kb4it, write_repo

THEME = ROOT / "kb4it" / "resources" / "themes" / "techdoc"

FOUR = "## One\n\nA.\n\n## Two\n\nB.\n\n## Three\n\nC.\n\n## Four\n\nD."
THREE = "## One\n\nA.\n\n## Two\n\nB.\n\n## Three\n\nC."
DOCS = {
    "four.md": page("Four sections", FOUR, Category="Note", Date="2026-10-01"),
    "three.md": page("Three sections", THREE, Category="Note", Date="2026-10-01"),
}


def theme_copy(base, toc_sidebar):
    path = base / "theme"
    shutil.copytree(THEME, path)
    conf_path = path / "theme.json"
    conf = json.loads(conf_path.read_text(encoding="utf-8"))
    conf["toc_sidebar"] = toc_sidebar
    conf_path.write_text(json.dumps(conf), encoding="utf-8")
    return path


def build(tmp_path, home):
    theme = theme_copy(tmp_path, True)
    cfg = write_repo(tmp_path / "repo", "techdoc", DOCS, theme_path=str(theme), **_app_conf("techdoc"))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return tmp_path / "repo" / "target"


def test_four_sections_get_the_sidebar(tmp_path, home):
    target = build(tmp_path, home)
    html = (target / "four.html").read_text(encoding="utf-8")
    assert '<aside class="kb-toc-sidebar kb-noprint" aria-label="Table of contents">' in html
    assert 'data-uk-scrollspy-nav="closest: li; scroll: true; offset: 80"' in html
    assert 'class="kb-main kb-main-sidebar"' in html
    sidebar = html[html.index("SIDE TABLE OF CONTENTS :: START"):html.index("SIDE TABLE OF CONTENTS :: END")]
    assert 'href="#four"' in sidebar
    inline = html[html.index("TABLE OF CONTENTS :: START"):html.index("TABLE OF CONTENTS :: END")]
    assert 'href="#four"' in inline


def test_three_sections_and_system_pages_do_not(tmp_path, home):
    target = build(tmp_path, home)
    assert "kb-toc-sidebar" not in (target / "three.html").read_text(encoding="utf-8")
    assert "kb-toc-sidebar" not in (target / "index.html").read_text(encoding="utf-8")


def test_sidebar_is_off_by_default(tmp_path, home):
    cfg = write_repo(tmp_path / "default", "techdoc", DOCS, **_app_conf("techdoc"))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "default" / "target" / "four.html").read_text(encoding="utf-8")
    assert "kb-toc-sidebar" not in html


def test_styles_show_the_sidebar_only_on_wide_screens():
    css = (THEME / "framework" / "kb4it" / "css" / "screen.css").read_text(encoding="utf-8")
    assert ".kb-toc-sidebar { display: none; }" in css
    assert "@media (min-width: 1400px)" in css
    assert ".kb-main-sidebar" in css and "grid-template-columns" in css
    assert ".kb-toc-sidebar .uk-active > a" in css


def test_theme_default_is_off():
    conf = json.loads((THEME / "theme.json").read_text(encoding="utf-8"))
    assert conf["toc_sidebar"] is False

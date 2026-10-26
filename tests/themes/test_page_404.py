"""404 page of techdoc, blog and bookshelf: written, kept out of listings, base href, reserved name."""

import json
import re

import pytest

from tests.helpers import ROOT, page, run_kb4it, write_repo

THEMES = ["techdoc", "blog", "bookshelf"]
PAGES = {"hello.md": page("Hello page", "Some text.", Category="Post", Date="2026-10-08", Tag="misc")}


def _conf(theme, **extra):
    path = ROOT / "kb4it" / "resources" / "themes" / theme / "apps" / "default" / "config" / "repo.json"
    conf = json.loads(path.read_text(encoding="utf-8"))
    for key in ("theme", "source", "target", "title"):
        conf.pop(key, None)
    conf.update(extra)
    return conf


def _build(tmp_path, home, theme, pages=PAGES, **extra):
    cfg = write_repo(tmp_path / theme, theme, pages, **_conf(theme, **extra))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return cfg, tmp_path / theme / "target", result


@pytest.mark.parametrize("theme", THEMES)
def test_404_page_written(tmp_path, home, theme):
    _cfg, target, _result = _build(tmp_path, home, theme)
    html = (target / "404.html").read_text(encoding="utf-8")
    assert 'href="index.html"' in html
    assert "Page not found" in html
    assert 'class="kb4it-search"' in html


@pytest.mark.parametrize("theme", THEMES)
def test_404_not_listed(tmp_path, home, theme):
    _cfg, target, _result = _build(tmp_path, home, theme, site_url="https://ex.org/kb")
    assert (target / "404.html").exists()
    assert "404.html" not in (target / "sitemap.xml").read_text(encoding="utf-8")
    assert "404" not in (target / "search-index.js").read_text(encoding="utf-8")
    feed = target / "feed.xml"
    if feed.exists():
        assert "404.html" not in feed.read_text(encoding="utf-8")
    for listing in ("all.html", "bookmarks.html"):
        if (target / listing).exists():
            assert "404.html" not in (target / listing).read_text(encoding="utf-8")


def test_404_base_with_site_url(tmp_path, home):
    _cfg, target, _result = _build(tmp_path, home, "techdoc", site_url="https://ex.org/kb")
    html = (target / "404.html").read_text(encoding="utf-8")
    assert re.search(r'<head[^>]*>\s*<base href="https://ex.org/kb/">', html)
    assert html.count("<base ") == 1
    other = (target / "hello.html").read_text(encoding="utf-8")
    assert "<base " not in other


def test_404_no_base_without_site_url(tmp_path, home):
    _cfg, target, _result = _build(tmp_path, home, "techdoc")
    assert "<base " not in (target / "404.html").read_text(encoding="utf-8")


def test_document_named_404_is_reserved(tmp_path, home):
    pages = dict(PAGES, **{"404.md": page("Mine", "Own 404.", Category="Post")})
    cfg, target, result = _build(tmp_path, home, "techdoc", pages)
    assert "DOC_NAME_RESERVED doc=404.md" in result.stdout
    assert "Page not found" in (target / "404.html").read_text(encoding="utf-8")
    verify = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert verify.returncode == 1, verify.stdout
    assert "404.md" in verify.stdout
    assert "reserved_name" in verify.stdout


def test_apphelp_404_unchanged():
    theme = (ROOT / "kb4it" / "resources" / "themes" / "apphelp" / "logic" / "theme.py").read_text(encoding="utf-8")
    assert theme.count('_emit("404"') == 1
    assert "build_page_404" not in theme


def test_base_tag_is_not_duplicated():
    from types import SimpleNamespace

    from kb4it.services.headmeta import HeadMetaMixin

    mixin = HeadMetaMixin()
    mixin.srvbes = SimpleNamespace(site_url="https://ex.org/kb/")
    html = '<html><head lang="en"><title>x</title></head><body></body></html>'
    once = mixin._with_base(html)
    twice = mixin._with_base(once)
    assert once == twice
    assert once.count("<base ") == 1
    assert once.startswith('<html><head lang="en">\n<base href="https://ex.org/kb/">')


def test_reserved_pages_only_where_a_404_page_is_written():
    import ast

    from kb4it.services.themekit import DocumentTheme

    assert DocumentTheme.reserved_pages == ()
    for theme in THEMES:
        source = (ROOT / "kb4it" / "resources" / "themes" / theme / "logic" / "theme.py").read_text(encoding="utf-8")
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == "Theme")
        values = [ast.literal_eval(n.value) for n in cls.body
                  if isinstance(n, ast.AnnAssign | ast.Assign) and "reserved_pages" in ast.unparse(n)]
        # Every theme reserves 404.md; techdoc also reserves the system pages it writes (quality-guide.md).
        assert len(values) == 1 and "404.md" in values[0], theme
        assert "self.build_page_404()" in source, theme


def test_document_named_add_is_reserved_while_editor_is_on(tmp_path, home):
    pages = dict(PAGES, **{"add.md": page("Mine", "Own add.", Category="Post")})
    cfg, target, result = _build(tmp_path, home, "techdoc", pages)
    assert "DOC_NAME_RESERVED doc=add.md" in result.stdout
    assert 'id="modal-add-' in (target / "add.html").read_text(encoding="utf-8")
    verify = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert "add.md" in verify.stdout and "reserved_name" in verify.stdout


def test_document_named_add_is_normal_while_editor_is_off(tmp_path, home):
    pages = dict(PAGES, **{"add.md": page("Mine", "Own add.", Category="Post", Date="2026-10-01")})
    cfg, target, result = _build(tmp_path, home, "blog", pages)
    assert "DOC_NAME_RESERVED doc=add.md" not in result.stdout
    assert "Own add." in (target / "add.html").read_text(encoding="utf-8")
    verify = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert "add.md" not in verify.stdout


def test_verify_loads_theme_py_once(tmp_path, home):
    import shutil

    theme_dir = tmp_path / "counted"
    shutil.copytree(ROOT / "kb4it" / "resources" / "themes" / "techdoc", theme_dir)
    logic = theme_dir / "logic" / "theme.py"
    logic.write_text(logic.read_text(encoding="utf-8")
                     + '\nwith open(__file__ + ".loads", "a", encoding="utf-8") as _fout:\n    _fout.write("x")\n', encoding="utf-8")
    cfg = write_repo(tmp_path / "repo", "techdoc", PAGES, theme_path=str(theme_dir))
    verify = run_kb4it("verify", cfg, cwd=tmp_path, home=home)
    assert verify.returncode == 0, verify.stdout
    assert (theme_dir / "logic" / "theme.py.loads").read_text(encoding="utf-8") == "x"

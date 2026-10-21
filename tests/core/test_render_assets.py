"""Bundled Mermaid and KaTeX: shipped in the package and deployed to sites whose pages use them."""

import re

import pytest

from tests.core.test_highlight import _app_conf
from tests.helpers import ROOT, page, run_kb4it, write_repo

RENDER = ROOT / "kb4it" / "resources" / "render"
FILES = [
    "mermaid/mermaid.min.js",
    "katex/katex.min.css",
    "katex/katex.min.js",
    "kb4it-render.js",
]


FENCE = "`" * 3
RICH_BODY = f"{FENCE}mermaid\ngraph TD; A-->B\n{FENCE}\n\nInline $a^2$.\n"
RICH = page("Rich", RICH_BODY, Category="Post", Date="2026-10-08", DocType="Reference")
# Text that names the folder is not a page that loads it.
PLAIN = page("One", "Text about `resources/render/`.\n", Category="Post", Date="2026-10-08", DocType="Reference")


def _build(tmp_path, home, theme, pages, **extra):
    cfg = write_repo(tmp_path / theme, theme, pages, **dict(_app_conf(theme), **extra))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return cfg, tmp_path / theme / "target"


@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf", "apphelp"])
def test_render_assets_deployed(tmp_path, home, theme):
    _cfg, target = _build(tmp_path, home, theme, {"one.md": PLAIN, "rich.md": RICH})
    for name in FILES:
        assert (target / "resources" / "render" / name).is_file(), name


@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf", "apphelp"])
def test_render_assets_not_deployed_without_diagrams_or_formulas(tmp_path, home, theme):
    _cfg, target = _build(tmp_path, home, theme, {"one.md": PLAIN})
    assert not (target / "resources" / "render").exists()


def test_render_assets_follow_the_pages(tmp_path, home):
    cfg, target = _build(tmp_path, home, "techdoc", {"one.md": PLAIN, "rich.md": RICH})
    render = target / "resources" / "render"
    assert render.is_dir()
    # Incremental build: only one.md changes, rich.html comes from the cache and still needs the files.
    source = tmp_path / "techdoc" / "source"
    (source / "one.md").write_text(PLAIN.replace("Text about", "Other text about"), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert (render / "kb4it-render.js").is_file()
    # The last page with a diagram or formula is gone: the stale folder goes too.
    (source / "rich.md").unlink()
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    assert not render.exists()


def test_render_assets_in_versioned_apphelp(tmp_path, home):
    _cfg, target = _build(tmp_path, home, "apphelp", {"rich.md": page("Rich", RICH_BODY, DocType="Reference")},
                          version="1.0", apphelp={"strict": False, "versions": {"enabled": True}})
    assert (target / "1.0" / "resources" / "render" / "kb4it-render.js").is_file()


def test_render_script_follows_the_page_background():
    text = (RENDER / "kb4it-render.js").read_text(encoding="utf-8")
    assert "prefers-color-scheme" not in text
    assert "getComputedStyle" in text and "backgroundColor" in text
    assert ".catch(function () {})" in text
    assert "pre.mermaid{background:transparent!important;" in text


def test_render_assets_in_package():
    for name in FILES:
        assert (RENDER / name).is_file(), name
    versions = (RENDER / "VERSIONS").read_text(encoding="utf-8").lower()
    assert "mermaid" in versions and "katex" in versions


def test_katex_css_fonts_are_relative():
    css = (RENDER / "katex" / "katex.min.css").read_text(encoding="utf-8")
    urls = re.findall(r"url\(([^)]+)\)", css)
    assert urls
    for url in urls:
        url = url.strip("'\"")
        assert url.startswith("fonts/"), url
        assert (RENDER / "katex" / url).is_file(), url


def test_mermaid_is_not_an_es_module():
    text = (RENDER / "mermaid" / "mermaid.min.js").read_text(encoding="utf-8")
    assert not re.search(r"^\s*(export|import)\s", text, re.M)

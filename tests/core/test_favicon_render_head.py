"""Favicon in every page head; Mermaid and KaTeX scripts only on pages that need them."""

import json
import re

import pytest

from tests.core.test_highlight import _app_conf
from tests.helpers import page, run_kb4it, write_repo

THEMES = ["techdoc", "blog", "bookshelf", "apphelp"]
FENCE = "`" * 3


def _pages():
    return {
        "plain.md": page("Plain", "Just text.\n", Category="Post", Date="2026-10-08", DocType="Reference"),
        "diagram.md": page("Diagram", f"{FENCE}mermaid\ngraph TD; A-->B\n{FENCE}\n",
                           Category="Post", Date="2026-10-08", DocType="Reference"),
        "formula.md": page("Formula", "Inline $a^2 + b^2$ here.\n\n$$\nE = mc^2\n$$\n",
                           Category="Post", Date="2026-10-08", DocType="Reference"),
    }


def _build(tmp_path, home, theme, drop=(), **extra):
    conf = _app_conf(theme)
    conf.update(extra)
    for key in drop:
        conf.pop(key, None)
    base = tmp_path / theme
    cfg = write_repo(base, theme, _pages(), **conf)
    if drop:  # write_repo merges defaults only for title/theme/source/target
        data = json.loads(cfg.read_text(encoding="utf-8"))
        assert all(key not in data for key in drop)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return base / "target"


def _icon(html):
    found = re.findall(r'<link rel="icon" href="([^"]*)"', html)
    return found


@pytest.mark.parametrize("theme", THEMES)
def test_favicon_uses_repo_logo(tmp_path, home, theme):
    target = _build(tmp_path, home, theme, logo="resources/mylogo.svg")
    pages = list(target.glob("*.html"))
    assert pages
    for path in pages:
        assert _icon(path.read_text(encoding="utf-8")) == ["resources/mylogo.svg"], path.name


@pytest.mark.parametrize("theme", THEMES)
def test_favicon_falls_back_to_theme_logo(tmp_path, home, theme):
    target = _build(tmp_path, home, theme, drop=("logo",))
    expected = f"resources/themes/{theme}/images/logo.svg"
    for path in target.glob("*.html"):
        assert _icon(path.read_text(encoding="utf-8")) == [expected], path.name
    assert (target / expected).is_file()


def test_favicon_full_url_logo(tmp_path, home):
    target = _build(tmp_path, home, "techdoc", logo="https://example.org/logo.png")
    html = (target / "plain.html").read_text(encoding="utf-8")
    assert _icon(html) == ["https://example.org/logo.png"]


@pytest.mark.parametrize("theme", THEMES)
def test_render_scripts_only_where_needed(tmp_path, home, theme):
    target = _build(tmp_path, home, theme)
    plain = (target / "plain.html").read_text(encoding="utf-8")
    diagram = (target / "diagram.html").read_text(encoding="utf-8")
    formula = (target / "formula.html").read_text(encoding="utf-8")
    assert "resources/render/" not in plain
    assert "resources/render/mermaid/mermaid.min.js" in diagram
    assert "resources/render/kb4it-render.js" in diagram
    assert "katex" not in diagram
    for name in ("katex/katex.min.css", "katex/katex.min.js", "kb4it-render.js"):
        assert f"resources/render/{name}" in formula
    assert "mermaid.min.js" not in formula
    assert formula.index("katex.min.js") < formula.index("kb4it-render.js")
    for name in ("mermaid/mermaid.min.js", "katex/katex.min.js", "katex/katex.min.css", "kb4it-render.js"):
        assert (target / "resources" / "render" / name).is_file()


def test_techdoc_header_logo_fallback_exists(tmp_path, home):
    target = _build(tmp_path, home, "techdoc", drop=("logo",))
    html = (target / "plain.html").read_text(encoding="utf-8")
    nav = html[html.index('class="uk-logo'):]
    src = re.search(r'<img src="([^"]*)"', nav).group(1)
    assert (target / src).is_file(), src


def test_admin_page_has_favicon(tmp_path, home):
    target = _build(tmp_path, home, "techdoc", admin=True, logo="resources/mylogo.svg")
    html = (target / "admin" / "index.html").read_text(encoding="utf-8")
    assert _icon(html) == ["../resources/mylogo.svg"]

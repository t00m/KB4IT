"""Bundled Mermaid and KaTeX: shipped in the package and deployed to every site."""

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


@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf", "apphelp"])
def test_render_assets_deployed(tmp_path, home, theme):
    cfg = write_repo(tmp_path / theme, theme,
                     {"one.md": page("One", "Text\n", Category="Post", Date="2026-10-08", DocType="Reference")},
                     **_app_conf(theme))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    for name in FILES:
        assert (tmp_path / theme / "target" / "resources" / "render" / name).is_file(), name


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

"""markdown.highlight: highlight.js in the browser (default), Pygments at build time, or none."""

import json

import pytest

from kb4it.core.mdconfig import load_settings, pygments_css
from tests.helpers import ROOT, page, run_kb4it, write_repo

CODE = "```python\nprint('hi')\n```\n"


def _app_conf(theme):
    """Settings of the theme's sample app, so every key the theme expects is present."""
    path = ROOT / "kb4it" / "resources" / "themes" / theme / "apps" / "default" / "config" / "repo.json"
    conf = json.loads(path.read_text(encoding="utf-8"))
    for key in ("theme", "source", "target", "title"):
        conf.pop(key, None)
    if theme == "apphelp":
        conf.setdefault("apphelp", {})["strict"] = False
    return conf


def _build(tmp_path, home, theme, highlight=None):
    extra = _app_conf(theme)
    if highlight:
        extra["markdown"] = {"highlight": highlight}
    cfg = write_repo(tmp_path / f"{theme}-{highlight}", theme,
                     {"code.md": page("Code", CODE, Category="Post", Date="2026-10-08", DocType="Reference")}, **extra)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    target = tmp_path / f"{theme}-{highlight}" / "target"
    return target, (target / "code.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf", "apphelp"])
def test_pygments_highlights_at_build_time(tmp_path, home, theme):
    target, html = _build(tmp_path, home, theme, "pygments")
    assert '<div class="highlight">' in html
    assert "highlight.js" not in html and "hljs.highlightAll" not in html
    assert 'href="resources/pygments.css"' in html
    css = (target / "resources" / "pygments.css").read_text(encoding="utf-8")
    assert ".highlight" in css and "prefers-color-scheme: dark" in css


@pytest.mark.parametrize("theme", ["techdoc", "blog"])
def test_client_is_the_default(tmp_path, home, theme):
    target, html = _build(tmp_path, home, theme)
    assert "highlight.js" in html and "hljs.highlightAll" in html
    assert '<div class="highlight">' not in html
    assert not (target / "resources" / "pygments.css").exists()


def test_none_turns_highlighting_off(tmp_path, home):
    _target, html = _build(tmp_path, home, "techdoc", "none")
    assert "highlight.js" not in html and '<div class="highlight">' not in html


def test_pygments_css_uses_the_chosen_styles():
    css = pygments_css(load_settings({"markdown": {"highlight": "pygments", "pygments_style": "friendly",
                                                   "pygments_style_dark": "native"}}))
    assert css.count(".highlight") > 10

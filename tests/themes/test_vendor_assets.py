"""Bundled themes load Highlight, UIkit, DataTables and the search engine from resources/vendor (P6)."""

import json
import re

import pytest

from kb4it.core.vendor import vendor_names
from tests.helpers import ROOT, page, run_kb4it, write_repo

THEMES = ROOT / "kb4it" / "resources" / "themes"
OLD_PATHS = ("/framework/Highlight", "/framework/uikit", "/framework/datatables", "/framework/TimelineJS",
             "resources/common/js/", "resources/common/css/kb4it-search")
LINK = re.compile(r"""(?:src|href)=["']([^"'#?]+)""")


def _conf(theme, **extra):
    path = THEMES / theme / "apps" / "default" / "config" / "repo.json"
    conf = json.loads(path.read_text(encoding="utf-8"))
    for key in ("theme", "source", "target", "title"):
        conf.pop(key, None)
    conf.update(extra)
    return conf


def _build(tmp_path, home, theme, **extra):
    if theme == "apphelp":
        pages = {"start.md": page("Start", "Text.", DocType="Tutorial", HelpId="start")}
        cfg = write_repo(tmp_path / theme, theme, pages, apphelp={"strict": False}, **extra)
    else:
        pages = {"a.md": page("Alpha", "Text.", Category="Post", Date="2026-10-08", Tag="fish")}
        cfg = write_repo(tmp_path / theme, theme, pages, **_conf(theme, **extra))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return cfg, tmp_path / theme / "target"


def _resource_links(html):
    return [link for link in LINK.findall(html) if "resources/" in link and "://" not in link]


def test_bundled_vendor_libraries():
    assert vendor_names() == ["datatables", "gallery", "highlight", "search", "tablefilter", "uikit"]


def test_no_duplicate_vendor_in_tree():
    for name in ("Highlight", "uikit", "datatables", "TimelineJS"):
        assert not list(THEMES.glob(f"*/framework/{name}")), name


@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf", "apphelp"])
def test_pages_link_vendor_assets(tmp_path, home, theme):
    _cfg, target = _build(tmp_path, home, theme)
    name = "start.html" if theme == "apphelp" else "index.html"
    links = _resource_links((target / name).read_text(encoding="utf-8"))
    assert any(link.startswith("resources/vendor/") for link in links), links
    for link in links:
        assert not any(old in link for old in OLD_PATHS), link
        assert (target / link).is_file(), link


def test_upgrade_drops_old_library_copies(tmp_path, home):
    """A target built before the move holds framework copies; the next build removes them (Review Focus 1)."""
    _cfg, target = _build(tmp_path, home, "blog")
    old = [target / "resources" / "themes" / "blog" / "framework" / "Highlight" / "highlight.js",
           target / "resources" / "themes" / "blog" / "framework" / "TimelineJS" / "js" / "timeline.js",
           target / "resources" / "common" / "js" / "kb4it-search.js"]
    for path in old:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("old", encoding="utf-8")
    result = run_kb4it("build", tmp_path / "blog" / "config" / "repo.json", cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    for path in old:
        assert not path.exists(), path
    assert not (target / "resources" / "themes" / "blog" / "framework" / "TimelineJS").exists()
    assert (target / "resources" / "vendor" / "highlight" / "highlight.js").is_file()


def test_apphelp_versioned_search_script(tmp_path, home):
    """With versions on, the engine sits in the version folder and the page links it relatively (Review Focus 2)."""
    cfg, _target = _build(tmp_path, home, "apphelp", version="1.0")
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["apphelp"]["versions"] = {"enabled": True}
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    site = tmp_path / "apphelp" / "target"
    assert (site / "1.0" / "resources" / "vendor" / "search" / "js" / "kb4it-search.js").is_file()
    html = (site / "1.0" / "start.html").read_text(encoding="utf-8")
    assert 'src="resources/vendor/search/js/kb4it-search.js"' in html

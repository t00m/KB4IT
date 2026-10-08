"""Publishing: site_url, sitemap.xml, robots.txt, Atom feed and page metadata."""

import pytest

from kb4it.core.exceptions import ConfigError
from kb4it.core.publish import absolute, site_url
from tests.helpers import page, run_kb4it, write_repo


@pytest.mark.parametrize("raw, expected", [
    (None, None), ("", None),
    ("https://t00m.github.io/blog", "https://t00m.github.io/blog/"),
    ("http://example.org/", "http://example.org/"),
])
def test_site_url(raw, expected):
    assert site_url({"site_url": raw} if raw is not None else {}) == expected


@pytest.mark.parametrize("raw", ["t00m.github.io/blog", "ftp://x.org/", 42])
def test_bad_site_url(raw):
    with pytest.raises(ConfigError):
        site_url({"site_url": raw})


def test_absolute():
    assert absolute("https://x.org/kb/", "a.html") == "https://x.org/kb/a.html"
    assert absolute("https://x.org/kb/", "admin\\index.html") == "https://x.org/kb/admin/index.html"


def test_bad_site_url_stops_the_build(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x")}, site_url="example.org")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "site_url" in result.stdout


def _techdoc(tmp_path, home, name="repo", **conf):
    pages = {"a.md": page("A", Date="2026-05-01", Tag="x"), "b.md": page("B", Tag="y")}
    cfg = write_repo(tmp_path / name, "techdoc", pages, **conf)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return cfg, tmp_path / name / "target", result


def test_sitemap_and_robots(tmp_path, home):
    import xml.etree.ElementTree as ET
    _cfg, target, result = _techdoc(tmp_path, home, site_url="https://x.org/kb")
    assert "[SITEMAP] WRITTEN" in result.stdout
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    tree = ET.parse(target / "sitemap.xml")
    urls = {u.find("s:loc", ns).text: u.find("s:lastmod", ns).text for u in tree.findall("s:url", ns)}
    assert urls["https://x.org/kb/a.html"] == "2026-05-01"
    assert "https://x.org/kb/b.html" in urls and "https://x.org/kb/index.html" in urls
    assert not any("search.html" in u or "/resources/" in u for u in urls)
    assert "Sitemap: https://x.org/kb/sitemap.xml" in (target / "robots.txt").read_text(encoding="utf-8")


def test_no_site_url_no_sitemap(tmp_path, home):
    _cfg, target, result = _techdoc(tmp_path, home)
    assert "[SITEMAP] SKIP reason=no_site_url" in result.stdout
    assert not (target / "sitemap.xml").exists() and not (target / "robots.txt").exists()


def test_user_robots_wins_and_sitemap_false(tmp_path, home):
    import json
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x")}, site_url="https://x.org/")
    (tmp_path / "repo" / "source" / "robots.txt").write_text("User-agent: *\nDisallow: /private/\n", encoding="utf-8")
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    target = tmp_path / "repo" / "target"
    assert "Disallow: /private/" in (target / "robots.txt").read_text(encoding="utf-8")
    conf = json.loads(cfg.read_text(encoding="utf-8"))
    conf["sitemap"] = False
    cfg.write_text(json.dumps(conf), encoding="utf-8")
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    assert not (target / "sitemap.xml").exists()
    assert (target / "robots.txt").exists(), "a robots.txt you wrote is never removed"

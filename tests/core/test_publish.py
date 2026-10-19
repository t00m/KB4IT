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


def _blog_conf(**extra):
    import json
    from tests.helpers import ROOT
    path = ROOT / "kb4it" / "resources" / "themes" / "blog" / "apps" / "default" / "config" / "repo.json"
    conf = json.loads(path.read_text(encoding="utf-8"))
    for key in ("theme", "source", "target", "title"):
        conf.pop(key, None)
    conf.update(extra)
    return conf


def _feed(path):
    import xml.etree.ElementTree as ET
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.parse(path).getroot()
    return [(e.find("a:title", ns).text, e.find("a:link", ns).get("href"), e.find("a:updated", ns).text,
             e.find("a:content", ns).text) for e in root.findall("a:entry", ns)]


def test_blog_feed(tmp_path, home):
    pages = {"old.md": page("Old post", "Old body.", Category="Post", Date="2026-01-01", Author="Ana"),
             "new.md": page("New post", "New *body*.", Category="Post", Date="2026-03-01 10:30", Author="Bo"),
             "note.md": page("A note", Category="Note", Date="2026-02-01")}
    cfg = write_repo(tmp_path / "blog", "blog", pages, **_blog_conf(site_url="https://x.org/blog/"))
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    entries = _feed(tmp_path / "blog" / "target" / "feed.xml")
    assert [e[0] for e in entries] == ["New post", "A note", "Old post"]
    assert entries[0][1] == "https://x.org/blog/new.html"
    assert entries[0][2] == "2026-03-01T10:30:00Z"
    assert "<em>body</em>" in entries[0][3]


def test_feed_filters_and_limits(tmp_path, home):
    pages = {f"p{n}.md": page(f"Post {n}", Category="Post", Date=f"2026-01-0{n}") for n in range(1, 5)}
    pages["note.md"] = page("Note", Category="Note", Date="2026-01-09")
    pages["undated.md"] = page("Undated", Category="Post")
    feed = {"enabled": True, "limit": 2, "categories": ["Post"], "full_content": False}
    cfg = write_repo(tmp_path / "td", "techdoc", pages, site_url="https://x.org/", feed=feed)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    entries = _feed(tmp_path / "td" / "target" / "feed.xml")
    assert [e[0] for e in entries] == ["Post 4", "Post 3"]


def test_feed_is_off_by_default_in_techdoc_and_needs_site_url(tmp_path, home):
    cfg = write_repo(tmp_path / "td", "techdoc", {"a.md": page("A", Date="2026-01-01", Tag="x")}, site_url="https://x.org/")
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    assert not (tmp_path / "td" / "target" / "feed.xml").exists()
    cfg = write_repo(tmp_path / "bl", "blog", {"a.md": page("A", Category="Post", Date="2026-01-01")}, **_blog_conf())
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert "[FEED] SKIP reason=no_site_url" in result.stdout
    assert not (tmp_path / "bl" / "target" / "feed.xml").exists()


def _head(html):
    return html[:html.index("</head>")]


def test_page_metadata_with_site_url(tmp_path, home):
    long_body = "First paragraph " + "word " * 60 + "end."
    pages = {"a.md": page("Alpha", long_body, Author="Ana", Tag="x"),
             "b.md": page("Beta", "Body.", Summary="Short summary", Tag="y")}
    cfg = write_repo(tmp_path / "repo", "techdoc", pages, site_url="https://x.org/kb/", og_image="resources/og.png")
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    target = tmp_path / "repo" / "target"
    head = _head((target / "a.html").read_text(encoding="utf-8"))
    assert '<link rel="canonical" href="https://x.org/kb/a.html">' in head
    assert '<meta property="og:title" content="Alpha">' in head
    assert '<meta property="og:type" content="article">' in head
    assert '<meta name="author" content="Ana">' in head
    assert '<meta property="og:image" content="https://x.org/kb/resources/og.png">' in head
    assert '<meta name="twitter:card" content="summary_large_image">' in head
    description = head.split('<meta name="description" content="')[1].split('"')[0]
    assert description.startswith("First paragraph") and len(description) <= 160 and description.endswith("…")
    assert head.count('name="description"') == 1, "the theme's fixed description is gone"
    assert '<meta name="description" content="Short summary">' in _head((target / "b.html").read_text(encoding="utf-8"))
    index_head = _head((target / "index.html").read_text(encoding="utf-8"))
    assert '<meta property="og:type" content="website">' in index_head


def test_page_metadata_without_site_url(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("Alpha", "Some text.", Tag="x")})
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    head = _head((tmp_path / "repo" / "target" / "a.html").read_text(encoding="utf-8"))
    assert "canonical" not in head and "og:url" not in head
    assert '<meta property="og:title" content="Alpha">' in head
    assert '<meta name="twitter:card" content="summary">' in head
    assert head.count("<!-- kb4it:meta -->") == 1


def test_blog_head_links_its_feed(tmp_path, home):
    cfg = write_repo(tmp_path / "bl", "blog", {"a.md": page("A", Category="Post", Date="2026-01-01")},
                     **_blog_conf(site_url="https://x.org/"))
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    head = _head((tmp_path / "bl" / "target" / "a.html").read_text(encoding="utf-8"))
    assert '<link rel="alternate" type="application/atom+xml"' in head and 'href="feed.xml"' in head

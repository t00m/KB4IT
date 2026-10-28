"""Indexing control (seo.index, seo.noindex_keys), dateModified and the Open Graph article tags in every theme."""

import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

import pytest

from tests.helpers import page, run_kb4it, write_repo

THEMES = ("techdoc", "blog", "bookshelf", "apphelp")
SITE = "https://kb.example.org/"
KEYS = {"Author": "Ana, Bo", "Date": "2026-10-23", "DocType": "How-to guide", "Tag": "service, binding",
        "Category": "Procedure", "Summary": "Bind the service."}
APPHELP = {"strict": True, "vocabulary": {"Feature": ["Binding"]}}
ROBOTS = re.compile(r'<meta name="robots" content="([^"]*)">')
JSONLD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
# Listing pages of the document themes; apphelp has none.
LISTING = ("Tag.html", "Tag_service.html", "properties.html", "stats.html")


def _pages(theme, **extra):
    keys = dict(KEYS, **extra)
    if theme == "apphelp":
        keys.update(Section="How-to", Order="10", Feature="Binding")
    return {"binding.md": page("Binding", "## Step 1\n\nText.", **keys)}


def _build(tmp_path, home, theme, extra=None, **config):
    if theme == "apphelp":
        config.setdefault("apphelp", APPHELP)
    config.setdefault("editor", True)
    cfg = write_repo(tmp_path / "repo", theme, _pages(theme, **(extra or {})), **config)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return tmp_path / "repo" / "target", result


def _robots(path):
    found = ROBOTS.findall(path.read_text(encoding="utf-8"))
    assert len(found) <= 1
    return found[0] if found else ""


def _sitemap(target):
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    tree = ET.parse(target / "sitemap.xml")
    return {u.find("s:loc", ns).text: u.find("s:lastmod", ns).text for u in tree.findall("s:url", ns)}


def _meta(html, prop):
    return re.findall(rf'<meta property="{prop}" content="([^"]*)">', html)


def _modified(html):
    return json.loads(JSONLD.findall(html)[0])["@graph"][-1]["dateModified"]


@pytest.mark.parametrize("theme", THEMES)
def test_index_false_hides_the_site(tmp_path, home, theme):
    target, result = _build(tmp_path, home, theme, seo={"index": False})
    pages = sorted(target.glob("*.html"))
    assert pages
    for path in pages:
        assert _robots(path) == "noindex, nofollow", path.name
    robots = (target / "robots.txt").read_text(encoding="utf-8")
    assert "User-agent: *\nDisallow: /" in robots, "written even without site_url"
    assert not (target / "sitemap.xml").exists()
    assert "INDEX_UNSET" not in result.stdout


@pytest.mark.parametrize("theme", THEMES)
def test_index_true_keeps_listing_pages_out(tmp_path, home, theme):
    target, result = _build(tmp_path, home, theme, site_url=SITE, seo={"index": True}, events=["Procedure"])
    urls = _sitemap(target)
    assert SITE + "binding.html" in urls
    assert _robots(target / "binding.html") == ""
    assert "INDEX_UNSET" not in result.stdout
    if theme == "apphelp":
        assert SITE + "topics.html" in urls and _robots(target / "topics.html") == ""
        return
    for name in LISTING:
        assert _robots(target / name) == "noindex, follow", name
        assert SITE + name not in urls
    events = sorted(p.name for p in target.glob("events_2026*.html"))
    assert events or theme == "bookshelf", "bookshelf builds no event pages"
    assert all(_robots(target / name) == "noindex, follow" for name in events)
    assert "Allow: /" in (target / "robots.txt").read_text(encoding="utf-8")


@pytest.mark.parametrize("theme", ("techdoc", "bookshelf"))
def test_noindex_keys_false(tmp_path, home, theme):
    target, _ = _build(tmp_path, home, theme, site_url=SITE, seo={"index": True, "noindex_keys": False})
    assert _robots(target / "Tag_service.html") == ""
    assert SITE + "Tag_service.html" in _sitemap(target)


@pytest.mark.parametrize("theme", THEMES)
def test_index_unset_is_reported(tmp_path, home, theme):
    _target, result = _build(tmp_path, home, theme)
    assert "[SEO] INDEX_UNSET" in result.stdout


@pytest.mark.parametrize("theme", THEMES)
def test_404_and_add_pages_are_never_indexed(tmp_path, home, theme):
    target, _ = _build(tmp_path, home, theme, site_url=SITE, seo={"index": True})
    assert _robots(target / "404.html") == "noindex"
    assert _robots(target / "add.html") == "noindex"
    urls = _sitemap(target)
    assert SITE + "404.html" not in urls and SITE + "add.html" not in urls


def test_techdoc_admin_page_is_never_indexed(tmp_path, home):
    target, _ = _build(tmp_path, home, "techdoc", site_url=SITE, seo={"index": True}, admin=True)
    assert "noindex" in _robots(target / "admin" / "index.html")


def test_user_robots_wins_over_index_false(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", _pages("techdoc"), seo={"index": False})
    (tmp_path / "repo" / "source" / "robots.txt").write_text("User-agent: *\nDisallow: /private/\n", encoding="utf-8")
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    assert "Disallow: /private/" in (tmp_path / "repo" / "target" / "robots.txt").read_text(encoding="utf-8")


def test_a_robots_txt_kb4it_did_not_write_is_kept(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", _pages("techdoc"), seo={"index": False})
    (tmp_path / "repo" / "target").mkdir()
    (tmp_path / "repo" / "target" / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0
    assert (tmp_path / "repo" / "target" / "robots.txt").read_text(encoding="utf-8") == "User-agent: *\nAllow: /\n"
    assert "ROBOTS_KEPT" in result.stdout


@pytest.mark.parametrize("theme", THEMES)
def test_article_tags_and_locale(tmp_path, home, theme):
    target, _ = _build(tmp_path, home, theme, site_url=SITE, seo={"index": True, "lang": "es-ES"})
    html = (target / "binding.html").read_text(encoding="utf-8")
    assert _meta(html, "og:locale") == ["es_ES"]
    assert _meta(html, "article:published_time") == ["2026-10-23"]
    assert _meta(html, "article:author") == ["Ana", "Bo"]
    assert _meta(html, "article:tag") == ["binding", "service"] or _meta(html, "article:tag") == ["service", "binding"]
    assert _meta(html, "article:section") == ["Procedure"]
    assert _meta(html, "article:modified_time") == [_modified(html)]
    assert _sitemap(target)[SITE + "binding.html"] == _modified(html), "the sitemap and the page agree"
    index = (target / "index.html").read_text(encoding="utf-8")
    assert not _meta(index, "article:tag") and _meta(index, "og:locale") == ["es_ES"]


def test_plain_language_has_no_locale(tmp_path, home):
    target, _ = _build(tmp_path, home, "techdoc", seo={"lang": "es"})
    assert not _meta((target / "binding.html").read_text(encoding="utf-8"), "og:locale")


def test_modified_key_wins(tmp_path, home):
    target, _ = _build(tmp_path, home, "techdoc", extra={"Modified": "2026-10-25"})
    html = (target / "binding.html").read_text(encoding="utf-8")
    assert _modified(html) == "2026-10-25"
    assert not (target / "Modified.html").exists(), "Modified is a blocked key, like Date"
    assert 'href="Modified_' not in html, "no link to a page that does not exist"


def test_modified_is_never_older_than_date(tmp_path, home):
    target, _ = _build(tmp_path, home, "techdoc", extra={"Date": "2099-01-01", "Modified": "2026-10-25"})
    assert _modified((target / "binding.html").read_text(encoding="utf-8")) == "2099-01-01"


def test_modified_falls_back_to_the_file_time(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", _pages("techdoc"))
    os.utime(tmp_path / "repo" / "source" / "binding.md", (1793000000, 1793000000))
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    from datetime import datetime
    value = _modified((tmp_path / "repo" / "target" / "binding.html").read_text(encoding="utf-8"))
    assert datetime.fromisoformat(value).timestamp() == 1793000000


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_modified_from_the_last_commit(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", _pages("techdoc"))
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@x", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@x", GIT_AUTHOR_DATE="2026-10-26T08:00:00+02:00",
               GIT_COMMITTER_DATE="2026-10-26T08:00:00+02:00")
    for args in (["init", "-q"], ["add", "source"], ["commit", "-q", "-m", "docs"]):
        subprocess.run(["git", "-C", str(tmp_path / "repo"), *args], check=True, capture_output=True, env=env)
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    target = tmp_path / "repo" / "target"
    assert _modified((target / "binding.html").read_text(encoding="utf-8")) == "2026-10-26T08:00:00+02:00"
    assert (tmp_path / "repo" / "var" / "db" / "gitdates.json").exists()

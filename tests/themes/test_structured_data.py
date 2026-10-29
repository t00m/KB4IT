"""JSON-LD and the page language in every bundled theme."""

import json
import re

import pytest

from tests.helpers import page, run_kb4it, write_repo

JSONLD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
TITLE = 'Update </script> "Peppol" & DRCCE'
KEYS = {"Author": "Tomás Vírseda", "Date": "2026-10-23", "DocType": "How-to guide", "Tag": "service, binding",
        "Category": "Procedure", "Summary": "Keep Peppol certificates up to date."}
APPHELP = {"strict": True, "vocabulary": {"Feature": ["Binding"]}}


def _pages(theme):
    keys = dict(KEYS)
    if theme == "apphelp":
        keys.update(Section="How-to", Order="10", Feature="Binding")
    return {"binding.md": page(TITLE, "## Step 1 - Get the URL\n\nText.", **keys)}


def _build(tmp_path, home, theme, **config):
    if theme == "apphelp":
        config.setdefault("apphelp", APPHELP)
    cfg = write_repo(tmp_path / "repo", theme, _pages(theme), **config)
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    return tmp_path / "repo" / "target", result


def _jsonld(html):
    found = JSONLD.findall(html)
    assert len(found) <= 1, "one JSON-LD block per page"
    return json.loads(found[0]) if found else None


@pytest.mark.parametrize("theme, page_type", [
    ("techdoc", ["TechArticle", "HowTo"]), ("blog", ["TechArticle", "HowTo"]),
    ("bookshelf", ["TechArticle", "HowTo"]), ("apphelp", ["TechArticle", "HowTo"]),
])
def test_document_jsonld(tmp_path, home, theme, page_type):
    target, _ = _build(tmp_path, home, theme, site_url="https://kb.example.org/", seo={"lang": "es"})
    html = (target / "binding.html").read_text(encoding="utf-8")
    assert re.search(r'<html lang="es"', html)
    data = _jsonld(html)
    node = data["@graph"][0]
    assert data["@context"] == "https://schema.org"
    assert node["@type"] == page_type
    assert node["headline"] == TITLE
    assert node["url"] == "https://kb.example.org/binding.html"
    assert node["inLanguage"] == "es"
    assert node["datePublished"] == "2026-10-23"
    assert node["description"] == "Keep Peppol certificates up to date."
    # One Person per author: its page in the themes with person pages, the home page in apphelp.
    person = "#person-Tomás_Vírseda" if theme == "apphelp" else "Author_Tomás_Vírseda.html#person"
    assert node["author"] == {"@type": "Person", "@id": f"https://kb.example.org/{person}", "name": "Tomás Vírseda"}
    assert "</script>" not in JSONLD.findall(html)[0]
    home_page = _jsonld((target / "index.html").read_text(encoding="utf-8"))
    website = [n for n in home_page["@graph"] if n["@type"] == "WebSite"][0]
    assert website["@id"] == "https://kb.example.org/#website"
    assert website["potentialAction"]["target"]["urlTemplate"].startswith("https://kb.example.org/search.html?q=")
    missing = _jsonld((target / "404.html").read_text(encoding="utf-8"))
    assert missing is None, "a system page is not content"


@pytest.mark.parametrize("theme, default_type", [
    ("techdoc", "TechArticle"), ("blog", "BlogPosting"), ("bookshelf", "Chapter"),
])
def test_theme_default_type(tmp_path, home, theme, default_type):
    cfg = write_repo(tmp_path / "repo", theme, {"a.md": page("A", Tag="x", Category="Post")})
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    node = _jsonld((tmp_path / "repo" / "target" / "a.html").read_text(encoding="utf-8"))["@graph"][0]
    assert node["@type"] == default_type
    assert "url" not in node, "no site_url, no absolute URLs"
    assert '<html lang="en"' in (tmp_path / "repo" / "target" / "a.html").read_text(encoding="utf-8")


def test_blog_category_is_the_section(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "blog", {"a.md": page("A", Tag="x", Category="Post")})
    assert run_kb4it("build", cfg, cwd=tmp_path, home=home).returncode == 0
    node = _jsonld((tmp_path / "repo" / "target" / "a.html").read_text(encoding="utf-8"))["@graph"][0]
    assert node["articleSection"] == "Post" and "genre" not in node


def test_apphelp_vocabulary(tmp_path, home):
    target, _ = _build(tmp_path, home, "apphelp")
    node = _jsonld((target / "binding.html").read_text(encoding="utf-8"))["@graph"][0]
    assert node["about"] == {"@type": "Thing", "name": "Binding"}
    assert node["articleSection"] == "How-to"
    assert "position" not in node and "Order" not in json.dumps(node)


def test_apphelp_lang_wins(tmp_path, home):
    target, _ = _build(tmp_path, home, "apphelp", seo={"lang": "es"}, apphelp=dict(APPHELP, lang="fr"))
    html = (target / "binding.html").read_text(encoding="utf-8")
    assert '<html lang="fr">' in html
    assert _jsonld(html)["@graph"][0]["inLanguage"] == "fr"


def test_map_override_and_switch_off(tmp_path, home):
    target, _ = _build(tmp_path, home, "techdoc", seo={"map": {"Category": None, "Tag": "about:DefinedTerm"}})
    node = _jsonld((target / "binding.html").read_text(encoding="utf-8"))["@graph"][0]
    assert "genre" not in node and "keywords" not in node
    assert {"@type": "DefinedTerm", "name": "binding"} in node["about"]
    target, _ = _build(tmp_path, home, "techdoc", seo={"structured_data": False})
    assert _jsonld((target / "binding.html").read_text(encoding="utf-8")) is None


def test_bad_seo_block_stops_the_build(tmp_path, home):
    cfg = write_repo(tmp_path / "repo", "techdoc", {"a.md": page("A", Tag="x")}, seo={"lang": "not a tag"})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 1
    assert "seo.lang" in result.stdout

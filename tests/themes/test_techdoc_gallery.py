"""techdoc gallery: the images of every document, filters from their properties, the menu link."""

import importlib.util
import json
import re
import sys

import pytest

from tests.helpers import ROOT, page, run_kb4it, write_repo
from tests.themes.test_techdoc_media import png

LOGIC = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic"
sys.path.insert(0, str(LOGIC))  # techdoc_gallery imports techdoc_media
_spec = importlib.util.spec_from_file_location("techdoc_gallery", LOGIC / "techdoc_gallery.py")
gallery = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gallery)

DOCS = {
    "storage.md": page("Storage screenshots",
                       "![Disk usage chart](resources/images/a.png)\n\n![Backup console](resources/images/b.png)\n\n"
                       "![Gone](resources/images/gone.png)\n",
                       Category="Procedure", Date="2026-03-01", Product="Linux", Tag="storage, backup"),
    "report.md": page("Monitoring report", '<img src="resources/images/c.png" alt="Alert &amp; dashboard">\n',
                      Category="Report", Date="2025-11-20", Product="SAP", Summary="Weekly report, short."),
    "plain.md": page("No pictures", "Text.", Category="Note"),
}


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-gallery")
    home = base / "home"
    home.mkdir()
    images = base / "source" / "resources" / "images"
    images.mkdir(parents=True)
    for name in ("a.png", "b.png", "c.png"):
        (images / name).write_bytes(png(400, 300))
    cfg = write_repo(base, "techdoc", DOCS)
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return {"target": base / "target", "log": result.stdout}


def read(site, name):
    return (site["target"] / name).read_text(encoding="utf-8")


def test_document_images_in_order_without_code_and_duplicates():
    text = ("---\nCategory: Note\n---\n\n# T\n\n![One](one.png \"title\")\n\n`![no](code.png)`\n\n"
            "```\n![no](fence.png)\n```\n\n<img alt='Two' src=\"two.png\">\n\n![Three][ref]\n\n"
            "![One again](one.png)\n\n![Four](<four five.png>)\n\n[ref]: three.png\n")
    assert gallery.document_images(text) == [("one.png", "One"), ("two.png", "Two"), ("three.png", "Three"),
                                             ("four five.png", "Four")]


def test_filter_keys_follow_the_menu_then_the_name():
    assert gallery.filter_keys({"Tag", "Author", "Product", "Category"}, ["Product", "Missing", "Category"]) == [
        "Product", "Category", "Author", "Tag"]


def test_gallery_page_shows_every_existing_image_newest_document_first(site):
    html = read(site, "gallery.html")
    srcs = re.findall(r'<a class="kb-gal-zoom" href="([^"]+)"', html)
    assert srcs == ["resources/images/a.png", "resources/images/b.png", "resources/images/c.png"]
    assert "gone.png" not in html
    assert '<a href="storage.html">Storage screenshots</a>' in html
    assert 'alt="Alert &amp; dashboard"' in html
    assert "3 images</span> from 2 documents" in html
    assert "[THEME] GALLERY images=3 docs=2" in site["log"]


def test_gallery_filters_come_from_document_properties(site):
    html = read(site, "gallery.html")
    keys = re.findall(r'<summary>([^<]+)</summary>', html[html.index("GALLERY FILTERS :: START"):])
    assert keys[-1] == "Year" and {"Category", "Product", "Tag"} <= set(keys)
    assert "Summary" not in keys and "Title" not in keys and "Date" not in keys
    assert 'data-key="Product" value="Linux"' in html and 'data-key="Year" value="2026"' in html
    assert re.search(r'value="Linux">\s*<label[^>]*>Linux</label>\s*<span class="kb-gal-n" data-count="2">', html)


def test_gallery_data_is_json_for_the_script(site):
    html = read(site, "gallery.html")
    raw = re.search(r'<script type="application/json" id="kb-gal-data">(.*?)</script>', html, re.DOTALL).group(1)
    items = json.loads(raw)["items"]
    assert [i["href"] for i in items] == ["storage.html", "storage.html", "report.html"]
    assert items[0]["props"]["Tag"] == ["backup", "storage"]
    assert items[2]["caption"] == "Alert & dashboard"
    assert "gallery.js" in html


def test_gallery_is_in_the_menu_and_a_system_page(site):
    assert 'href="gallery.html"' in read(site, "storage.html")
    table = read(site, "all.html")
    table = table[table.index("<table"):]
    assert "gallery.html" not in table


def test_gallery_without_images_says_so(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    cfg = write_repo(tmp_path, "techdoc", {"plain.md": DOCS["plain.md"]})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "target" / "gallery.html").read_text(encoding="utf-8")
    assert "No document shows an image yet" in html and "kb-gal-data" not in html

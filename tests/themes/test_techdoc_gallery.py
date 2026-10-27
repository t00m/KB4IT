"""techdoc gallery: thumbnails, filters from document properties, no image in the page, the menu link."""

import importlib.util
import json
import os
import re
import sys

import pytest
from PIL import Image

from tests.helpers import ROOT, page, run_kb4it, write_repo
from tests.themes.test_techdoc_media import png

LOGIC = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic"
sys.path.insert(0, str(LOGIC))  # techdoc_gallery imports techdoc_media and techdoc_thumbs


def _load(name):
    spec = importlib.util.spec_from_file_location(name, LOGIC / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gallery = _load("techdoc_gallery")
thumbs = _load("techdoc_thumbs")

DOCS = {
    "storage.md": page("Storage screenshots",
                       "![Disk usage chart](resources/images/a.png)\n\n![Backup console](resources/images/b.jpg)\n\n"
                       "![Gone](resources/images/gone.png)\n",
                       Category="Procedure", Date="2026-03-01", Product="Linux", Tag="storage, backup"),
    "report.md": page("Monitoring report", '<img src="resources/images/c.png" alt="Alert &amp; dashboard">\n',
                      Category="Report", Date="2025-11-20", Product="SAP", Summary="Weekly report, short."),
    "plain.md": page("No pictures", "Text.", Category="Note"),
}


def real_image(path, size, mode="RGB"):
    Image.new(mode, size, (200, 60, 60) if mode == "RGB" else (200, 60, 60, 128)).save(path)


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-gallery")
    home = base / "home"
    home.mkdir()
    images = base / "source" / "resources" / "images"
    images.mkdir(parents=True)
    real_image(images / "a.png", (1600, 900))
    real_image(images / "b.jpg", (1200, 1600))
    (images / "c.png").write_bytes(png(300, 200))  # a header only: Pillow cannot read it, the original is shown
    cfg = write_repo(base, "techdoc", DOCS)
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return {"base": base, "home": home, "cfg": cfg, "target": base / "target", "log": result.stdout}


def read(site, name):
    return (site["target"] / name).read_text(encoding="utf-8")


def data(site):
    html = read(site, "gallery.html")
    raw = re.search(r'<script type="application/json" id="kb-gal-data">(.*?)</script>', html, re.DOTALL).group(1)
    return json.loads(raw)


def test_document_images_in_order_without_code_and_duplicates():
    text = ("---\nCategory: Note\n---\n\n# T\n\n![One](one.png \"title\")\n\n`![no](code.png)`\n\n"
            "```\n![no](fence.png)\n```\n\n<img alt='Two' src=\"two.png\">\n\n![Three][ref]\n\n"
            "![One again](one.png)\n\n![Four](<four five.png>)\n\n[ref]: three.png\n")
    assert gallery.document_images(text) == [("one.png", "One"), ("two.png", "Two"), ("three.png", "Three"),
                                             ("four five.png", "Four")]


def test_filter_keys_follow_the_menu_then_the_name():
    assert gallery.filter_keys({"Tag", "Author", "Product", "Category"}, ["Product", "Missing", "Category"]) == [
        "Product", "Category", "Author", "Tag"]


def test_thumbnail_is_a_smaller_webp_reused_until_the_file_changes(tmp_path):
    original = tmp_path / "shot.png"
    real_image(original, (1600, 900), "RGBA")
    cache = tmp_path / "cache"
    name, width, height = thumbs.make_thumbnail(str(original), str(cache))
    assert name.endswith(".webp") and (width, height) == (thumbs.THUMB_WIDTH, 270)
    with Image.open(cache / name) as made:
        assert made.format == "WEBP" and made.size == (width, height) and made.mode == "RGBA"
    stamp = os.stat(cache / name).st_mtime_ns
    assert thumbs.make_thumbnail(str(original), str(cache))[0] == name
    assert os.stat(cache / name).st_mtime_ns == stamp
    real_image(original, (1600, 800))
    os.utime(original, ns=(stamp + 10**9, stamp + 10**9))
    assert thumbs.make_thumbnail(str(original), str(cache))[0] != name


def test_no_thumbnail_for_small_vector_or_unreadable_images(tmp_path):
    small = tmp_path / "small.png"
    real_image(small, (200, 100))
    (tmp_path / "logo.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="900" height="90"/>', encoding="utf-8")
    (tmp_path / "bad.png").write_bytes(b"not an image")
    for name in ("small.png", "logo.svg", "bad.png"):
        assert thumbs.make_thumbnail(str(tmp_path / name), str(tmp_path / "cache")) is None


def test_gallery_page_loads_no_image(site):
    html = read(site, "gallery.html")
    main = html[html.index("GALLERY PAGE :: START"):html.index("GALLERY PAGE :: END")]
    assert "<img" not in main
    assert "3 images in 2 documents. Choose a property on the right" in main
    assert 'data-uk-grid="masonry: pack"' in main and "gallery.js" in main
    assert "[THEME] GALLERY images=3 docs=2 thumbs=2" in site["log"]


def test_gallery_data_has_thumbnails_sizes_and_documents_newest_first(site):
    d = data(site)
    assert [doc["href"] for doc in d["docs"]] == ["storage.html", "report.html"]
    a, b, c = d["items"]
    assert a["src"] == "resources/images/a.png" and a["thumb"].startswith("resources/kb4it-thumbs/")
    assert (a["w"], a["h"]) == (480, 270) and (b["w"], b["h"]) == (480, 640)
    assert c["thumb"] == c["src"] == "resources/images/c.png" and (c["w"], c["h"]) == (300, 200)
    assert c["caption"] == "Alert & dashboard" and c["d"] == 1
    assert d["docs"][0]["props"]["Tag"] == ["backup", "storage"]
    assert all("gone.png" not in item["src"] for item in d["items"])


def test_thumbnails_are_deployed_and_stale_ones_removed(site):
    folder = site["target"] / "resources" / "kb4it-thumbs"
    used = sorted(item["thumb"].rsplit("/", 1)[1] for item in data(site)["items"] if "kb4it-thumbs" in item["thumb"])
    assert sorted(os.listdir(folder)) == used
    (folder / "stale.webp").write_bytes(b"x")
    result = run_kb4it("build", site["cfg"], cwd=site["base"], home=site["home"])
    assert result.returncode == 0, result.stdout
    assert "GALLERY_THUMBS used=2 copied=0 deleted=1" in result.stdout
    assert sorted(os.listdir(folder)) == used


def test_gallery_filters_are_property_buttons(site):
    html = read(site, "gallery.html")
    keys = re.findall(r'<button type="button" class="kb-gal-key" data-key="([^"]+)"', html)
    assert keys[-1] == "Year" and {"Category", "Product", "Tag"} <= set(keys)
    assert "Summary" not in keys and "Title" not in keys and "Date" not in keys
    assert 'id="kb-gal-modal"' in html
    product = next(f for f in data(site)["filters"] if f["key"] == "Product")
    assert product["values"] == [["Linux", 2], ["SAP", 1]]


def test_gallery_is_in_the_menu_and_a_system_page(site):
    assert 'href="gallery.html"' in read(site, "storage.html")
    table = read(site, "all.html")
    assert "gallery.html" not in table[table.index("<table"):]


def test_gallery_without_images_says_so(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    cfg = write_repo(tmp_path, "techdoc", {"plain.md": DOCS["plain.md"]})
    result = run_kb4it("build", cfg, cwd=tmp_path, home=home)
    assert result.returncode == 0, result.stdout
    html = (tmp_path / "target" / "gallery.html").read_text(encoding="utf-8")
    assert "No document shows an image yet" in html and "kb-gal-data" not in html


def test_gallery_script_is_offline_and_builds_no_html():
    script = (ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "framework" / "kb4it" / "js" / "gallery.js")
    text = script.read_text(encoding="utf-8")
    assert "http://" not in text and "https://" not in text
    assert "innerHTML" not in text

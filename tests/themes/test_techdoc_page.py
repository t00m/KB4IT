"""techdoc document page: images, header strip, Summary, banners and the info card."""

import re

import pytest

from tests.helpers import page, run_kb4it, write_repo
from tests.themes.test_techdoc_media import png

BODY_FULL = "## Steps\n\nSee SAP note 736902 first.\n\nRun it."
BODY_IMAGES = "![User list in SU01](resources/images/wide.png)\n\n![Gone](resources/images/gone.png)\n"

DOCS = {
    "full.md": page("Full document", BODY_FULL, Author="Ana", Date="2026-10-01", DocType="How-to guide",
                    Status="Draft", Priority="High", Environment="Production", SID="PRD, PRA",
                    Transaction="SU01", Product="ADS", Category="Procedure", Color="Blue",
                    Summary="Request the credential, then register it."),
    "plain.md": page("Plain document", "Text.", Category="Note", Status="Obsolete"),
    "images.md": page("Images", BODY_IMAGES, Category="Note"),
}


@pytest.fixture(scope="module")
def page_site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-page")
    home = base / "home"
    home.mkdir()
    cfg = write_repo(base / "repo", "techdoc", DOCS)
    images = base / "repo" / "source" / "resources" / "images"
    images.mkdir(parents=True)
    (images / "wide.png").write_bytes(png(1100, 480))
    for i in (1, 2, 3):
        (images / f"s{i}.png").write_bytes(png(900, 420))
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return {"target": base / "repo" / "target", "log": result.stdout}


def read(site, name):
    # build_page pretty-prints the page, so whitespace between tags is dropped before comparing.
    return re.sub(r">\s+<", "><", (site["target"] / name).read_text(encoding="utf-8"))


def test_images_page_has_figures_lightbox_and_placeholder(page_site):
    html = read(page_site, "images.html")
    assert '<figure class="kb-figure"><a class="kb-zoom" href="resources/images/wide.png"' in html
    assert 'data-uk-lightbox="toggle: a.kb-zoom; animation: fade"' in html
    assert "Image missing: <code>resources/images/gone.png</code>" in html


def test_missing_image_is_logged(page_site):
    assert "[THEME] IMAGE_MISSING doc=images.md src=resources/images/gone.png" in page_site["log"]


def test_header_strip_shows_badges_then_links(page_site):
    html = read(page_site, "full.html")
    strip = html[html.index("HEADER STRIP :: START"):html.index("HEADER STRIP :: END")]
    assert strip.index("How-to guide") < strip.index("Draft") < strip.index("High") < strip.index("Ana")
    assert 'href="events_20261001.html"' in strip and 'href="Author_Ana.html"' in strip and 'href="Product_ADS.html"' in strip
    assert "Handover" not in strip                       # empty keys are skipped


def test_summary_keeps_its_commas(page_site):
    assert '<p class="kb-summary">Request the credential, then register it.</p>' in read(page_site, "full.html")
    assert "kb-summary" not in read(page_site, "plain.html")


def test_banners_in_spec_order(page_site):
    html = read(page_site, "full.html")
    assert "<strong>Production</strong> This document changes production systems: PRD, PRA." in html
    assert "<strong>Draft</strong> Not final. Check with the author before you follow it." in html
    assert html.index("kb-banner prod") < html.index("kb-banner draft")
    assert "<strong>Obsolete</strong> Do not follow this document." in read(page_site, "plain.html")


def test_system_pages_have_no_header(page_site):
    assert "HEADER STRIP :: START" not in read(page_site, "index.html")

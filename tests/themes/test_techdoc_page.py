"""techdoc document page: images, header strip, Summary, banners and the info card."""

import importlib.util
import json
import re
import sys

import pytest

from tests.helpers import ROOT, page, run_kb4it, write_repo
from tests.themes.test_techdoc_media import png

LOGIC = ROOT / "kb4it" / "resources" / "themes" / "techdoc" / "logic"
sys.path.insert(0, str(LOGIC))  # techdoc_docpage imports techdoc_dashboard
_spec = importlib.util.spec_from_file_location("techdoc_docpage", LOGIC / "techdoc_docpage.py")
docpage = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(docpage)

BODY_FULL = "## Steps\n\nSee SAP note 736902 first.\n\nRun it."
FILLER = " ".join(["Renew the credential with the portal and record the date of the change."] * 16)
BODY_EXEMPLARY = (f"## Introduction\n\n{FILLER}\n\n## Prerequisites\n\nAccess to the portal.\n\n"
                  "## Steps\n\n1. Open the portal.\n2. Request the credential.\n3. Install it.\n\n"
                  "## Verification\n\nThe service starts.\n\n"
                  "## References\n\n- [Full document](full.md)\n- [Vendor guide](https://example.org/guide)\n")
BODY_IMAGES = "![User list in SU01](resources/images/wide.png)\n\n![Gone](resources/images/gone.png)\n"

DOCS = {
    "full.md": page("Full document", BODY_FULL, Author="Ana", Date="2026-10-01", DocType="How-to guide",
                    Status="Draft", Priority="High", Environment="Production", SID="PRD, PRA",
                    Transaction="SU01", Product="ADS", Category="Procedure", Color="Blue",
                    Summary="Request the credential, then register it."),
    "plain.md": page("Plain document", "Text.", Category="Note", Status="Obsolete"),
    "images.md": page("Images", BODY_IMAGES, Category="Note"),
    "exemplary.md": page("Exemplary document", BODY_EXEMPLARY, Author="Ana", Date="2026-10-20", DocType="How-to guide",
                         Category="Procedure", Status="Released", Priority="Normal", Tag="credential", Topic="Security",
                         Scope="Infrastructure", Product="ADS", Summary="Renew the credential before it expires."),
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


def card(site, name):
    html = read(site, name)
    return html[html.index("INFO CARD :: START"):html.index("INFO CARD :: END")]


def test_card_is_closed_with_summary_and_open_without(page_site):
    assert '<section class="kb-info-card" id="kb-info-card"' in card(page_site, "full.html")
    assert 'aria-expanded="false"' in card(page_site, "full.html")
    assert '<section class="kb-info-card kb-open" id="kb-info-card"' in card(page_site, "plain.html")


def test_details_groups_and_chips(page_site):
    c = card(page_site, "full.html")
    assert c.index("<h3>Classification</h3>") < c.index("<h3>Systems</h3>") < c.index("<h3>Technical objects</h3>") < c.index("<h3>Other</h3>")
    assert '<a class="kb-obj" href="Transaction_SU01.html">SU01</a>' in c
    assert '<a class="kb-obj" href="https://me.sap.com/notes/736902">736902</a>' in c
    details = c[c.index("DETAILS PANEL :: START"):c.index("DETAILS PANEL :: END")]
    assert "Color" in details and "Summary" not in details and "<dt>Title</dt>" not in details
    assert "<h3>Systems</h3>" not in card(page_site, "plain.html")   # empty groups are hidden


def test_panels_have_headings_and_print_classes(page_site):
    c = card(page_site, "full.html")
    assert re.search(r'<div id="kb-info-details" class="kb-print uk-active">\s*<h2 class="kb-info-heading">Document details</h2>', c)
    assert re.search(r'<div id="kb-info-history" class="kb-noprint">\s*<h2 class="kb-info-heading">History</h2>', c)
    assert "uk-switcher" not in c and 'class="kb-info-toggle kb-noprint"' in c


def test_page_script_and_properties_action(page_site):
    html = read(page_site, "full.html")
    assert "document.documentElement.classList.add('kb-js')" in html and "js/page.js" in html
    assert "modal-metadata" not in html
    assert 'href="#kb-info-details" data-uk-tooltip="title: Document properties"' in html
    assert "kb-info-card-tab" in (page_site["target"] / "resources/themes/techdoc/framework/kb4it/js/page.js").read_text(encoding="utf-8")


def test_sap_notes_found_in_text():
    assert docpage.sap_notes("See SAP note 736902 and Note #1234567, not notes 12.") == ["736902", "1234567"]


def test_strip_date_shows_the_time_below_the_date(page_site):
    html = read(page_site, "full.html")
    strip = html[html.index("HEADER STRIP :: START"):html.index("HEADER STRIP :: END")]
    assert ('<a class="kb-date" href="events_20261001.html" title="2026-10-01 00:00:00">'
            '<span class="kb-day">2026-10-01</span><span class="kb-time">00:00</span></a>') in strip


def test_strip_date_without_time_shows_only_the_date():
    assert docpage.date_parts("2026-10-01") == ("2026-10-01", "")
    assert docpage.date_parts("2026-10-01 08:15") == ("2026-10-01", "08:15")
    assert docpage.date_parts("2026-10-01 08:15:59") == ("2026-10-01", "08:15")


def test_quality_index_is_written(page_site):
    text = (page_site["target"] / "quality-index.js").read_text(encoding="utf-8")
    assert text.startswith("window.KB_QUALITY = ")
    data = json.loads(text[len("window.KB_QUALITY = "):].rstrip(";\n"))
    assert isinstance(data["docs"]["full.html"]["score"], int)
    assert "plain.html" not in data["docs"]          # Status: Obsolete is retired


@pytest.fixture(scope="module")
def off_site(tmp_path_factory):
    base = tmp_path_factory.mktemp("techdoc-quality-off")
    home = base / "home"
    home.mkdir()
    cfg = write_repo(base / "repo", "techdoc", {"full.md": DOCS["full.md"]}, quality=False)
    result = run_kb4it("build", cfg, cwd=base, home=home)
    assert result.returncode == 0, result.stdout
    return {"target": base / "repo" / "target", "log": result.stdout}


def test_quality_off_removes_the_index(off_site):
    assert not (off_site["target"] / "quality-index.js").exists()
    html = read(off_site, "full.html")
    assert "kb-q-" not in html and "kb-info-quality" not in html


def test_emblem_tab_and_note_for_an_exemplary_document(page_site):
    html = read(page_site, "exemplary.html")
    assert re.search(r'class="kb-q-emblem-link kb-noprint" href="#kb-info-quality" title="Quality \d+ of 100, Exemplary"', html)
    assert 'class="kb-exemplary-note kb-noprint"' in html and "kb-exemplary" in html[:html.index("<head>")]
    assert re.search(r'<div id="kb-info-quality" class="kb-noprint"><h2 class="kb-info-heading">Quality</h2>', card(page_site, "exemplary.html"))
    assert "It does not check that the content is correct." in html


def test_basic_page_has_a_grey_ring_and_next_steps_but_no_note(page_site):
    html = read(page_site, "full.html")
    assert "kb-q-emblem" in html and "kb-exemplary-note" not in html
    assert '<li class="todo">Add a References section<span class="gain">+3</span></li>' in html


def test_retired_document_has_no_score(page_site):
    html = read(page_site, "plain.html")      # Status: Obsolete
    assert "kb-q-emblem" not in html and "kb-info-quality" not in html


def test_star_action_opens_the_quality_tab(page_site):
    assert 'href="#kb-info-quality" data-uk-tooltip="title: Document quality"' in read(page_site, "full.html")

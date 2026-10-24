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
    cfg = write_repo(base / "repo", "techdoc", DOCS, datatable=["Date", "Title", "Status", "Quality"])
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
    assert strip.index("How-to guide") < strip.index("Draft") < strip.index("High") < strip.index("events_20261001")
    assert 'href="events_20261001.html"' in strip and 'href="Product_ADS.html"' in strip
    assert "Author_Ana" not in strip and "Topic" not in strip   # Author is not a strip key; full.md has no Topic
    ex = read(page_site, "exemplary.html")
    ex_strip = ex[ex.index("HEADER STRIP :: START"):ex.index("HEADER STRIP :: END")]
    assert ex_strip.index("events_20261020") < ex_strip.index("Topic_Security.html") < ex_strip.index("Product_ADS.html")


def test_strip_links_are_date_worktype_topic_product():
    conf = json.loads((ROOT / "kb4it/resources/themes/techdoc/theme.json").read_text(encoding="utf-8"))
    assert conf["header_keys"]["links"] == ["Date", "WorkType", "Topic", "Product"]


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
    cfg = write_repo(base / "repo", "techdoc", {"full.md": DOCS["full.md"]}, quality=False,
                     datatable=["Date", "Title", "Status", "Quality"])
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
    assert 'class="kb-exemplary-note kb-noprint"' in html and '<html lang="en" class="kb-exemplary">' in html
    assert re.search(r'<div id="kb-info-quality" class="kb-noprint"><h2 class="kb-info-heading">Quality</h2>', card(page_site, "exemplary.html"))
    assert "It does not check that the content is correct." in html


def test_basic_page_has_a_grey_ring_and_next_steps_but_no_note(page_site):
    html = read(page_site, "full.html")
    assert "kb-q-emblem" in html and "kb-exemplary-note" not in html
    assert '<a href="quality-guide.html#check-references">Add a References section</a><span class="gain">+3</span></li>' in html


def test_retired_document_has_no_score(page_site):
    html = read(page_site, "plain.html")      # Status: Obsolete
    assert "kb-q-emblem" not in html and "kb-info-quality" not in html


def test_star_action_opens_the_quality_tab(page_site):
    assert 'href="#kb-info-quality" data-uk-tooltip="title: Document quality"' in read(page_site, "full.html")


def test_quality_scripts_are_loaded(page_site):
    html = read(page_site, "full.html")
    assert '<script defer src="quality-index.js"></script>' in html and "js/quality.js" in html
    assert "quality-index.js" not in read(page_site, "index.html")
    script = (page_site["target"] / "resources/themes/techdoc/framework/kb4it/js/quality.js").read_text(encoding="utf-8")
    assert "KB_QUALITY" in script and "better than" in script


def test_quality_items_have_tips_and_guide_links(page_site):
    q = card(page_site, "full.html")
    q = q[q.index("QUALITY PANEL :: START"):q.index("QUALITY PANEL :: END")]
    # lxml quotes an attribute with single quotes when its value holds double quotes.
    assert re.search(r"""<li class="todo" title=(["']).*?## References.*?\1 data-uk-tooltip="pos: top-left">"""
                     r'<a href="quality-guide.html#check-references">Add a References section</a>', q)
    assert '<a href="quality-guide.html#dim-findable">Findable</a>' in q
    assert re.search(r"""<li class="ok" title=(["']).+?\1 data-uk-tooltip="pos: top-left"><a href="quality-guide.html#check-""", q)


def test_quality_guide_page_explains_every_check(page_site):
    sys.path.insert(0, str(LOGIC))
    import techdoc_quality_guide as guide
    html = read(page_site, "quality-guide.html")
    for key in guide.CHECKS:
        assert f'id="{key}"' in html, key
    assert 'id="skeleton-incident"' in html and "## Timeline" in html
    assert "Summary: " in html and "https://me.sap.com/notes/" in html


def test_markdown_system_pages_keep_their_headings(page_site):
    # Mako reads a line starting with ## as a comment, so the templates must escape it.
    assert re.search(r'<h2 class="kb-h2" id="what-is-kb4it">', read(page_site, "help.html"))
    assert re.search(r'<h3 class="kb-h3" id="check-summary">', read(page_site, "quality-guide.html"))


def test_no_template_line_starts_with_a_mako_comment_by_accident():
    # In Mako, "##" at the start of a line is a comment: a Markdown heading there vanishes.
    found = [f"{p.relative_to(ROOT)}:{n}" for p in (ROOT / "kb4it" / "resources").rglob("*.tpl")
             for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if line.startswith("##")]
    assert not found, found


def _table_headers(html):
    return re.findall(r'<span class="uk-text-secondary">([^<]+)</span>', html[html.index("<thead>"):html.index("</thead>")])


def test_quality_column_sorts_by_score(page_site):
    html = read(page_site, "Category_Procedure.html")
    assert "Quality" in _table_headers(html)
    assert re.search(r'<td data-order="\d+"><span class="kb-q-meter kb-q-exemplary">(<i class="on"></i>){5}</span>'
                     r'<span class="kb-q-chip kb-q-exemplary">Exemplary</span></td>', html)


def test_quality_column_is_left_out_when_quality_is_off(off_site):
    assert "Quality" not in _table_headers(read(off_site, "Category_Procedure.html"))


def test_related_tab_holds_linked_from_and_related_documents(page_site):
    c = card(page_site, "full.html")
    panel = c[c.index("RELATED PANEL :: START"):c.index("RELATED PANEL :: END")]
    assert '<li data-kb-tab="related"><a href="#kb-info-related">Related</a></li>' in c
    assert "Linked from" in panel and 'href="exemplary.html"' in panel and "kb-q-chip" in panel
    assert "Related documents" in panel and "Product: ADS" in panel
    body = read(page_site, "full.html")
    body = body[body.index("DOCUMENT BODY :: START"):body.index("DOCUMENT BODY :: END")]
    assert "kb4it-backlinks" not in body


def test_no_related_tab_without_entries(page_site):
    assert 'data-kb-tab="related"' not in read(page_site, "plain.html")


def test_quality_page_lists_the_maintenance_work(page_site):
    html = read(page_site, "quality.html")
    for section in ("quality-mix", "quality-exemplary", "quality-wins", "quality-broken", "quality-images",
                    "quality-summary", "quality-duplicates"):
        assert f'id="{section}"' in html, section
    images = html[html.index('id="quality-images"'):html.index('id="quality-summary"')]
    assert 'href="images.html"' in images and "resources/images/gone.png" in images
    exemplary = html[html.index('id="quality-exemplary"'):html.index('id="quality-wins"')]
    assert 'href="exemplary.html"' in exemplary
    assert 'href="quality.html"' in read(page_site, "full.html")      # logo menu


def test_no_quality_page_when_quality_is_off(off_site):
    assert not (off_site["target"] / "quality.html").exists()
    assert 'href="quality.html"' not in read(off_site, "full.html")


def _block(html, name):
    return html[html.index(f"{name} :: START"):html.index(f"{name} :: END")]


def test_dashboard_shows_exemplary_count_mix_and_best_documents(page_site):
    index = read(page_site, "index.html")
    hero = _block(index, "SUMMARY COUNTS")
    assert re.search(r'<a class="kb-hero-stat" href="quality.html"><span class="num">(★|&#9733;) 1</span><span class="label">Exemplary</span></a>', hero)
    types = _block(index, "DOCUMENT TYPES")
    assert '<span class="kb-q-mixlabel">1 exemplary, 0 complete of 2</span>' in types
    shelf = _block(index, "BEST DOCUMENTS")
    assert 'data-kb-section="best-documents"' in shelf and 'href="exemplary.html"' in shelf and "kb-best-card" in shelf


def test_dashboard_without_quality_has_no_stat_mix_or_shelf(off_site):
    index = read(off_site, "index.html")
    assert "quality.html" not in _block(index, "SUMMARY COUNTS")
    assert "kb-q-mix" not in index and "BEST DOCUMENTS" not in index

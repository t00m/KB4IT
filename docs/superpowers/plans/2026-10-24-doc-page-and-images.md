# Document page and images (phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every techdoc document page a header strip, its Summary, warning banners and an info card with Details and History, with print rules, and make its images readable: real size, captions, lightbox, frames, galleries and a placeholder for missing files.

**Architecture:** Two new pure modules in `techdoc/logic/`: `techdoc_media.py` rewrites the images of the compiled body (an HTML string in, an HTML string and the missing files out), and `techdoc_docpage.py` turns the properties of a document into plain dicts for the header and the info card. `build_page` calls both and renders two new templates, `DOC_HEADER.tpl` and `INFO_CARD.tpl`; a small `page.js` handles the card state. The Quality and Related tabs, the quality emblem and the Exemplary note are phases 2 to 4 and are not built here.

**Tech Stack:** Python 3.11, lxml (already a dependency), Mako templates, UIkit 3.21.13, plain JavaScript, pytest (build-based tests through `tests/helpers`).

**Spec:** `docs/superpowers/specs/2026-10-24-document-quality-design.md`: Part A (except the quality emblem and the Related documents line), Part D sections D1, D2 (Details and History tabs only), D3 and D6 (rows for the blocks built here), Part E section E1, and "Phases" item 1. The mockup `docs/superpowers/specs/2026-10-24-document-quality-mockup.html` shows the markup and the class names.

## Global Constraints

- techdoc only. No change in `kb4it/` outside `kb4it/resources/themes/techdoc/`, except help pages and `CHANGELOG.md`.
- Tests: `pytest tests/themes -q` and `scripts/devel/check_themes.sh`; the task that adds a log code also runs `pytest tests/help -q`. No full suite, no browser tests (user rule for theme-only work).
- HTML stays W3C valid; UIkit attributes are written `data-uk-*`; every new block in a template has a `<!-- NAME :: START -->` / `<!-- NAME :: END -->` pair.
- Class names from the mockup: `kb-doc-strip`, `kb-summary`, `kb-banner` with `prod`, `retired`, `draft`, `kb-info-card`, `kb-open`, `kb-info-bar`, `kb-info-toggle`, `kb-info-panels`, `kb-groups`, `kb-group`, `kb-obj`, `kb-figure`, `kb-shot`, `kb-zoom`, `kb-gallery`, `kb-img-missing`, `kb-noprint`, `kb-print`.
- Banner copy, verbatim: Production: "This document changes production systems: <SID values>." (without SID values: "This document changes production systems."); retired: "Do not follow this document."; draft: "Not final. Check with the author before you follow it." The bold label before the text is `Production`, the Status value (`Obsolete`, ...), or `Draft`.
- Retired statuses: `Obsolete`, `Deprecated`, `Withdrawn`, `Rejected`. Only `Status: Draft` gets the draft banner; `Planned` and `Open` get none.
- Keys never listed in Details: `Title`, `Summary`, `Bookmark`, `SystemPage`.
- localStorage keys: `kb-info-card-tab` (last tab, all pages) and `kb-info-card:<page file name>` (open or closed, one page). Every access in `try`/`catch`.
- Log line for a missing image: `[THEME] IMAGE_MISSING doc=<doc> src=<src>`, at warning level.
- Comments are one line, plain English; never the em dash (AGENTS.md, nonia). Help pages never name the documentation framework (the `test_no_framework_name_in_the_sources` check).
- Commits: one-line Conventional Commits message, no trailers, never push, never branch. Never stage `CLAUDE.md`, `claude/`, `skills/`, `uv.lock`.
- sapbasis-docs is never put under git. Rebuilds of it use `--force`, because an incremental build keeps old pages when only the theme changed.

## Review Focus

- **Summary with commas.** KB4IT splits a value on commas, so `Summary: A, B` arrives as `["A", "B"]`. The page must show "A, B", not "A". Test in Task 4.
- **Images that are not local files.** `http(s)://` and `data:` sources must keep working: no size lookup, never reported missing. Test in Task 2.
- **Image file names with spaces or `%20`.** `resources/images/my%20shot.png` must find `my shot.png`. Test in Task 1 (`resolve_src`).
- **Image inside a sentence that is missing.** A `<figure>` inside `<p>` is invalid HTML; the placeholder there must be an inline `<span>`. Test in Task 2.
- **No JavaScript.** Every panel of the info card is in the HTML in reading order, each under its own `<h2>`, and the closed or open state comes from the HTML, not from a script. Test in Task 5.

---

### Task 1: Image size reader and alt text rule

**Files:**
- Create: `kb4it/resources/themes/techdoc/logic/techdoc_media.py`
- Test: `tests/themes/test_techdoc_media.py`

**Interfaces:**
- Produces:
  - `image_size(path: str) -> tuple[int, int] | None`: width and height from PNG (IHDR), JPEG (first SOF0 to SOF15 marker except C4, C8, CC), GIF (logical screen) and SVG (`width`/`height` in px, else `viewBox`); `None` for anything else or a read error. Reads at most the first 64 KB; stdlib only.
  - `is_filename_alt(alt: str, src: str) -> bool`: `True` when the alt is empty, equals the file stem of `src` (any case), or has no space and contains a digit, `_` or `-`.
  - `resolve_src(src: str, source_dir: str) -> str | None`: the local file a relative `src` points to (`urllib.parse.unquote`, joined to `source_dir`); `None` for `http:`, `https:`, `data:`, `//` and absolute paths.

- [ ] **Step 1: Write the failing tests.** Load the module with `importlib.util.spec_from_file_location` from `ROOT / "kb4it/resources/themes/techdoc/logic/techdoc_media.py"`. A helper builds tiny files in `tmp_path`:

```python
def png(w, h):
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", w, h) + b"\x08\x02\x00\x00\x00" + b"\x00" * 4

def jpeg(w, h):
    return b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x00" * 9 + b"\xff\xc0" + struct.pack(">HBHH", 17, 8, h, w) + b"\x00" * 10

def gif(w, h):
    return b"GIF89a" + struct.pack("<HH", w, h) + b"\x00" * 7

def test_image_size_reads_png_jpeg_gif_and_svg(tmp_path):
    for name, data, size in (("a.png", png(1100, 480), (1100, 480)), ("b.jpg", jpeg(640, 360), (640, 360)),
                             ("c.gif", gif(32, 16), (32, 16)),
                             ("d.svg", b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 420"></svg>', (900, 420)),
                             ("e.svg", b'<svg xmlns="http://www.w3.org/2000/svg" width="120px" height="40" viewBox="0 0 1 1"></svg>', (120, 40))):
        (tmp_path / name).write_bytes(data)
        assert media.image_size(str(tmp_path / name)) == size

def test_image_size_is_none_for_unknown_or_broken_files(tmp_path):
    (tmp_path / "x.png").write_bytes(b"not an image")
    assert media.image_size(str(tmp_path / "x.png")) is None
    assert media.image_size(str(tmp_path / "missing.png")) is None

def test_filename_like_alt_texts():
    assert media.is_filename_alt("SAP-BC-SC-DMS-00", "resources/images/SAP-BC-SC-DMS-00.png")
    assert media.is_filename_alt("image12", "x.png")
    assert media.is_filename_alt("", "x.png")
    assert media.is_filename_alt("Shot", "resources/images/shot.png")
    assert not media.is_filename_alt("Transaction SU01 with the user list", "x.png")
    assert not media.is_filename_alt("Diagram", "x.png")

def test_resolve_src(tmp_path):
    assert media.resolve_src("resources/images/my%20shot.png", str(tmp_path)) == str(tmp_path / "resources/images/my shot.png")
    for src in ("https://x.org/a.png", "http://x.org/a.png", "data:image/png;base64,AA", "//x.org/a.png", "/abs/a.png"):
        assert media.resolve_src(src, str(tmp_path)) is None
```

- [ ] **Step 2: Run them and see them fail.** Run: `pytest tests/themes/test_techdoc_media.py -q`. Expected: FAIL (module file not found).
- [ ] **Step 3: Implement the three functions** in `techdoc_media.py`, with a module docstring and one-line comments. SVG: parse the root tag's attributes with a regex on the first 64 KB; accept plain numbers or a `px` suffix only.
- [ ] **Step 4: Run them.** Run: `pytest tests/themes/test_techdoc_media.py -q`. Expected: PASS.
- [ ] **Step 5: Commit.**

```bash
git add kb4it/resources/themes/techdoc/logic/techdoc_media.py tests/themes/test_techdoc_media.py
git commit -m "feat(techdoc): read image sizes and tell file-name alt texts from captions"
```

### Task 2: Rewrite the images of a document body

**Files:**
- Modify: `kb4it/resources/themes/techdoc/logic/techdoc_media.py`
- Test: `tests/themes/test_techdoc_media.py`

**Interfaces:**
- Consumes: `image_size`, `is_filename_alt`, `resolve_src` (Task 1).
- Produces: `enhance_images(html: str, source_dir: str) -> tuple[str, list[str]]`: the rewritten body HTML and the `src` of each missing local image, in document order. Parses with `lxml.html.fragment_fromstring(html, create_parent="div")` and returns the inner HTML of that wrapper.

Rules, in this order (spec E1):

1. **Size:** every `<img>` with a local file gets `width` and `height` from `image_size` unless it already has both.
2. **Lazy:** every `<img>` except the first in the body gets `loading="lazy"` and `decoding="async"`.
3. **Left alone:** an image inside an `<a>`, an image whose known width is under 64, and an image in a `<p>` that also holds text (any non-whitespace text or any element other than `<img>` and `<br>`) keep their place; they get only rules 1, 2 and 8.
4. **Figure:** any other image becomes `<figure class="kb-figure"><a class="kb-zoom" href="SRC" data-caption="CAPTION"><img class="kb-shot" ...></a><figcaption>Figure N. ALT</figcaption></figure>`. A `<p>` holding only that image is replaced by the figure. With a file-name-like alt there is no `<figcaption>` and `data-caption` is the alt. `N` counts captioned figures from 1.
5. **Gallery:** three or more figures in a row with nothing but whitespace between them (one `<p>` with several images, or consecutive `<p>` elements with one image each) go into `<div class="kb-gallery uk-child-width-1-2 uk-child-width-1-3@m" data-uk-grid="masonry: false">` (an explicit value, so lxml cannot print the attribute two ways), one `<div>` per figure.
6. **Missing:** a local image whose file does not exist becomes, at block level, `<figure class="kb-figure kb-img-missing">Image missing: <code>SRC</code></figure>`; inside a paragraph with text, `<span class="kb-img-missing">Image missing: <code>SRC</code></span>`. Its `src` goes into the returned list. It never joins a gallery.
7. **Remote** (`resolve_src` is `None`): no size, never missing, otherwise as rules 2 to 5.

- [ ] **Step 1: Write the failing tests** (reuse `png()` from Task 1; `site` is a `tmp_path` with `resources/images/` holding `wide.png` (1100x480), `icon.png` (16x16), `s1.png` to `s3.png` (900x420)):

```python
def test_block_image_becomes_numbered_figure_with_lightbox_link(site):
    html, missing = media.enhance_images('<p><img alt="User list in SU01" src="resources/images/wide.png"></p>', str(site))
    assert missing == []
    assert '<figure class="kb-figure"><a class="kb-zoom" href="resources/images/wide.png" data-caption="User list in SU01">' in html
    assert 'class="kb-shot"' in html and 'width="1100"' in html and 'height="480"' in html
    assert "<figcaption>Figure 1. User list in SU01</figcaption>" in html
    assert "loading=" not in html            # the first image loads at once

def test_file_name_alt_gets_no_caption_and_second_image_is_lazy(site):
    html, _ = media.enhance_images('<p><img alt="x" src="resources/images/icon.png"></p><p><img alt="SAP-BC-00" src="resources/images/wide.png"></p>', str(site))
    assert "<figcaption>" not in html
    assert html.count('loading="lazy"') == 1 and 'decoding="async"' in html

def test_small_linked_and_inline_images_are_left_alone(site):
    for body in ('<p><img alt="Icon here" src="resources/images/icon.png"></p>',
                 '<p><a href="x.html"><img alt="Big link" src="resources/images/wide.png"></a></p>',
                 '<p>Click <img alt="the button" src="resources/images/wide.png"> to go on.</p>'):
        html, _ = media.enhance_images(body, str(site))
        assert "<figure" not in html and "kb-zoom" not in html

def test_three_images_in_a_row_make_a_gallery(site):
    body = "".join(f'<p><img alt="Step {i} of the wizard" src="resources/images/s{i}.png"></p>' for i in (1, 2, 3))
    html, _ = media.enhance_images(body, str(site))
    assert html.count('<div class="kb-gallery uk-child-width-1-2 uk-child-width-1-3@m" data-uk-grid="masonry: false">') == 1
    assert html.count('<figure class="kb-figure">') == 3
    two, _ = media.enhance_images(body.rsplit("<p>", 1)[0], str(site))
    assert "kb-gallery" not in two

def test_missing_images_become_placeholders(site):
    html, missing = media.enhance_images('<p><img alt="Gone" src="resources/images/gone.png"></p><p>See <img alt="g" src="resources/images/g2.png"> here.</p>', str(site))
    assert missing == ["resources/images/gone.png", "resources/images/g2.png"]
    assert '<figure class="kb-figure kb-img-missing">Image missing: <code>resources/images/gone.png</code></figure>' in html
    assert '<span class="kb-img-missing">Image missing: <code>resources/images/g2.png</code></span>' in html
    assert "<p><figure" not in html

def test_remote_images_are_never_missing(site):
    html, missing = media.enhance_images('<p><img alt="Remote diagram" src="https://x.org/a.png"></p>', str(site))
    assert missing == [] and 'href="https://x.org/a.png"' in html and "width=" not in html

def test_text_and_other_markup_are_kept(site):
    body = '<h2 id="s">Steps</h2><p>Run <code>a &lt; b</code>.</p><pre><code class="language-bash">ls</code></pre>'
    assert media.enhance_images(body, str(site)) == (body, [])
```

- [ ] **Step 2: Run them and see them fail.** Run: `pytest tests/themes/test_techdoc_media.py -q -k "figure or alone or gallery or missing or remote or kept"`. Expected: FAIL (`enhance_images` not defined).
- [ ] **Step 3: Implement `enhance_images`.** When the body has no `<img>`, return the input string unchanged (this keeps `test_text_and_other_markup_are_kept` exact and skips the parse). Serialize the wrapper's text and children with `lxml.html.tostring(child, encoding="unicode")`.
- [ ] **Step 4: Run the file.** Run: `pytest tests/themes/test_techdoc_media.py -q`. Expected: PASS.
- [ ] **Step 5: Commit.**

```bash
git add kb4it/resources/themes/techdoc/logic/techdoc_media.py tests/themes/test_techdoc_media.py
git commit -m "feat(techdoc): turn document images into sized figures with captions, lightbox links and galleries"
```

### Task 3: Images on the built page

**Files:**
- Modify: `kb4it/resources/themes/techdoc/logic/theme.py` (`build_page`)
- Modify: `kb4it/resources/themes/techdoc/templates/HTML_BODY.tpl` (the DOCUMENT BODY div)
- Modify: `kb4it/resources/themes/techdoc/framework/kb4it/css/screen.css`, `print.css`
- Modify: `help/source/troubleshooting.md` (the `IMAGE_MISSING` code), `help/source/reference-theme-techdoc.md` (section "Document pages")
- Test: `tests/themes/test_techdoc_page.py` (new)

**Interfaces:**
- Consumes: `enhance_images` (Task 2).
- Produces: the module fixture `page_site` in `tests/themes/test_techdoc_page.py`, reused by Tasks 4 and 5: a techdoc site built with `write_repo` + `run_kb4it` from `DOCS` (below) and the files `source/resources/images/wide.png` (1100x480) and `s1.png` to `s3.png`; it returns `{"target": Path, "log": str}`. Helper `read(site, name)` returns the page with the whitespace between tags removed (`re.sub(r">\s+<", "><", text)`), because `build_page` pretty-prints the page through lxml. The PNG files come from `png()`, imported from `tests.themes.test_techdoc_media`.

```python
DOCS = {
    "full.md": page("Full document", BODY_FULL, Author="Ana", Date="2026-10-01", DocType="How-to guide",
                    Status="Draft", Priority="High", Environment="Production", SID="PRD, PRA",
                    Transaction="SU01", Product="ADS", Category="Procedure", Color="Blue",
                    Summary="Request the credential, then register it."),
    "plain.md": page("Plain document", "Text.", Category="Note", Status="Obsolete"),
    "images.md": page("Images", BODY_IMAGES, Category="Note"),
}
BODY_FULL = "## Steps\n\nSee SAP note 736902 first.\n\nRun it."
BODY_IMAGES = "![User list in SU01](resources/images/wide.png)\n\n![Gone](resources/images/gone.png)\n"
```

- [ ] **Step 1: Write the failing tests.**

```python
def test_images_page_has_figures_lightbox_and_placeholder(page_site):
    html = read(page_site, "images.html")
    assert '<figure class="kb-figure"><a class="kb-zoom" href="resources/images/wide.png"' in html
    assert 'data-uk-lightbox="toggle: a.kb-zoom; animation: fade"' in html
    assert "Image missing: <code>resources/images/gone.png</code>" in html

def test_missing_image_is_logged(page_site):
    assert "[THEME] IMAGE_MISSING doc=images.md src=resources/images/gone.png" in page_site["log"]
```

- [ ] **Step 2: Run them and see them fail.** Run: `pytest tests/themes/test_techdoc_page.py -q`. Expected: FAIL (no `kb-figure` in `images.html`).
- [ ] **Step 3: Implement.** In `build_page`, for documents that are not system pages: `var['source_html'], missing = enhance_images(self.apply_transformations(source_html), self.srvbes.get_path('source'))`, then one `self.log.warning(...)` per missing `src` with the Global Constraints format. In `HTML_BODY.tpl` add `data-uk-lightbox="toggle: a.kb-zoom; animation: fade"` to the DOCUMENT BODY div only. `screen.css`: `.kb-figure` (centered, margin), `.kb-shot` (1px solid `#e5e5e5` border, 4px radius, `box-shadow: 0 1px 4px rgba(0,0,0,.08)`, `max-width: 100%; height: auto`), `.kb-zoom` (`cursor: zoom-in`), `figcaption` (small muted text), `.kb-img-missing` (grey dashed box, monospace path; inline-block for the span). `print.css`: `.kb-figure { break-inside: avoid; }`, `.kb-zoom { cursor: auto; }`, `.kb-gallery > * { width: 100% !important; }`. Help: add `IMAGE_MISSING` to the troubleshooting table with what it means and the fix (copy the file into `source/resources/images` or fix the path); in `reference-theme-techdoc.md` "Document pages", one short list of the image behaviour (size, caption from the alt text, click to zoom, three or more images make a gallery, missing files show a placeholder).
- [ ] **Step 4: Run the tests and the checks.** Run: `pytest tests/themes tests/help -q && scripts/devel/check_themes.sh`. Expected: all pass, all themes compliant.
- [ ] **Step 5: Commit.**

```bash
git add kb4it/resources/themes/techdoc/logic/theme.py kb4it/resources/themes/techdoc/templates/HTML_BODY.tpl kb4it/resources/themes/techdoc/framework/kb4it/css/screen.css kb4it/resources/themes/techdoc/framework/kb4it/css/print.css help/source/troubleshooting.md help/source/reference-theme-techdoc.md tests/themes/test_techdoc_page.py
git commit -m "feat(techdoc): show document images as figures with zoom and report missing image files"
```

### Task 4: Header strip, Summary and banners

**Files:**
- Create: `kb4it/resources/themes/techdoc/logic/techdoc_docpage.py`
- Create: `kb4it/resources/themes/techdoc/templates/DOC_HEADER.tpl`
- Modify: `kb4it/resources/themes/techdoc/theme.json` (`header_keys`)
- Modify: `kb4it/resources/themes/techdoc/logic/theme.py` (`build_page`), `templates/HTML_BODY.tpl`, `framework/kb4it/css/screen.css`, `print.css`
- Test: `tests/themes/test_techdoc_page.py`

**Interfaces:**
- Consumes: `priority_css`, `status_css` from `techdoc_dashboard`; `page_site` fixture (Task 3).
- Produces (in `techdoc_docpage.py`):
  - `RETIRED_STATUSES = ('Obsolete', 'Deprecated', 'Withdrawn', 'Rejected')`
  - `value_url(props: dict, key: str, value: str) -> str`: `events_YYYYMMDD.html` for `Date` (from the first 10 characters), else `props[f'{key}_{value}_Url']`, else `f'{valid_filename(key)}_{valid_filename(value)}.html'`.
  - `values(srvdtb, doc_id, key) -> list[str]`: the non-empty values.
  - `summary(srvdtb, doc_id) -> str`: the `Summary` values joined with `", "`.
  - `header_strip(srvdtb, doc_id, conf: dict) -> dict`: `{'badges': [{'key', 'text', 'css', 'url'}], 'links': [{'key', 'items': [{'text', 'url'}]}]}` from `conf['badges']` and `conf['links']`; empty keys skipped. Badge `css`: `priority_css` for Priority, `status_css` for Status, `kb-label-doctype` for anything else.
  - `banners(srvdtb, doc_id) -> list[dict]`: `[{'kind': 'prod' | 'retired' | 'draft', 'label': str, 'text': str}]`, in the spec order: Production, retired, draft.
- `theme.json` gains `"header_keys": {"badges": ["DocType", "Status", "Priority"], "links": ["Date", "Author", "Product", "Handover"]}`.
- `build_page` sets `var['doc_header']` (rendered `DOC_HEADER.tpl`, empty string for system pages); `HTML_BODY.tpl` prints it after the PRINT HEADER block.

- [ ] **Step 1: Write the failing tests** in `tests/themes/test_techdoc_page.py`:

```python
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
```

- [ ] **Step 2: Run them and see them fail.** Run: `pytest tests/themes/test_techdoc_page.py -q -k "header or summary or banners"`. Expected: FAIL.
- [ ] **Step 3: Implement** the module, the template (HEADER STRIP and BANNERS blocks with START/END pairs; badges as `<a class="uk-label kb-badge CSS" href="URL">`, links as `<span><span class="k">KEY</span><a href="URL">TEXT</a>, ...</span>` inside `<span class="meta">`), the `theme.json` key, the `build_page` and `HTML_BODY.tpl` wiring, and the CSS from the mockup (`.kb-doc-strip`, `.kb-summary`: larger muted text; `.kb-banner` with `prod` red, `retired` grey, `draft` amber tints). `print.css` (D6): the strip as one line of plain text (badges without background, black text), the Summary as on screen, banners with a 1px border, bold label and no background.
- [ ] **Step 4: Run the tests and the checks.** Run: `pytest tests/themes -q && scripts/devel/check_themes.sh`. Expected: all pass.
- [ ] **Step 5: Commit.**

```bash
git add kb4it/resources/themes/techdoc/logic/techdoc_docpage.py kb4it/resources/themes/techdoc/templates/DOC_HEADER.tpl kb4it/resources/themes/techdoc/theme.json kb4it/resources/themes/techdoc/logic/theme.py kb4it/resources/themes/techdoc/templates/HTML_BODY.tpl kb4it/resources/themes/techdoc/framework/kb4it/css/screen.css kb4it/resources/themes/techdoc/framework/kb4it/css/print.css tests/themes/test_techdoc_page.py
git commit -m "feat(techdoc): add a header strip, the Summary and warning banners to document pages"
```

### Task 5: Info card with Details and History

**Files:**
- Modify: `kb4it/resources/themes/techdoc/logic/techdoc_docpage.py`
- Create: `kb4it/resources/themes/techdoc/templates/INFO_CARD.tpl`
- Create: `kb4it/resources/themes/techdoc/framework/kb4it/js/page.js`
- Modify: `kb4it/resources/themes/techdoc/theme.json` (`info_groups`, `info_tabs`)
- Modify: `kb4it/resources/themes/techdoc/logic/theme.py` (`build_page`), `templates/HTML_BODY.tpl`, `templates/HTML_HEADER_COMMON.tpl` (the `kb-js` line and the `page.js` script), `templates/SECTION_ACTIONS.tpl` (Document properties), `framework/kb4it/css/screen.css`, `print.css`
- Test: `tests/themes/test_techdoc_page.py`

**Interfaces:**
- Consumes: `value_url`, `values`, `summary` (Task 4); `page_site` fixture.
- Produces (in `techdoc_docpage.py`):
  - `HIDDEN_KEYS = ('Title', 'Summary', 'Bookmark', 'SystemPage')`
  - `sap_notes(text: str) -> list[str]`: numbers matched by `(?i)\bnotes?\s+#?(\d{5,8})\b` in the Markdown body, unique, in order.
  - `info_groups(srvdtb, doc_id, groups: list[dict], body_md: str) -> list[dict]`: one dict per non-empty group, `{'name', 'chips': bool, 'items': [{'key', 'values': [{'text', 'url'}]}]}`, keys in the order of `groups`, then `Other` with every remaining key from `srvdtb.get_custom_keys(doc_id)` minus `HIDDEN_KEYS`. The group with `"chips": true` also gets the pseudo key `SAP note` with `https://me.sap.com/notes/<n>` URLs.
- `theme.json` gains `info_groups` (spec D3 table, in order: Classification; Systems; Technical objects with `"chips": true`; Organisation; Lifecycle) and `"info_tabs": {"details": {"print": true}, "history": {"print": false}}`.
- `build_page` sets `var['info_card']` (rendered `INFO_CARD.tpl`, empty for system pages) with `var['card']`: `{'open': bool, 'groups': [...], 'history': {'date', 'source', 'built', 'edit_url' or ''}, 'print': {'details': bool, 'history': bool}}`. `open` is `True` when the document has no Summary.

Markup decisions (spec D2):
- `<section class="kb-info-card[ kb-open]" id="kb-info-card" aria-label="Document information">`, a `kb-info-bar` with `<ul data-uk-tab="connect: #kb-info-panels; animation: uk-animation-fade">` (Details first, active) and `<button class="kb-info-toggle kb-noprint" type="button" aria-expanded="true|false" aria-controls="kb-info-panels">`. The tab bar has `kb-noprint`.
- `<div class="kb-info-panels" id="kb-info-panels">` without the `uk-switcher` class, so panels show without JavaScript. CSS hides inactive panels and the panels of a closed card only under `.kb-js`.
- Panels: `<div id="details" class="kb-print|kb-noprint">` starting `<h2 class="kb-info-heading">Document details</h2>`; `<div id="history" ...>` starting `<h2 class="kb-info-heading">History</h2>`. Under `.kb-js` the heading is visually hidden on screen; it shows in print and without JavaScript.
- History lists Date, the source file name, a "View source" link (`href="#modal-full-source" data-uk-toggle`), an "Edit" link when `var['git_ok']` (the URL `SECTION_ACTIONS.tpl` builds today) and the build time (`var['timestamp']`).
- `HTML_HEADER_COMMON.tpl` gets `<script>document.documentElement.classList.add('kb-js');</script>` in the head and `<script src="resources/themes/techdoc/framework/kb4it/js/page.js" defer></script>`.
- `SECTION_ACTIONS.tpl`: the Document properties action becomes `<a class="kb4it-page-action" href="#details" ...>`; the `modal-metadata` dialog is removed, and `build_page` no longer calls `build_metadata_section`.
- `page.js`: open and close (the chevron, and a click on the active tab when the card is open); the last tab in `kb-info-card-tab`, the open state in `kb-info-card:<page>`; a document without a Summary (card rendered open) always starts on Details; `#details` and `#history` in the URL, on load and on `hashchange`, open the card on that tab. Use `UIkit.tab(el).show(index)`.

- [ ] **Step 1: Write the failing tests:**

```python
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
    assert "Color" in c and "Summary" not in c and "<dt>Title</dt>" not in c
    assert "<h3>Systems</h3>" not in card(page_site, "plain.html")   # empty groups are hidden

def test_panels_have_headings_and_print_classes(page_site):
    c = card(page_site, "full.html")
    assert re.search(r'<div id="details" class="kb-print">\s*<h2 class="kb-info-heading">Document details</h2>', c)
    assert re.search(r'<div id="history" class="kb-noprint">\s*<h2 class="kb-info-heading">History</h2>', c)
    assert "uk-switcher" not in c and 'class="kb-info-toggle kb-noprint"' in c

def test_page_script_and_properties_action(page_site):
    html = read(page_site, "full.html")
    assert "document.documentElement.classList.add('kb-js')" in html and "js/page.js" in html
    assert "modal-metadata" not in html and 'href="#details"' in html
    assert "kb-info-card-tab" in (page_site["target"] / "resources/themes/techdoc/framework/kb4it/js/page.js").read_text(encoding="utf-8")

def test_sap_notes_found_in_text():
    assert docpage.sap_notes("See SAP note 736902 and Note #1234567, not notes 12.") == ["736902", "1234567"]
```

(`docpage` is loaded with `importlib.util.spec_from_file_location`, adding the techdoc `logic` folder to `sys.path` first, since the module imports `techdoc_dashboard`.)

- [ ] **Step 2: Run them and see them fail.** Run: `pytest tests/themes/test_techdoc_page.py -q -k "card or details or panels or script or notes"`. Expected: FAIL.
- [ ] **Step 3: Implement** the functions, `theme.json` keys, template, script, wiring and CSS. `screen.css` from the mockup (`.kb-info-card`, `.kb-info-bar`, `.kb-info-toggle` rotating its chevron when closed, `.kb-groups` as a grid of `auto-fill, minmax(16rem, 1fr)` and one column under 640px, `.kb-obj` monospace chips). `print.css` (D6): `.kb-noprint { display: none !important; }`, `.kb-info-panels > .kb-print { display: block !important; }`, `.kb-info-heading` visible, `.kb-groups` in two columns.
- [ ] **Step 4: Run the tests and the checks.** Run: `pytest tests/themes -q && scripts/devel/check_themes.sh`. Expected: all pass.
- [ ] **Step 5: Commit.**

```bash
git add kb4it/resources/themes/techdoc/logic/techdoc_docpage.py kb4it/resources/themes/techdoc/templates/INFO_CARD.tpl kb4it/resources/themes/techdoc/framework/kb4it/js/page.js kb4it/resources/themes/techdoc/theme.json kb4it/resources/themes/techdoc/logic/theme.py kb4it/resources/themes/techdoc/templates/HTML_BODY.tpl kb4it/resources/themes/techdoc/templates/HTML_HEADER_COMMON.tpl kb4it/resources/themes/techdoc/templates/SECTION_ACTIONS.tpl kb4it/resources/themes/techdoc/framework/kb4it/css/screen.css kb4it/resources/themes/techdoc/framework/kb4it/css/print.css tests/themes/test_techdoc_page.py
git commit -m "feat(techdoc): add an info card with grouped details and history to document pages"
```

### Task 6: Help, changelog and a check on sapbasis-docs

**Files:**
- Modify: `help/source/reference-theme-techdoc.md` ("Document pages": header strip, Summary, banners, info card, the `header_keys`, `info_groups` and `info_tabs` settings of `theme.json`), `kb4it/resources/themes/techdoc/templates/PAGE_HELP.tpl` (add `Summary` to the built-in properties table: "One-sentence summary, shown under the title"), `CHANGELOG.md` (Unreleased, Added: one entry for the document page, one for images).

- [ ] **Step 1: Write the help and changelog text.** Plain sentences, no em dash, no framework name.
- [ ] **Step 2: Run the checks.** Run: `pytest tests/themes tests/help -q && scripts/devel/check_themes.sh`. Expected: all pass.
- [ ] **Step 3: HTML check.** Run: `uv run --no-project --with-requirements requirements.txt --with html5validator python scripts/devel/validate_html.py`. Expected: `0 errors and warnings`.
- [ ] **Step 4: Rebuild sapbasis-docs.** Run: `PYTHONPATH=$PWD python3 -c "import sys; from kb4it.core.main import main; sys.argv[0] = 'kb4it'; main()" build --force /home/t00m/Documents/devel/tests/kb4it/sapbasis-docs/config/repo.json`. Expected: exit 0, no `ERROR |` lines, and `IMAGE_MISSING` warnings for the 131 broken references (`grep -c IMAGE_MISSING` on the output).
- [ ] **Step 5: Look at it.** With a Playwright script run through `uv run --no-project --with playwright` (not a committed test), take screenshots at 1280px of `SAP-BC-ADS-READERRIGHTS.html` and one document without images, then click a Details tab, the chevron and a figure, and print one page to PDF (`page.pdf`). Check: card opens and closes, the tab is remembered after a reload, the lightbox opens on a figure only, the PDF shows "Document details" and no tab bar. Write what you saw in the response file.
- [ ] **Step 6: Commit.**

```bash
git add help/source/reference-theme-techdoc.md kb4it/resources/themes/techdoc/templates/PAGE_HELP.tpl CHANGELOG.md
git commit -m "docs(techdoc): describe the document header, info card and image handling"
```

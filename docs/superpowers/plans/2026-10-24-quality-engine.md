# Quality engine, emblem and Quality tab (WP4, quality phase 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Score every techdoc document from 0 to 100 in five dimensions, show the score as a ring in the header strip, explain it in a Quality tab of the info card, mark Exemplary documents, and write `quality-index.js` with ranks and peer medians.

**Architecture:** `techdoc_quality.py` is pure: `assess()` takes one document's Markdown, properties and backlink count and returns an `Assessment`; `peer_stats()` turns all assessments into ranks and medians. The theme's `build()` (which runs before compilation) assesses every document once and keeps the results in memory; `build_page()` reads them; `post_deploy_activities()` writes `target/quality-index.js`. A small `quality.js` fills the rank sentence and the median ticks in the browser; without it the page still shows the score, the bars and the checklist.

**Tech Stack:** Python 3.11 (stdlib only in the engine), Mako templates, UIkit 3.21.13, plain JavaScript, pytest.

**Spec:** `docs/superpowers/specs/2026-10-24-document-quality-design.md`: Part B (all), Part C sections 1 and 2, Part D2 (Quality tab), D6 (print rows for the emblem, the note and the Quality tab), Part E1.8 (missing-image penalty), Architecture rows for `techdoc_quality.py`, `quality.js`, `theme.json` and `repo.json`. Order and updates: `docs/superpowers/specs/2026-10-24-open-items-design.md`, WP4.

## Global Constraints

- techdoc only, plus help pages and `CHANGELOG.md`. Tests: `pytest tests/themes tests/help -q` and `scripts/devel/check_themes.sh`. No browser tests; a Playwright look is written in the response file.
- Values verbatim from the spec: dimension maxima Findable 15, Structured 25, Complete 25, Connected 15, Current 20; tiers Exemplary ≥ 75, Complete 60 to 74, Basic 40 to 59, Stub < 40, Retired for `Obsolete`, `Deprecated`, `Withdrawn`, `Rejected` (no score); targets How-to guide 150, Reference 200, Explanation 500, Tutorial 800, records 60; half-lives How-to guide and Tutorial 3, Reference 4, Explanation 8 years; final statuses `Released`, `Completed`, `Finished`, `Successful`.
- Colours: `--q-exemplary #f5b301`, `--q-exemplary-ink #8a6100`, `--q-complete #32d296`, `--q-complete-ink #1b7a55`, `--q-basic #8592a6`, `--q-stub #c3c9d2` (Stub chip text `#6b7480`). No tier uses red. A tier is never shown by colour alone (name, star, dashed outline).
- The checklist is worded as next steps ("Add a Summary key +3"), never as faults. Basic and Stub pages show a grey ring and nothing else alarming.
- `repo.json` `"quality": false` removes every `.kb-q-*` element, the Quality tab and `quality-index.js`. Default on.
- HTML stays W3C valid; `data-uk-*` attributes; every new template block has a `NAME :: START/END` pair.
- Comments one line, plain English, no em dash. Commits: one-line Conventional Commits, no trailers, never push, never branch.
- sapbasis-docs rebuilds use `--force`.

## Review Focus

- **Documents with almost nothing.** No frontmatter keys beyond `Category`, no sections, no Date: `assess` must not raise and gives a Stub with a sensible checklist. Test in Task 1.
- **A Date that does not parse** (`Date: soon`): freshness is 0, no exception. Test in Task 2.
- **A peer group of one.** Rank 1 of 1 and medians equal to the document's own values. Test in Task 3.
- **Retired documents.** No score, no ring, no Quality tab, not counted in peers. Test in Task 3 (stats) and Task 4 (page).
- **`"quality": false`.** No `.kb-q-` class, no Quality tab, no `quality-index.js` on disk, even when an older build wrote one. Test in Task 4.

---

### Task 1: Engine part 1: profile, skeletons, Findable and Structured

**Files:**
- Create: `kb4it/resources/themes/techdoc/logic/techdoc_quality.py`
- Test: `tests/themes/test_techdoc_quality.py`

**Interfaces:**
- Produces:
  - `DEFAULTS: dict`: the `quality` block of `theme.json` with the Global Constraints values: `{"enabled": True, "tiers": {"exemplary": 75, "complete": 60, "basic": 40}, "targets": {...}, "record_target": 60, "half_life": {...}, "final_status": [...], "retired_status": [...], "known_values": {"Status": [...], "Priority": [...], "DocType": [...]}}`. `known_values`: Status `New, Open, Draft, Planned, Completed, Released, Finished, Successful, Deprecated, Obsolete, Withdrawn, Rejected`; Priority `Critical, Very high, High, Medium, Normal, Low`; DocType the four Diátaxis names.
  - `profile(theme_conf: dict) -> dict`: `DEFAULTS` updated key by key with `theme_conf.get("quality", {})`.
  - `Skeleton(headings: list[str], placeholders: list[str])` (dataclass) and `load_skeletons(folder: str) -> dict[str, Skeleton]`: keyed by the upper-case file prefix (`PROCEDURE`, `CHANGE`, ...); `headings` are the `##` titles in lower case; `placeholders` are the non-empty body lines with list marks removed (`Step one`, `List prerequisites here.`), at least 8 characters or a `Step ...` line.
  - `Check(dim: str, name: str, todo: str, points: float, max: float)` (dataclass; passed when `points >= max`), `Assessment(score: int, tier: str, dims: dict[str, float], checks: list[Check], peer: str)` (dataclass; `score` rounded, `tier` one of `exemplary`, `complete`, `basic`, `stub`, `retired`).
  - `DocInput(text: str, meta: dict[str, list[str]], backlinks: int, known_docs: set[str], source_dir: str, work_type: str)` (dataclass). `text` is the whole Markdown file; `meta` the property values as KB4IT stores them.
  - `findable(doc, prof) -> list[Check]` and `structured(doc, prof, skeletons) -> list[Check]`.
- Rules, from spec Part B, with these calls:
  - Findable: one `Check` per core key (Author, Date, DocType, Category, Status, Tag, Topic, Scope, Product), 1 point each; "known values" 3 when at least one of Status, Priority, DocType is set and every one set is in `known_values` (my call: a document with none set gets 0, not 3); Summary 3.
  - Structured, knowledge documents: sections 5 (one section 3); context first 4 (first `##` matches `description|introduction|overview|summary|objective|context|problem`); DocType fit 8 (how-to: 3+ numbered steps or a fenced code block; tutorial: both; reference: a table or 5+ list items; explanation: 3+ sections); skeleton 8 × fraction found, using the skeleton of the first `Category` value, synonyms as in the spec (and `steps` matches `procedure`); no skeleton: 8 with 3+ sections, else 4. Records (`work_type` set): sections, context first, skeleton of the WorkType × 16, no DocType fit. Empty sections −3 each, at most 2; any skeleton placeholder line found in the body −6. The dimension never goes below 0.
  - Words, sections and lists are counted on the body after the frontmatter. Words (`\w+`) leave out the `# ` title line and fenced code.

- [ ] **Step 1: Write the failing tests** (load the module with `importlib.util.spec_from_file_location`, logic folder on `sys.path` as in `tests/themes/test_techdoc_page.py`; helper `doc(text, work_type="", backlinks=0, **meta)` builds a `DocInput` with `known_docs={"a.md", "b.md"}` and a `tmp_path` source dir):

```python
def test_findable_counts_core_keys_known_values_and_summary(prof):
    full = doc("# T\n", Author="A", Date="2026-01-01", DocType="How-to guide", Category="Procedure", Status="Released",
               Tag="x", Topic="y", Scope="z", Product="p", Summary="S")
    assert sum(c.points for c in quality.findable(full, prof)) == 15
    assert sum(c.points for c in quality.findable(doc("# T\n", Status="Whatever"), prof)) == 1

def test_structured_how_to_with_skeleton_sections(prof, skeletons):
    body = "# T\n\n## Introduction\n\nWhy.\n\n## Prerequisites\n\nA.\n\n## Steps\n\n1. a\n2. b\n3. c\n\n## Verification\n\nOk.\n"
    checks = quality.structured(doc(body, DocType="How-to guide", Category="Procedure"), prof, skeletons)
    assert sum(c.points for c in checks) == 25

def test_structured_record_uses_worktype_skeleton_times_16(prof, skeletons):
    body = "# T\n\n## Overview\n\nX.\n\n## Impact\n\nY.\n\n## Rollback\n\nZ.\n"
    checks = quality.structured(doc(body, work_type="Change", Category="Record"), prof, skeletons)
    assert sum(c.points for c in checks) == 25 and not any(c.name.startswith("Fits") for c in checks)

def test_empty_sections_and_placeholders_cost_points(prof, skeletons):
    body = "# T\n\n## Introduction\n\n## Steps\n\n1. Step one\n2. Step two\n3. Step three\n"
    total = sum(c.points for c in quality.structured(doc(body, DocType="How-to guide", Category="Procedure"), prof, skeletons))
    assert total == max(0, 5 + 4 + 8 + 8 * 1 / 3 - 3 - 6)

def test_almost_empty_document_does_not_raise(prof, skeletons):
    d = doc("# T\n", Category="Note")
    assert quality.findable(d, prof) and quality.structured(d, prof, skeletons)
```

(`prof` is `quality.profile({})`; `skeletons` is `quality.load_skeletons(<techdoc templates/skeletons>)`.)

- [ ] **Step 2: Run them and see them fail.** Run: `pytest tests/themes/test_techdoc_quality.py -q`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** the names above. Regexes may follow the calibration script: numbered steps `^\s*\d+\.\s`, list items `^\s*([-*]|\d+\.)\s`, tables `^\|?\s*:?-{3,}`, empty section `^#{2,4} .+\n\s*(?=^#{1,4} |\Z)`.
- [ ] **Step 4: Run them.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat(techdoc): score how findable and structured a document is"` (engine and its test).

### Task 2: Engine part 2: Complete, Connected, Current, tier and `assess`

**Files:**
- Modify: `kb4it/resources/themes/techdoc/logic/techdoc_quality.py`
- Test: `tests/themes/test_techdoc_quality.py`

**Interfaces:**
- Consumes: Task 1 names.
- Produces: `complete(doc, prof) -> list[Check]`, `connected(doc, prof) -> list[Check]`, `current(doc, prof, today: date) -> list[Check]`, `tier_of(score: int, status: list[str], prof) -> str`, `peer_of(doc) -> str` (WorkType for records, else the first DocType, else `"Other"`), `assess(doc, prof, skeletons, today: date) -> Assessment`.
- Rules:
  - Complete: `25 × min(words / target, 1)`, at most 3 under 50 words (records: target 60, at most 3 under 20 words). Unknown DocType: target 200.
  - Connected: backlinks ≥ 1: 4; links to an existing document (a relative `.md` link whose path is in `known_docs`): 3; external source (`](http`, `](https` or `<http`): 3; a `##` section named References, Documentation or Related: 3; an image or a fenced `mermaid` block: 2; each broken document link (relative `.md` link not in `known_docs`, or a link `bare_link_path` returns a path for) −3; each missing local image (`resolve_src` from `techdoc_media`, file absent) −3; never below 0.
  - Current, knowledge documents: final status 8, any other live status 3; freshness `12 × 0.5 ** (age_years / half_life)` from the first 10 characters of `Date` (`date.fromisoformat`); no or bad Date: 0. Records: final status 20, any other live status 10, no freshness.
  - `assess`: `score = round(sum of all points)`; `tier_of` returns `retired` when any Status value is a retired status, else by the thresholds. Retired documents keep their checks but the page does not show them.

- [ ] **Step 1: Write the failing tests:**

```python
def test_complete_is_capped_for_short_documents(prof):
    words = lambda n: "# T\n\n" + " ".join(["w"] * n) + "\n"
    assert sum(c.points for c in quality.complete(doc(words(40), DocType="How-to guide"), prof)) == 3
    assert sum(c.points for c in quality.complete(doc(words(75), DocType="How-to guide"), prof)) == 12.5
    assert sum(c.points for c in quality.complete(doc(words(300), DocType="How-to guide"), prof)) == 25
    assert sum(c.points for c in quality.complete(doc(words(30), work_type="Change"), prof)) == 12.5

def test_connected_rewards_links_and_penalises_broken_ones(prof):
    body = "# T\n\nSee [b](b.md), [gone](gone.md), [web](https://x.org) and ![i](resources/images/none.png).\n\n## References\n\nx\n"
    points = sum(c.points for c in quality.connected(doc(body, backlinks=2), prof))
    assert points == max(0, 4 + 3 + 3 + 3 + 2 - 3 - 3)

def test_current_decays_with_age_and_tolerates_bad_dates(prof):
    today = date(2026, 10, 24)
    fresh = quality.current(doc("# T\n", DocType="Reference", Status="Released", Date="2026-10-24"), prof, today)
    old = quality.current(doc("# T\n", DocType="Reference", Status="Released", Date="2018-10-24"), prof, today)
    bad = quality.current(doc("# T\n", DocType="Reference", Status="Draft", Date="soon"), prof, today)
    assert sum(c.points for c in fresh) == 20
    assert round(sum(c.points for c in old), 1) == 11.0          # 8 + 12 * 0.5 ** 2
    assert sum(c.points for c in bad) == 3
    assert sum(c.points for c in quality.current(doc("# T\n", work_type="Incident", Status="Open"), prof, today)) == 10

def test_assess_gives_tier_and_peer(prof, skeletons):
    a = quality.assess(doc("# T\n", Status="Obsolete", DocType="Reference"), prof, skeletons, date(2026, 10, 24))
    assert a.tier == "retired" and a.peer == "Reference"
    assert quality.assess(doc("# T\n", work_type="Change"), prof, skeletons, date(2026, 10, 24)).peer == "Change"
    assert quality.tier_of(75, [], prof) == "exemplary" and quality.tier_of(74, [], prof) == "complete"
    assert quality.tier_of(40, [], prof) == "basic" and quality.tier_of(39, [], prof) == "stub"
```

- [ ] **Step 2: Run them and see them fail.** Expected: FAIL (names missing).
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the file.** Expected: PASS.
- [ ] **Step 5: Commit.** `git commit -m "feat(techdoc): score completeness, connections and currency, and give each document a tier"`

### Task 3: Peers, `quality-index.js` and the build

**Files:**
- Modify: `kb4it/resources/themes/techdoc/logic/techdoc_quality.py` (`peer_stats`, `index_js`)
- Modify: `kb4it/resources/themes/techdoc/logic/theme.py` (`build`, `post_deploy_activities`)
- Modify: `kb4it/resources/themes/techdoc/theme.json` (`quality` block = `DEFAULTS` minus `enabled`)
- Test: `tests/themes/test_techdoc_quality.py`, `tests/themes/test_techdoc_page.py`

**Interfaces:**
- Produces:
  - `peer_stats(assessments: dict[str, Assessment]) -> dict`: `{"peers": {peer: {"count": n, "median": {dim: value}}}, "docs": {page: {"score", "tier", "peer", "rank"}}}`, where `page` is the HTML name of the document, retired documents are left out, `rank` is 1 + the number of peers with a higher score, and medians are the middle value (lower middle for even counts), rounded to 1 decimal.
  - `index_js(stats: dict) -> str`: `"window.KB_QUALITY = " + json.dumps(stats, ensure_ascii=False, separators=(",", ":")) + ";\n"`.
  - Theme: `self.quality: dict[str, Assessment]` (empty when off), `self.quality_stats: dict`; `quality_on() -> bool` (`repo.json` `quality` is not `False` and the profile is enabled). `build()` assesses every non-system document first; logs `[THEME] QUALITY docs=<n> exemplary=<n> complete=<n> basic=<n> stub=<n> retired=<n>` at info level. `post_deploy_activities()` writes `target/quality-index.js`, or removes it when quality is off.

- [ ] **Step 1: Write the failing tests:**

```python
def test_peer_stats_ranks_within_peers_and_skips_retired():
    A = quality.Assessment
    dims = lambda v: {k: v for k in ("findable", "structured", "complete", "connected", "current")}
    stats = quality.peer_stats({"a.md": A(80, "exemplary", dims(16), [], "Reference"),
                                "b.md": A(50, "basic", dims(10), [], "Reference"),
                                "c.md": A(0, "retired", dims(0), [], "Reference"),
                                "d.md": A(62, "complete", dims(12), [], "Change")})
    assert stats["peers"]["Reference"]["count"] == 2 and stats["peers"]["Change"]["count"] == 1
    assert stats["docs"]["a.html"]["rank"] == 1 and stats["docs"]["b.html"]["rank"] == 2
    assert stats["docs"]["d.html"]["rank"] == 1 and stats["peers"]["Change"]["median"]["findable"] == 12
    assert "c.html" not in stats["docs"]
```

In `tests/themes/test_techdoc_page.py`: `test_quality_index_is_written` (`target/quality-index.js` starts with `window.KB_QUALITY = ` and its JSON has `docs["full.html"]["score"]` as an int) and `test_quality_off_removes_the_index` (a second site built with `quality=False` in `write_repo` has no `quality-index.js`, no `kb-q-` in `full.html`, no `kb-info-quality`).

- [ ] **Step 2: Run them and see them fail.**
- [ ] **Step 3: Implement.** In `build()`, call a new `assess_documents()` before the other pages: for each document in `self.srvdtb.get_documents()` that is not a system page, read the source file from `self.srvbes.get_path('source')`, build the `DocInput` (`meta` from `get_doc_properties`, `backlinks` from `len(self.srvbes.get_plan().backlinks.get(doc_id, []))`, `known_docs` from the source file names, `work_type` from `techdoc_records.work_type`), and store `assess(...)`. Skeletons are loaded once from the theme's `templates/skeletons`.
- [ ] **Step 4: Run** `pytest tests/themes -q && scripts/devel/check_themes.sh`. Expected: all pass.
- [ ] **Step 5: Commit.** `git commit -m "feat(techdoc): assess every document at build time and write quality-index.js"`

### Task 4: The emblem, the Exemplary note and the Quality tab

**Files:**
- Create: `kb4it/resources/themes/techdoc/templates/QUALITY_PANEL.tpl`
- Modify: `templates/DOC_HEADER.tpl` (emblem first in the strip, Exemplary note above the strip), `templates/INFO_CARD.tpl` (Quality tab between Details and History), `templates/SECTION_ACTIONS.tpl` (star action, `href="#kb-info-quality"`), `logic/theme.py` (`build_page` passes the assessment), `framework/kb4it/js/page.js` (no change expected: tabs come from `data-kb-tab`), `framework/kb4it/css/screen.css` (tokens on `:root` and the `.kb-q-*` rules from the mockup), `print.css` (emblem, note and Quality tab not printed)
- Test: `tests/themes/test_techdoc_page.py`

**Interfaces:**
- Consumes: `self.quality[doc]` (`Assessment`), `self.quality_on()`.
- Markup (class names from the mockup `docs/superpowers/specs/2026-10-24-document-quality-mockup.html`):
  - Emblem: `<a class="kb-q-emblem-link kb-noprint" href="#kb-info-quality" title="Quality 78 of 100, Exemplary" aria-label="Quality 78 of 100, Exemplary"><span class="kb-q-emblem kb-q-<tier>">` + the SVG ring of the mockup (`stroke-dasharray="<score> 100"`, colour from the tier token; grey for basic and stub) + the number. Not shown for retired documents or with quality off.
  - Exemplary: `<html>` page gets the class `kb-exemplary` (3px gold line under the top bar, CSS); above the strip `<div class="kb-exemplary-note kb-noprint" data-kb-peer="<peer>">★ Exemplary <peer in lower case>: <span class="kb-q-rank"></span></div>` (the rank text is filled by Task 5).
  - Quality tab: `<li data-kb-tab="quality"><a href="#kb-info-quality">Quality</a></li>` and `<div id="kb-info-quality" class="kb-noprint">` with `<h2 class="kb-info-heading">Quality</h2>`, the large ring, the tier chip (`kb-q-chip kb-q-<tier>`, star for exemplary), `<p class="kb-q-rank" data-kb-doc="<page>"></p>`, five `kb-q-dim` rows (name, `points / max`, a `kb-q-bar` with the fill width in % and an empty `kb-q-tick` that Task 5 positions), and the checklist: two lists, "Done" (`check.name`) and "Next steps" (`check.todo +<missing points>`, missing points rounded to whole numbers), and the sentence "Quality measures structure, metadata, links and age. It does not check that the content is correct."
  - `info_tabs` in `theme.json` gains `"quality": {"print": false}`.

- [ ] **Step 1: Write the failing tests** in `tests/themes/test_techdoc_page.py` (add to `DOCS` an `exemplary.md` built to score 75 or more, for example a recent `Released` how-to guide with every core key, a Summary, Introduction/Prerequisites/Steps/Verification/References sections, 3 numbered steps, 200 words, a link to `full.md` and an external link):

```python
def test_emblem_tab_and_note_for_an_exemplary_document(page_site):
    html = read(page_site, "exemplary.html")
    assert re.search(r'class="kb-q-emblem-link kb-noprint" href="#kb-info-quality" title="Quality \d+ of 100, Exemplary"', html)
    assert 'class="kb-exemplary-note kb-noprint"' in html and "kb-exemplary" in html[:html.index("<head>")]
    assert re.search(r'<div id="kb-info-quality" class="kb-noprint">\s*<h2 class="kb-info-heading">Quality</h2>', card(page_site, "exemplary.html"))
    assert "It does not check that the content is correct." in html

def test_basic_page_has_a_grey_ring_and_next_steps_but_no_note(page_site):
    html = read(page_site, "full.html")
    assert "kb-q-emblem" in html and "kb-exemplary-note" not in html
    assert re.search(r"Add a Summary key|Add a References section", html) or "Next steps" in html

def test_retired_document_has_no_score(page_site):
    html = read(page_site, "plain.html")      # Status: Obsolete
    assert "kb-q-emblem" not in html and "kb-info-quality" not in html

def test_star_action_opens_the_quality_tab(page_site):
    assert 'href="#kb-info-quality" data-uk-tooltip="title: Document quality"' in read(page_site, "full.html")
```

- [ ] **Step 2: Run them and see them fail.**
- [ ] **Step 3: Implement.** The checklist todo phrases come from `Check.todo`; write them in Tasks 1 and 2 as next steps: "Add the <key> key", "Use a known value for Status, Priority and DocType", "Add a Summary key", "Split it into two or more sections", "Open with a Description or Introduction section", "Add numbered steps or a command" (and the matching text per DocType), "Add the <section> section", "Fill or remove the empty section", "Replace the skeleton text", "Write more: about <n> words", "Link it from another document", "Link to a related document", "Cite a source", "Add a References section", "Add an image or a diagram", "Fix the broken link to <path>", "Add the missing image <src>", "Set a final status", "Review it: it is <n> years old".
- [ ] **Step 4: Run** `pytest tests/themes -q && scripts/devel/check_themes.sh`. Expected: all pass.
- [ ] **Step 5: Commit.** `git commit -m "feat(techdoc): show the quality score as a ring, a Quality tab and an Exemplary note"`

### Task 5: `quality.js`, help and a check on sapbasis-docs

**Files:**
- Create: `kb4it/resources/themes/techdoc/framework/kb4it/js/quality.js`
- Modify: `templates/HTML_HEADER_COMMON.tpl` (on document pages with quality on: `<script defer src="quality-index.js"></script>` and `quality.js` after it), `help/source/reference-theme-techdoc.md` (a "Quality" section: the five dimensions with their points, the tiers, records, how to read the tab, `"quality": false`, the `quality` block of `theme.json`), `CHANGELOG.md`
- Test: `tests/themes/test_techdoc_page.py`

**Interfaces:**
- Consumes: `window.KB_QUALITY` (Task 3), the markup of Task 4.
- `quality.js` (runs on DOMContentLoaded, does nothing without `window.KB_QUALITY` or the panel): fills every `.kb-q-rank` with "Rank R of N <peer plural>, better than P% of them" (`P = round((1 - (R - 1) / N) * 100)`; for `N = 1`: "The only <peer> so far"); the Exemplary note's span gets "rank R of N <peer plural>"; each `.kb-q-tick` gets `left: <median / max × 100>%` and a `title` "Median of <peer plural>: <value>". Plurals: How-to guide → how-to guides, Reference → reference documents, Explanation → explanations, Tutorial → tutorials, Change → changes, Incident → incidents, Task → tasks, Meeting → meetings, Other → documents.

- [ ] **Step 1: Write the failing test:** `test_quality_scripts_are_loaded` asserts `quality-index.js` and `js/quality.js` script tags on `full.html` and not on `index.html`, and that `quality.js` mentions `KB_QUALITY` and `better than`.
- [ ] **Step 2: Run it and see it fail.**
- [ ] **Step 3: Implement** the script, the tags and the help text.
- [ ] **Step 4: Checks.** `pytest tests/themes tests/help -q && scripts/devel/check_themes.sh`; HTML validator on the scratch site; rebuild sapbasis-docs with `--force` and compare the `[THEME] QUALITY` counts with the spec's calibration table (49 Exemplary, 424 Complete, 463 Basic, 78 Stub, 20 Retired on 2026-10-24; the WP2 data fixes moved links and statuses, so the numbers will differ: write both in the response file and explain the difference); Playwright: emblem click opens Quality, ticks are placed, rank text is filled, print hides the emblem and the tab.
- [ ] **Step 5: Commit.** `git commit -m "feat(techdoc): fill ranks and peer medians from quality-index.js, and document the quality score"`

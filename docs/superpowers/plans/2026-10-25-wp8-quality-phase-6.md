# Quality phase 6: sticky table of contents and quality in search (WP8) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the optional sticky table of contents to techdoc document pages and carry the quality tier into the shared search results, where the score also breaks a ranking tie.

**Architecture:** The techdoc theme decides whether a page gets the sidebar from `toc_sidebar` in `theme.json`, the document not being a system page, and at least four H2 sections. `HTML_BODY.tpl` wraps the current page content and adds the sidebar only when that flag is set; the sidebar is hidden below 1400px and uses UIkit scrollspy to mark the current section. `Theme.search_record()` adds a small quality object to the record, `kb4it-search-ui.js` renders it as the existing `.kb-q-chip`, and the engine sorts on quality after relevance.

**Tech Stack:** Python 3.11, Mako, UIkit, plain ES2017, pytest, node for the search engine test.

**Spec:** `docs/superpowers/specs/2026-10-24-document-quality-design.md`, sections E4 and "Phases" item 6; order in `docs/superpowers/specs/2026-10-24-open-items-design.md`.

## Global Constraints

- Theme change: run `tests/themes` and `scripts/devel/check_themes.sh`; run the full suite without browser tests before the final commit. Never run the browser tests.
- HTML stays W3C valid (`scripts/devel/validate_html.py`); every new block gets a `NAME :: START` / `NAME :: END` comment pair, inside the same `% if`.
- Sticky table of contents is off by default (`theme.json` `toc_sidebar`), shown only at 1400px or wider, and only for a document with four or more sections. System pages never get it.
- Search results stay readable without the chip: a record without quality data renders as today.
- No em dash in code, comments, messages or documentation. One-line Conventional Commits, no trailers, never push, never branch.

## Review Focus

- **Default off:** the bundled `theme.json` says `false`, so no existing site changes until the setting is turned on.
- **Count:** only H2 headings count as sections; three sections do not get a sidebar, four do.
- **Fold and print:** the sidebar is not printed and does not change section folding or the inline table of contents.
- **Escaping:** the sidebar prints the TOC that `extract_toc` built, with `| n`, like the existing title menu.
- **Search fallback:** quality off means no `q` field, no chip and the old ranking.
- **Tie-breaker:** it never beats relevance, only decides between equal scores.

---

### Task 1: Optional sticky table of contents

**Files:** modify `kb4it/resources/themes/techdoc/logic/theme.py`, `kb4it/resources/themes/techdoc/templates/HTML_BODY.tpl`, `kb4it/resources/themes/techdoc/framework/kb4it/css/screen.css`, `kb4it/resources/themes/techdoc/theme.json`; create `tests/themes/test_techdoc_toc_sidebar.py`.

**Interfaces:**
- `Theme.toc_sidebar(source_html: str) -> bool`: true when `theme.json` sets `toc_sidebar` to true and the compiled HTML has four or more `<h2>` headings.
- `build_page()` sets `var['toc_sidebar'] = False` for system pages, otherwise the method result.
- `HTML_BODY.tpl` wraps the existing content in `.kb-main-body`; when `var['toc_sidebar']` is true it adds an `<aside class="kb-toc-sidebar kb-noprint">` with the TOC and `data-uk-scrollspy-nav="closest: li; scroll: true; offset: 80"`.
- `screen.css`: `.kb-toc-sidebar` hidden by default; at `min-width: 1400px` `.kb-main-sidebar` is a two-column grid and the sidebar sticks below the top bar. Its active link uses the existing blue highlight.

- [x] RED: a copied techdoc theme with `toc_sidebar: true` gives a four-section document the sidebar, a three-section document none, and a system page none; the default theme gives none. The CSS carries the 1400px rule and the scrollspy attribute.
- [x] GREEN: implement the flag, template and styles.
- [x] Run `python3 -m pytest tests/themes/test_techdoc_toc_sidebar.py tests/themes/test_techdoc.py tests/themes/test_html_quality.py -q`.
- [x] Commit `feat(techdoc): add an optional sticky table of contents`.

### Task 2: Quality in the search index and results

**Files:** modify `kb4it/resources/themes/techdoc/logic/theme.py`, `kb4it/resources/common/js/kb4it-search.js`, `kb4it/resources/common/js/kb4it-search-ui.js`, `kb4it/resources/themes/techdoc/framework/kb4it/css/screen.css`; create `tests/themes/test_techdoc_quality_search.py`.

**Interfaces:**
- `Theme.search_record(doc_id) -> dict`: the base record plus `q = {"score": int, "tier": str, "label": str}` when an assessment exists; no `q` when quality is off.
- Engine sort: relevance first, then `record.q.score` (missing counts as 0), then title.
- UI: a chip is added before the title in both the dropdown and the search page. It reuses `.kb-q-chip kb-q-<tier>` and carries `title="Quality <score> of 100, <label>"`. All text uses `textContent`.

- [ ] RED: the techdoc index carries the tier and score for a scored document; `"quality": false` removes `q`; the engine puts the higher quality record first when relevance ties; the UI script names the chip class and reads `record.q`.
- [ ] GREEN: implement the override, the sort and the chip.
- [ ] Run `python3 -m pytest tests/themes/test_techdoc_quality_search.py tests/themes/test_search.py tests/core/test_search_core.py -q` (the node test skips when node is missing).
- [ ] Commit `feat(techdoc): show the quality tier in search results`.

### Task 3: Help, changelog, full check and report

**Files:** modify `help/source/reference-theme-techdoc.md`, `CHANGELOG.md`; update this plan; create `responses/<timestamp>_WP8-QUALITY-PHASE-6.md`.

- [ ] Document the `toc_sidebar` option and the search chip in the techdoc reference page.
- [ ] Run `python3 -m pytest --ignore=tests/browser -q` and `scripts/devel/check_themes.sh`.
- [ ] Build and verify the help site; record the counts.
- [ ] Add the `CHANGELOG.md` entries under `## [Unreleased]`.
- [ ] Save the report and commit `docs(changelog): note the quality phase 6`.

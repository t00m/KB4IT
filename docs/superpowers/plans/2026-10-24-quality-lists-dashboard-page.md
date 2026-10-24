# Quality in lists, dashboard, Quality page and Related tab (WP5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the quality score outside the document page: a Quality column in the document tables, a quality stat, tier mixes and a Best documents shelf on the dashboard, one tabbed Activity card, a Quality page for maintainers, and a Related tab in the info card.

**Architecture:** The assessments of WP4 (`self.quality`, `self.quality_stats`) feed everything. A small core hook lets a theme render a table cell itself. Two new pure modules: `techdoc_related.py` (related documents by shared rare values) and `techdoc_quality_page.py` (quick wins, duplicates, tier mixes). New templates: `PAGE_QUALITY.tpl`; `PAGE_INDEX.tpl` and `INFO_CARD.tpl` change.

**Tech Stack:** Python 3.11, Mako, UIkit 3.21.13, DataTables, pytest.

**Spec:** `docs/superpowers/specs/2026-10-24-document-quality-design.md`: Part A item 7, Part C sections 3 to 6, Part D2 (Related tab) and D5. Order: `docs/superpowers/specs/2026-10-24-open-items-design.md`, WP5.

## Global Constraints

- techdoc, plus one core hook in `kb4it/services/themekit/tables.py` (Task 1). Task 1 runs the full suite without browser tests; the others run `pytest tests/themes tests/help -q` and `scripts/devel/check_themes.sh`. No browser tests; a Playwright look goes in the response file.
- Tier thresholds, colours and words as in WP4. No tier uses red; a tier is never shown by colour alone.
- With quality off (`"quality": false`) none of this appears: no Quality column content, no stat, no mix, no shelf, no Quality page, no tier chips in Related. The Related tab and the Activity card stay.
- With `"backlinks": false`, the Related tab has no Linked from list.
- HTML stays W3C valid; `data-uk-*`; `NAME :: START/END` pairs on new blocks. Mako: never start a template line with `##`.
- Comments one line, plain English, no em dash. One-line Conventional Commits, no trailers, never push, never branch.

## Review Focus

- **A site with no knowledge documents or no Exemplary document:** no empty shelf, no division by zero in the mixes. Test in Task 4.
- **A document with no shared values:** no Related documents; with no backlinks either, no Related tab. Test in Task 2.
- **Journal series** ("SAP Basis notes on Friday, July 02, 2021" and "... July 05 ..."): never listed as duplicates. Test in Task 3.
- **A Quality column in `datatable` with quality off:** the column stays out of the table. Test in Task 1.
- **Activity tabs with no entries** are hidden; with none at all, no card. Test in Task 5.

---

### Task 1: Quality column in document tables

**Files:** `kb4it/services/themekit/tables.py` (hook), `kb4it/resources/themes/techdoc/logic/theme.py` (`datatable_custom_cell`, `build_datatable` keeps Quality), CSS; tests `tests/core/test_tables_hook.py` (or the existing table test file), `tests/themes/test_techdoc_page.py`.

**Interfaces:**
- Core: `TableMixin.datatable_custom_cell(self, doc_id: str, key: str) -> str | None`, default `None`; `build_datatable` calls it for every non-Date, non-Title column first and uses its `<td>` when not `None`.
- techdoc: for `key == 'Quality'` returns `<td data-order="<score>"><span class="kb-q-meter kb-q-<tier>"><i class="on"></i>...(5 squares, one per 20 points)</span><span class="kb-q-chip kb-q-<tier>">Tier</span></td>`; retired: `data-order="-1"` and the Retired chip; no assessment or quality off: `None`. `build_datatable` keeps `Quality` only when quality is on.

- [ ] Tests: core: a theme whose hook returns `<td>X</td>` for key `Q` gets that cell; techdoc: with `Quality` in `datatable`, `Category_Procedure.html` (page_site) has `data-order` cells and `kb-q-meter`; with quality off the header has no Quality.
- [ ] RED, implement, GREEN; full suite without browser tests; commit `feat(techdoc): add a sortable Quality column to document tables`.

### Task 2: Related tab

**Files:** create `logic/techdoc_related.py`; modify `logic/theme.py` (`backlinks_html` returns `''`, `build_page` passes related data), `templates/INFO_CARD.tpl` (Related tab between Quality and History), `theme.json` (`info_tabs.related.print: false`), CSS; tests `tests/themes/test_techdoc_related.py`, `tests/themes/test_techdoc_page.py`.

**Interfaces:**
- `RELATED_KEYS = ('SID', 'Product', 'Transaction', 'Component', 'Tag')`.
- `related(doc_id: str, meta: dict[str, dict[str, list[str]]], limit: int = 5) -> list[dict]`: other documents sharing at least one value of `RELATED_KEYS`, scored by the sum of `log(N / df)` of the shared values (`df`: documents with that key and value), best first; each `{'doc', 'score', 'shared': ['SID: BWP', ...]}`. Retired documents are left out by the caller.
- Panel: "Linked from" (backlinks, as today but inside the card, each with its tier chip) and "Related documents" (title link, tier chip, shared values). The tab shows when either list has an entry. The body no longer ends with Linked from.

- [ ] Tests: unit tests for `related` (rare shared value ranks first; no shared value gives `[]`; limit 5); page: `b.html` linked from `a.html` shows "Linked from" inside `INFO CARD`, not after the body; a page with neither list has no Related tab. Existing backlink tests in `tests/core/test_backlinks.py` keep passing (they look for "Linked from" in the page).
- [ ] RED, implement, GREEN; commit `feat(techdoc): add a Related tab with Linked from and related documents`.

### Task 3: Quality page

**Files:** create `logic/techdoc_quality_page.py`, `templates/PAGE_QUALITY.tpl`; modify `logic/theme.py` (`build_page_quality`, `reserved_pages` gains `quality.md`), `templates/HTML_HEADER_COMMON.tpl` (logo menu entry "Quality" when quality is on), CSS; tests.

**Interfaces:**
- `quick_wins(assessments, prof, limit=50) -> list[dict]`: live documents whose score is within 5 points of the next tier and that have one missing check whose gain reaches it; `{'doc', 'score', 'tier', 'next', 'missing', 'check': todo text, 'gain'}`, sorted by points missing.
- `duplicates(titles: dict[str, str], threshold=0.8) -> list[tuple[str, str, float]]`: pairs with token Jaccard ≥ threshold (tokens: lowercase words of 3+ characters), skipping pairs whose titles are equal once digits, month and weekday names are removed.
- `tier_mix(assessments, peers) -> list[dict]`: per peer: counts per tier, total, percentages.
- Page sections (collapsible): tier mix per peer (stacked bars), Exemplary documents, quick wins, broken links (from the checks `check-broken-link`), missing images (`check-missing-image`), documents without a Summary, possible duplicates.

- [ ] Tests: unit tests for the three functions (journal series excluded); page: `quality.html` exists with each section id and is in the logo menu; absent with quality off.
- [ ] RED, implement, GREEN; commit `feat(techdoc): add a Quality page with quick wins, broken links, missing summaries and possible duplicates`.

### Task 4: Dashboard: stat, tier mix and Best documents

**Files:** `logic/techdoc_dashboard.py`, `templates/PAGE_INDEX.tpl`, CSS; tests in `tests/themes/test_techdoc.py`.

- Hero bar: a stat "★ N Exemplary" linking to `quality.html` (only with quality on and N ≥ 1).
- Diátaxis cards: a `kb-q-mix` bar of the knowledge documents of that DocType and a caption "13 exemplary, 106 complete of 234"; nothing for a card with no documents.
- Best documents: a collapsible section (`data-kb-section="best-documents"`) right after the Diátaxis grid: up to three Exemplary or best-scoring Complete documents per DocType, best first, as `kb-best-card` with the small ring, title, type and year. Hidden when empty.

- [ ] Tests: stat and link present on `index.html` when an Exemplary document exists; mix caption; shelf lists the exemplary document; no shelf on a site without scores of 60 or more.
- [ ] RED, implement, GREEN; commit `feat(techdoc): show the quality mix, the Exemplary count and the best documents on the dashboard`.

### Task 5: Activity card

**Files:** `logic/techdoc_dashboard.py`, `templates/PAGE_INDEX.tpl`, a small script (in `page.js` or the template), CSS; tests in `tests/themes/test_techdoc.py`.

- One collapsible section `data-kb-section="activity"` replaces Changes and incidents, Upcoming events, Monitoring and Recent events. Tabs: Changes, Incidents, Events (upcoming, then recent), Monitoring; a tab without entries is not rendered; no tabs at all, no card. The last tab is kept in `localStorage` (`kb-activity-tab`, in `try`/`catch`). Open items stays its own section.
- Existing tests that slice `CHANGES AND INCIDENTS :: START/END` and list the folding sections are updated to the new block names.

- [ ] Tests: the card has the four tabs on the test site and no separate changes or events sections; the folding list is `["open-items", "best-documents", "activity"]` (best-documents only when present).
- [ ] RED, implement, GREEN; commit `feat(techdoc): merge changes, incidents, events and monitoring into one Activity card`.

### Task 6: Help, CHANGELOG and checks

- Help: techdoc reference (dashboard description, Quality column, Quality page, Related tab, logo menu), CHANGELOG.
- Checks: `pytest tests/themes tests/help -q`, `check_themes.sh`, HTML validator on the scratch site, sapbasis-docs `--force` rebuild with `Quality` added to its `datatable`, Playwright look at the dashboard, a document with Related, the Quality page and a table sorted by Quality.
- Commit `docs(techdoc): describe the Quality column, the Quality page, the Related tab and the Activity card`.

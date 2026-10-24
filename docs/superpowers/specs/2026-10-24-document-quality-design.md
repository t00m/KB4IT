# Document quality and frontmatter display in techdoc

Status: draft, for review.
Date: 2026-10-24
Theme: techdoc
Mockup: [`2026-10-24-document-quality-mockup.html`](2026-10-24-document-quality-mockup.html) (open it from this folder; it loads the real techdoc CSS)
Data: sapbasis-docs, 1034 documents, profiled on 2026-10-24 with the draft model in this spec.

## Intent

Two related changes to techdoc:

1. **Use the frontmatter on the document page.** Today a document page shows no metadata at all. The Document Properties section was removed in 0.10.0, and nothing replaced it.
2. **Measure the quality of each document and show it.** Quality is shown in absolute terms (a score and a tier) and relative to the other documents of the same type (a rank). A good document must look good: the reader sees at a glance that it is one of the best in the repository.

The design rewards good documents in plain sight and keeps weak ones quiet. Weak documents are listed for maintainers on a separate page. They are not marked in red on the page a reader opens.

## Findings

These numbers come from the profile of sapbasis-docs. They drive the design.

### Frontmatter

| Fact | Number |
|---|---|
| Documents | 1034 |
| Keys in use | 56 |
| Keys techdoc reads (Title, DocType, Status, Priority, Author, Bookmark, Topic, Periodicity) | 8 |
| Documents with `Environment` | 332 (316 Production) |
| Documents with `SID` | 501 |
| Documents with `Transaction`, `Command` | 238, 195 |
| Documents with a `Summary` key | 0 |
| Distinct `Status` values | 12 (Completed, Finished and Successful mean the same) |
| Distinct `Priority` values | 8 (Normal and Standard overlap; Unknown in 48 documents) |
| `Date` formats | 3 (10, 16 and 19 characters) |
| Distinct tags | 838, of which 436 are used once |
| Documents that name an SAP note in the body | 122 (one has a `SAPNote` key) |

`build_page` still builds `var['metadata']` for every page, but no template prints it.

### Content

| Signal | How-to guide (510) | Reference (499) | Explanation (21) | Tutorial (4) |
|---|---|---|---|---|
| Median words (code excluded) | 49 | 75 | 514 | 919 |
| 90th percentile words | 623 | 537 | 2195 | 1917 |
| Median `##` sections | 2 | 2 | 5 | 11 |
| Without numbered steps | 389 | 448 | 11 | 2 |
| Without code blocks | 321 | 321 | 16 | 2 |

- 422 documents have under 50 words, and 637 have under 100. Many are change and incident records: a title, a Description section and one line.
- 273 how-to guides have neither numbered steps nor a code block.
- 271 documents have at least one empty section.
- The most common first sections are Description (420) and Introduction (342). A document that opens with context is common and easy to detect.
- techdoc ships skeletons with the expected sections per Category: Procedure (Prerequisites, Steps, Verification), Incident (Summary, Timeline, Root Cause, Resolution), Change (Overview, Impact, Rollback), Meeting, Task, Report and Note. They are the natural reference for "is this document complete for its kind".

### Links between documents

- No document links to another one in a way KB4IT recognizes. Backlinks are empty on all 1034 pages.
- 50 documents hold 275 links to existing documents, but written without an extension: `[x](SAP-BC-TSK-MANAGE-BATCH)`. The site renders `href="SAP-BC-TSK-MANAGE-BATCH"`, which is a broken link on disk and on most web servers.
- 10 links point to `.adoc` files from the old AsciiDoc repository. 63 extensionless links point to nothing.
- `LINK_BROKEN` (`workflow.py`, `compiler.py`) only checks links ending in `.md`, so none of these are reported.

### Age

Median document age: 4.4 years. How-to guides: median 5.0 years, 90th percentile 7.0 years.

### Prior decisions that limit this design

The 0.9.1 spec (`2026-10-21-404-favicon-diagrams-math-design.md`) set two non-goals:

- **`Updated` key:** `Date` is the only date property. This design uses `Date` for freshness and adds no new date key.
- **Drafts:** "a draft is built and published like any other document, with no label." A Draft banner (Part A) reopens this. It is listed under open questions, not decided here.

## Background: what makes a document good

The model takes ideas from five known sources:

- **Functional and structural quality** (Riona MacNamara, Google, Write the Docs). Functional quality is whether a document does its job: accurate, complete, findable. Structural quality is how it is written: clear, organized, consistent. A tool can measure structure and some proxies of function (metadata, links, freshness). It cannot measure accuracy. The score never claims to.
- **Diátaxis.** Each type has its own shape. A how-to guide needs steps. A reference needs lists or tables. An explanation needs room to discuss. A tutorial needs both steps and runnable commands. The model judges each document against its own type.
- **Every Page is Page One** (Mark Baker). Readers land on a page from search, not from a table of contents. A good page states its context first and links to its neighbours.
- **Wikipedia content assessment.** Named classes (Featured, Good, B, C, Start, Stub) are easier to read than a raw number. "Stub" is a neutral, well-known word.
- **Lighthouse and the GitHub community profile.** A score earns trust when it opens into a checklist that says what passed and what to do next.

## Goals

1. A document page shows its main metadata in a header strip and, when present, the `Summary` as an opening line.
2. Banners make critical states visible: production impact and retired documents.
3. Technical keys (SID, Transaction, Command and others) become chips that open their key pages.
4. Every document gets a quality score from 0 to 100, five dimension scores, a checklist with the points each missing item would add, and a tier.
5. The reader sees how the document compares with the others of the same Diátaxis type: rank, percentile and the median of each dimension.
6. Exemplary documents stand out on their page, on the dashboard and in every list.
7. Maintainers get a Quality page with quick wins: documents one change away from the next tier.
8. All of it works from disk (`file://`) and in incremental builds.
9. A repository can turn quality off with one setting.

## Non-goals

- Judging accuracy or truth. No check reads the meaning of the text.
- Readability formulas (Flesch and similar). They are tuned for English prose and give noise on command-heavy SAP Basis text. The profile shows a median sentence length of 13.7 words; it is no problem to solve.
- AI review of documents.
- Changes to the source documents. Fixing the corpus is a separate task (see "Data fixes").
- Other themes. The engine lives in techdoc. It moves to the core only if another theme needs it.
- Search ranking by quality. It is possible later (phase 3), but search is in the shared templates.

## Part A: frontmatter on the document page

Order from the top of a document page, below the top bar:

1. **Exemplary note** (only for Exemplary documents, see Part C).
2. **Header strip.** Quality emblem, then DocType, Status and Priority badges (the existing `.kb-badge` colours), then Date, Author, Product and Handover as links to their key pages. Which keys appear is set in `theme.json` (`header_keys`). Empty keys are skipped.
3. **Summary.** When the `Summary` key exists, it shows as a lead paragraph (larger, muted text). Missing: nothing shows.
4. **Banners.** One line each, in this order:
   - `Environment` contains Production: red, "This document changes production systems: <SID values>."
   - `Status` is Obsolete, Deprecated, Withdrawn or Rejected: grey, "Do not follow this document." The quality tier is Retired.
   - `Status` is Draft, Planned or Open: amber. Open question 1.
5. **Objects box.** Chips for `SID`, `Transaction`, `Command`, `Program`, `Table`, `Component`, `Server`, `User`, `Database` and the SAP notes. Each chip links to its key-value page. The list of keys is in `theme.json` (`object_keys`). SAP note numbers found in the body (pattern `note 123456`) link to `https://me.sap.com/notes/<n>`.
6. Table of contents and document body, as today.
7. **Linked from** (backlinks, exists) and **Related documents**: up to five documents sharing values of `SID`, `Product`, `Transaction`, `Component` or `Tag`, weighted by how rare the shared value is. Each line shows the tier chip of the related document and the shared values.

Head: `<meta name="author">` from `Author`. The description already comes from `Summary` (`headmeta.py`).

Print: the strip prints as plain text. Banners print. The emblem, objects box chips and the related list print as text without colour. The Exemplary note does not print.

## Part B: the quality model

### Principles

- **Per document, absolute.** The score of a document depends only on that document and its backlinks. When another document changes, this page doesn't need rebuilding. Backlinks already trigger a rebuild when they change (`processor.py`, `backlinks_changed`).
- **Relative at view time.** Rank, percentile and peer medians change whenever any document changes. They are written to `quality-index.js` on every build and read by the page in the browser. This follows the `search-index.js` pattern, which works from `file://`.
- **Judged against its type.** Targets and expected shapes depend on DocType and Category.
- **Explainable.** Every point comes from a named check. The panel lists all checks.
- **Capped.** No check rewards length beyond its target, so padding a document gains nothing.

### Dimensions and checks

Total 100. Words are counted outside code blocks.

**Findable (15):** can a reader find it and know what it is?

| Check | Points |
|---|---|
| Each core key set: Author, Date, DocType, Category, Status, Tag, Topic, Scope, Product | 1 each, 9 |
| Status, Priority and DocType use a known value (list in `theme.json`) | 3 |
| `Summary` key set | 3 |

**Structured (25):** is it organized like its kind?

| Check | Points |
|---|---|
| Two or more `##` sections (one section: 3) | 5 |
| The first section gives context: Description, Introduction, Overview, Summary, Objective, Context or Problem | 4 |
| Fits its DocType: how-to has 3+ numbered steps or a code block; tutorial has both; reference has a table or 5+ list items; explanation has 3+ sections | 8 |
| Has the sections of its Category skeleton (fraction found × 8). No skeleton: 8 with 3+ sections, else 4 | 8 |
| Each empty section (max 2) | −3 |
| Skeleton placeholder text left in (for example "Step one") | −6 |

**Complete (25):** is there enough of it?

`25 × min(words / target, 1)`, capped at 3 when the document has under 50 words.

| DocType | Target words | Corpus median |
|---|---|---|
| How-to guide | 150 | 49 |
| Reference | 200 | 75 |
| Explanation | 500 | 514 |
| Tutorial | 800 | 919 |

**Connected (15):** is it part of the knowledge base?

| Check | Points |
|---|---|
| Linked from at least one document (backlinks) | 4 |
| Links to at least one existing document | 3 |
| Cites an external source | 3 |
| Has a References, Documentation or Related section | 3 |
| Has an image or a diagram | 2 |
| Each broken link to another document (min total 0) | −3 |

**Current (20):** can a reader trust it today?

| Check | Points |
|---|---|
| Status is final: Released, Completed, Finished, Successful (other live statuses: 3) | 8 |
| Freshness: `12 × 0.5 ^ (age in years / half-life)`, from `Date` | 12 |

| DocType | Half-life (years) |
|---|---|
| How-to guide, Tutorial | 3 |
| Reference | 4 |
| Explanation | 8 |

### Tiers

| Tier | Score | Look |
|---|---|---|
| Exemplary | 75 and up | gold, star |
| Complete | 60 to 74 | green |
| Basic | 40 to 59 | slate grey |
| Stub | under 40 | dashed outline |
| Retired | Status Obsolete, Deprecated, Withdrawn or Rejected | struck-through grey, no score |

Thresholds are absolute, so a repository moves up as its documents improve. They live in `theme.json` (`quality.tiers`).

### Calibration on sapbasis-docs

| | Exemplary | Complete | Basic | Stub | Retired | Median score |
|---|---|---|---|---|---|---|
| How-to guide (510) | 14 | 124 | 111 | 246 | 15 | 40 |
| Reference (499) | 19 | 132 | 219 | 124 | 5 | 48 |
| Explanation (21) | 4 | 10 | 7 | 0 | 0 | 61 |
| Tutorial (4) | 0 | 1 | 2 | 1 | 0 | 53 |
| All (1034) | 37 | 267 | 339 | 371 | 20 | 47 |

- Exemplary is 3.6% of the corpus: rare, but reachable.
- Spot check: the highest scores go to self-contained documents with context, steps, sources and references. The ReaderRights how-to (75) has Introduction, Solution, a note, SAP and Help Portal links and screenshots. A typical Stub is a change record with a title and one line.
- Connected scores low (median 0) because no internal link works in this corpus. After the link fix, up to 7 more points become reachable.
- A `Summary` key alone (+3) would lift 129 documents to the next tier. 227 documents are within 5 points of the next tier.

### Relative comparison

`quality-index.js` sets `window.KB_QUALITY`:

```js
window.KB_QUALITY = {
  "peers": {"How-to guide": {"count": 495, "median": {"findable": 11, "structured": 9, "complete": 3, "connected": 0, "current": 11.3}}},
  "docs": {"SAP-BC-ADS-READERRIGHTS.html": {"score": 75, "tier": "exemplary", "type": "How-to guide", "rank": 10}}
};
```

- Peers are the live documents (Retired excluded) with the same DocType.
- Percentile: `1 - (rank - 1) / count`, shown as "Better than 98% of how-to guides".
- The page script fills the rank and draws the median ticks in the panel. Without the script (an old copy, or no JavaScript), the panel still shows the score, the dimensions and the checklist from the static HTML.

## Part C: visual integration

The mockup shows each item. Colours are CSS tokens on `:root` in `screen.css`:

| Token | Value | Use |
|---|---|---|
| `--q-exemplary` | `#f5b301` | ring, ribbon, meter |
| `--q-exemplary-ink` | `#8a6100` | text on light gold (contrast 5.0:1) |
| `--q-complete` | `#32d296` | as the existing green badge |
| `--q-complete-ink` | `#1b7a55` | text on light green (4.8:1) |
| `--q-basic` | `#8592a6` | slate |
| `--q-stub` | `#c3c9d2` | dashed outline; the chip text is `#6b7480` (4.7:1) |

No tier uses red. Red stays for production and incidents, as today. The tier is never shown by colour alone: each chip has the tier name, the Exemplary chip has a star, and the Stub chip is dashed.

### 1. Document page

- **Quality emblem** in the header strip: a 40px ring filled to the score, in the tier colour, with the number inside. Click or Enter opens the Quality panel. `title` and `aria-label`: "Quality 75 of 100, Exemplary".
- **Exemplary documents** get a 3px gold line under the top bar and a gold note: "★ Exemplary how-to guide: rank 10 of 495 how-to guides". This is the main way a reader recognises a good document.
- **Complete documents:** green emblem, no note.
- **Basic and Stub documents:** grey emblem, no note, no warning. The reader sees the number but nothing on the page is alarming.
- **Retired documents:** no emblem; the grey banner says why.

### 2. Quality panel

A `uk-drop` from the emblem and an entry in the title menu actions row (icon `star`). It contains:

- the large ring, the tier chip, and the rank sentence from `quality-index.js`;
- five bars (Findable, Structured, Complete, Connected, Current), each with points, maximum, and a tick at the peer median;
- the checklist in two columns: passed checks with a tick, missing checks with the points they add ("Add a Summary key +3").

Missing checks are worded as next steps, not as faults.

### 3. Dashboard

- **Hero bar:** a new stat "★ 37 Exemplary", linking to the Quality page.
- **Diátaxis cards:** a 6px stacked bar under each card with the tier mix of that type, and a caption ("14 exemplary, 124 complete").
- **Best documents:** a new collapsible section right after the Diátaxis grid. Cards with a gold top border, the small ring, the title, the type and the year. Top three per Diátaxis type, best first. This shelf is where good work gets seen.

### 4. Document lists (datatables)

A Quality column, enabled by adding `Quality` to the `datatable` list in `repo.json`. The cell holds a five-square meter (one square per 20 points, all gold when Exemplary) and the tier chip, with `data-order="<score>"` so the column sorts by score. Retired documents sort last.

### 5. Related and linked documents

Each line shows the tier chip of the target. When two documents cover the same topic, the reader picks the better one.

### 6. Quality page (`quality.html`)

A system page linked from the logo menu, with collapsible sections:

1. Tier mix per Diátaxis type (stacked bars with counts).
2. Exemplary documents (full list).
3. Quick wins: documents within 5 points of the next tier, with the one check that gets them there. Sorted by points missing.
4. Broken links between documents, with the source and the target.
5. Documents without a `Summary`.
6. Possible duplicates: title similarity of 0.8 or more, shown side by side with their scores. Titles that differ only by a date (journal series such as "SAP Basis notes on …") are excluded.

### 7. Print

Prints the strip and the banners as text. Does not print the emblem ring, the panel, the Exemplary note or the chip colours.

## Architecture

| File | Change |
|---|---|
| `techdoc/logic/techdoc_quality.py` (new) | Pure functions: `assess(text, meta, backlinks, profile) -> Assessment` (score, tier, dimensions, checks) and `peer_stats(assessments) -> dict`. No I/O except reading skeleton headings once. |
| `techdoc/logic/theme.py` | `build()` assesses every document once per build (keyed by docId, kept in memory), writes `quality-index.js`, builds `quality.html`. `build_page()` reads the cached assessment and passes it to the templates. `datatable_value_link` adds the Quality cell. |
| `techdoc/logic/techdoc_dashboard.py` | Hero stat, tier mix per Diátaxis card, Best documents section. |
| `techdoc/theme.json` | `quality` block: `enabled`, `tiers`, `targets`, `half_life`, `final_status`, `retired_status`, `known_values`; plus `header_keys` and `object_keys`. |
| `techdoc/templates/` | New `DOC_HEADER.tpl` (strip, Summary, banners, objects box), `QUALITY_PANEL.tpl`, `PAGE_QUALITY.tpl`; `HTML_BODY.tpl` includes the header; `PAGE_INDEX.tpl` gets the shelf. All with `NAME :: START/END` comment pairs. |
| `techdoc/framework/kb4it/css/screen.css`, `print.css` | Tokens and the `.kb-q-*` classes from the mockup. |
| `techdoc/framework/kb4it/js/quality.js` (new) | Fills the rank and the median ticks from `window.KB_QUALITY`. |
| `repo.json` | `"quality": false` turns everything off. Default: on. |

Cost: the profile script scans 1034 documents in under 1 second. The assessment reads the source Markdown that `build_page` already reads.

The checklist and the score are in the static HTML. `quality-index.js` only adds rank and medians, so a page whose script fails to load is still correct.

Out of the theme, in the core, as separate small fixes:

- `LINK_BROKEN` should also catch extensionless links and links to non-Markdown documents (`.adoc`) that match no file.

## Data fixes in sapbasis-docs (separate task)

Scripted, with a backup in the scratchpad and no git in the repository, as for the DocType work:

1. Rewrite the 271 extensionless links to existing documents as `.md` links, and the 4 `.adoc` links whose `.md` exists. List the other 75 for review.
2. Normalize `Date` to one format, and `Status` and `Priority` to fixed sets.
3. Add a `Summary` key, starting with the quick wins.

## Phases

1. **Engine and document page:** `techdoc_quality.py`, header strip, Summary, banners, emblem, panel, Exemplary note, `quality-index.js`.
2. **Lists and dashboard:** Quality column, hero stat, tier mix on Diátaxis cards, Best documents shelf.
3. **Quality page:** quick wins, broken links, missing Summary, duplicates. Objects box and Related documents.
4. **Later, optional:** search results show the tier chip; score as a tie-breaker in search ranking.

## Testing

Theme-only changes: `tests/themes` and `check_themes.sh`, no browser tests (user rule).

- `tests/themes/test_techdoc_quality.py`: one test per check with a small Markdown fixture; target cap; stub cap; Retired statuses; freshness half-life; tier thresholds; `peer_stats` rank and median.
- Build tests: an Exemplary fixture shows the note and the gold emblem; a Stub fixture shows no note; `quality-index.js` exists and parses; the Quality column sorts by `data-order`; `"quality": false` removes every `.kb-q-*` element and the index file.
- HTML: the W3C check (`scripts/devel/validate_html.py`) stays at 0 errors and 0 warnings; block comments stay paired.

## Risks

- **Gaming the score.** Authors may add sections or words for points. Caps limit this, and the checklist shows what each point means. The score is a guide for maintainers, not a target for authors.
- **Records are not documents.** Change and incident records are short by nature, and many will be Stubs. That is accurate, but it may annoy. Open question 3.
- **False confidence.** A high score does not mean the content is right. The panel says "Quality measures structure, metadata, links and age. It does not check that the content is correct."
- **Discouragement.** Low tiers stay neutral grey and appear only in lists and on the Quality page.

## Open questions

1. **Draft banner.** It reopens the 0.9.1 non-goal "a draft is published with no label". Keep the banner, or rely on the Draft badge in the strip only?
2. **Freshness source.** `Date` is the only date property. When `git` is set in `repo.json`, should freshness use the last commit date of the file instead? That would read git history at build time.
3. **Records.** Should the categories in the `events` list (Change, Incident, Meeting, Task) use a lighter profile, or no score at all, with the score kept for knowledge documents?
4. **Visibility.** Show the emblem on Basic and Stub pages (current design) or only on Complete and Exemplary pages?
5. **Category and DocType overlap.** Category mixes document form (Report, Template) with work type (Change, Incident). Split it before this lands, or after?

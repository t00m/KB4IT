# Document quality, page organisation and images in techdoc

Status: decisions taken, ready for an implementation plan.
Date: 2026-10-24
Theme: techdoc
Mockup: [`2026-10-24-document-quality-mockup.html`](2026-10-24-document-quality-mockup.html) (open it from this folder; it loads the real techdoc CSS and UIkit, so the tabs and the lightbox work)
Data: sapbasis-docs, 1034 documents, profiled on 2026-10-24 with the draft model in this spec.

## Intent

Two related changes to techdoc:

1. **Use the frontmatter on the document page.** Today a document page shows no metadata at all. The Document Properties section was removed in 0.10.0, and nothing replaced it.
2. **Measure the quality of each document and show it.** Quality is shown in absolute terms (a score and a tier) and relative to the other documents of the same type (a rank). A good document must look good: the reader sees at a glance that it is one of the best in the repository.
3. **Organise the page.** UIkit tabs and accordions hold what surrounds the text (metadata, quality, related documents, history), with a print rule for each block.
4. **Improve images and content blocks.** Lightbox, captions, galleries, copy buttons on code, scrolling tables.
5. **Split Category** into the form of the document (`Category`) and the type of work it records (`WorkType`), before the rest (Part F).

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
- **Drafts:** "a draft is built and published like any other document, with no label." This design changes that for techdoc only: a document with `Status: Draft` shows a Draft banner (decided 2026-10-24). The core behaviour does not change.

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
10. The page keeps the body in reading order. Metadata, quality, related documents and history sit in one tabbed info card, closed by default.
11. Every block has a print rule: what helps on paper prints, screen-only panels do not.
12. Images open full size in a lightbox, have captions and stable sizes, and missing images are reported.

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
   - `Status` is Draft: amber, "Draft: not final. Check with the author before you follow it." Planned and Open get no banner: on records they describe the work, not the document.
5. **Technical objects** (shown in the Details tab of the info card, Part D). Chips for `SID`, `Transaction`, `Command`, `Program`, `Table`, `Component`, `Server`, `User`, `Database` and the SAP notes. Each chip links to its key-value page. The keys are the Technical objects group of `info_groups` in `theme.json`. SAP note numbers found in the body (pattern `note 123456`) link to `https://me.sap.com/notes/<n>`.
6. Info card (Part D), then the table of contents and the document body, as today.
7. **Linked from** (backlinks, exists) and **Related documents**, shown in the Related tab of the info card (Part D): up to five documents sharing values of `SID`, `Product`, `Transaction`, `Component` or `Tag`, weighted by how rare the shared value is. Each line shows the tier chip of the related document and the shared values.

Head: `<meta name="author">` from `Author`. The description already comes from `Summary` (`headmeta.py`).

Print: see the print table in Part D (D6).

## Part B: the quality model

### Principles

- **Per document, absolute.** The score of a document depends only on that document and its backlinks. When another document changes, this page doesn't need rebuilding. Backlinks already trigger a rebuild when they change (`processor.py`, `backlinks_changed`).
- **Relative at view time.** Rank, percentile and peer medians change whenever any document changes. They are written to `quality-index.js` on every build and read by the page in the browser. This follows the `search-index.js` pattern, which works from `file://`.
- **Judged against its type.** Knowledge documents are judged by DocType and their Category skeleton; records by their WorkType (see "Records" below).
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
| Has the sections of its skeleton (fraction found × 8). No skeleton: 8 with 3+ sections, else 4. Section names match by synonyms: Overview also matches Description, Introduction or Information; Impact matches Scope, Risk or Justification; Rollback matches Fallback or Backout; Verification matches Validation or Check; Resolution matches Solution or Fix | 8 |
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

### Records

Change, incident, task and meeting records are short by nature, and their age does not make them wrong: they describe something that happened. They are scored on a lighter scale with the same five dimensions, the same 100 points and the same tiers:

| Dimension | Knowledge document | Record |
|---|---|---|
| Findable | as above | as above |
| Structured | sections, context first, DocType fit 8, skeleton 8 | sections, context first, WorkType skeleton 16 (no DocType fit) |
| Complete | target by DocType (150 to 800 words); under 50 words: max 3 | target 60 words; under 20 words: max 3 |
| Connected | as above | as above |
| Current | final status 8, freshness 12 | final status (Released, Completed, Finished, Successful) 20; any other live status 10; no freshness |

Peers for rank and medians are records of the same WorkType: a change is compared with changes, not with how-to guides.

### Calibration on sapbasis-docs

With the split of Part F applied (529 records, 505 knowledge documents) and section synonyms:

| | Exemplary | Complete | Basic | Stub | Retired | Median score |
|---|---|---|---|---|---|---|
| How-to guide (234) | 13 | 106 | 76 | 35 | 4 | 60 |
| Reference (251) | 25 | 84 | 99 | 41 | 2 | 55 |
| Explanation (16) | 2 | 7 | 7 | 0 | 0 | 61 |
| Tutorial (4) | 0 | 2 | 1 | 1 | 0 | 61 |
| Change records (307) | 1 | 51 | 243 | 0 | 12 | 49 |
| Incident records (169) | 6 | 145 | 15 | 1 | 2 | 68 |
| Task records (44) | 2 | 26 | 16 | 0 | 0 | 64 |
| Meeting minutes (9) | 0 | 3 | 6 | 0 | 0 | 55 |
| All (1034) | 49 | 424 | 463 | 78 | 20 | 58 |

The first draft, with one scale for all, gave 37 Exemplary and 371 Stubs: most Stubs were short records judged as how-to guides.


- Exemplary is 4.7% of the corpus: rare, but reachable.
- Spot check: the highest scores go to self-contained documents with context, steps, sources and references. The ReaderRights how-to (78, rank 2 of 230) has Introduction, Solution, a check section, SAP and Help Portal links and screenshots. The best records are recent incidents that follow their skeleton (Overview, Impact, Root Cause, Resolution).
- 289 of the 307 change records have one section, Description, and no Impact or Rollback. Their Basic tier is accurate.
- Connected scores low (median 0) because no internal link works in this corpus. After the link fix, up to 7 more points become reachable.
- A `Summary` key alone (+3) would lift 163 documents to the next tier. 294 documents are within 5 points of the next tier.

### Relative comparison

`quality-index.js` sets `window.KB_QUALITY`:

```js
window.KB_QUALITY = {
  "peers": {"How-to guide": {"count": 230, "median": {"findable": 12, "structured": 15.7, "complete": 23.5, "connected": 2, "current": 10.6}},
            "Change": {"count": 295, "median": {}}},
  "docs": {"SAP-BC-ADS-READERRIGHTS.html": {"score": 78, "tier": "exemplary", "peer": "How-to guide", "rank": 2}}
};
```

- Peers are the live documents (Retired excluded) of the same DocType for knowledge documents, or of the same WorkType for records.
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
- **Exemplary documents** get a 3px gold line under the top bar and a gold note: "★ Exemplary how-to guide: rank 2 of 230 how-to guides". This is the main way a reader recognises a good document.
- **Complete documents:** green emblem, no note.
- **Basic and Stub documents:** grey emblem, no note, no warning. The reader sees the number but nothing on the page is alarming.
- **Retired documents:** no emblem; the grey banner says why.

### 2. Quality panel

The Quality tab of the info card (Part D). The emblem and an entry in the title menu actions row (icon `star`) open the card on this tab. It contains:

- the large ring, the tier chip, and the rank sentence from `quality-index.js`;
- five bars (Findable, Structured, Complete, Connected, Current), each with points, maximum, and a tick at the peer median;
- the checklist in two columns: passed checks with a tick, missing checks with the points they add ("Add a Summary key +3").

Missing checks are worded as next steps, not as faults.

### 3. Dashboard

- **Hero bar:** a new stat "★ 49 Exemplary", linking to the Quality page.
- **Diátaxis cards:** a 6px stacked bar under each card with the tier mix of the knowledge documents of that type, and a caption ("13 exemplary, 106 complete of 234"). Records are scored apart; their tier mix shows on the Quality page.
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

See the print table in Part D (D6).

## Part D: page organisation

### Rule

The document text stays visible and in reading order. Tabs and accordions organise what surrounds it: metadata, quality, related documents, history. Browser find (Ctrl+F) skips text in a hidden panel, and readers skim the body, so the body never goes into tabs. The only exception is tabs the author writes on purpose (D4).

### D1. Page order

1. Top bar (as today).
2. Exemplary note (Part C).
3. Header strip, Summary and banners (Part A). Always visible.
4. **Info card** (D2).
5. Inline table of contents and the body with its folding sections (as today).
6. Footer.

### D2. Info card

One card between the banners and the body, built with `data-uk-tab` and `data-uk-switcher`:

| Tab | Content | Shown when |
|---|---|---|
| Details | Frontmatter keys in groups (D3) | always |
| Quality | The quality panel (Part C, section 2) | quality is on and the document is not Retired |
| Related | Linked from (backlinks) and Related documents | at least one entry |
| History | Date, source file name, "View source" and "Edit" links (edit only when git is set), build time | always |

Behaviour:

- **Default state.** A document with a `Summary` starts with the card closed: one line with the tab names and a chevron. A document without a `Summary` starts with the card open on Details, so the reader still gets context before the text. The template sets this state in the HTML, so it is right without JavaScript and before any script runs.
- **Opening and closing.** Clicking a tab opens the card on that tab. Clicking the open tab, or the chevron, closes it.
- **Remembered.** The last tab the reader chose is kept across pages in `localStorage` (key `kb-info-card-tab`); a document without a `Summary` still opens on Details. When the reader closes or opens the card, that choice is kept for that page only (key `kb-info-card:<page>`). Every access is wrapped in `try`/`catch` so private windows still work.
- **Entry points.** The quality emblem opens the card on Quality. The "Document properties" action in the title menu opens it on Details. A URL ending in `#details`, `#quality`, `#related` or `#history` opens that tab.
- **Without JavaScript.** UIkit's CSS hides inactive switcher panels even with no script. A one-line script in the head adds the class `kb-js` to `<html>`. The theme hides inactive panels only under `.kb-js`. Without it, every panel shows in order, each under its own heading.
- **Headings.** Each panel starts with an `<h2>` (Details, Quality, Related, History). On screen, with JavaScript, the heading is visually hidden because the tab already names it (`uk-hidden-visually`). It stays visible in print and without JavaScript. This keeps the outline valid for the W3C checker.
- **Accessibility.** UIkit sets `role="tablist"`, `role="tab"` and `aria-selected`. The chevron is a `<button>` with `aria-expanded`.

### D3. Details tab: keys in groups

A grid of definition lists, one per group. The groups and their keys are set in `theme.json` (`info_groups`), in order:

| Group | Keys |
|---|---|
| Classification | DocType, Category, WorkType, Topic, Scope, Handover |
| Systems | Product, SID, Environment, Database, OS, Stack, Server, Kernel |
| Technical objects | Transaction, Command, Program, Table, Job, RFC, Component, User, Role, Filesystem, SAP notes found in the body |
| Organisation | Author, Team, Project, Milestone, Company |
| Lifecycle | Status, Priority, Date, Periodicity, Public |
| Other | every key not listed above |

- Values link to their key-value pages, as in the old Document Properties section.
- Technical object values are monospace chips. This replaces the separate Objects box of Part A.
- Empty groups are hidden. `Title`, `Summary`, `Bookmark` and `SystemPage` are never listed.
- On phones the grid is one column.

### D4. Inside the body

- **Folding sections** stay as they are: the first section and the inline table of contents start open, the rest closed.
- **Author tabs** for real variants of the same content (Linux or Windows, Oracle or DB2). They use `pymdownx.tabbed` with `alternate_style: true`. `pymdown-extensions` is already the optional extra `kb4it[extras]`; a repository turns it on in the `markdown` block of `repo.json`. The theme styles `.tabbed-set` like `uk-tab`. The extension builds tabs from radio buttons and CSS, so they work without JavaScript.
- **Collapsible notes** (`??? note "Title"`) use `pymdownx.details`. They render as `<details>` and look like the existing admonitions with a chevron.
- The help gains a short page on both, with examples.

### D5. Dashboard

The Changes, Incidents, Events and Monitoring sections become one **Activity** card with four tabs. Tabs with no entries are hidden. The last tab is remembered. The card is collapsible like the other dashboard sections.

### D6. Print

Some panels belong only on screen. Every block has a fixed print rule; the four info card tabs can be changed in `theme.json` (`info_tabs.<name>.print`).

| Block | Printed | How |
|---|---|---|
| Header strip | yes | one line of plain text, no ring, no badge colours |
| Summary | yes | as on screen |
| Banners | yes | border and bold label, no background fill |
| Exemplary note | no | |
| Info card: Details | yes | after the title, under the heading "Document details", groups in two columns |
| Info card: Quality | no | |
| Info card: Related | no | links do not work on paper |
| Info card: History | no | |
| Info card tab bar and chevron | no | |
| Inline table of contents | yes | as today |
| Folding sections | yes | all open, as today |
| Author tabs | yes | every panel, with its label as a bold line above it |
| Collapsible notes | yes | open |
| Images | yes | figure and caption (Part E), no zoom icon, kept on one page |
| Image gallery grid | yes | thumbnails become full-width figures |
| Code copy button, language label, "Show all" button | no | |
| Folded long code | yes | printed in full |
| Sticky table of contents, back-to-top | no | |
| Dashboard Activity card | active tab only | the dashboard is a screen page |

`print.css` implements this with one class, `kb-noprint` (`display: none` in print), set by the templates from these rules, and with `.uk-switcher > *` forced visible for printable panels.

## Part E: images and content components

### E1. Images

The theme rewrites each `<img>` inside the document body while `build_page` already holds the page as an lxml tree:

1. **Size.** Width and height attributes come from the image file: PNG, JPEG and GIF headers, SVG `viewBox`. A small reader in the theme, no new dependency. With the size known, the page does not jump while images load.
2. **Lazy loading.** `loading="lazy"` and `decoding="async"`. The first image of the page loads normally.
3. **Figure.** The image is wrapped in `<figure class="kb-figure">`. When the alt text is descriptive, it becomes the `<figcaption>`, numbered "Figure 3." A file-name-like alt text (`SAP-BC-SC-DMS-00`, `image12`) gets no caption. sapbasis-docs: 407 descriptive, 176 file-name-like.
4. **Lightbox.** The body gets `data-uk-lightbox="animation: fade"`. Each figure image is a link to the full file with `data-caption`. One gallery per document, with previous and next. The cursor shows a zoom icon. 96 of the 259 PNG screenshots are wider than 900px and unreadable at page width.
5. **Screenshot frame.** `.kb-shot`: 1px border, 4px radius, a light shadow. White SAP screens no longer merge into the page.
6. **Galleries.** Three or more images in a row, with no text between them, become a grid of thumbnails (`uk-child-width-1-2 uk-child-width-1-3@m`). The lightbox still shows them one by one. One document has 58 screenshots.
7. **Left alone.** Images inside a link keep the link and get no lightbox. Images smaller than 64px wide and images inside a paragraph of text stay inline, without figure or frame.
8. **Missing files.** A missing image becomes a grey placeholder box with the file name: "Image missing: resources/images/x.png". The build logs `[THEME] IMAGE_MISSING doc=<doc> src=<src>`. The Quality page lists them. In the quality model, each missing image takes 3 points from Connected, like a broken link. The calibration above ran without this check; with today's sapbasis-docs, where every image file is missing, it would lower 158 documents.

The lightbox reads images through plain `<img>` elements, so it works from `file://`.

### E2. Code blocks

1,312 code blocks in sapbasis-docs.

- **Copy button** in the top right corner (`data-uk-icon="copy"`), showing "Copied" for two seconds. It uses `navigator.clipboard` and falls back to a hidden textarea with `document.execCommand("copy")`.
- **Language label** from the `language-*` class, top left, small caps.
- **Long blocks** of more than 30 lines show the first 20 and a "Show all N lines" button. Print shows them in full.

### E3. Tables

- Wide tables are wrapped in `.uk-overflow-auto`, so they scroll sideways instead of widening the page.
- Tables with more than 15 rows get a sticky header (`position: sticky` on `th`).

### E4. Long documents

- **Back to top:** a `data-uk-totop` button bottom right, shown after one screen of scroll.
- **Sticky table of contents (optional):** on screens 1400px or wider, for documents with four or more sections, the table of contents also sits in a right column with `data-uk-scrollspy-nav`, which highlights the current section. Off by default (`theme.json`: `toc_sidebar`), because the title menu and the inline table of contents already cover it.

### E5. What is not used

- **Slider and slideshow.** They hide content from readers, from search and from print.
- **Automatic tabs** built from sections. Readers would not know the content is there.
- **Modal dialogs for content.** The lightbox is the only overlay, and only for images.

## Part F: splitting Category (phase 0)

Category mixes two things: the **form** of a document (Procedure, Note, Report, Template) and the **type of work** it records (Change, Incident, Task, Meeting). The quality model needs to know which documents are records, and the dashboard needs the type of work. The split comes before everything else.

### F1. Keys

| Key | Meaning | Values |
|---|---|---|
| `Category` | Form of the document | Procedure, Note, Report, Template, Record, Minutes |
| `WorkType` (new) | Type of work the document records; only on records | Change, Incident, Task, Meeting |

`Record` is the form of change, incident and task records. `Minutes` is the form of meeting notes. A document with a `WorkType` is a **record**; any other document is a **knowledge document**.

### F2. Mapping for sapbasis-docs

| Category today | Documents | Category after | WorkType after |
|---|---|---|---|
| Change | 307 | Record | Change |
| Incident | 167 | Record | Incident |
| Task | 44 | Record | Task |
| Meeting | 9 | Minutes | Meeting |
| Report, Incident | 2 | Report | Incident |
| Procedure, Note, Report, Template and their combinations | 503 | unchanged | none |
| no Category | 2 | unchanged | none |

Scripted, with a backup in the scratchpad and no git in the repository. The script writes a CSV with every change, like `doctype-classification.csv`.

### F3. Code and configuration

| Place | Change |
|---|---|
| techdoc dashboard (`techdoc_dashboard.py`, `PAGE_INDEX.tpl`) | The alert bar and the open items read `WorkType` instead of `Category`. Links go to `WorkType_Change.html` and `WorkType_Incident.html`. |
| techdoc events page (`theme.py`) | The event type of a document is its `WorkType` when set, otherwise its `Category`. The `events` list in `repo.json` keeps its values. |
| techdoc skeletons | Change, Incident and Task skeletons get `Category: Record` and `WorkType: <type>`; Meeting gets `Category: Minutes` and `WorkType: Meeting`. |
| techdoc `apps/*/config/repo.json` | `WorkType` added to the `datatable` columns and the menu, after `Category`. |
| techdoc help (`PAGE_HELP.tpl`, `help/source/reference-theme-techdoc.md`) | Both keys described, with the value lists. |
| core search facets (`builder.py`) | `WorkType` added next to `Category` and `Tag`. |
| core feed filter (`builder.py`) | A feed category matches `Category` or `WorkType`, so existing feed settings keep working. |

**Older repositories.** When a document has no `WorkType` and its `Category` is Change, Incident, Task or Meeting, techdoc reads that value as the `WorkType`. A repository that is not migrated keeps its dashboard, events and quality profiles.

The core changes run the full test suite without browser tests; the rest is theme-only.

## Architecture

| File | Change |
|---|---|
| `techdoc/logic/techdoc_quality.py` (new) | Pure functions: `assess(text, meta, backlinks, profile) -> Assessment` (score, tier, dimensions, checks) and `peer_stats(assessments) -> dict`. No I/O except reading skeleton headings once. |
| `techdoc/logic/theme.py` | `build()` assesses every document once per build (keyed by docId, kept in memory), writes `quality-index.js`, builds `quality.html`. `build_page()` reads the cached assessment and passes it to the templates. `datatable_value_link` adds the Quality cell. |
| `techdoc/logic/techdoc_dashboard.py` | Hero stat, tier mix per Diátaxis card, Best documents section. |
| `techdoc/theme.json` | `quality` block: `enabled`, `tiers`, `targets`, `half_life`, `final_status`, `retired_status`, `known_values`; plus `header_keys`, `info_groups`, `info_tabs` (with `print`) and `toc_sidebar`. |
| `techdoc/templates/` | New `DOC_HEADER.tpl` (strip, Summary, banners), `INFO_CARD.tpl` (tabs and the four panels), `QUALITY_PANEL.tpl`, `PAGE_QUALITY.tpl`; `HTML_BODY.tpl` includes the header and the card; `PAGE_INDEX.tpl` gets the shelf and the Activity card. All with `NAME :: START/END` comment pairs. |
| `techdoc/framework/kb4it/css/screen.css`, `print.css` | Tokens and the `.kb-q-*` classes from the mockup. |
| `techdoc/framework/kb4it/js/quality.js` (new) | Fills the rank and the median ticks from `window.KB_QUALITY`. |
| `techdoc/framework/kb4it/js/page.js` (new) | Info card state and URL tabs, code copy and "Show all", Activity tab memory. |
| `techdoc/logic/techdoc_media.py` (new) | Image size reader, figure and caption, lightbox links, galleries, missing-image placeholder; code block and table wrappers. Works on the lxml tree in `build_page`. |
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
4. Copy the image files into `source/resources/images`. The documents reference 390 files and none is in the repository. 267 are in `~/Downloads/sap-basis-doc-img/resources/images`; 123 are missing everywhere.

## Phases

0. **Category split:** `WorkType` key, mapping script for sapbasis-docs, dashboard, events, skeletons, help, search facets and feed filter, fallback for older repositories (Part F).
1. **Page organisation and images:** header strip, Summary, banners, info card with Details and History, print rules, and all of E1 (images). Images come first because they are broken today and need no quality engine.
2. **Quality engine:** `techdoc_quality.py` with both scales, `quality-index.js`, emblem, Quality tab, Exemplary note.
3. **Lists and dashboard:** Quality column, hero stat, tier mix on Diátaxis cards, Best documents shelf, Activity card.
4. **Quality page and Related tab:** quick wins, broken links, missing Summary, missing images, duplicates; Related documents.
5. **Content blocks:** code copy and folding, tables, back-to-top; author tabs and collapsible notes with their help page.
6. **Later, optional:** sticky table of contents; tier chip in search results; score as a tie-breaker in search ranking.

## Testing

Theme-only changes: `tests/themes` and `check_themes.sh`, no browser tests (user rule). Phase 0 touches the core (search facets, feed filter), so it runs the full suite without browser tests.

- Category split: the dashboard alert bar reads `WorkType`; a document with `Category: Change` and no `WorkType` still shows there (fallback); the events page groups by `WorkType` then `Category`; search facets list `WorkType`; a feed filter on `Change` matches `WorkType: Change`.
- Records scale: a 60-word change with Overview, Impact and Rollback gets full Structured and Complete points; an old record keeps its Current points; records rank only against records of the same WorkType.
- Draft banner: shown for `Status: Draft`, not for Planned or Open.

- `tests/themes/test_techdoc_quality.py`: one test per check with a small Markdown fixture; target cap; stub cap; Retired statuses; freshness half-life; tier thresholds; `peer_stats` rank and median.
- Build tests: an Exemplary fixture shows the note and the gold emblem; a Stub fixture shows no note; `quality-index.js` exists and parses; the Quality column sorts by `data-order`; `"quality": false` removes every `.kb-q-*` element and the index file.
- Info card: a document with a `Summary` renders the card closed; one without renders it open on Details; each tab panel exists only when it has content; panels carry the `kb-noprint` class according to `info_tabs.*.print`; every panel has its `<h2>`.
- Images: width and height match the file; a descriptive alt gives a numbered `<figcaption>`, a file-name alt gives none; images in links get no lightbox; three images in a row make a gallery; a missing file gives the placeholder and the `IMAGE_MISSING` log line.
- Code and tables: copy button and language label present; tables are wrapped in `.uk-overflow-auto`.
- Print CSS: a test reads `print.css` and checks that `.kb-noprint` is hidden and printable switcher panels are forced visible.
- HTML: the W3C check (`scripts/devel/validate_html.py`) stays at 0 errors and 0 warnings; block comments stay paired.

## Risks

- **Gaming the score.** Authors may add sections or words for points. Caps limit this, and the checklist shows what each point means. The score is a guide for maintainers, not a target for authors.
- **Records are not documents.** Handled by the lighter scale for records. Change records still score lower than incidents, because most lack Impact and Rollback sections; that is accurate.
- **False confidence.** A high score does not mean the content is right. The panel says "Quality measures structure, metadata, links and age. It does not check that the content is correct."
- **Discouragement.** Low tiers stay neutral grey and appear only in lists and on the Quality page.

## Decisions

Taken on 2026-10-24:

1. **Draft banner:** yes, for `Status: Draft` only (Part A).
2. **Freshness:** from `Date` only. No git dates, no `Updated` key.
3. **Records:** scored on a lighter scale (Part B, "Records").
4. **Score ring on Basic and Stub pages:** shown, in neutral grey.
5. **Category:** split into `Category` (form) and `WorkType` (type of work) before the rest (Part F, phase 0).
6. **Info card:** closed when the document has a `Summary`; open on Details when it has none (Part D).

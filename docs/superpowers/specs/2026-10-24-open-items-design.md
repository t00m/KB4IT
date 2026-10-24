# Open items after the techdoc document page (phase 1)

Status: draft, written without a question round at the user's request; calls marked "my call" are open to review.
Date: 2026-10-24
Scope: KB4IT core, the techdoc theme, and the sapbasis-docs knowledge base.
Related: [`2026-10-24-document-quality-design.md`](2026-10-24-document-quality-design.md) (the quality spec; phases 0 and 1 are done).

## Intent

Phase 1 of the quality spec is built. This spec collects every item still open, so each one can get its own plan, and fixes their order. Phases 2 to 6 of the quality spec stay specified there; this spec only sets where they fall in the order and what they depend on.

## Order of work

Each work package (WP) gets its own implementation plan and is done in this order, except WP7, which can come at any time:

1. **WP1 Core fixes.** Small, independent, and they help everything after them.
2. **WP2 sapbasis-docs data.** Needs WP1 (link check) to verify the link rewrite.
3. **WP3 techdoc small fixes.**
4. **WP4 Quality phase 2:** engine, score ring, Quality tab, Exemplary note.
5. **WP5 Quality phases 3 and 4:** lists and dashboard; Quality page and Related tab.
6. **WP6 Quality phase 5:** code blocks, tables, back-to-top, author tabs.
7. **WP7 Header cache** (core performance).
8. **WP8 Quality phase 6** (optional): sticky table of contents, tier chip in search.

Why this order: the quality score's Connected dimension is near 0 for every sapbasis document until the links are fixed (WP2), and phases 3 and 4 show the score, so they need phase 2 first. The header cache is separate from all of it.

## Global constraints

- Core changes run the full suite without browser tests (`pytest --ignore=tests/browser`); theme-only changes run `tests/themes` and `scripts/devel/check_themes.sh`. Browser tests are never run; a Playwright look at real pages is allowed and written in the response file.
- HTML stays W3C valid (`scripts/devel/validate_html.py`), UIkit attributes as `data-uk-*`, every new template block with a `NAME :: START/END` comment pair.
- Every new log code a user can see is documented in `help/source/troubleshooting.md` or a `reference-*.md` page (`test_every_logged_error_code_is_documented`).
- sapbasis-docs never goes under git. Every scripted change first backs up `source/` to the scratchpad and writes a CSV of its changes. Rebuilds after a theme change use `build --force` (WP1 item 2).
- Commits: one-line Conventional Commits, no trailers, never push, never branch.
- Writing: no em dash, plain sentences, no framework name in help pages.

## WP1 Core fixes

### 1. A Summary with commas is cut

**Problem.** `kb4it/core/documents.py` splits every string value on commas, so `Summary: Request the credential, then register it.` is stored as two values. `headmeta.py` (page description), `builder.py` `search_record` (search result text) and the feed writer read only the first value, so all three show "Request the credential". techdoc (`techdoc_docpage.summary`) and apphelp (`_joined`) already join the values back.

**Change.** A core helper `joined_value(values: list[str]) -> str` (in `kb4it/core/documents.py`) that joins the non-empty values with `", "`. The three core readers use it. techdoc's `summary()` and apphelp's `_joined` call it too, so there is one rule. The split itself does not change: other keys rely on it.

**Test.** A document with `Summary: A, B` gets `<meta name="description" content="A, B">`, the search record `"s": "A, B"` and the feed entry summary "A, B".

### 2. A theme change does not rebuild pages

**Problem.** An incremental build skips documents whose source did not change, so after a theme change (templates, theme logic, `theme.json`) the old pages stay.

**Decision (user, 2026-10-24).** Keep `kb4it build --force` as the way to rebuild after a theme change; no automatic detection.

**Change.** The help says it: in `help/source/howto-create-theme.md` (where theme files are edited) and in the troubleshooting page, a short entry "Pages do not change after a theme edit" with the fix `kb4it build --force`.

**Test.** The existing help tests pass; no code change.

### 3. Links without an extension are not checked

**Problem.** `kb4it/core/mdlinks.py` only records relative links ending in `.md` or `.markdown`. A link written `[x](SAP-BC-TSK-MANAGE-BATCH)` or `[x](old.adoc)` renders as is, is broken on disk and on most servers, and nothing reports it. sapbasis-docs has 275 such links to existing documents and 75 to nothing.

**Change.** `_MdLinkProcessor` also records relative links (no scheme, no leading `/` or `#`, not ending in `/`) whose last path part has no extension or ends in `.adoc`. They are not rewritten. The build and `kb4it verify` report them as `LINK_NO_EXTENSION from=<doc> to=<path> suggest=<name>.md` when `<path>.md` exists in the source (warning), else as `LINK_BROKEN` as today. My call: report, do not rewrite. KB4IT's link format stays `.md`; the editor and `verify` already teach it, and WP2 fixes the data.

**Test.** Three documents: one links to `b` (exists as `b.md`), one to `c.adoc` (no `c.md`), one to `b.md`. The build logs one `LINK_NO_EXTENSION ... suggest=b.md`, one `LINK_BROKEN ... to=c.adoc`, and nothing for `b.md`; `kb4it verify` lists the same two and exits 1.

### 4. A repeated value is listed twice

**Problem.** `Tag: zeta, zeta` puts the document twice under `zeta` in `kbdict["metadata"]`, so it shows twice on `Tag_zeta.html`.

**Change.** `documents.py` drops repeated values of a key, keeping the first, before the document is stored.

**Test.** The page `Tag_zeta.html` lists the document once.

### 5. The wheel test hides its error

**Problem.** `tests/packaging/test_scripts.py::test_build_python_makes_wheel_and_sdist` failed once in a full run (`build_python.sh` exit 2) and passed alone. `capture_output=True` with `check=True` drops the script's output, so the cause is unknown.

**Change.** The test runs without `check=True` and asserts the return code with the script's stdout and stderr in the message. Then the full suite runs three times; if it fails again, the output names the cause and a fix follows under superpowers:systematic-debugging. If it does not fail in three runs, the item closes with the better message in place.

## WP2 sapbasis-docs data

Scripted, each step with a backup and a CSV, in `/home/t00m/Documents/devel/tests/kb4it/sapbasis-docs/bin/` (no git there). The scripts `doctype.py`, `handover.py` and `docs.py` were copied there on 2026-10-24 from a session scratchpad that is lost on reboot; `handover.py` loads `docs.py` from its own folder, so they stay together.

1. **Links.** Rewrite the 271 extensionless links to existing documents as `<name>.md`, and the 4 `.adoc` links whose `.md` exists. The other 75 go to `links-unresolved.csv` for the user. After the rebuild, the build reports no `LINK_NO_EXTENSION`, and backlinks appear on the target pages.
2. **Status.** `Finished` (3) and `Successful` (2) become `Completed`. The other values stay.
3. **Priority.** `Standard` (76) becomes `Normal`. `Unknown` (48) stays; techdoc styles it as muted.
4. **Date.** The one RFC date (`Thu, 26 Jan 2023 09:26:54 GMT`) becomes `2023-01-26 09:26:54`. The other dates keep their format: `YYYY-MM-DD` (542), `YYYY-MM-DD HH:MM` (37) and `YYYY-MM-DD HH:MM:SS` (455) are all valid, and adding `00:00:00` would invent a time. My call.
5. **Drafts.** 193 documents have `Status: Draft` and now show the amber Draft banner: 167 knowledge documents and 26 records. A CSV `drafts.csv` lists them with title, DocType, date and word count, for the user to mark which are really final. The script then sets `Released` (knowledge documents) or `Completed` (records) on the ones marked. Nothing changes without that list.
6. **Summaries.** A script drafts one `Summary` per document from the first sentence of its first section (Description, Introduction or the first paragraph), cut to 160 characters, and writes `summaries.csv` (file, title, draft). The user edits or deletes rows; only the rows left are applied. The CSV lists every document without a Summary, records last; after WP4, the Quality page names the quick wins. My call: draft and review, never apply generated text unseen.
7. **Missing images.** 138 files: 123 under `resources/images/` (listed in `images-missing.txt`) and 15 under `extracted-media/`. A search by file name in `~/Downloads`, `~/Documents` and any folder the user names; found files are copied, the rest stay listed. The build then shows the real count of `IMAGE_MISSING`.
8. **Projects list.** Remove `My project` (`/home/t00m/Documents/devel/tests/kb4it/config/repo.json`, the file no longer exists) from `~/.kb4it/projects.json`, after a backup.

## WP3 techdoc small fixes

1. **Date in the header strip (user, 2026-10-24).** Show the date on one line and the time below it, without seconds: `YYYY-MM-DD`, then `HH:MM`. A date without a time shows only `YYYY-MM-DD`. The full value stays in the `title` attribute and in the Details tab.
2. **Tables between 960 and 1199 px.** At 1024px a wide table (sapbasis `Category_Record.html`) still scrolls sideways by about 190px. Below 1200px: badges shrink from 6.5rem to 5rem and the title floor drops from 12rem to 8rem. The date column keeps `YYYY-MM-DD` with `HH:MM` below it, as in the header strip. If the table still scrolls at 1024px on `Category_Record.html`, the Scope and Topic columns are hidden below 1200px (they stay in the search filters and on the document page). My call; check it on the real page.
3. **Fold subsections.** Today top-level sections start folded except the first, and subsections start open. Subsections also start folded, except those under the first section. Links to a section still unfold it and its parents; print still shows everything. My call.
4. **Footer filter script.** `HTML_FOOTER.tpl` has an old `text_filter` script that throws `Cannot read properties of null` on pages without the filter box. It returns early when the box is missing.
5. **`#details` next to a heading with the same id.** When the body has a heading with the id `details` or `history`, the browser first jumps to that heading. `page.js` then scrolls to the card. A Playwright check confirms that the card ends up in view; only if it does not does the script change.

## WP4 to WP6, WP8: quality phases 2 to 6

As specified in the quality spec, sections "Part B", "Part C", "Part D" (D2 Quality and Related tabs, D4, D5), "Part E" (E2 to E4) and "Phases". Two updates from phase 1:

- The info card, `page.js` and the print rules exist. Phase 2 adds the Quality tab and the emblem to them; the emblem opens the card on Quality through the same `show()` path as `#details`.
- Missing images are already found (`enhance_images` returns them). Phase 2 uses that list for the 3-point Connected penalty; phase 4 lists them on the Quality page.

## WP7 Header cache

From the analysis of 2026-10-23 (`responses/20261023_154000_SORT-FIX-PROFILER-HELP-HEADER-CACHE.md`): every build reads each document twice and parses its YAML header, changed or not. On 1000 documents that is about 390 ms of a 960 ms build with no changes.

**Change.** Read each file once and hash its bytes. When the hash equals the `file_hash` stored for the document in `kbdict.json`, reuse the stored keys, body hash and metadata hash, and skip the YAML parse. Otherwise parse and store the new hash.

**Invalidation.** A new KB4IT version and `--force` already start empty. The kbdict also stores the PyYAML version; a different one drops the cache. Invalid documents are never cached, so they are reported at every build. A document that logged a warning while parsed (`title_in_frontmatter_ignored`) is not served from the cache, so the warning stays.

**Not changed.** The database, the `Date` conversion and the metadata index run for every document. `kb4it verify` and the editor checks parse directly.

**Test.** A second build without changes parses no header (counted through a debug log line or a test hook); editing one document parses only that one; a document with a frontmatter `Title` warns at every build.

## Non-goals

- Rewriting links automatically at build time (WP1 item 3 reports them).
- Changing the comma split rule for all keys (WP1 item 1 joins Summary back).
- Checking links to non-document files (images, PDFs) in WP1; `enhance_images` covers images.
- AI-written Summaries applied without review (WP2 item 6).
- New tests in `tests/browser`.

## Calls made without the user, to check

Decided by the user on 2026-10-24: WP1.2 keeps `--force` (no theme fingerprint); WP3.1 shows `YYYY-MM-DD` with `HH:MM` below it.


- WP1.3: extensionless links are reported, not rewritten.
- WP2.4: dates keep their three valid formats.
- WP2.5 and WP2.6: Drafts and Summaries change only from lists the user edits.
- WP3.2: Scope and Topic columns may be hidden below 1200px.
- WP3.3: subsections start folded.

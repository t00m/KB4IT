# Changelog

All notable changes to KB4IT are documented here.

---

## [0.7.38] – Unreleased

### Theme: Techdoc — Document view

- **Collapsible TOC**: a `<details>` panel appears at the top of every document; open by default, collapses on click. Renders correctly in print (forced open, no max-height).
- **Redesigned headings**: `h2`/`h3`/`h4` now carry a coloured left-accent bar (blue gradient by depth) instead of the generic UIKit card title style.
- **Collapsible sections**: clicking any `h2` heading toggles the section body open/closed. The indicator arrow (`▾`/`▸`) is rendered via CSS `::after` to avoid HTML-entity display bugs in `textContent`.
- **Document Properties section**: document metadata moved from a hidden top block to a collapsible `kb-sect1` section at the end of the document. Collapsed by default on screen; forced open and link-free in print. Keys are bold; values are comma-separated inline links.
- **Print CSS overhaul**:
  - Page margins reduced from `1.5cm 2cm` to `1cm 1.5cm`.
  - Line height reduced from `1.6` to `1.35`; paragraph spacing from `6pt` to `4pt`.
  - Document title block shown in print (hidden on screen).
  - TOC included in print output.
  - Metadata values displayed as a bullet list (sans-serif, black, no URL suffixes).
  - Section card padding zeroed; `uk-card-body` padding suppressed.
  - All collapsed section bodies forced visible in print.
- **Print button**: added to the document actions bar.
- **Add document page**: new page with per-category AsciiDoc skeletons loaded from `.adoc` files; copy-to-clipboard button restored and modernised.
- **Add document — metadata form**: clicking *Create* now opens a two-step modal. Step 1 is a form with one field per AsciiDoc attribute in the skeleton; step 2 shows the filled skeleton ready to copy. `Date` auto-fills to today; `Category` is read-only; all other fields support free-text entry.
- **Add document — multi-select tag chips**: keys with known values in the live metadata database render as clickable chip selectors (multiple values selectable). Keys with more than 8 known values open a popup picker with a live filter, custom-value entry, and a *Clear all* button, avoiding cluttered chip clouds in the form.
- **Copy-to-clipboard**: migrated to `navigator.clipboard` API with `execCommand` fallback.

### Theme: Techdoc — Landing page

- **Hero stats bar**: document counts per Diataxis category link to their respective listing pages. Diataxis count corrected; avoids 404 when a category has no documents.
- **Changes/Incidents alert bar**: two-column panel showing recent changes and open incidents.
- **Upcoming events**: panel now shows only future events; month headers and alert bar headers are clickable links.
- **Color-coded category labels**: event tables show labels with uniform fixed width and per-category colour.
- **Landing page layout reorganised**.

### Theme: Techdoc — Events

- Events page replaced year-card layout with a year-selector, 12-month calendar grid, and a DataTable.
- Unchanged event pages are skipped during recompilation.

### Theme: Techdoc — Other pages

- Key-value, key, and stats pages redesigned with modern CSS (word cloud, bar charts, breadcrumbs).
- Help page is auto-generated when the repository has no `help.adoc`.

### Theme: Blog

- "Read more…" link appended after each post excerpt on the index page.
- New index page renders posts by excerpt instead of full content.
- Visual and style improvements to datatables and post layout.

### Core — Performance

- **Incremental deployment**: deployer now copies only new or changed files and deletes stale ones, skipping unchanged assets.
- **Incremental compilation**: split body/metadata hashes ensure key pages are recompiled whenever any document's metadata changes.
- **BLAKE2b hashing**: replaced MD5 with BLAKE2b for content and file hashing.
- **Compiler**: removed random sleep from `compilation_finished` callback.

### Core — Features

- `Date` is now the hardcoded sort key for all themes; the configurable `sort` property is removed.
- `About KB4IT` source page is auto-created in the repository if missing.
- Mako templating library updated from 1.3.6 to 1.3.11.
- `Date` key is blocked from appearing in the stats page and word cloud.
- Keys listed in `ignored_keys` are excluded from stats and word cloud.

### Core — Bug fixes

- **Template cache race condition**: `builder.template()` previously cached `Template("")` between fallback attempts, causing concurrent compiler workers to read a half-built entry and render empty content. Downstream `content.replace("", …)` then exhausted memory. The cache is now locked and only populated on success.
- `kb4it themes` command restored after a regression caused by repo-dict loading during theme listing.
- `ignored_keys` now loaded correctly from repo config.
- Backend and deployer fail early with a clear error when runtime theme data is missing.
- `reason` variable in `get_asciidoctor_attributes` initialised to prevent `UnboundLocalError`.
- Removed stale references to the `Updated` document property.
- Theme pages are registered as build targets even when not recompiled in the current run.
- Invalid (non-AsciiDoc) documents are excluded from the compilation pipeline.
- Successful compilations no longer emit a spurious error-level debug message.

### Refactoring / Chores

- Dead code removed and missing docstrings added across core and service modules.
- Debug log format unified across all modules for diff-friendly output.
- Core modules (`env`, `log`, `service`, `util`) and service modules (`backend`, `builder`, `compiler`, `deployer`, `frontend`, `processor`) reformatted and cleaned up.
- README revised for clarity and updated information.

---

## [0.7.26] and earlier

See git history.

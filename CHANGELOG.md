# Changelog

All notable changes to KB4IT are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Fixed

- A source document with unreadable frontmatter (for example an unquoted value containing `: `) no longer vanishes silently. It is recorded in `BuildPlan.invalid_docs` and counted as `invalid=N` in the build summary, and the log gives the YAML line, column and problem.
- apphelp: with `strict` on, an invalid document fails the build as `DOC_INVALID`, together with the other metadata problems.
- `kb4it verify` exits 1 when it finds a non-conformant file or a theme problem, so it can gate CI.
- `kb4it create` makes the `source/` and `target/` folders when the theme's sample app has none. Git cannot store empty folders, so `kb4it create bookshelf` from a git checkout or a PyPI install produced a repository that did not build.

### Added

- `repo.json` switch `fail_on_invalid` (default `false`) makes any theme fail the build on invalid documents.
- apphelp: theme documentation in `kb4it/resources/themes/apphelp/README.md`.
- The `kb4it` requirement in a theme's `theme.json` (for example `">=0.7.9"`, or `">=0.7.9, <0.8"`) is enforced: a theme that needs a newer KB4IT is refused with `THEME_REQUIREMENT_UNMET`, and an unreadable requirement with `THEME_REQUIREMENT_INVALID`. A theme without one loads with a warning.
- `kb4it --version` run from a git checkout adds `git describe`, so a development build is identifiable without changing any file.
- Release process (`RELEASING.md`): `scripts/release.sh` prepares a release (version, dated changelog, release notes) and commits it only after the tests, the theme check and the wheel check pass. It never tags or pushes.
- `scripts/devel/check_themes.sh` checks every tracked theme before a release: complete `theme.json`, a `kb4it` requirement met by the release, required templates, and sample apps that build with no error or warning. CI runs it too.
- The publish workflow runs on plain `vX.Y.Z` tags only. It checks that the tag matches the committed version, the changelog and the release notes, runs the tests and the theme check, publishes to PyPI with trusted publishing and creates the GitHub release.

### Changed

- apphelp: every page is classified by type of document with `DocType`, the same key and values as `techdoc`: `Tutorial`, `How-to guide`, `Reference` or `Explanation`. A page without a valid `DocType` is left out of the site, the navigation, the search and the help ids, and fails the build when `strict` is on. The landing page groups pages by type of document, and search filters by it.
- apphelp: the `Kind` key is replaced. Use `DocType` for the type of document and the optional `Layout` key (`faq`, `tips`, `troubleshooting`) for the special renderings. A page that still has `Kind` is reported as `META_INVALID`.
- apphelp: the labels `kind_*` and `facet_Kind` are now `doctype_*` and `facet_DocType`.

### Removed

- `setup.py`, unused since the build moved to `pyproject.toml`.
- `scripts/devel/genbuild.py` and the `+build.N` counter it wrote into `kb4it/VERSION` and `pyproject.toml` on every local install. PyPI rejects such versions, and the changing version forced every site to recompile after each install.
- The legacy upload scripts in `scripts/distribution/pip/` and `scripts/distribution/deb/create_deb.sh`, which used `setup.py`.

---

## [0.7.9] - 2026-10-01

### Added

- New theme `apphelp`: help sites for applications, with strict metadata, offline search, help ids and `go.html`.
- `theme.json` `metadata_pages` turns the metadata pages off.
- `theme.json` `deploy_dirs` deploys only the listed theme folders.
- `repo.json` `publish_sources` controls copying the sources to the target.
- Optional `logic/verify.py` theme hook, run by `kb4it verify`.
- `Builder.site_signature()` rebuilds every page when the site shape changes.
- Tests run with `./scripts/devel/test.sh`; CI runs them and checks the wheel for every tracked theme.

### Changed

- Markdown links to `.md` files are rewritten to `.html`, keeping the fragment; unknown targets log `LINK_BROKEN`.
- `source` and `target` are relative to the repository root (`PATH_CWD_RELATIVE` fallback); `kb4it create` writes them that way.
- The backend no longer writes into `source/`; `Builder.create_page_about_app()` builds the about page.
- `Date` is optional; undated documents come after dated ones and show an empty date cell.
- YAML null frontmatter values become `[]`.
- Custom themes: the about pages are no longer added for every theme. A custom theme must call `create_page_about_kb4it()` and `create_page_about_app()` in its `build()` to get them. An untouched generated `source/about_kb4it.md` from older versions is removed.

---

## [0.7.38]

### Theme: Techdoc: Document view

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
- **Add document: metadata form**: clicking *Create* now opens a two-step modal. Step 1 is a form with one field per AsciiDoc attribute in the skeleton; step 2 shows the filled skeleton ready to copy. `Date` auto-fills to today; `Category` is read-only; all other fields support free-text entry.
- **Add document: multi-select tag chips**: keys with known values in the live metadata database render as clickable chip selectors (multiple values selectable). Keys with more than 8 known values open a popup picker with a live filter, custom-value entry, and a *Clear all* button, avoiding cluttered chip clouds in the form.
- **Copy-to-clipboard**: migrated to `navigator.clipboard` API with `execCommand` fallback.

### Theme: Techdoc: Landing page

- **Hero stats bar**: document counts per Diataxis category link to their respective listing pages. Diataxis count corrected; avoids 404 when a category has no documents.
- **Changes/Incidents alert bar**: two-column panel showing recent changes and open incidents.
- **Upcoming events**: panel now shows only future events; month headers and alert bar headers are clickable links.
- **Color-coded category labels**: event tables show labels with uniform fixed width and per-category colour.
- **Landing page layout reorganised**.

### Theme: Techdoc: Events

- Events page replaced year-card layout with a year-selector, 12-month calendar grid, and a DataTable.
- Unchanged event pages are skipped during recompilation.

### Theme: Techdoc: Other pages

- Key-value, key, and stats pages redesigned with modern CSS (word cloud, bar charts, breadcrumbs).
- Help page is auto-generated when the repository has no `help.adoc`.

### Theme: Blog

- "Read more…" link appended after each post excerpt on the index page.
- New index page renders posts by excerpt instead of full content.
- Visual and style improvements to datatables and post layout.

### Core: Performance

- **Incremental deployment**: deployer now copies only new or changed files and deletes stale ones, skipping unchanged assets.
- **Incremental compilation**: split body/metadata hashes ensure key pages are recompiled whenever any document's metadata changes.
- **BLAKE2b hashing**: replaced MD5 with BLAKE2b for content and file hashing.
- **Compiler**: removed random sleep from `compilation_finished` callback.

### Core: Features

- `Date` is now the hardcoded sort key for all themes; the configurable `sort` property is removed.
- `About KB4IT` source page is auto-created in the repository if missing.
- Mako templating library updated from 1.3.6 to 1.3.11.
- `Date` key is blocked from appearing in the stats page and word cloud.
- Keys listed in `ignored_keys` are excluded from stats and word cloud.

### Core: Bug fixes

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

---

## [0.7] - 2019-11-15

### Added

- Asciidoctor 2.0.
- Layout based on UIkit.
- Smart compiling.

## [0.6] - 2019-09-10

- Released.

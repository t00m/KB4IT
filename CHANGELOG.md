# Changelog

All notable changes to KB4IT are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added

- techdoc: **Edit in the editor**, in the title menu and the History tab of every document page, opens the Add page editor on the document's Markdown, with the toolbar, checks and properties pane. **Save** suggests the document's own file name, to save it over the file in `source/`. The text travels in the address of `add.html#edit=...`, so it works offline from `file://` and from a web server; the address is cleared once the dialog opens. It shows when the editor is on; the git **Edit** button stays when `"git": true`. Every Add page has the new Edit dialog (`EDITOR_DIALOGS.tpl`, `KB4ITEditor.edit()`).
- techdoc Gallery: a new Gallery entry in the logo menu opens `gallery.html`. The page loads no image until you choose what to see: the filter panel on the right has one button per document property (and Year), each opening a dialog to pick its values, with the number of images each value adds and a search box for long lists; a text box matches words of the document title or the image caption. The chosen values show as chips you can remove, and they are kept in the address (`gallery.html#Product=SAP`), so a view can be linked. The images appear as thumbnails in a masonry grid; a click enlarges the original in a lightbox whose previous and next follow the filters. The build makes the thumbnails (WebP, 480 pixels wide) with Pillow into `var/thumbs/`, makes each one again only when its image changes, and copies the ones in use to `resources/kb4it-thumbs/` of the site. Vector, small and unreadable images are shown as they are. `gallery.md` is a reserved page name.
- Pillow is a new dependency of KB4IT, for the gallery thumbnails.
- techdoc tables: every table of a document gets the UIkit table style (padded cells, row dividers, stripes, hover). A table with more than 15 rows and a plain grid (one header row, no merged cells) also gets a "Filter rows" search box, a row count and sortable columns, through the DataTables library the theme already loads; columns of numbers with a unit, such as `10 GB`, sort by the number. Print shows every row and no search box. `"table_filter": false` in `theme.json` turns the search and sort off. The theme's document lists (all documents, bookmarks, property pages) keep their own table setup. The techdoc theme is now version 1.2.0.
- Nested lists may be indented by two or three spaces, as most editors and GitHub write them, not only by four. Python-Markdown nested such items into their parent's list as siblings; KB4IT now moves a list that nests by two or three spaces to four spaces per level before the conversion, with the text, code and notes under each item. Lists nested by four spaces render as before.
- Task lists out of the box: `pymdown-extensions` is now a dependency of KB4IT (the `extras` keep nh3 only), every sample app turns on `pymdownx.tasklist`, so `kb4it create` makes a repository where `- [ ]` and `- [x]` show as checkboxes, and techdoc, blog, bookshelf and apphelp show the checkbox in place of the bullet. An older repository adds `"markdown": {"extensions": ["pymdownx.tasklist"]}` to its `repo.json`.
- Every theme writes structured data (schema.org JSON-LD) into each page head: a document becomes an article whose type follows its `DocType` (`How-to guide` is a `HowTo`), with title, `Summary`, `Date`, `Author` and the mapped properties (`Tag`, `Topic`, `Category`, `Scope`, `Product`, `Protocol`, `Project`, `Status`...), and the home page describes the website and its search page. Each theme adds its own vocabulary: blog posts are `BlogPosting`, bookshelf notes are a `Chapter` of their `Book`, apphelp maps `Feature`, `Level`, `Platform` and `Since`. Absolute addresses need `site_url`.
- Author profiles, core part: a document with a `Person` property describes one person that documents name in `Author` (`Alias` for other spellings; `Team`, `Role`, `Email` and any other property for the rest). A profile gets no page of its own and stays out of lists, search, the feed and the sitemap; a link to its file leads to the person's page (`Author_Jane_Doe.html`). The `repo.json` `people` block sets which properties name people (`keys`), which profile properties are contact details (`contact_keys`) and which stay off the pages (`private`). A profile with two names, or claiming a name another profile has, is left out (`PROFILE_INVALID`, `PROFILE_DUPLICATE`, `PROFILE_ALIAS_IS_PERSON`). `kb4it verify` also lists profiles without contact details, unused profiles and authors without a profile. The person pages showing the profile come next.
- `repo.json` `seo` block: `lang` sets the language of the pages (`<html lang>` and the structured data) in every theme, `structured_data: false` leaves the JSON-LD out and `map` changes which properties are written. A malformed block stops the build; changing it rebuilds every page.
- Search engine control, per site: `seo.index: false` adds `<meta name="robots" content="noindex, nofollow">` to every page, writes a `robots.txt` that disallows everything (also without `site_url`) and no `sitemap.xml`; `seo.index: true` keeps today's behaviour. While `seo.index` is not set the site stays indexable, and each build logs `[SEO] INDEX_UNSET` and `kb4it verify` shows a notice. `seo.noindex_keys` (default `true`) gives the pages that only list documents (property, value, properties, event, stats, bookmarks, all-documents) `noindex, follow` and leaves them out of the sitemap. `404.html`, the Add page and the techdoc admin page are always `noindex`. A robots tag written by a template wins, and a `robots.txt` KB4IT did not write is never replaced (`ROBOTS_KEPT`).
- `kb4it create --index yes|no` writes `seo.index` into the new `repo.json`; the terminal interface asks the same question ("Allow search engines") and creates nothing until it is answered.
- `dateModified`: each document page gets the date it last changed, in the JSON-LD (`dateModified`), as `article:modified_time` and as the `<lastmod>` of `sitemap.xml`, which now agree. It is the new `Modified` property, else the date of the last git commit of the file (one `git log` per build, kept in `var/db/gitdates.json`), else the file time, and never older than `Date`. A page is rebuilt when this date changes. `Modified` gets no property page, like `Date`; `kb4it verify` reports a value it cannot read (`bad_modified_date`).
- Open Graph article tags on document pages: `article:published_time`, `article:modified_time`, `article:author`, `article:section` (first `Category`) and `article:tag`; and `og:locale` on every page when `seo.lang` has a region (`es-ES` gives `es_ES`).

### Changed

- Stats page, in techdoc, blog and bookshelf: it shows the totals (documents, properties, values, share of dated documents, bookmarks, links between documents), the documents per year and in the last 12 months, the coverage of each property (documents that set it and its three most used values), metadata health (values of a property that differ only by case or spacing, properties used by one document, documents with two properties or fewer) and links (most linked documents, documents no other links to). Each section is a card with a one-line summary; its Details button opens the full section in a modal (a UIkit modal in techdoc and blog, a native dialog in bookshelf), so the page fits on one screen. `Summary` is left out (`stats_skip_keys`). Templates get `var['stats']`; `var['count_docs']`, `var['count_keys']` and `var['leader_items']` are gone, so an override of `PAGE_STATS.tpl` must be updated.
- techdoc: the Properties page lists every property on one line, with a dotted leader to its number of values and of documents, instead of a word cloud of buttons. Each line links to the property's page. Property pages (such as `Author.html`) drop their Leader tab and keep Cloud and Table. Shared theme code has a new class attribute, `properties_cloud` (default `True`), that techdoc turns off.
- About KB4IT, in every theme: the page shows the KB4IT README (from the source checkout, or from the installed package), without the badges, which load from the network, and with relative links pointing to the repository.
- techdoc and bookshelf: Help opens the KB4IT help site (https://t00m.github.io/KB4IT/) in a new window. The old built-in `help.html` page, a short and outdated guide, is no longer built.
- techdoc dashboard: Open items and Activity are two tabs of one card, "Open items and activity". Activity keeps its tabs for changes, incidents, events and monitoring, and each tab bar opens on the tab chosen last.

### Fixed

- The About KB4IT page shows the README's diagram and formulas as their source. Live, they made every site deploy Mermaid and KaTeX (`resources/render/`), even a site with no diagram or formula of its own. A four-backtick example in the README that holds a three-backtick fence now stays one code block.
- Stats page: blog and bookshelf kept the cached page when only documents changed; it is now rebuilt when a document or a property changes. System pages are never counted as documents.
- techdoc dashboard: the first two panels showed the titles "Summary" and "Document types", meant only for screen readers. The build gave their headings its own class, which dropped the class that hides them.
- techdoc: a document page opened without a `#` in the address made Firefox warn "Empty string passed to getElementById()".

---

## [0.10.0] - 2026-10-26

### Added

- BI: every KB4IT build names the commit it came from. `kb4it --version` prints the build version (`X.Y.Z` for a release, `X.Y.Z-dev+<n>.g<sha7>` for any other commit, `.dirty` with uncommitted changes) and, on a second line, the commit and build date. Packages carry it in `kb4it/BUILD.json`, written by the new `scripts/devel/stamp_build.py` from `build_python.sh`, CI and the publish workflow, which refuses a release build that is not the clean commit of its tag. The log, `kb4it info`, the `[WORKFLOW] SUMMARY` line (`kb4it=`), the TUI title, the About page and the `generator` meta tag show it too.
- SI: `kb4it doctor` prints the build version and commit, Python, the folders KB4IT runs from, the offline help and every theme with its version, fingerprint and folder (flagging a user copy that hides a bundled theme), and exits 1 with `PROBLEM` lines when a bundled file or theme is missing.
- SI: the source installer has a `venv` method that needs only Python 3.11 or newer (`~/.local/share/kb4it/venv`, linked from `~/.local/bin/kb4it`), plus `--method`, `--python`, `--allow-dirty`, `--extras` and `--wheel`. `uninstall.sh` removes that venv too.
- TV: themes have their own `version` in `theme.json` (the four bundled themes start at `1.0.0`) and a fingerprint of their files, shown as `techdoc 1.0.0+3f9a1c0b7e21` by `kb4it themes` (with scope and folder, so a user copy that hides a bundled theme is visible), the TUI Themes screen, the summary line (`theme=`) and the `generator` meta tag. A theme without `version` logs `THEME_VERSION_MISSING`; one that is not `X.Y.Z` stops with `THEME_VERSION_INVALID`. `check_themes.sh` requires the key and fails a release when a theme changed since the previous release tag without a new version.
- techdoc quality phase 6: an optional sticky table of contents in a right column (`"toc_sidebar": true` in `theme.json`, off by default; documents with four or more sections, screens 1400 pixels or wider, current section highlighted) and the quality tier in the search dialog and page, where the score breaks a tie between matches of the same relevance.
- techdoc content blocks: a copy button and a language label on code blocks, long blocks folded to 20 lines with a "Show all N lines" button, wide tables scrolling and tables over 15 rows keeping their header, a back-to-top button after one screen of scrolling, `pymdownx.tabbed` author tabs and `pymdownx.details` notes styled like the rest of the theme, all with print rules. The help page "Make code, tables and notes easier to read" shows how to write the tabs and the notes.
- techdoc Quality guide: every item of the Quality tab has a tooltip on what to do and links to `quality-guide.html`, a system page that explains each check, shows the Markdown to write and lists every skeleton.

- techdoc quality score: every document gets a score from 0 to 100 in five dimensions (Findable, Structured, Complete, Connected, Current) and a tier (Exemplary, Complete, Basic, Stub, or Retired with no score). Records are scored on a lighter scale and compared with records of the same WorkType. A ring in the header strip opens the new Quality tab of the info card, with bars, the median of similar documents and the next steps with the points they add. Exemplary documents get a gold line and a note. `quality-index.js` holds ranks and medians; `"quality": false` in `repo.json` turns it all off; the `quality` block of `theme.json` holds the thresholds.
- techdoc document pages: a header strip with the DocType, Status and Priority badges and the Date, WorkType, Topic and Product links; the `Summary` as an opening line; banners for production documents, retired documents (`Obsolete`, `Deprecated`, `Withdrawn`, `Rejected`) and drafts; and an info card with a Details tab (properties in groups, technical objects as chips, SAP notes from the text) and a History tab. The card starts closed when the document has a Summary and open on Details when it does not, and remembers the last tab. The document properties button opens Details; the old properties dialog is gone. Print keeps the strip, the banners and Details. `theme.json` sets the keys with `header_keys`, `info_groups` and `info_tabs`.
- techdoc document images: width and height from the file, lazy loading, figures with a numbered caption from a descriptive alt text, a frame, click to zoom with previous and next, galleries for three or more images in a row, and a placeholder for missing files with the warning `[THEME] IMAGE_MISSING`.
- techdoc: the `WorkType` property holds the type of work a record documents (`Change`, `Incident`, `Task`, `Meeting`); `Category` keeps the form of the document, with the new values `Record` and `Minutes`. The dashboard (latest changes and incidents, open items, event badges) and the events page read `WorkType`. A document without `WorkType` whose `Category` is `Change`, `Incident`, `Task` or `Meeting` is still read as that type of work, so older repositories keep working. The record skeletons and the sample apps use the new keys. `scripts/conv/split_category.py` moves an older repository to the new keys and writes a CSV of its changes.
- `python -m kb4it` runs the same as the `kb4it` command. The developer help (Run and test from source) shows how to profile a build with cProfile and py-spy.
- `kb4it build --trace` and `kb4it serve --trace` time each build stage, each processor and deploy step and each document compile. The build prints a table and writes `var/log/trace.json` (Chrome Trace Event format; open it in https://ui.perfetto.dev). Timings no longer go to the log: the `[PERFORMANCE]` debug lines are gone. Logged as `[WORKFLOW] TRACE path=...`.
- ET-05: skeleton sets for the Add page. The first of `overrides/templates/skeletons/`, the theme's `templates/skeletons/` and the common set (one generic `DOCUMENT` skeleton) that holds a `*-SKELETON.md` is used; sets are never merged. An optional `skeletons.json` sets id, name, description, color, icon and the card order; errors name the file and unlisted files are logged as `[BUILDER] SKELETON_UNLISTED`.
- ET-11, ET-12: tests for the setting, skeleton sets, the page in each theme and a browser subset on all four themes; the help pages and the offline help describe the editor setting, the skeleton sets and how a custom theme adds the page.
- ET-10: the apphelp theme builds the Add page when `"editor": true` is set in `repo.json` (off by default). The sidebar links to it with the new label `add` ("Add a page"), and the page ships Tutorial, How-to guide, Reference and Explanation skeletons. Completion also offers the `vocabulary` values, the `DocType` names and the `Layout` names that no document uses yet.
- ET-08, ET-09: the blog and bookshelf themes build the Add page when `"editor": true` is set in `repo.json` (off by default). blog shows an "Add document" link in the footer and ships `POST-SKELETON.md`; bookshelf shows a plus button in the top bar and ships `CHAPTER-SKELETON.md`. Every bundled `theme.json` now requires KB4IT `>=0.10.0`.
- ET-06, ET-07: the Add page is built in core (`AddPageMixin.create_page_add()`, `editor_keys()`) from the common templates `PAGE_ADD.tpl` and `EDITOR_DIALOGS.tpl`. A theme gets the page by setting `add_page = True` on its `Theme` class and calling `self.create_page_add()` in `build()`; techdoc keeps its UIkit cards and its `techdoc_addpage.py` is gone. `ADD_PAGE` is now logged by `create_page_add()` as `[BUILDER] ADD_PAGE enabled=<bool> skeletons=<source> categories=<n>`.
- ET-04: the `editor` key in `repo.json` (`true` or `false`) turns the Add page on or off; the default comes from `theme.json` (techdoc on, other themes off). A value that is not a boolean stops the build and shows in `kb4it verify`; the same holds for `"editor"` in `theme.json`. `add.html` is left out of `sitemap.xml`. Two skeleton files that give the same id (`Foo-SKELETON.md` and `FOO-SKELETON.md`) stop the build. The apphelp page title is the `add` label. With the editor off, `add.html` and the link to it are removed. Logged as `[BUILDER] ADD_PAGE enabled=<bool>`.
- techdoc Add page editor (ED-01 to ED-12): the Add page now edits new documents in a Markdown editor that works offline, also from `file://`. The items below describe its parts.
- ED-01: a CodeMirror 6 bundle (`kb4it/resources/editor/codemirror.min.js`, global `KB4ITEditor.cm`) for the techdoc Add page editor. It is built with `scripts/devel/editor/build.sh`, committed, works offline from `file://` and stays under 700 KB. `check_wheel_themes.py` also checks that the wheel ships it.
- ED-02: the editor files (`resources/editor/`) are deployed only to sites with a page that loads them, and removed from the site when no page does. Logged as `[DEPLOYER] EDITOR_ASSETS deployed=<bool>`.
- ED-03: CodeMirror licence and `THIRD-PARTY-NOTICES.txt` ship with the package; `THANKS` credits CodeMirror.
- ED-05, ED-06: the Add page editor completes property names and values of the repository inside the frontmatter (values most used first, quoted when YAML needs it; new names and values can always be typed) and shows diagnostics in a lint gutter with the build's reason names: missing or unclosed frontmatter, YAML errors, missing H1, `Title` in the frontmatter, bad property names and values, new properties and values. Tab indents the selected lines and Shift-Tab outdents them. Completion into a flow list `[a, ]` now quotes values with `?`, `:`, `#`, `,`, brackets or braces.
- ED-07: the right pane of the Add page is now Properties, a form for the frontmatter: one row per property with removable value chips, an input that suggests the repository's values (most used first, with counts), a property selector plus "New property..." for a free name, and a word cloud per property whose words add a value on click. Every form action is one editor change, so undo works. Values cannot contain a comma (KB4IT splits on commas). Properties written as lists or blocks are shown read-only.
- ED-08: the Properties pane follows the text. 300 ms after the last edit the frontmatter is parsed again and the form is redrawn, keeping the focus and the text typed in a value input. While the frontmatter has an error (missing or unclosed `---`, YAML error, not a mapping) the pane shows the reason and its inputs and buttons are disabled.
- ED-09: a toolbar above the Add page editor inserts Markdown and KB4IT elements: bold, italic, inline code, link, headings H2 to H4, bullet, numbered and task lists, quote, code block, horizontal rule, table, image, admonitions (note, tip, warning, danger), Mermaid diagram, inline formula and formula block. A button wraps the selection or inserts a template and selects the text to write next; one action is one undo step. `Ctrl+B`, `Ctrl+I`, `Ctrl+E` and `Ctrl+K` work as shortcuts (`Ctrl+I` replaces CodeMirror's select parent syntax). While the cursor is in the frontmatter the buttons are disabled and the shortcuts do nothing. Several cursors can be used (`Ctrl+click`).
- ED-10: the Add page has a Save button. In Chromium browsers it opens the system save dialog (suggested name from the title, the folder used last time) and later saves write the same file without asking, the button showing `Save (<name>)`; elsewhere, or when the dialog is cancelled and a download is accepted, the file is downloaded. The file is UTF-8 with LF line endings and one final newline. Documents with errors ask for confirmation first; closing the modal or leaving the page with unsaved edits asks too. Copy writes the same text. The page note now says the page saves or downloads the file and that it goes in the `source` folder before a rebuild.
- ED-11: help pages for the editor: the new how-to "Write a document in the editor" and an editor section in the techdoc reference, with the list of checks and the browser support for saving. `AGENTS.md` describes `kb4it/resources/editor/`, `scripts/devel/editor/build.sh`, `deploy_editor_assets()` and the browser test command.
- ED-12: tests for the editor: asset and deploy tests in Python, the frontmatter logic run with `node` (skipped when node is missing) and browser tests with Playwright and Chromium (skipped when Playwright is missing; required in the CI browser job).

- techdoc skeletons meet the quality standard: every core key plus `Summary` and `Product`, a first section that gives context, the shape of their type (steps and a command for a procedure, a table for a report, three sections for notes and posts) and a References section. A filled-in skeleton scores Exemplary. A References section in a skeleton is scored only under Connected, not again as a skeleton section.

- techdoc document tables leave out a column that is empty in every row, such as WorkType on a page that lists only procedures. Date and Title always stay.

- techdoc quality everywhere: a Quality column for document tables (`"Quality"` in `datatable`, sorted by score), the Exemplary count, a tier mix on each DocType card and a Best documents shelf on the dashboard, a Quality page (`quality.html`) with quick wins, broken links, missing images, documents without a Summary and possible duplicates, and a Related tab in the info card with Linked from and related documents. A theme can draw a table column itself with the new `datatable_custom_cell()` hook.

### Fixed

- Windows: the path of a local image in a techdoc document mixed `\` and `/` (`resources/images/...` was kept as written); it is now a normal Windows path, as the missing-image check and the image size reader expect.
- Windows: a skeleton saved with CRLF line ends put `\r` characters into the Add page editor. Skeletons are now read with LF line ends.
- macOS: `install_kb4it_from_source.sh` reported "kb4it on PATH is the new installation" for any other `kb4it` when no Python 3.11 or newer was on `PATH` (the default on macOS), because both paths resolved to nothing. It now compares the paths as given in that case and exits 2 as intended.
- `install_kb4it_from_source.sh` installed the working tree directly, so the package had no offline help, and it reported success for whatever `kb4it` came first on `PATH`. It now builds the wheel with `build_python.sh` (offline help and build stamp included), checks it with `check_wheel_themes.py`, installs the wheel file, refuses uncommitted changes unless `--allow-dirty`, never picks a Python older than 3.11, and checks that the installed command reports the wheel's build, passes `kb4it doctor` and is the first `kb4it` on `PATH` (exit 2 otherwise).
- Installing another commit of the same version reused every cached page, so changes such as the new logo menu entries did not show until `kb4it build --force`. `kbdict.json` now records the build (`kb4it_build`) and a different one rebuilds everything once (`KBDICT_BUILD_MISMATCH`).
- A change to a theme's templates, logic or assets, its template base or the common templates did not rebuild the cached pages. The theme fingerprint is now part of the core signature, so the next build rebuilds every page (`CORE_SIGNATURE_CHANGED`).
- techdoc: the logo menu links to the full search page (`search.html`), which was only reachable from the search icon before.
- The help pages of techdoc and blog lost every heading: Mako reads a line starting with `##` as a comment. The templates now escape it, and a test keeps every template free of such lines.

### Changed

- Sample apps: every theme now starts you with a set of samples. techdoc `default` has seven (a procedure, an incident, a change, meeting minutes, an open task, a note and a draft report) and the `sapbasis` app, empty until now, has five SAP Basis samples. blog has four posts and bookshelf five chapters in two books. The techdoc samples follow their skeletons and score Exemplary; the blog posts have an `## Excerpt` and a `## Body`, so the home page no longer shows "Excerpt missing"; the chapters carry `PartTitle`. Authors, hosts and system ids are made up.
- Theme READMEs and the theme reference pages describe the sample apps, the techdoc `Category` and `WorkType` split and the bookshelf chapter properties.
- `kb4it --version` prints two lines: `KB4IT <build version>`, then `commit <sha> built <date>` (or `from the source checkout`). Scripts that read the version should take the first line.
- `kb4it themes` names where each theme comes from as `scope=builtin`, `scope=user`, `scope=source` or `scope=theme_path` (before: `scope=global` and `scope=local`), and adds `version=`, `fingerprint=` and `path=`.
- The `version` key of a custom theme's `theme.json` is now read: it is the theme's own version, shown in `kb4it themes` and the build summary. A value that is not `X.Y.Z` logs `THEME_VERSION_INVALID` and the theme loads as `unversioned`; from 0.11.0 it will stop the build.
- Every site is rebuilt once on its first build with 0.10.0, and again whenever another build of KB4IT (another commit, other uncommitted changes) or a changed theme builds it.
- Release process (RA-01 to RA-13): `check_themes.py` warns in CI about a theme changed since the last release without a new version (CI now fetches tags) and fails on it with `--release` (`release.sh --commit`, `publish.yml`), which also fails without release tags; `--changed` lists the themes to raise, shown by `release.sh --dry-run`. `check_wheel_themes.py --stamp X.Y.Z` and `--release X.Y.Z` check the wheel's build stamp, in `release.sh --commit` and `publish.yml`. The image smoke test of a release wants exactly `KB4IT X.Y.Z`. The manual PyPI scripts refuse to run outside a git clone and check the stamp. `smoke_build.py --doctor --all-apps` checks an installation: `kb4it doctor`, then every sample app of every theme. `RELEASING.md` has a "Theme versions" section and a step 2c, and both release guides describe the build version.
- Faster builds without changes: each source document is read once, and when its bytes match the last
  successful build its YAML header, body hash and metadata hash come from `kbdict.json` instead of being
  parsed again. A document with a `Title` in the frontmatter still warns on every build, and a PyYAML
  upgrade rebuilds everything. On the 1,000-document test site an unchanged build went from 2.22 s to
  1.74 s (21%).
- techdoc dashboard: Changes and incidents, Upcoming events, Monitoring and Recent events become one Activity card with tabs; the card remembers the last tab. The Linked from list moves from the end of the document into the Related tab.
- HTML output of every bundled theme marks its blocks with comment pairs, `<!-- NAME :: START -->` and `<!-- NAME :: END -->` (PAGE METADATA, STYLESHEETS, TOP BAR or SIDEBAR, MAIN CONTENT, TABLE OF CONTENTS, DOCUMENT BODY, FOOTER, PAGE SCRIPTS and the blocks of each page), so a block is easy to find in the source. Old comments named after template files, unpaired comments and mismatched names are gone. Cleanup on the way: the viewport meta tag was declared twice (techdoc, blog); techdoc and blog lost a footer script for a filter box no page has, which threw an error on every page; techdoc lost a hidden duplicate title and a one-tab switcher around the document; techdoc and blog footers and the blog sidebar use `<footer>` and `<aside>`; the blog sidebar menu is a `<nav>`. The help page on creating a theme describes the rules.
- HTML output passes the W3C Nu HTML Checker with no error and no warning on every bundled theme. UIkit components are written as `data-uk-*` attributes (`uk-*` is not HTML; UIkit reads both). Script tags lost the unneeded `type="text/javascript"`. techdoc dashboard: the counts and the Diátaxis cards have headings for screen readers. blog: each post card is one `<article>` holding its header, and index titles are `<h2>` instead of `<h5>`. apphelp: the home tagline is no longer an untitled `<section>`. `scripts/devel/validate_html.py` now fails on `uk-*` attributes and on warnings. Custom templates that still use `uk-*` keep working.
- techdoc dashboard: the four document types (Diátaxis cards) now come right after the counts, before Open items. Open items, Changes and incidents (new title), Upcoming events, Monitoring and Recent events fold when you click their title; the browser remembers folded sections in `localStorage`. Every coloured label on the dashboard (priority, status, category) has the same width and size; a longer value ends in an ellipsis and shows whole in its tooltip. The Priority and Status labels in datatables (events, bookmarks, property pages) use the same width.
- techdoc document pages: every heading level folds when you click it (or press Enter on it). Only the table of contents and the first section start open; a link to a section unfolds it. The Document Properties section at the end is gone; the properties button in the title menu shows them. The table of contents at the top of a document uses the title menu style: top-level entries in bold, each lower level indented with a left rule.
- techdoc printing: tooltips and dropdowns no longer print (the "Print document" tooltip showed at the top of the page). Printed pages use the screen's sans-serif font instead of Georgia (Times on most Linux systems) at 11pt, with larger headings, tables, notes and table of contents, and a lighter table of contents box. Links no longer print their address after the text; in a PDF they stay clickable.
- techdoc document pages: section headings and subsections no longer have a vertical line on their left, on screen or in print. Subsections keep their indentation; note boxes and blockquotes keep their coloured bar.
- techdoc printing: every printed page has a small footer with the page title on the left and `page/pages` on the right (CSS page-margin boxes; Chrome and Edge).
- techdoc top bar: the document title takes the room between the left and right blocks and a long title ends in an ellipsis, with the full title as a tooltip; it no longer runs over the search box. The title is no longer cut to 70 characters with `...` in the middle, so the browser tab and the printed title show it whole. Search opens in a dialog from the search icon, `/` or `Ctrl+K`. Reload page, Help, About this app and About KB4IT moved into the logo menu. The document buttons (edit, properties, source, print) moved into the title menu, in one row above the table of contents; the menu is wider (up to 40rem), scrolls when it is long and indents each heading level.
- Every header value is text, kept as written; only an empty value, `null` or `~` means none. YAML used to change them: `Bookmark: Yes` became `True` (page `Bookmark_True.html`, now `Bookmark_Yes.html`), `0.10` became `0.1`, `010` became `8`, `12:30` became `750`. The Bookmarks page and the techdoc dashboard count `yes`, `true` and `on` in any case. The Add page editor reads values the same way: numbers and dates are editable in the Properties pane and are no longer quoted. A `Date` such as `2026-10-22T10:00:00Z` now sorts correctly. Existing sites rebuild the affected property pages once.
- Faster processing of the document headers with many documents. The list of documents of each property value was sorted again after each document was added, a cost that grew with the square of the documents (4.7 s for 10,000 documents sharing one value). It is now sorted once; `kbdict.json` is unchanged.
- Faster builds. The deploy copies only new or changed files (same size and modification time means unchanged; copies keep the time) instead of every page and every theme, common, render and editor file. On a 1000-document techdoc site a build without changes went from 1.76 s to 0.99 s and its deploy stage from 855 ms to 100 ms. The deploy also deletes what the repository or theme no longer has: files removed from the theme, `common`, `render` or `editor` folders, and files removed from `source/resources` or `overrides/static` (recorded in `kbdict.json` as `deployed_static`). Files the user put in the target are left alone. The sources are no longer copied into the cache, which only ever kept HTML pages.
- bookshelf no longer loads Google Fonts. Its pages use fonts installed on the reader's computer: Red Hat Display, Red Hat Text and IBM Plex Mono when present, then system font stacks. Sites built with it make no remote requests for fonts and work fully offline.
- ET-01 to ET-03: the Add page editor no longer uses UIkit. Each category opens in a native `<dialog>` (Escape and Close ask before losing edits, the page behind does not scroll), messages are shown by `KB4ITEditor.notify()` in a `#kb-toasts` container, toolbar icons are inline SVG, and buttons use `data-kb-open`, `data-kb-save`, `data-kb-copy` and `data-kb-close` handled by one delegated listener. The `kb-add-skeletons` data is now `{cat: {"name", "text"}}`. The editor styles moved from techdoc's `screen.css` to `kb4it-editor.css`, and the UIkit MIT notice is in `THIRD-PARTY-NOTICES.txt`.
- ED-03: techdoc requires KB4IT 0.10.0 or later.
- ED-04: the techdoc Add page edits documents in a CodeMirror editor instead of a plain text box: line numbers, Markdown and frontmatter highlighting, undo and redo, search (`Ctrl+F`), bracket closing, lists and quotes continued on Enter, Tab inserts four spaces (`Escape` then `Tab` leaves the editor). The colours follow the page background, light or dark. Opening a category again asks before discarding an edited document. Browser tests (Playwright and Chromium) run in a separate CI job and are skipped where Playwright is missing.

### Removed

- The APIs deprecated in 0.9: `KB4IT.get_service("Processor")`, `"Compiler"` and `"Deployer"` (use `backend.pipeline`), `kb4it.services.compiler.set_progress_callback` and `set_compile_start_callback` with their `clear_*` partners (pass `progress_callback` and `compile_start_callback` to `KB4IT(params)`), and the template value `var['repo']['updated']` (use `var['updated']`).

---

## [0.9.1] - 2026-10-21

### Added

- `kb4it help` opens the copy of the help that ships inside the package, with no network; `kb4it help --url` prints the online address. Until `kb4it help --dismiss`, every command prints a two-line notice with both addresses (never when `CI` is set), and the terminal interface shows it as a banner (press `d` to hide it).
- `kb4it create` prints three next steps, and the default apps of techdoc, blog and bookshelf come with sample documents to read and replace. The terminal interface shows the same next steps.
- Mermaid diagrams: a fenced block named `mermaid` is drawn in the browser, in all four themes. The files are bundled and deployed to `resources/render/` only when a page of the site uses them, so it works from `file://`; only pages with a diagram load them. Diagrams use dark colours when the page background is dark. A diagram with an error shows a message in the page, does not fail the build and does not stop the other diagrams of the page. Mermaid 11.17.2 is bundled (12.2.0 hangs on state and class diagrams).
- Help: a [diagram and formula gallery](https://t00m.github.io/KB4IT/reference-diagrams-formulas.html) with the source and the result of each example, and live examples in "Write a document".
- Math formulas: `$...$` (inline), `$$...$$` (display) and `$$` blocks are drawn with KaTeX, in all four themes, with the same offline files. `\$` writes a literal dollar sign and code is never changed. `pymdownx.arithmatex` or `markdown_katex` in `markdown.extensions` turns the built-in formula handling off; diagrams still work. A price such as `$5/$10` is now read as a formula; see the troubleshooting entry "Text between dollar signs shows as a formula".
- Favicon on every page: `repo.json` `logo`, else the theme's own logo. Themes name it with the new optional `theme.json` key `favicon`.
- 404 page: techdoc, blog and bookshelf write `404.html`, with the search box and a link home (absolute links when `site_url` is set). A document named `404.md` is left out with `DOC_NAME_RESERVED`, also reported by `kb4it verify`; themes declare such names with `reserved_pages`.
- `kb4it serve` answers a missing page with the site's `404.html` and status 404, with its `<base>` pointed at the local server.
- apphelp: its own `404.html` now also gets a `<base>` element with `site_url` when `site_url` is set, so it finds its files from any depth.

### Changed

- Every version is read from `kb4it/VERSION`. Themes get KB4IT's version when they load; `theme.json` no longer has a `version` key.
- blog: `tagline` is optional.

### Fixed

- `kb4it create` keeps files of yours that share a name with a sample, and writes the theme's `config/repo.json` even when the folder already has one, so the theme matches the one you asked for.
- The default apps no longer ship an `EMPTY` marker file.
- `scripts/devel/check_themes.sh` no longer asks for a `version` key in `theme.json`.
- techdoc: the header logo fallback pointed to a file that does not exist; it now uses the theme's logo.

---

## [0.9.0] - 2026-10-19

### Added

- `KB4IT_HOME` environment variable: puts the per-user files (`projects.json`, user themes, logs) in another folder instead of `~/.kb4it`. The test suite uses it so that it never writes to the real profile, also on Windows (CP-03).
- Terminal interface: **Copy Log** uses `pbcopy` on macOS and `clip.exe` on Windows, before falling back to the terminal's OSC 52 (CP-05).
- Documents named like a Windows device (`con.md`, `nul.md`, `com1.md`, ...) are left out of the site on every system with `DOC_NAME_RESERVED`, so a site builds the same everywhere. Two documents whose pages differ only by letter case or extension (`Note.md`, `note.md`, `note.markdown`) log `DOC_NAME_CLASH`; `kb4it verify` reports both problems, and `fail_on_invalid` makes them stop the build (CP-06).
- CI runs the tests and a create-and-build of every bundled theme on Linux, macOS and Windows, with Python 3.11 and 3.13. `scripts/devel/test.sh --python X.Y` picks the Python version, and `scripts/devel/smoke_build.py` runs the same smoke build locally (CP-09).
- `kb4it serve CONFIG`: builds the site, serves it at `http://127.0.0.1:8642/` and rebuilds it when a document, `repo.json`, your own theme, overrides or hooks change. Open pages reload after each rebuild, and a failed build shows its first error in a bar at the top of the page; the files in `target/` never contain the reload script. Options: `--host`, `--port`, `--open`, `--no-watch`, `--no-reload`, `--interval`, `--force` (SV-01).
- Terminal interface: **Browse via Web Server** rebuilds the site when you save a document, reloads open pages and shows a notification after each rebuild (SV-02).
- `markdown` block in `repo.json`: `extensions` and `extension_configs` add python-markdown extensions to the built-in ones. A missing extension stops the build with `MD_EXTENSION_MISSING` and an install hint, and `kb4it verify` reports it; changing the block rebuilds every page. `KB4IT[extras]` installs PyMdown Extensions (MD-01).
- `markdown.highlight`: `pygments` colours code blocks at build time with Pygments, writes `resources/pygments.css` (a light and a dark style, `pygments_style` and `pygments_style_dark`) and drops highlight.js from the pages, in all four themes; `none` turns colouring off. The default, `client`, keeps highlight.js. Pygments is a new dependency (MD-02).
- Full-text search in techdoc, blog and bookshelf: a search box that shows the best matches as you type, and a `search.html` page with all results and filters by Category and Tag. The index (`search-index.js`) holds the text of every document by section, works from `file://`, and is updated incrementally: documents that did not change are not parsed again. `"search": false` in `repo.json` turns it off. The search engine is now shared with apphelp (SR-01, SR-02, SR-03).
- `site_url` in `repo.json`: the public address of the site, used by the sitemap, the feed and the canonical and Open Graph tags. A value that is not an `http://` or `https://` address stops the build (PB-01).
- With `site_url` set, every build writes `sitemap.xml` (with the document `Date` as last change) and `robots.txt`; a `robots.txt` in `source/` is published instead of the generated one. `"sitemap": false` turns both off (PB-02).
- Atom feed `feed.xml` with the newest dated documents: on by default in the blog theme when `site_url` is set, and available in techdoc and bookshelf with `"feed": {"enabled": true}`. Options: `limit`, `categories`, `full_content` (PB-03).
- Every page carries a description (the `Summary` property, or the first lines of the document) and Open Graph tags; with `site_url` also a canonical link, and `og_image` adds a preview image for shared links. The fixed "KB4IT document" description and author tags of techdoc, blog and bookshelf are gone. A theme can replace the tags with its own `HTML_HEAD_META.tpl` (PB-04).
- Per-repository overrides: a template in `overrides/templates/` replaces the theme's template of the same name, and files in `overrides/static/` are copied into the website. Changing them rebuilds every page; `overrides` in `repo.json` picks another folder. `kb4it serve` watches the folder (CU-01).
- Build hooks: `"hooks": "hooks/hooks.py"` in `repo.json` loads Python functions that KB4IT calls during the build: `on_config`, `on_document`, `on_page` and `on_build_end`. An error in a hook stops the build; editing the file rebuilds every page (CU-02).
- "Linked from": every document ends with the list of documents that link to it, in all four themes. Links are kept in `kbdict.json`, so only changed documents are scanned, and a page is rebuilt when its list changes. `"backlinks": false` hides the list (KG-01).
- apphelp versions: with `"versions": {"enabled": true}` each build goes to `target/<version>/` and keeps the other versions, `latest/` copies the newest one, and `index.html`, `versions.json` and `helpids.js` at the top point to it. A version selector in the header opens the same page in another version (VH-01, VH-02). The GitHub Pages guide shows how to publish all versions (VH-03).
- `scripts/distribution/wheels/download_wheels.sh ARCH` downloads the binary wheels of every KB4IT dependency for Python 3.11, 3.12 and 3.13 on `x86_64` or `aarch64` into `dist/wheels/`, about 20 MB per architecture. The `.deb` and `.rpm` ship them so they install without network access (DS-05).
- Python 3.14 is supported: the full test suite passes on it, CI runs it on Linux, macOS and Windows next to 3.11 and 3.13, and the `.deb` and `.rpm` carry wheels for it. Fedora 44 ships Python 3.14 as `python3`.
- CI job `packages`: checks every distribution script with shellcheck, builds the sdist, wheel, source tarball, `.deb` and `.rpm` for both architectures, installs the packages offline in Debian 12, Ubuntu 24.04, Fedora and Rocky Linux 9 containers, builds the container image and smoke-tests it with Docker and Podman. The packages and tarballs are kept as workflow artifacts for 7 days (DS-08).
- Each release publishes the container image `ghcr.io/t00m/kb4it` for amd64 and arm64, tagged `X.Y.Z`, `X.Y` and `latest`, from the same wheel as PyPI. The image is smoke-tested before the push, carries an SBOM and a build provenance attestation, and the GitHub release waits for it and names its digest. The workflow pushes with its own token; no secret is stored (GI-02, GI-03).
- Each GitHub release carries the `.deb` (amd64, arm64) and `.rpm` (x86_64, aarch64), built from the released wheel and installed offline in containers before the release is created (GI-04).
- GitHub Action: `uses: t00m/KB4IT@vX.Y.Z` installs KB4IT with uv, runs `kb4it verify` (any problem fails the step) and `kb4it build`, and writes a job summary with the version and the build counters. Inputs: `config`, `version` (empty: the KB4IT of the action itself), `python-version`, `extras`, `verify`, `force`; outputs: `target`, the absolute path of the built site, and `version`. It runs on Linux, macOS and Windows runners and never deploys (GA-01).
- CI workflow `action`: runs the GitHub Action of the same commit with `uses: ./` on Linux, macOS and Windows, checks its outputs, and checks that a broken link makes it fail (GA-02).
- Help page "GitHub Action" lists the action inputs and outputs and how to pin its version; "Publish on GitHub Pages" uses the action, and keeps the plain commands as an alternative. `README.md` mentions the action, `RELEASING.md` says how to list a release on the GitHub Marketplace and that there is no moving `v0` tag, and `AGENTS.md` describes the distribution scripts and the action (GA-04).
- `scripts/devel/theme_snapshot.py --content DIR` also saves every page of each sample site, normalised (build dates, times and the version replaced), with the documents of `tests/fixtures/audit/` added, so `diff -r` of two runs shows every change in the HTML a theme or template change makes.
- `kb4it verify` warns with `MD_FENCE_IN_BLOCK doc=... lines=...` about a fenced code block inside an admonition or a list item, which the default extensions render as inline code; the warning does not fail the check, and it is silent when `pymdownx.superfences` is enabled. The document format help explains both ways to write such code (OC-05, MD-01).
- Themes can escape template output: with `"autoescape": true` in `theme.json`, every `${...}` is HTML-escaped unless it is marked `| n`. KB4IT's common templates are always escaped. A custom theme without the key prints values as before and gets one `[BUILDER] THEME_AUTOESCAPE_OFF` warning per build. `scripts/devel/escape_audit.py` lists the expressions of a theme for review, and the theme how-to explains the flag (SC-01, SEC-01).
- `"markdown": {"sanitize": true}` cleans the HTML of each document with [nh3](https://nh3.readthedocs.io/): what Markdown and the bundled extensions make stays, while scripts, styles, event handlers, `javascript:` links and `data:` URLs other than images go. Off by default; nh3 joins the `extras` (also in the GitHub Action and the container image). With it off, `kb4it verify` lists documents holding a script or an `on...=` handler outside code (`DOC_RAW_SCRIPT`, information only), and the help explains the trust model (SC-02, SEC-02).
- `scripts/devel/validate_html.py` builds the sample site of every bundled theme (with the audit documents) and checks every page with the Nu HTML Checker, ignoring only the UIkit `uk-*` attributes; CI runs it in the `package` job, so the markup fixed in this release stays valid (TS-02, TST-02).
- Tests for the failure branches of the compiler: a document that cannot compile, a page that runs out of memory and a progress callback that fails; the next build makes the failed pages. Test coverage, with the builds the tests start in their own process, rose from 85% at the audit to 91% (TS-01, TST-01).
- Themes can share templates: `"template_base": "uikit"` in `theme.json` adds a bundled set of templates to the lookup, after the theme and before KB4IT's shared ones. techdoc and blog use it for the 17 templates they had in identical copies (AR-01, ARC-01).
- `scripts/devel/typecheck.sh` runs `mypy --strict` on the modules with type annotations (`core/paths.py`, `core/dates.py`, `core/documents.py`, `core/files.py`, `services/themekit/`, `services/pipeline.py`), and CI runs it in the `package` job. `KB4IT.get_service` tells type checkers which service each name returns (AR-06, ARC-07).

### Changed

- KB4IT no longer stops with "KB4IT only runs in GNU/Linux systems" when the system has no `/etc/os-release`, and no longer reads `/proc` at start-up; on macOS and Windows the platform is described with Python's `platform.platform()`. The debug log names the platform family (CP-01).
- The lock moved from `~/.kb4it/var/kb4it.lock` to each knowledge base (`var/kb4it.lock`), and it uses `flock` on Linux and macOS and `msvcrt` on Windows. Two knowledge bases can now build at the same time, and listing themes, apps or projects, `info` and `verify` never wait for a build. A second build of the same knowledge base still stops with exit status 1 and names the PID that holds it. `projects.json` is written under a short lock, so two `kb4it create` runs cannot lose an entry (CP-02).
- `kb4it create` writes `bin/compile.cmd` on Windows instead of `bin/compile.sh`. Both scripts quote the path of `repo.json`, so a knowledge base in a folder with spaces builds with them; `compile.sh` starts with `#!/bin/sh` (CP-04).
- KB4IT is declared OS independent on PyPI, and the install page explains how to install it on Windows (PowerShell) and macOS (CP-08).
- `kb4it verify` also checks the links between documents: a link to a missing document (`LINK_BROKEN`) or to a missing section (`ANCHOR_MISSING`) is reported and makes it exit with status 1. A build still only warns (KG-02).
- The `.deb` package is built per architecture (`build_deb.sh amd64` or `arm64`) and carries the wheels of every dependency, so it installs without network access; it no longer runs `pip install --upgrade pip` during installation. It refuses, with a clear message, a `python3` it has no wheels for. `scripts/distribution/test/test_packages.sh` builds it and tests install, a smoke build and removal in Debian 12 and Ubuntu 24.04 containers with networking off (DS-04).
- The `.rpm` package is built per architecture (`build_rpm.sh x86_64` or `aarch64`, in `dist/rpm_build/`) from the release wheel and the dependency wheels, so `rpmbuild` and the installation need no network; it no longer builds a second wheel with `pip install --user build`. It requires any Python from 3.11 to 3.14 as `python3` or as `python3.11` to `python3.14`, so it installs on RHEL 9, Rocky Linux 9 and AlmaLinux 9 next to their Python 3.9. `%post` uses the newest supported Python it finds and logs which one; `test_packages.sh rpm` tests it in Fedora and Rocky Linux 9 containers (DS-03).
- The container image installs the release wheel with its extras on `python:3.13-slim`, instead of building its own wheel on 3.12. It runs as the non-root user `kb4it` (UID 1000), works in `/work`, exposes port 8642 for `kb4it serve`, keeps its per-user files in `/tmp/kb4it` so it also runs with `--user "$(id -u):$(id -g)"`, and carries the OCI labels (version, revision, source, licence, documentation). `scripts/distribution/docker/smoke.sh IMAGE` checks the version, a build owned by the calling user and `serve` (GI-01, DS-07).
- `scripts/distribution/README.md` describes what each distribution script builds and needs, and the help page "Install KB4IT" has a section on the `.deb` and `.rpm` packages (DS-09).
- `README.md` and the help page "Install KB4IT" show how to run KB4IT from the container image with Docker or Podman (with `:Z` on SELinux hosts), and where to find the Linux packages. `RELEASING.md` and the help page "Release a version" describe the image and package jobs, what to do when one fails after the PyPI upload, and the one-time step that makes the image public on GitHub (GI-05).
- The help site is built and checked with the KB4IT GitHub Action of the same commit (`uses: ./`), so every change to the help also tests the action (GA-03).
- The help pages "Command line" and "GitHub Action" list every case in which `kb4it build` ends with status 1, including a page that could not be made (BO-03).
- `scripts/devel/theme_snapshot.py --content` builds every app of every theme (techdoc's `sapbasis` too) and, for techdoc and blog, a second incremental build after one document changed, so refactors can be checked against the output of both paths (AR-01 to AR-05, support).
- techdoc, blog and bookshelf share their code: `kb4it.services.themekit.DocumentTheme` holds the property and value pages, the properties, stats, bookmarks and all-documents pages, the document table, the event pages, the table of contents and the metadata section, with class attributes and small methods where the themes differ. The three `theme.py` files lost about 1,300 lines; pages are unchanged. The help page "Create your own theme" explains how a theme builds on it (AR-01, ARC-01).
- No Python module of KB4IT is over 600 lines, and a test keeps it so: `kb4it.core.util` is split into `core/dates.py`, `core/documents.py` and `core/files.py`, the TUI into `tui/projects.py`, `tui/servers.py`, `tui/clipboard.py` and one module per screen under `tui/screens/`, and the techdoc dashboard and "Add" page into `techdoc_dashboard.py` and `techdoc_addpage.py`. `kb4it.core.util` and `kb4it.tui.app` still offer every name they had, so themes, hooks and templates that import from them keep working (AR-02, ARC-02).
- Build callbacks belong to their build: `KB4IT(params)` takes `progress_callback` and `compile_start_callback`, and the TUI passes them that way. `kb4it.services.compiler.set_progress_callback` and `set_compile_start_callback` still work in 0.9.x, for the next build only, and log `[COMPILER] CALLBACK_DEPRECATED`; they go in 0.10.0 (AR-05, ARC-06).
- A build no longer writes into its settings: the decision to rebuild everything (`--force`, `"force"` in `repo.json`, an unreadable or older cache) is `runtime["force_all"]`, and the generation time is `var["updated"]` for templates. `var["repo"]` is a copy that still carries `updated` in 0.9.x; hooks see `repo.json` as loaded, and `Builder.theme_var` belongs to one builder (AR-05, ARC-06).
- The Processor, Compiler and Deployer of a build are made together, once the theme is loaded, as `backend.pipeline` (`kb4it/services/pipeline.py`), and get the backend, database and theme they use instead of looking them up. `KB4IT.get_service("Processor")`, `"Compiler"` and `"Deployer"` still answer from the current pipeline in 0.9.x, with a `[CONTROLLER] SERVICE_DEPRECATED` debug line; they go in 0.10.0 (AR-03, ARC-03).

### Fixed

- A second build in the same process, as the TUI does, reused the templates loaded by the first build: an edited template was ignored, and a second project whose theme shares a template name with the first rendered the first theme's template. Template caches now belong to each build (FX-01).
- Pages, logs and theme files are always read and written as UTF-8. On Windows, or on Linux with a non-UTF-8 locale, documents with accents failed to build or were written in the wrong encoding, and log lines with accents could stop the build. A test fails when any text file is opened without naming its encoding (FX-02).
- `requirements.txt` was missing `Markdown` and `PyYAML`; a test now keeps it equal to the dependencies in `pyproject.toml`. `pixi.toml` lists macOS and Windows platforms (FX-03).
- Documents and `repo.json` saved with a UTF-8 byte order mark, as some Windows editors do, were rejected (`missing_frontmatter`, or a JSON error). They now load like any other file. CRLF line endings give the same metadata and body hash as LF, so a checkout with `core.autocrlf` does not rebuild every page (CP-07).
- A document whose closing `---` line ends with spaces showed its title twice: the compiler now skips the whole closing line, as the frontmatter reader already did (MD-03).
- `scripts/distribution/build/build_python.sh` exists again: the `.deb` script, `build_all.sh`, the manual PyPI scripts and `install_pipx.sh wheel` called it but it was missing. It removes earlier KB4IT wheels from `dist/` before building, so no script picks a stale one. The distribution scripts share their settings in `scripts/distribution/lib/common.sh`, and a test checks that every script they call exists (DS-01).
- `scripts/distribution/build/build_python.sh` is in the repository: the `build/` line of `.gitignore` had kept it out, so the `.deb` script, `build_all.sh`, the manual PyPI scripts and `install_pipx.sh wheel` called a missing file. It removes earlier KB4IT wheels from `dist/` before building, so no script picks a stale one. The distribution scripts share their settings in `scripts/distribution/lib/common.sh`; tests check that every script they call exists and that no script is ignored by git (DS-01).
- The `.rpm` spec and the container `Dockerfile` name `CHANGELOG.md` instead of the old `Changelog`, so `rpmbuild` and `docker build` no longer stop on a missing file; the `.deb` no longer skips its documents silently. The `.deb`, the `.rpm` and the container image share one description, which lists the four bundled themes (DS-02).
- `scripts/install/local/install_kb4it_from_source.sh` lists its real requirements (uv, or pipx with Python 3.11 or newer) instead of asciidoctor. With uv it needs no Python in `/usr/bin`, so it also works on macOS; with pipx it passes the newest Python 3.11+ it finds in `/usr/bin` or on `PATH`. It works from any folder and no longer deletes `dist/` (DS-02).
- `scripts/uninstall/local/uninstall.sh` removes KB4IT installed with uv, pipx or `pip --user`, whichever has it, instead of only pip. `--purge` also deletes `~/.kb4it` (or `KB4IT_HOME`) after asking. The unused install routine with `pip --trusted-host`, which turned off certificate checks, is gone (DS-06).
- A page that cannot be made now fails the build: `kb4it build` exits 1, logs `[WORKFLOW] PAGES_FAILED` with the page names, and the summary (also in the GitHub Action job summary and the `on_build_end` hook) has a `failed=` count. Before, a page whose Markdown or template failed was only logged and the build reported success. Every other page is still deployed, and the deployer no longer stops at the first page missing from its cache (COR-01, COR-09).
- `var/db/kbdict.json` is written only after a build succeeds. Before, it was written during the analysis, so after a failed or interrupted build the next incremental build treated the changed documents as done and kept serving their old pages until `--force` (COR-02).
- The build refuses a `target` folder that is, or holds, the repository root, `source`, `config/`, `var/`, the home folder or a filesystem root, or that lies inside `source`; before, `"target": "."` let the deployer delete files of the repository (FS-01, COR-03).
- The deployer removes from `target` only the pages that an earlier build recorded as its own (`deployed` in `var/db/kbdict.json`). Other `.html` files you keep in `target` are no longer deleted, and the first build after an upgrade deletes nothing. The unused step that emptied the whole target is gone (FS-01, COR-03).
- JSON files (`projects.json`, `var/db/kbdict.json`) are written to a temporary file and then moved into place, so a crash or a full disk leaves the old file whole. An unreadable `projects.json` is kept as `projects.json.corrupt-<timestamp>` with a `PROJECTS_CORRUPT` warning instead of being replaced by a list holding only the new project; an unreadable `kbdict.json` logs `KBDICT_CORRUPT` and the build runs as a full rebuild instead of failing (FS-02, COR-04).
- Changing a `repo.json` setting that a theme can print, such as `title`, `tagline` or a theme option, rebuilds every page. Before, unchanged documents kept the old header until `--force`. `workers`, `force`, `fail_on_invalid`, `source` and `target` do not trigger a rebuild (OC-01, COR-05).
- A template that exists but does not compile (an override, a custom theme) fails the build with `[BUILDER] TEMPLATE_COMPILE_FAIL`, the file and the line, logged once. Before, it was skipped in silence and the theme's own template was used, or the build said the template was not found (OC-02, COR-06).
- The document title is the first `# ` heading outside fenced and indented code blocks. Before, a `# comment` in a shell or Python block above the title became the title. The same rule finds the line that the page body leaves out and that the change detection ignores (OC-03, COR-07).
- A blog post without `Date` no longer stops the blog: it is listed after the dated posts, has no calendar line, and is logged once with `[THEME] DOC_UNDATED`. An unexpected error now prints its type and the log file, as in `Error: KeyError: 'Date' (see <repo>/var/log/kb4it.log)`, instead of the bare message (OC-04, COR-08).
- With `pymdownx.superfences` and the default `"highlight": "client"`, code blocks get plain `language-*` classes for highlight.js instead of Pygments markup without its stylesheet; `pygments` mode still gives Pygments markup and `pygments.css`. `scripts/devel/test.sh` installs `pymdown-extensions`, so these paths run in CI (OC-05, MD-03).
- Help pages "Customize templates", "Create a theme" and "Release" showed the commands of their numbered steps as inline code; the new `verify` warning found them, and they are now code blocks (MD-01).
- Page names made from property names and values never start with a dot. A property such as `.note` used to make a hidden key page that was never built, and with it no page reached the target; it now makes `note.html`. A property name or value that cleans to nothing, such as `...`, makes the document invalid (`bad_property_name` or `bad_property_value`, so `fail_on_invalid` applies) instead of breaking the site (SC-03, SEC-03).
- Links in documents are no longer rewritten: the `HTML_TAG_A` transformation added an empty `target=""` and `class=""` (techdoc, blog) or a second `class` to links that had one (bookshelf, where it also overrode the tag cloud style). bookshelf colours document links with CSS instead, and the blog key modal title no longer gets a second `class` (HT-01, HTML-01).
- blog marks document sections with the classes `kb-sect1` to `kb-sect4` and `kb-section-body` instead of the same `id` on every section, which repeated ids on any page with more than one section (HT-01, HTML-01).
- Valid markup in techdoc and blog pages: the blog footer no longer closes two `div`s it never opened; the blog home page gives the metadata and source dialogs of each post their own ids; the datatable tooltips are a `span`, not a `div` inside a `span`; the techdoc contents menu no longer puts a list inside a list; the techdoc logo has `width="24"` instead of `24px`; and the styles of the techdoc "Add" page moved from a `<style>` element in the body to `screen.css`. The Nu HTML Checker reports no errors on the techdoc sample site other than UIkit attributes (HT-01, HTML-01).
- Accessible defaults for new sites: the sample `repo.json` files of techdoc and blog no longer carry `{placeholder}` values (`logo_alt` is empty, the `git_*` keys are gone), the logo falls back to the site title as its `alt`, and the "Built with KB4IT" badge has an `alt`. Edit and "Create new post" links appear only when `"git": true` and the git server, user, repository and branch are set; before, every blog post linked to `{https://{server.fqdn}/...}`. Every page of techdoc and blog has one `h1` and a `<main>` landmark (blog posts use their title, other blog pages a heading for screen readers), and bookshelf pages without a heading get the page title (HT-02, HTML-02).
- blog rebuilt every day, month and year page on each build; it now reuses them like techdoc. Both themes rebuild an event page only when one of its documents changed, its documents are not the ones it had after the last successful build (recorded as `events` in `kbdict.json`), or its cached copy is missing, so deleting a document or changing its date no longer leaves it on the cached page of its old day in techdoc (AR-01).
- On Windows, an application that embeds KB4IT and builds twice in the same process stopped the second build with `PermissionError` while rotating `var/log/kb4it.log`, which the first build still held open. On Linux the start of the second build's log was lost. The handlers of the earlier build are now closed first.
- `kb4it serve` missed a change saved right after the site came up: the watcher took its first snapshot only after the server started answering.
- The Podman commands in the help page "Install KB4IT" and in `scripts/distribution/README.md` failed with `Permission denied` under rootless Podman. They now pass `--userns=keep-id --user "$(id -u):$(id -g)"`, so the container writes to the folder as you. `smoke.sh` does the same.

### Removed

- The unused `exec_cmd` helper, which ran commands through a shell (`shell=True`). A test now checks that no module of the package uses a shell (FS-03, BASE-01).
- 115 bundled templates that could never reach a page: the 52 files of 13 transformation pairs written for Asciidoctor markup that python-markdown never produces (`HTML_TAG_PRE`, `HTML_TAG_TABLE`, `HTML_TAG_TABLE_KB4IT`, the `HTML_TAG_ADMONITION_*` and `HTML_TAG_ADMONITION_ICON_*` families), and 63 templates no code renders. Pages are unchanged; tests now fail if a transformation can never match or a template is never used (AR-04, ARC-05).
- The root `index.html`, an old redirect that GitHub Pages no longer serves (the help site is published by `help.yml`), and the unused `pypi/README.rst` (AR-07, ARC-08).

### Security

- apphelp escapes template output (`"autoescape": true`); only the page body, the `aria-current` attribute and the labels for the scripts are printed raw. Its explicit `| h` filters are gone (SC-01, SEC-01).
- techdoc escapes template output. Titles, property names and values, dates and the document source shown under "Source" print as text; before, a value such as `<img src=x onerror=...>` ran in every page that listed it. The tables, the date cells and the tooltips that techdoc builds in Python escape the values they hold, and the JSON of the "Add" page cannot close its `<script>` (SC-01, SEC-01).
- blog escapes template output. Post titles, property names and values and the source shown under "Source" print as text; the tables and tooltips it builds in Python escape the values they hold (SC-01, SEC-01).
- bookshelf escapes template output. Book, part and chapter titles, authors, tags and other property values print as text; the separators next to them stay as they were, and the tables it builds in Python escape the values they hold. All four bundled themes now escape (SC-01, SEC-01).

---

## [0.8.0] - 2026-10-03

### Fixed

- A second build in the same process, as the TUI does when you compile another project, ran the first theme's logic. Each theme load now imports its own `logic/theme.py`.
- `kb4it themes` no longer logs `'Backend' object has no attribute 'repo'` while listing apphelp.
- `kb4it create` with an unknown theme exits 1 instead of 0.
- blog: posts without an `Author` were left out of the index page (`INDEX_SKIP`) and rendered without the post layout.
- TUI: a failed build showed "Done" instead of "FAILED". After a build, the project screen now refreshes, so Explore, View Build Log and Browse are enabled without leaving the project.
- apphelp: table columns no longer break words in the middle; a wide table scrolls instead.

### Added

- User help at https://t00m.github.io/KB4IT/, built with the apphelp theme from `help/`: getting started, installing, writing documents, building, the terminal interface, publishing, the four themes, creating a theme, a command and settings reference, troubleshooting, and development notes. `.github/workflows/help.yml` builds it on every push that touches the help or the code and publishes it from `master` (#68).

- Tests for the command line (`themes`, `apps`, `projects`, `info`, `create`, configuration and theme errors, `--force`, the process lock), the `kb4it.core.util` helpers, the techdoc, blog and bookshelf themes, and every TUI screen. Line coverage of `kb4it` goes from 60% to 90%.

### Changed

- CI and the publish workflow use the current major versions of their GitHub Actions (`checkout` v7, `upload-artifact` v7, `download-artifact` v8, `setup-uv` v10.2.0), which run on Node 24 instead of the deprecated Node 20. A downloaded build that does not match its recorded hash now fails the publish workflow. `setup-uv` is pinned to a full version because it publishes no `v10` tag.

### Removed

- `docs/`, which held an empty page and an example of an API that no longer exists. The help in `help/` replaces it.

---

## [0.7.10] - 2026-10-03

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

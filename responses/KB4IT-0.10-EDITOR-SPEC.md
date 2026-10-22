---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-22
DocType: Reference
OS: Linux, macOS, Windows
Product: KB4IT
Scope: Development
Status: Approved
Tag: specification, editor, markdown, frontmatter, codemirror
Topic: Architecture, Documentation
---

# KB4IT 0.10 specification: Markdown editor in the techdoc Add page

## Overview

This specification defines the Markdown editor that KB4IT 0.10.0 adds to the techdoc "Add" page (`add.html`). Today that page opens a plain `<textarea>` with a skeleton per category, a "Values reference" panel with the values of every property, and a **Copy** button. The new page keeps the same flow and adds:

1. A source editor based on CodeMirror 6: Markdown and YAML highlighting, undo, search, list continuation.
2. Autocompletion of frontmatter properties and values, taken from the documents of the repository.
3. A visual frontmatter form, kept in sync with the text.
4. A toolbar for the basic Markdown elements and for the KB4IT ones (admonitions, Mermaid, formulas).
5. A **Save** button: the system save dialog in Chromium browsers, a download of the `.md` file everywhere else.

The base is release 0.9.1. Each requirement has an ID (`ED-01`, `ED-02`, ...). The implementation plan, the commits and the CHANGELOG entries will refer to these IDs.

### Hard constraints

These come from the user and are not open to trade-offs:

- **Browser first.** The editor is a web page of the generated site.
- **Offline.** No request leaves the page: no CDN, no web font, no dictionary download. It works from `file://` and from `kb4it serve`.
- **Transparent for the user.** Users install KB4IT as today (`pip`, `uv tool`, `pipx`, `.deb`, `.rpm`, container image). They never run npm, Node or any build step. Every file the editor needs ships inside `kb4it/resources/`.
- **The text is never rewritten.** What the user types is what is saved, byte for byte. No WYSIWYG round trip.
- **Licences compatible with GPL-3.0-or-later**, with their notices kept.

### Evidence behind the choice

Checked on 2026-10-22 in Chromium 141, page opened from `file://` with every network request blocked. Each editor loaded a KB4IT document (frontmatter, `!!! note` admonition, `mermaid` fence, `$E=mc^2$`, `\$5`), then a line was typed with the keyboard.

| Editor | Version | Size (min) | Network requests | Text intact |
|---|---|---|---|---|
| CodeMirror 6, bundled with esbuild (IIFE) | 6.x | 626 KB (214 KB gzip) | none | yes |
| OverType | 2.6.1 | 137 KB | none | yes |
| Tiny MDE | 0.2.35 | 71 KB | none | yes |
| EasyMDE | 2.21.0 | 327 KB + CSS | 3 by default (Font Awesome, 2 spell checker dictionaries) | yes |

Also confirmed: `<script type="module">` is blocked from `file://` (CORS, origin `null`), so the editor must load as a classic script. `showSaveFilePicker` and `showDirectoryPicker` exist on `file://` pages and `isSecureContext` is true.

CodeMirror 6 was chosen (decision D-1) because it is the only candidate with context-aware autocompletion, lint diagnostics and a syntax tree that separates the YAML frontmatter from the Markdown body, all through its extension system. The other three would need the same features written outside the library.

### Phases

| Phase | Name | IDs | Depends on |
|---|---|---|---|
| 1 | Packaging and deployment | ED-01 to ED-03 | none |
| 2 | Editor | ED-04 to ED-06 | 1 |
| 3 | Frontmatter form | ED-07, ED-08 | 2 |
| 4 | Toolbar | ED-09 | 2 |
| 5 | Saving | ED-10 | 2 |
| 6 | Documentation and tests | ED-11, ED-12 | all |

### Non-goals for 0.10

- **WYSIWYG editing.** It reformats Markdown and breaks python-markdown syntax such as `!!!` admonitions.
- **Live HTML preview.** A JavaScript parser would not match python-markdown, its extensions, `RichContentExtension` or the theme transformations; a preview that differs from the built page misleads. A faithful preview through `kb4it serve` is future work.
- **Writing into `source/` through `kb4it serve`.** The web server stays read-only (GET only).
- **Editing existing documents.** The page creates new documents, as today. Opening a local `.md` file is future work (see "Future work").
- **Other themes.** blog, bookshelf and apphelp do not get the editor in 0.10. The assets and the editor script are theme independent, so adding it later is a template change.
- **Spell checking** beyond the browser's own.

## Conventions for all changes

- **Logging**: new events use `[<COMPONENT>] EVENT key=value`. New event: `[DEPLOYER] EDITOR_ASSETS deployed=<bool>`.
- **Errors**: services raise `ConfigError`, `ThemeError`, `CompilationError` or `KB4ITError`.
- **Text files**: every read or write in `kb4it/` names `encoding="utf-8"`.
- **Escaping**: data from documents reaches the DOM only through `textContent`, attributes set with `setAttribute`, or CodeMirror's own rendering. Never through `innerHTML`. JSON printed inside `<script>` replaces `<` with `<`, as `techdoc_addpage.py` already does.
- **JavaScript**: plain ES2017 in classic scripts, no build step for KB4IT's own code, no globals except one namespace per file (`KB4ITEditor`, `KB4ITFrontmatter`).
- **Tests**: every requirement has at least one pytest test.
- **Docs**: each user-visible change updates `help/source/`, `AGENTS.md`, `README.md` where relevant, and `CHANGELOG.md` under `## [Unreleased]`.
- **Commits**: one line, Conventional Commits, no trailers.

## Phase 1: Packaging and deployment

### ED-01 Vendored CodeMirror bundle

**Layout.**

```text
kb4it/resources/editor/
    codemirror.min.js          # CodeMirror 6 bundle, IIFE, global KB4ITEditor.cm (generated, committed)
    kb4it-frontmatter.js       # Frontmatter parser and serializer (KB4IT code, ED-08)
    kb4it-editor.js            # Editor set-up, completion, lint, toolbar, form, save (KB4IT code)
    kb4it-editor.css           # Editor, toolbar and form styles
    LICENSE                    # CodeMirror MIT licence
    THIRD-PARTY-NOTICES.txt    # Licence text of every package inside the bundle (generated)
    VERSIONS                   # One "package version" line per bundled package, plus esbuild
scripts/devel/editor/
    package.json               # Exact versions, no ranges
    package-lock.json
    entry.js                   # What the bundle exports
    build.sh                   # npm ci, esbuild, notices, VERSIONS
```

**Bundle content.** Only what the editor uses: `@codemirror/state`, `view`, `commands`, `language`, `search`, `autocomplete`, `lint`, `lang-markdown`, `lang-yaml` (for `yamlFrontmatter`), and their `@lezer/*` dependencies. `@codemirror/language-data` is left out: code inside fences is not highlighted, which keeps the bundle small. `basicSetup` is not used; `kb4it-editor.js` lists the extensions it needs.

**Split between bundle and KB4IT code (decision D-3).** The bundle only exposes the CodeMirror API under `KB4ITEditor.cm` (`EditorView`, `EditorState`, `keymap`, `autocompletion`, `linter`, `syntaxTree`, ...). Everything KB4IT specific lives in plain `kb4it-editor.js` and `kb4it-frontmatter.js`. A contributor changes the editor's behaviour by editing those files; npm is only needed to upgrade CodeMirror.

**`build.sh`.**

1. `npm ci` in `scripts/devel/editor/` (pinned by `package-lock.json`).
2. `esbuild entry.js --bundle --minify --format=iife --global-name=KB4ITEditor --legal-comments=eof --outfile=kb4it/resources/editor/codemirror.min.js`.
3. Writes `THIRD-PARTY-NOTICES.txt` from the `LICENSE` file of every package that ends in the bundle (from esbuild's metafile, not from the whole `node_modules`).
4. Writes `VERSIONS`.
5. Prints the size of the bundle. The bundle must stay under 700 KB minified; the script fails above it.

Users and CI never run `build.sh`. The generated files are committed, like `kb4it/resources/render/mermaid/mermaid.min.js` (decision D-2).

**Acceptance.**

- `tests/core/test_editor_assets.py` checks that every file of the layout exists, `VERSIONS` names `@codemirror/view` and `esbuild`, and `THIRD-PARTY-NOTICES.txt` names every package in `VERSIONS`.
- The same test reads `codemirror.min.js`, `kb4it-editor.js` and `kb4it-editor.css` and fails on any `http://` or `https://` string except `http://www.w3.org/` namespaces. This is the offline guarantee.
- `scripts/devel/check_wheel_themes.py` (or a sibling check) confirms `kb4it/resources/editor/` is inside `dist/*.whl`. `pyproject.toml` already includes `kb4it/resources/**/*`; no change is expected.

### ED-02 Deploy the editor only where it is used

**Requirement.** `Deployer.deploy_editor_assets()` mirrors `deploy_render_assets()`:

- `EDITOR_REF = re.compile(r'(?:src|href)="[^"]*resources/editor/')`.
- When any `*.html` page in the target (built now or kept from an earlier build) matches, copy `ENV["GPATH"]["RESOURCES"]/editor` to `target/resources/editor/`; otherwise remove a stale `target/resources/editor/`.
- Log `[DEPLOYER] EDITOR_ASSETS deployed=<bool>`.
- Called right after `deploy_render_assets()` in the same deploy step.

The editor files live in their own folder, not under `resources/render/` (decision D-4): a page that loads the editor must not pull Mermaid and KaTeX, and the reverse.

**Acceptance.** A techdoc build deploys `resources/editor/`; a blog build does not; removing the Add page reference (test fixture) removes the folder on the next build.

### ED-03 Licences and credits

- `kb4it/resources/editor/LICENSE` and `THIRD-PARTY-NOTICES.txt` ship with the package and are deployed with the assets.
- `THANKS` gains: `* CodeMirror (https://codemirror.net, MIT): source editor of the techdoc Add page`.
- `techdoc/theme.json` `kb4it` becomes `">=0.10.0"`.

**Acceptance.** `tests/core/test_editor_assets.py` checks the `THANKS` line; `check_themes.sh` passes.

## Phase 2: Editor

### ED-04 CodeMirror replaces the textarea

**Page.** `PAGE_ADD.tpl` keeps the category cards and the full-screen modal per category. In each modal the `<textarea id="kb-editor-<cat>">` becomes a `<div id="kb-editor-<cat>">` host. The page loads, in this order and as classic scripts, `resources/editor/codemirror.min.js`, `resources/editor/kb4it-frontmatter.js`, `resources/editor/kb4it-editor.js`, and the stylesheet `resources/editor/kb4it-editor.css`.

**Creation.** `kbAddOpen(cat)` creates the editor the first time the modal of a category opens, with the skeleton as today (date filled in, title placeholder). Opening the same category again asks before replacing an edited document ("Discard your changes and start again?").

**Extensions.** Line numbers, line wrapping, history (undo, redo), search panel (`Ctrl+F`), bracket closing, the Markdown keymap (Enter continues lists and quotes), `yamlFrontmatter({content: markdown()})`, and the completion, lint and toolbar of ED-05, ED-06 and ED-09. Tab inserts four spaces, which is what python-markdown needs inside admonitions and nested lists; `Escape` then `Tab` leaves the editor (keyboard accessibility).

**Look.** A CodeMirror theme built on CSS custom properties in `kb4it-editor.css`, light by default. Dark colours apply when the page background is dark, measured the same way as `kb4it-render.js` (luminance of the first opaque background), so the editor follows the theme and not `prefers-color-scheme`.

**Text.** The editor never changes the text on its own: no trimming, no reflow, LF line endings, UTF-8.

**Acceptance.** Browser test (ED-12): open each category, type, undo, check the text.

### ED-05 Frontmatter autocompletion

**Data.** `techdoc_addpage.py` keeps `keys_json` (`{key: [{v, c}]}`) and adds nothing else for this requirement.

**Behaviour.** Active only inside the frontmatter (the YAML node of the syntax tree):

| Cursor position | Suggestions |
|---|---|
| Start of a line, typing a name | Property names of the repository not yet in the frontmatter, with their number of values |
| After `Key:` or after a comma in its value | Values of that property, most used first, with the number of documents; values already present are left out |
| Value of an unknown property | None |

Choosing a property inserts `Key: `. Choosing a value inserts the value; a value that needs quoting in YAML (ED-08 rules) is inserted quoted. New names and values can always be typed: completion suggests, it never restricts.

**Acceptance.** Browser test: type `Cat` in the frontmatter, accept, check `Category: `; type `N`, accept, check `Category: Note`.

### ED-06 Lint diagnostics

Diagnostics use CodeMirror's lint gutter and underline. They mirror what the build and `kb4it verify` report, with the same reason names, so the user fixes problems before saving.

| Check | Level | Reason |
|---|---|---|
| Text does not start with `---` | error | `missing_frontmatter` |
| Frontmatter not closed | error | `missing_frontmatter_close` |
| YAML syntax error (error node in the YAML tree) | error | `invalid_frontmatter` |
| No `# ` heading outside code | error | `missing_h1_title` |
| `Title` or `title` in the frontmatter | warning | `title_in_frontmatter_ignored` |
| Property name or value that cleans to nothing (`valid_filename`) | error | `bad_property_name`, `bad_property_value` |
| Property unknown in the repository | info | new property |
| Value unknown for a known property | info | new value |

The H1 rule follows `util.first_heading`: the first `# ` line outside fenced and indented code. The `valid_filename` rule is ported to JavaScript in `kb4it-frontmatter.js` (decision D-6) and tested against the Python function with a shared table of cases.

**Acceptance.** Browser test: a document without H1 shows `missing_h1_title`; adding one clears it. Parser test: the shared `valid_filename` table passes in Python and in JavaScript.

## Phase 3: Frontmatter form

### ED-07 Visual property editor

The right pane of the modal, today "Values reference", becomes **Properties**:

- **One row per property** of the frontmatter, in text order: the name, the values as removable chips, an input to add a value, and a button to remove the property.
- **Value input.** Suggests values of that property from `keys_json` (most used first, with counts), filters as the user types, accepts new values. Enter or a click adds the chip.
- **Add property.** A selector with the repository's properties not yet in the document, plus "New property..." for a free name checked with `valid_filename`.
- **Value cloud.** Each property row can expand the current word cloud of its values (existing code, weights unchanged). A click on a word adds it as a value.
- **Commas.** KB4IT splits a string value on commas (`documents.get_markdown_attributes`), so a value cannot hold a comma. The input refuses it and says why.
- **Security.** The existing accordion builds its title with `innerHTML` from the property name; the new pane uses `textContent` only.

**Acceptance.** Browser test: add `Tag: sap` from the form and see it in the text; remove a chip and see the text change.

### ED-08 Sync between form and text (decision D-5)

**Parser.** `kb4it-frontmatter.js` exposes `KB4ITFrontmatter.parse(text)` and `KB4ITFrontmatter.setValues(text, key, values)` and has no DOM code. It reads the subset KB4IT documents use:

| Line form | Values |
|---|---|
| `Key:` | `[]` |
| `Key: a` | `["a"]` |
| `Key: a, b` | `["a", "b"]` |
| `Key: [a, b]` | `["a", "b"]` |
| `Key: "a: b"` or `'a: b'` | `["a: b"]` |

Anything else (block lists with `- item`, multi-line scalars, nested maps, anchors) marks that property **complex**: the form shows it read-only with "Edit this property in the text". The parser never guesses.

**Form to text.** A change in the form replaces only the line of that property (or appends a line before the closing `---` for a new one) with one CodeMirror transaction, so undo works and the rest of the text is untouched. Lines are written as `Key: a, b`, the style of the skeletons. A value is quoted with double quotes when YAML would read it differently: it starts with a YAML indicator (any of `[ ] { } & * ! | > ' " % @` or a backtick) or with `- `, contains `: ` or ` #`, or is `true`, `false`, `yes`, `no`, `null`, `~` or a number.

**Text to form.** After each edit, debounced 300 ms, the frontmatter is parsed again and the form is redrawn. While the frontmatter has an error (ED-06), the form shows the error and is read-only.

**Acceptance.** Parser tests over a table of cases (each line form, quoting, complex properties, CRLF input). Round trip: `parse(setValues(t, k, v))[k]` equals `v` for every case. Browser test: edit the text, see the form change, and the reverse.

## Phase 4: Toolbar

### ED-09 Markdown and KB4IT elements

A toolbar above the editor, UIkit buttons and UIkit icons (already in the theme, no icon font). Each button applies to the selection when there is one and inserts a template at the cursor when there is not; the inserted text is selected or the cursor is placed where the user writes next.

| Group | Buttons | Shortcut |
|---|---|---|
| Inline | Bold `**`, italic `*`, inline code, link `[text](url)` | `Ctrl+B`, `Ctrl+I`, `Ctrl+E`, `Ctrl+K` |
| Headings | H2, H3, H4 (H1 is the title; the button is not offered) | |
| Blocks | Bullet list, numbered list, task list, quote, code block, horizontal rule | |
| Insert | Table (3 x 2 with header), image `![alt](path)` | |
| KB4IT | Admonition (menu: note, tip, warning, danger), Mermaid diagram, inline formula `$...$`, display formula `$$` block | |
| Document | Link to a document of the repository (future work, see below) | |

The admonition template follows python-markdown's `admonition` extension:

```text
!!! note "Title"
    Text of the note, indented by four spaces.
```

The Mermaid template is a fenced block named `mermaid` with a two-node `graph TD`. Formulas use the `$` rules of `core/mdrich.py`.

**Acceptance.** Browser test per button: empty selection and selected text, checked against the expected text.

## Phase 5: Saving

### ED-10 Save, download and copy

**Buttons** in the modal header: **Save** (primary), **Copy** (as today).

**File name.** `slugify(<H1 title>) + ".md"`, with `slugify` ported from `util.slugify`; `<category>.md` while there is no title.

**Save (decision D-7).**

1. When `window.showSaveFilePicker` exists (Chrome, Edge and other Chromium browsers): open the system dialog with the suggested name, type `text/markdown` / `.md`, and `id: "kb4it-source"` so the browser reopens the folder used last time. Write the text. Keep the file handle while the modal is open, so the next **Save** writes the same file without asking; the button label becomes "Save (<name>)".
2. Otherwise (Firefox, Safari), or when the user cancels the dialog and asks to download instead: download the text as a `Blob` (`text/markdown;charset=utf-8`) through an `<a download>` link.
3. Before saving, error diagnostics (ED-06) are listed in a confirmation ("This document has 2 errors and will not build. Save anyway?").

**Text written.** Exactly the editor content, UTF-8, LF line endings, ending with one newline (added only if missing).

**Unsaved changes.** Closing the modal or leaving the page with unsaved edits asks for confirmation.

**Page note.** The alert "KB4IT is a static site generator, it cannot create files for you" is rewritten: the page saves or downloads the file; the user puts it in the repository's `source` folder and rebuilds.

**Acceptance.** Browser test with the download path (the save dialog cannot run headless): the downloaded file equals the editor text plus the final newline. A test stubs `showSaveFilePicker` and checks the name, the options and the written text.

## Phase 6: Documentation and tests

### ED-11 Documentation

- `help/source/reference-theme-techdoc.md`: the Add page, its editor, the property pane, the toolbar, saving and browser support.
- New how-to `help/source/howto-write-document-editor.md` (`DocType: How-to guide`): create a document with the editor and add it to the repository.
- `AGENTS.md`: `kb4it/resources/editor/`, `scripts/devel/editor/build.sh`, `deploy_editor_assets()`, the split between bundle and KB4IT code, the commands table.
- `README.md`: one line in the techdoc feature list.
- `CHANGELOG.md` under `## [Unreleased]`, `### Added`, with the ED IDs.
- `kb4it verify help/config/repo.json` passes.

### ED-12 Tests

| Layer | Where | What |
|---|---|---|
| Python | `tests/core/test_editor_assets.py` | ED-01 files, notices, offline scan; ED-03 `THANKS` |
| Python | `tests/core/test_deployer_editor.py` | ED-02 deploy and removal |
| Python | `tests/themes/test_techdoc_add.py` | The Add page loads the four editor files; `keys_json` has no raw `<`; hostile property names stay escaped |
| JavaScript logic | `tests/js/test_frontmatter.py` | Runs the ED-06/ED-08 case tables against `kb4it-frontmatter.js` with `node` when it is installed; skipped otherwise |
| Browser | `tests/browser/test_add_editor.py` | ED-04 to ED-10 with Playwright and Chromium from `file://`, network blocked; marked `browser`, skipped when Playwright is missing (decision D-8) |

The browser tests run in a new CI job on Linux only (Playwright with its own Chromium). The OS matrix keeps running everything else.

## Compatibility

| Change | Why |
|---|---|
| The Add page shows an editor, a property pane and a toolbar instead of a textarea and a value cloud | ED-04, ED-07, ED-09 |
| techdoc sites gain `resources/editor/` (about 0.7 MB) | ED-02; other themes are unchanged |
| techdoc needs KB4IT 0.10.0 | ED-03 |
| The wheel, `.deb`, `.rpm` and container image grow by the same amount | ED-01 |

No `repo.json` key, document rule or command changes. Existing repositories build without edits.

## Decisions

D-1 and D-7 were approved by the user on 2026-10-22, together with the hard constraints. D-2 to D-6 and D-8 are proposed in this specification; they hold unless the user changes them before implementation starts.

| # | Decision | Chosen | Alternative not taken |
|---|---|---|---|
| D-1 | Editor library | CodeMirror 6 | OverType (light, no completion or lint), EasyMDE (CodeMirror 5, external downloads), Tiny MDE (little extension support) |
| D-2 | Bundle source | Generated by the maintainer, committed | Built in CI or at install time: puts npm in the release path |
| D-3 | KB4IT code | Plain JS files next to a bundle that only exports CodeMirror | Everything inside the bundle: every KB4IT change would need npm |
| D-4 | Asset folder | `resources/editor/`, deployed on its own | Inside `resources/render/`: the Add page would pull Mermaid and KaTeX |
| D-5 | Form and text | Two-way sync, line-level edits, complex properties read-only | Form owns the frontmatter and the editor holds only the body: simpler, but loses completion and lint in the text |
| D-6 | Name rules in the browser | Port `valid_filename` and `slugify`, tested against Python with shared cases | Skip the checks and rely on `kb4it verify` |
| D-7 | Saving | Save dialog in Chromium, download elsewhere, copy kept; no server writes | Write through `kb4it serve`: needs POST endpoints and only works while serving |
| D-8 | Browser tests | Playwright, Linux CI job, skipped when missing | No browser tests: the editor logic would go untested |

## Future work

- **Open an existing document**: `showOpenFilePicker` in Chromium (then **Save** writes it back), `<input type="file">` elsewhere.
- **Link completion**: after `](`, suggest the repository's documents by title (needs a `docs_json` with names and titles).
- **Faithful preview** through `kb4it serve`, compiling the text with the same pipeline as the build.
- **Editor in other themes** (blog, bookshelf).

## Testing summary

- Python tests for packaging, deployment and the page template run in the existing CI matrix (Linux, macOS, Windows).
- The JavaScript parser tests run wherever `node` is present.
- Browser tests run in a Linux CI job with Playwright and Chromium from `file://` with the network blocked, which is the offline guarantee checked end to end.
- Firefox is checked by hand once per release for the download path, since it has no save dialog API.

## Related Topics

- `AGENTS.md`: architecture and contribution rules.
- `responses/KB4IT-0.9-SPEC.md`: format of this specification and the `kb4it serve` design.
- `scripts/devel/fetch_render_assets.sh`: the model for vendored browser assets.
- `kb4it/resources/themes/techdoc/templates/PAGE_ADD.tpl` and `logic/techdoc_addpage.py`: the page this specification changes.

---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-22
DocType: How-to guide
OS: Linux, macOS, Windows
Product: KB4IT
Scope: Development
Status: Draft
Tag: implementation-plan, editor, markdown, codemirror
Topic: Architecture, Development
---

# KB4IT 0.10 Markdown editor implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the textarea of the techdoc Add page with an offline CodeMirror 6 editor that completes and checks frontmatter, edits properties in a form, inserts Markdown and KB4IT elements, and saves the `.md` file.

**Architecture:** A committed esbuild bundle (`codemirror.min.js`) exposes only the CodeMirror API as `KB4ITEditor.cm`. KB4IT logic lives in two plain classic scripts: `kb4it-frontmatter.js` (no DOM: parsing, quoting, name rules, lint, completion; tested with `node`) and `kb4it-editor.js` (DOM glue: views, toolbar, property pane, save). The deployer copies `resources/editor/` only when a page references it.

**Tech Stack:** CodeMirror 6, esbuild (maintainer only), plain ES2017, Mako, pytest, node (optional, JS logic tests), Playwright with Chromium (optional, browser tests).

**Spec:** `responses/KB4IT-0.10-EDITOR-SPEC.md`. Read it with this plan; requirement IDs (ED-xx) and decisions (D-x) refer to it.

## Global Constraints

- Offline: no request leaves the page; no `http://` or `https://` string in `codemirror.min.js`, `kb4it-editor.js`, `kb4it-editor.css` except `http://www.w3.org/` namespaces.
- Classic scripts only (`<script type="module">` is blocked from `file://`).
- Users never run npm, Node or a build step; generated files are committed (D-2).
- The editor never rewrites text: no trimming, no reflow, LF line endings, UTF-8. Saving adds one final newline only if missing.
- Bundle under 700 KB minified; `build.sh` fails above it.
- Licences compatible with GPL-3.0-or-later; notices shipped.
- Logging: `[<COMPONENT>] EVENT key=value`; new event `[DEPLOYER] EDITOR_ASSETS deployed=<bool>`.
- Every text read or write in `kb4it/` names `encoding="utf-8"`.
- Document data reaches the DOM only through `textContent`, `setAttribute` or CodeMirror rendering, never `innerHTML`. JSON inside `<script>` replaces `<` with `<`.
- JavaScript: ES2017, no build step for KB4IT code, globals limited to `KB4ITEditor` (bundle plus `kb4it-editor.js`) and `KB4ITFrontmatter`.
- No Python module over 600 lines (`tests/test_module_size.py`).
- Each task updates `CHANGELOG.md` under `## [Unreleased]` / `### Added` (or `### Changed`) with its ED IDs, and `help/source/` where the user sees a change.
- Commits: one line, Conventional Commits, no trailers. Never push, never branch. No em dashes anywhere.

## Corrections to the spec found while planning

- **ED-06 reason for YAML syntax errors.** The build reports a YAML syntax error as `yaml_error` and a frontmatter that is not a mapping as `invalid_frontmatter` (`kb4it/core/documents.py:200-206, 243`). The spec asks for "the same reason names" as the build, so the editor uses `yaml_error` for syntax errors and `invalid_frontmatter` for a non-mapping frontmatter.
- **ED-08 quoted values with commas.** The build splits every string value on commas, quoted or not (`documents.py:228`). The parser mirrors the build: `Key: "a, b"` gives `["a", "b"]`; the form refuses commas (ED-07) so it never writes one.
- **Frontmatter boundaries.** The build opens the frontmatter when the text starts with `---` and closes it at the first `"\n---"` after offset 3 (`documents.py:189-195`). The parser and lint use the same rule, so a BOM before `---` is `missing_frontmatter`, as in the build.

## Review Focus

1. **CRLF text** pasted or loaded: parse, lint and `setValues` treat `\r\n` like `\n`; saved text is LF. Test in Task 3 (`test_crlf_input`) and Task 10 (`test_save_writes_lf`).
2. **Titles with no ASCII letters** (`# 日本語`, `# ¿?`): `slugify` returns `""` and the file name falls back to `<category>.md`. Test in Task 3 (`test_file_name_fallback`).
3. **Quoted value with a comma** (`Tag: "a, b"`): the form shows two chips, matching what the build will index. Test in Task 3 (`test_quoted_comma_splits`).
4. **Hostile repository data** (a property value `<img src=x onerror=alert(1)>`, a name containing `</script>`): it shows as text in completion, chips and cloud; no element is created. Test in Task 5 (template) and Task 7 (browser, `test_hostile_values_stay_text`).
5. **Reopening a category after edits**: the confirm "Discard your changes and start again?" appears; Cancel keeps the text and the undo history. Test in Task 5 (`test_reopen_keeps_edits_on_cancel`).

---

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `scripts/devel/editor/package.json`, `package-lock.json` | Pinned CodeMirror and esbuild versions | 1 |
| `scripts/devel/editor/entry.js` | Names the CodeMirror API the bundle exports as `cm` | 1 |
| `scripts/devel/editor/build.sh` | npm ci, esbuild, notices, VERSIONS, size check | 1 |
| `kb4it/resources/editor/codemirror.min.js`, `LICENSE`, `THIRD-PARTY-NOTICES.txt`, `VERSIONS` | Generated, committed | 1 |
| `kb4it/services/deployer.py` | `deploy_editor_assets()` | 2 |
| `kb4it/resources/editor/kb4it-frontmatter.js` | `KB4ITFrontmatter`: parse, setValues, quote, validFilename, slugify, firstHeading, lint, complete | 3, 4 |
| `tests/fixtures/editor/names.json` | Shared `valid_filename` and `slugify` cases (Python and JS) | 3 |
| `tests/js/nodejs.py` | `run_node(calls)` harness | 3 |
| `kb4it/resources/editor/kb4it-editor.js` | `KB4ITEditor` glue: views, completion and lint sources, pane, toolbar, save | 5 to 10 |
| `kb4it/resources/editor/kb4it-editor.css` | Editor theme (light and dark tokens), toolbar, pane | 5 to 9 |
| `kb4it/resources/themes/techdoc/templates/PAGE_ADD.tpl` | Host divs, script tags, buttons, pane markup | 5 to 10 |
| `tests/browser/conftest.py` | Session techdoc site, Playwright page with network blocked, helpers | 5 |
| `.github/workflows/kb4it.yml` | New `browser` job (Linux) | 5 |

The inline `<script>` of `PAGE_ADD.tpl` shrinks to a call into `KB4ITEditor`; skeleton building (`buildTemplateMd`) and the word cloud move into `kb4it-editor.js`.

---

### Task 1: Vendored CodeMirror bundle, licences and credits (ED-01, ED-03)

**Files:**
- Create: `scripts/devel/editor/{package.json,package-lock.json,entry.js,build.sh}`
- Create (generated): `kb4it/resources/editor/{codemirror.min.js,LICENSE,THIRD-PARTY-NOTICES.txt,VERSIONS}`
- Modify: `THANKS`, `kb4it/resources/themes/techdoc/theme.json:10`, `scripts/devel/check_wheel_themes.py`
- Test: `tests/core/test_editor_assets.py`

**Interfaces:**
- Produces: global `KB4ITEditor.cm` with at least `EditorView, EditorState, Compartment, keymap, lineNumbers, highlightActiveLine, drawSelection, history, historyKeymap, defaultKeymap, indentWithTab, undo, redo, searchKeymap, closeBrackets, closeBracketsKeymap, autocompletion, completionKeymap, linter, lintGutter, forceLinting, syntaxTree, HighlightStyle, syntaxHighlighting, tags, markdown, markdownKeymap, yamlFrontmatter`.
- Produces: `EDITOR_FILES` list in the test module, extended by Tasks 3 and 5.

- [ ] **Step 1: Write the failing tests** in `tests/core/test_editor_assets.py`:
  - `EDITOR = ROOT / "kb4it" / "resources" / "editor"`; `EDITOR_FILES = ["codemirror.min.js", "LICENSE", "THIRD-PARTY-NOTICES.txt", "VERSIONS"]`.
  - `test_editor_files_in_package`: each of `EDITOR_FILES` is a file.
  - `test_versions_name_codemirror_and_esbuild`: the first word of the `VERSIONS` lines includes `@codemirror/view` and `esbuild`.
  - `test_notices_cover_every_bundled_package`: every package of `VERSIONS` except `esbuild` appears in `THIRD-PARTY-NOTICES.txt`.
  - `test_editor_assets_are_offline`: for each `*.js` and `*.css` in `EDITOR`, `re.findall(r"https?://[^\s\"'<>)]+", text)` minus URLs starting `http://www.w3.org/` is empty.
  - `test_bundle_under_budget`: `codemirror.min.js` is under `700 * 1024` bytes.
  - `test_thanks_credits_codemirror`: `THANKS` contains `* CodeMirror (https://codemirror.net, MIT): source editor of the techdoc Add page`.
  - `test_techdoc_requires_0_10`: `theme.json["kb4it"] == ">=0.10.0"`.
- [ ] **Step 2: Run** `./scripts/devel/test.sh tests/core/test_editor_assets.py -v`. Expected: FAIL (missing files).
- [ ] **Step 3: Write `package.json`** with exact versions (no `^`/`~`) of `@codemirror/{state,view,commands,language,search,autocomplete,lint,lang-markdown,lang-yaml}`, `@lezer/highlight` and `esbuild`; `"private": true`. Run `npm install` once to produce `package-lock.json`. Add `scripts/devel/editor/node_modules/` to `.gitignore`.
- [ ] **Step 4: Write `entry.js`**: `export const cm = { ... }` with the names above, imported from their packages. No `basicSetup`, no `@codemirror/language-data`.
- [ ] **Step 5: Write `build.sh`** (`set -euo pipefail`, model: `scripts/devel/fetch_render_assets.sh`): `npm ci`; `npx esbuild entry.js --bundle --minify --format=iife --global-name=KB4ITEditor --legal-comments=eof --metafile=meta.json --outfile=$DEST/codemirror.min.js`; a `node -e` snippet that reads `meta.json`, takes the package of each input path under `node_modules/`, and writes `THIRD-PARTY-NOTICES.txt` (package, version, its `LICENSE` file text) and `VERSIONS` (`<package> <version>` sorted, plus `esbuild <version>`); copy `node_modules/@codemirror/view/LICENSE` to `$DEST/LICENSE`; print the size and exit 1 above 700 KB.
- [ ] **Step 6: Run** `scripts/devel/editor/build.sh`. If `test_editor_assets_are_offline` then finds a URL inside the bundle (for example a doc link in a minified error message), strip it in `build.sh` with a post-build replacement and say so in a comment; never weaken the test.
- [ ] **Step 7: Edit `THANKS`, `theme.json`** (`"kb4it": ">=0.10.0"`), and `check_wheel_themes.py` (also fail when `kb4it/resources/editor/codemirror.min.js` is missing from the wheel, same style as `has_offline_help`).
- [ ] **Step 8: Run** `./scripts/devel/test.sh tests/core/test_editor_assets.py -v`, `./scripts/devel/check_themes.sh`, and `uv build --wheel && python scripts/devel/check_wheel_themes.py` (offline help must be built first, see `RELEASING.md`). Expected: all pass.
- [ ] **Step 9: CHANGELOG** (`### Added`: ED-01, ED-03) and commit: `git commit -m "build(editor): vendor a codemirror 6 bundle for the techdoc add page"`.

### Task 2: Deploy the editor only where it is used (ED-02)

**Files:**
- Modify: `kb4it/services/deployer.py:25, 218, 236-251`
- Test: `tests/core/test_deployer_editor.py`

**Interfaces:**
- Produces: `EDITOR_REF = re.compile(r'(?:src|href)="[^"]*resources/editor/')`; `Deployer.deploy_editor_assets(self) -> None`, called right after `self.deploy_render_assets()`.

- [ ] **Step 1: Write the failing tests:**
  - `test_deploy_copies_when_a_page_loads_the_editor` and `test_deploy_removes_stale_folder`: unit level, with a `_Backend` stub like `tests/core/test_build_failures.py:63-80` (`get_path("target")`). Write `target/add.html` containing `<script src="resources/editor/kb4it-editor.js">`, call `deploy_editor_assets()`, assert `target/resources/editor/codemirror.min.js` exists; replace the page with plain HTML, call again, assert the folder is gone.
  - `test_text_naming_the_folder_does_not_count`: a page whose text is `resources/editor/` (no `src=`/`href=`) deploys nothing.
  - `test_techdoc_build_deploys_editor` and `test_blog_build_has_no_editor`: full builds with `write_repo` / `run_kb4it` as in `tests/core/test_render_assets.py:26-30`; techdoc target has `resources/editor/codemirror.min.js`, blog target has no `resources/editor`. The techdoc test fails until Task 5 adds the script tags, so mark it `xfail(strict=True, reason="Task 5")` here and remove the mark in Task 5.
  - `test_log_event`: `run_kb4it("-L", "DEBUG", "build", cfg, ...)` of a blog site has `[DEPLOYER] EDITOR_ASSETS deployed=False` in `result.stdout` (pattern: `tests/themes/test_blog.py:102`).
- [ ] **Step 2: Run** `./scripts/devel/test.sh tests/core/test_deployer_editor.py -v`. Expected: FAIL (no method).
- [ ] **Step 3: Implement** `deploy_editor_assets` by mirroring `deploy_render_assets` with `EDITOR_REF` and folder `editor`. Generalise `_page_uses_render(path)` into `_page_matches(path, pattern)` rather than duplicating it.
- [ ] **Step 4: Run** the test file and `tests/core/test_render_assets.py`. Expected: PASS (xfail for the techdoc build).
- [ ] **Step 5: Commit**: `feat(deployer): deploy the editor assets only to sites that load them`.

### Task 3: Frontmatter parser, quoting and name rules (ED-08 parser, D-6)

**Files:**
- Create: `kb4it/resources/editor/kb4it-frontmatter.js`, `tests/fixtures/editor/names.json`, `tests/js/__init__.py`, `tests/js/nodejs.py`, `tests/js/test_frontmatter.py`, `tests/core/test_editor_names.py`
- Modify: `tests/core/test_editor_assets.py` (`EDITOR_FILES` gains `kb4it-frontmatter.js`)

**Interfaces:**
- Produces, on `var KB4ITFrontmatter` (no DOM, ES2017):
  - `bounds(text) -> {open: bool, close: int|null, start: int, end: int}`: build rule; `start`/`end` are offsets of the frontmatter content.
  - `parse(text) -> {ok: bool, reason: string|null, props: [{key, values: string[], complex: bool, line: int, from: int, to: int}]}` (`line` 0-based, `from`/`to` offsets of the whole property, including continuation lines of a complex one).
  - `setValues(text, key, values) -> {from, to, insert}`: a single change; replaces the property's line, or inserts `Key: a, b\n` before the closing `---` for a new key; `values === null` removes the property line.
  - `quote(value) -> string`: ED-08 quoting rule.
  - `validFilename(s) -> string`, `slugify(s) -> string`, `firstHeading(body) -> {title, line}|null`.
  - `fileName(text, category) -> string`: `slugify(title) + ".md"`, or `category + ".md"` when there is no title or the slug is empty.
- Produces: `tests/js/nodejs.py`: `NODE = shutil.which("node")`; `run_node(calls: list[tuple[str, list]]) -> list`, which loads `kb4it-frontmatter.js` with `vm.runInNewContext` in one `node` process, applies `KB4ITFrontmatter[name](...args)` to each call and returns the JSON results. `tests/js/test_frontmatter.py` has `pytestmark = pytest.mark.skipif(NODE is None, reason="node not installed")`.

- [ ] **Step 1: Write `names.json`**: `{"valid_filename": [[input, expected], ...], "slugify": [[input, expected], ...]}` with at least: plain, spaces, `john's portrait in 2004.jpg`, `...`, `???`, `.hidden`, `..`, accents (`Café`), CJK (`日本語`), Cyrillic, digits, `_`, `-`, combining marks (`é`), emoji, tab, leading/trailing spaces. Fill `expected` by running the Python functions (`kb4it.core.files.valid_filename`, `kb4it.core.util.slugify`) once.
- [ ] **Step 2: Write the failing tests.**
  - `tests/core/test_editor_names.py::test_python_matches_shared_table`: every pair holds for the Python functions (guards the table itself).
  - `tests/js/test_frontmatter.py`:
    - `test_js_matches_shared_table`: same pairs through `validFilename` and `slugify`.
    - `test_parse_line_forms` (parametrized): `Key:` -> `[]`; `Key: a` -> `["a"]`; `Key: a, b` -> `["a","b"]`; `Key: [a, b]` -> `["a","b"]`; `Key: "a: b"` -> `["a: b"]`; `Key: 'a: b'` -> `["a: b"]`.
    - `test_parse_complex`: `Tags:\n  - a\n  - b`, `Text: |\n  x`, `Map:\n  k: v`, `Ref: &a x` give `complex: true` and `values: []`, and the next property parses normally.
    - `test_quoted_comma_splits`: `Tag: "a, b"` -> `["a","b"]`.
    - `test_crlf_input`: the same document with `\r\n` gives the same keys and values as with `\n`.
    - `test_bounds_follow_the_build`: no leading `---` -> `reason == "missing_frontmatter"`; no closing -> `"missing_frontmatter_close"`; BOM first -> `"missing_frontmatter"`.
    - `test_quote_rule` (parametrized): quoted: `[x`, `]`, `{`, `}`, `&a`, `*a`, `!a`, `|a`, `>a`, `'a`, `"a`, `%a`, `@a`, `` `a ``, `- a`, `a: b`, `a #b`, `true`, `False`, `yes`, `NO`, `null`, `~`, `12`, `1.5`, `-3`; not quoted: `sap`, `a-b`, `a#b`, `SAP Basis`, `2026-10-22`. Quoted form is `"` + value with `\` and `"` backslash-escaped + `"`.
    - `test_set_values_round_trip` (parametrized over every line form and quoting case): applying `setValues(t, k, v)` then `parse(...)` gives `v` for `k`, and every other line of `t` is unchanged.
    - `test_set_values_new_key_before_close` and `test_set_values_remove`.
    - `test_first_heading_skips_code`: `# x` inside a ``` fence, a `~~~` fence and an indented block is skipped; mirrors `kb4it/core/documents.py:60-90`.
    - `test_file_name_fallback`: `# 日本語` with category `note` -> `note.md`; `# Disk full on SAP` -> `disk-full-on-sap.md`; no H1 -> `note.md`.
- [ ] **Step 3: Run** `./scripts/devel/test.sh tests/js tests/core/test_editor_names.py -v`. Expected: FAIL (file missing).
- [ ] **Step 4: Implement `kb4it-frontmatter.js`.** `validFilename`: trim, spaces to `_`, remove `/[^\p{L}\p{N}_.-]/gu`, strip leading dots; adjust the class until the shared table passes (Python `\w` is `str.isalnum()` plus `_`). `slugify`: `normalize("NFKD")`, drop non-ASCII, lower case, `/[^a-z0-9]+/g` to `-`, trim dashes. Work on a copy of the text with `\r\n` replaced by `\n` and map offsets back, or keep offsets in the original text; `setValues` must return offsets in the text it received.
- [ ] **Step 5: Run** the same tests. Expected: PASS. Also `node --check kb4it/resources/editor/kb4it-frontmatter.js`.
- [ ] **Step 6: Commit**: `feat(editor): add the frontmatter parser and name rules`.

### Task 4: Lint and completion logic (ED-05, ED-06 logic)

**Files:**
- Modify: `kb4it/resources/editor/kb4it-frontmatter.js`
- Test: `tests/js/test_frontmatter.py`

**Interfaces:**
- Consumes: `parse`, `bounds`, `firstHeading`, `validFilename`, `quote` (Task 3); `keys` is the `keys_json` object `{key: [{v, c}]}`.
- Produces:
  - `lint(text, keys) -> [{from, to, severity: "error"|"warning"|"info", reason, message}]`, `reason` one of `missing_frontmatter`, `missing_frontmatter_close`, `yaml_error`, `invalid_frontmatter`, `missing_h1_title`, `title_in_frontmatter_ignored`, `bad_property_name`, `bad_property_value`, `new_property`, `new_value`.
  - `complete(text, pos, keys) -> {from, options: [{label, insert, detail}]}|null`.

- [ ] **Step 1: Write the failing tests:**
  - `test_lint_reasons` (parametrized, one document per reason, assert the reason and severity from spec ED-06, with `yaml_error` for a syntax error such as `Key: [a`, and `invalid_frontmatter` for a frontmatter that is a plain scalar such as `just text`).
  - `test_lint_clean_document`: a skeleton-like document with known keys and values gives `[]`.
  - `test_lint_h1_rule_matches_python`: a `# x` only inside a fence gives `missing_h1_title`.
  - `test_lint_title_key_both_cases`: `Title:` and `title:` each give a warning.
  - `test_complete_property_names`: text `---\nCat` with cursor at end and `keys = {"Category": [...3 values], "Tag": [...]}` -> options include label `Category` with insert `Category: ` and detail `3 values`; a key already present is left out; `Title` is never offered.
  - `test_complete_values_by_use`: after `Category: ` -> labels ordered by `c` descending, detail `N documents`; after `Tag: a, ` the value `a` is left out; a value needing quotes is inserted quoted.
  - `test_complete_outside_frontmatter`: cursor in the body or after an unknown key -> `null`.
- [ ] **Step 2: Run** `./scripts/devel/test.sh tests/js -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `lint` and `complete`. YAML syntax checks are done by the editor's YAML tree in Task 6; here `yaml_error` covers what the line parser can see (unclosed `[` or quote, a line that is neither `Key: ...`, a continuation of a complex property, nor blank or a comment). `from`/`to` point to the offending line, or to `0..0` for document-level reasons.
- [ ] **Step 4: Run** the tests. Expected: PASS.
- [ ] **Step 5: Commit**: `feat(editor): add frontmatter lint and completion logic`.

### Task 5: CodeMirror replaces the textarea, browser test harness (ED-04)

**Files:**
- Create: `kb4it/resources/editor/kb4it-editor.js`, `kb4it/resources/editor/kb4it-editor.css`, `tests/browser/__init__.py`, `tests/browser/conftest.py`, `tests/browser/test_add_editor.py`, `tests/themes/test_techdoc_add.py`
- Modify: `kb4it/resources/themes/techdoc/templates/PAGE_ADD.tpl`, `kb4it/resources/themes/techdoc/framework/kb4it/css/screen.css:1212` (drop textarea-only rules), `.github/workflows/kb4it.yml`, `pyproject.toml` (`markers = ["browser: needs Playwright and Chromium"]`), `tests/core/test_editor_assets.py`, `tests/core/test_deployer_editor.py` (remove the xfail)

**Interfaces:**
- Consumes: `KB4ITEditor.cm` (Task 1), `KB4ITFrontmatter` (Tasks 3, 4).
- Produces, on `KB4ITEditor`:
  - `open(cat)`, `copy(cat)`; `views` (`{cat: EditorView}`, also used by tests); `text(cat) -> string`; `dirty(cat) -> bool` (doc differs from the text at creation or last save).
  - `extensions(cat) -> Extension[]`, the place where Tasks 6, 8 add their extensions.
  - Template keeps the global names `kbAddOpen` and `kbAddCopy` as thin wrappers so card buttons do not change.
- Produces, in `tests/browser/conftest.py`: `pytest.importorskip("playwright.sync_api")`; session fixture `site` (techdoc build with `tmp_path_factory`, `write_repo` and `run_kb4it`; four documents: two with `Category: Note`, one with `Category: Procedure` and `Tag: sap, linux`, one with `Tag: x<b>y</b>`, a value the build accepts because `valid_filename` leaves `xbyb`, so it reaches `keys_json` as HTML-looking text); fixture `add_page` (Chromium, `context.route("**/*", lambda r: r.continue_() if r.request.url.startswith("file://") else r.abort())`, records any aborted request in `page.aborted`, opens `site / "add.html"`); helper `editor_text(page, cat)` = `page.evaluate("c => KB4ITEditor.text(c)", cat)`.

- [ ] **Step 1: Write the failing Python tests** in `tests/themes/test_techdoc_add.py` (built techdoc site):
  - `test_add_page_loads_editor_files_in_order`: `add.html` contains, in this order, `resources/editor/codemirror.min.js`, `kb4it-frontmatter.js`, `kb4it-editor.js` as `<script src=...>` without `type="module"`, and a `<link rel="stylesheet" href="resources/editor/kb4it-editor.css">`.
  - `test_editor_hosts_are_divs`: `<div id="kb-editor-note"` exists, no `<textarea id="kb-editor-`.
  - `test_keys_json_has_no_raw_lt`: the `kb-add-keys` script body has no `<`.
  - `test_hostile_property_names_stay_escaped`: a document with property name `Bad</script>` builds (or is rejected by `bad_property_name`); either way `add.html` has exactly the expected number of `</script>` closings.
  - `test_editor_js_never_uses_innerhtml`: `kb4it-editor.js` and `kb4it-frontmatter.js` contain no `innerHTML`, `outerHTML`, `insertAdjacentHTML` or `document.write`.
- [ ] **Step 2: Write the failing browser tests** in `tests/browser/test_add_editor.py`, all `@pytest.mark.browser`:
  - `test_no_network_requests`: after opening the page and the Note modal, `page.aborted == []`.
  - `test_open_each_category` (parametrized over the eight categories): click its Create button; the editor text starts with `---\n`, contains `Date: <today>` and `# <Cat> title`.
  - `test_type_and_undo`: type `Hello` at the end; text ends with `Hello`; `Control+z` restores the skeleton.
  - `test_tab_inserts_four_spaces`, `test_enter_continues_list` (`- a` + Enter -> `- a\n- `).
  - `test_reopen_keeps_edits_on_cancel`: edit, close, Create again, dismiss the confirm; text and undo still there. Accepting it restores the skeleton.
  - `test_dark_background_switches_theme`: set `document.body.style.background = '#111'` before opening; the editor root has class `kb4it-cm-dark`.
- [ ] **Step 3: Run** `./scripts/devel/test.sh tests/themes/test_techdoc_add.py -v` and `uv run --no-project --with pytest --with playwright ... python -m pytest -m browser tests/browser -v` (first `uv run --with playwright playwright install chromium`). Expected: FAIL.
- [ ] **Step 4: Implement.** Template: script and link tags, `<div id="kb-editor-${cat['id']}" class="kb-editor-host">`, inline script reduced to the JSON blocks and the two wrappers. `kb4it-editor.js`: move `timestamp`, `buildTemplateMd` and the word cloud builder from the template (word cloud rewritten with `textContent` only); `open(cat)` creates the view on first open, asks `"Discard your changes and start again?"` on reopen when `dirty(cat)`; extensions per spec ED-04 (`indentUnit` of four spaces; Tab via a keymap that inserts four spaces; `Escape` then `Tab` leaves, which is CodeMirror's default tab-focus behaviour, keep it); dark detection copied from `kb4it-render.js:pageIsDark` and applied as a class on `.cm-editor` plus a `Compartment` for the highlight style. CSS: tokens on `.kb4it-cm` and `.kb4it-cm-dark`.
- [ ] **Step 5: CI job** in `kb4it.yml`: `browser` on `ubuntu-latest`, Python 3.11, `uv run --no-project --with pytest --with playwright <the deps of test.sh> playwright install --with-deps chromium`, then `python -m pytest -m browser tests/browser`. The OS matrix stays as is (browser tests skip there without Playwright).
- [ ] **Step 6: Run** the Python suite (`./scripts/devel/test.sh`), the browser suite, and `./scripts/devel/check_themes.sh`. Expected: PASS, including the un-xfailed techdoc deploy test.
- [ ] **Step 7: CHANGELOG** (`### Changed`: ED-04) and commit: `feat(techdoc): replace the add page textarea with a codemirror editor`.

### Task 6: Completion and lint in the editor (ED-05, ED-06)

**Files:**
- Modify: `kb4it/resources/editor/kb4it-editor.js`, `kb4it-editor.css`
- Test: `tests/browser/test_add_editor.py`

**Interfaces:**
- Consumes: `KB4ITFrontmatter.complete`, `KB4ITFrontmatter.lint`, `KB4ITEditor.extensions(cat)`, `KB_KEYS`.
- Produces: `KB4ITEditor.diagnostics(cat) -> [{reason, severity}]` (also used by Tasks 8 and 10).

- [ ] **Step 1: Write the failing browser tests:**
  - `test_complete_property_then_value`: in the Note editor, put the cursor on a new frontmatter line, type `Cat`, press Enter on the completion; line is `Category: `; type `N`, accept; line is `Category: Note`.
  - `test_free_values_allowed`: type `Category: Brandnew` and Escape; text keeps it; diagnostics include `new_value` (info).
  - `test_missing_h1_then_fixed`: delete the H1 line; `diagnostics` has `missing_h1_title`; type `# T`; it is gone.
  - `test_yaml_syntax_error`: `Tag: [a` gives `yaml_error`.
- [ ] **Step 2: Run** the browser tests. Expected: FAIL.
- [ ] **Step 3: Implement**: `autocompletion({override: [source]})` where `source(ctx)` calls `complete(doc, ctx.pos, KB_KEYS)` and maps to CodeMirror options; `linter(view => lint(...).concat(yamlTreeErrors(view)))` plus `lintGutter()`, where `yamlTreeErrors` walks `syntaxTree(view.state)` inside the frontmatter and reports `⚠` error nodes as `yaml_error`, de-duplicated with the line-parser ones.
- [ ] **Step 4: Run** the browser tests. Expected: PASS.
- [ ] **Step 5: Commit**: `feat(editor): complete and check frontmatter properties`.

### Task 7: Properties pane (ED-07)

**Files:**
- Modify: `PAGE_ADD.tpl` (right pane label `Properties`, container `kb-props-<cat>`), `kb4it-editor.js`, `kb4it-editor.css`
- Test: `tests/browser/test_add_editor.py`

**Interfaces:**
- Consumes: `KB4ITFrontmatter.parse`, `setValues`, `validFilename`; `KB_KEYS`.
- Produces: `KB4ITEditor.renderPane(cat)`, pane DOM with stable test hooks: row `[data-key="<key>"]`, chip `.kb-chip[data-value="<v>"]` with a remove button `.kb-chip-remove`, value input `.kb-value-input`, property selector `.kb-add-prop`, complex rows `.kb-prop-complex`.

- [ ] **Step 1: Write the failing browser tests:**
  - `test_add_value_from_form`: in the `Tag` row (add the property via `.kb-add-prop` if absent), type `sap`, Enter; editor text has the line `Tag: sap`.
  - `test_remove_chip_changes_text`: from `Tag: sap, linux`, remove the `linux` chip; line becomes `Tag: sap`; `Control+z` in the editor brings it back.
  - `test_comma_refused`: typing `a,b` in a value input shows the message `A value cannot contain a comma: KB4IT splits values on commas.` and adds no chip.
  - `test_new_property_name_checked`: "New property..." with `???` is refused; with `Owner` it appends `Owner: ` before the closing `---`.
  - `test_complex_property_read_only`: a `Tags:\n  - a` block shows `.kb-prop-complex` with the text `Edit this property in the text` and no inputs.
  - `test_cloud_click_adds_value`: expanding the cloud of `Category` and clicking `Procedure` sets the line to include `Procedure`.
  - `test_hostile_values_stay_text`: add the `x<b>y</b>` value of the site fixture as a `Tag` chip, open its completion and its cloud; each shows the literal text `x<b>y</b>`, and `page.locator("#modal-add-note b").count() == 0`.
- [ ] **Step 2: Run**. Expected: FAIL.
- [ ] **Step 3: Implement**: every form action dispatches one transaction from `setValues`; pane built with `createElement`, `textContent`, `setAttribute` only.
- [ ] **Step 4: Run**. Expected: PASS.
- [ ] **Step 5: CHANGELOG** (`### Added`: ED-07) and commit: `feat(editor): edit frontmatter properties in a form`.

### Task 8: Sync from text to form (ED-08)

**Files:**
- Modify: `kb4it-editor.js`
- Test: `tests/browser/test_add_editor.py`

**Interfaces:**
- Consumes: `renderPane(cat)` (Task 7), `diagnostics(cat)` (Task 6).

- [ ] **Step 1: Write the failing browser tests:**
  - `test_text_edit_updates_form`: type `, linux` at the end of `Tag: sap`; after 400 ms the `Tag` row has chips `sap` and `linux`.
  - `test_form_read_only_on_error`: break the closing `---`; after 400 ms the pane shows the error reason and its inputs are disabled; fixing it re-enables them.
- [ ] **Step 2: Run**. Expected: FAIL.
- [ ] **Step 3: Implement**: an `EditorView.updateListener` that, on `docChanged`, debounces 300 ms and calls `renderPane(cat)`; the pane is read-only while `diagnostics(cat)` has any of the frontmatter errors (`missing_frontmatter`, `missing_frontmatter_close`, `yaml_error`, `invalid_frontmatter`).
- [ ] **Step 4: Run**. Expected: PASS.
- [ ] **Step 5: Commit**: `feat(editor): keep the property form in sync with the text`.

### Task 9: Toolbar (ED-09)

**Files:**
- Modify: `PAGE_ADD.tpl` (toolbar container `kb-toolbar-<cat>` above the host), `kb4it-editor.js`, `kb4it-editor.css`
- Test: `tests/browser/test_toolbar.py`

**Interfaces:**
- Produces: `KB4ITEditor.ACTIONS`: `{bold, italic, code, link, h2, h3, h4, ul, ol, task, quote, codeblock, hr, table, image, note, tip, warning, danger, mermaid, math, mathblock}`, each `function(view)`; buttons carry `data-action="<name>"`, a UIkit icon or text label, and `title` with the shortcut. Keymap: `Mod-b`, `Mod-i`, `Mod-e`, `Mod-k`.

- [ ] **Step 1: Write the failing test** `test_toolbar_action` parametrized over every action, twice (empty selection at the end of the body; selection of the word `word` on its own line). Expected texts:
  - Inline wraps: `**word**`, `*word*`, `` `word` ``, `[word](url)` with `url` selected; with no selection the template is inserted and its placeholder (`text`, `code`) selected.
  - Headings and blocks prefix the line(s): `## `, `### `, `#### `, `- `, `1. `, `- [ ] `, `> `; code block wraps in ```` ``` ```` fences on their own lines; `hr` inserts `\n---\n` on its own line (never inside the frontmatter: the action is disabled when the cursor is in it).
  - `table`: `| Column 1 | Column 2 | Column 3 |\n| --- | --- | --- |\n|  |  |  |\n|  |  |  |`.
  - `image`: `![alt](path)` with `path` selected.
  - Admonitions: `!!! note "Title"\n    Text of the note, indented by four spaces.` (and `tip`, `warning`, `danger`); with a selection, the selected lines become the indented body.
  - `mermaid`: a ```` ```mermaid ```` fence with `graph TD\n    A --> B`.
  - `math`: `$word$` / `$x$`; `mathblock`: `$$\nword\n$$` on its own lines.
  - `test_shortcuts`: `Control+b` on a selection gives `**word**`.
- [ ] **Step 2: Run** `pytest -m browser tests/browser/test_toolbar.py`. Expected: FAIL.
- [ ] **Step 3: Implement** the actions with `view.dispatch(view.state.changeByRange(...))` so multiple selections and undo work.
- [ ] **Step 4: Run**. Expected: PASS.
- [ ] **Step 5: CHANGELOG** (ED-09) and commit: `feat(editor): add a toolbar for markdown and kb4it elements`.

### Task 10: Save, download and copy (ED-10)

**Files:**
- Modify: `PAGE_ADD.tpl` (Save button `#kb-save-<cat>`, note text), `kb4it-editor.js`
- Test: `tests/browser/test_save.py`

**Interfaces:**
- Consumes: `KB4ITFrontmatter.fileName`, `KB4ITEditor.diagnostics`, `dirty`.
- Produces: `KB4ITEditor.save(cat) -> Promise<"saved"|"downloaded"|"cancelled">`, `KB4ITEditor.download(cat)`.

- [ ] **Step 1: Write the failing browser tests:**
  - `test_download_path` (delete `window.showSaveFilePicker` before load): click Save; `page.expect_download()` gives file name `<slug>.md`; its bytes equal the editor text encoded UTF-8 plus `\n` when missing.
  - `test_save_writes_lf`: text set through `view.dispatch` with `\r\n` lines; the downloaded file has no `\r`.
  - `test_save_picker_stub`: an init script stubs `showSaveFilePicker` to record its options and return a handle whose `createWritable()` collects writes; assert `suggestedName`, `id == "kb4it-source"`, `types[0].accept == {"text/markdown": [".md"]}`, the written text, the button label `Save (<name>)`, and that a second Save reuses the handle (stub called once).
  - `test_picker_cancel_offers_download`: the stub rejects with `AbortError`; a confirm offers the download; accepting downloads.
  - `test_errors_confirm`: with no H1, Save shows `This document has 1 error and will not build. Save anyway?` (plural `errors` for more than one); dismissing saves nothing.
  - `test_unsaved_changes_prompt`: edit, then close the modal; a confirm appears; after a save, closing does not ask. `beforeunload` is registered while any category is dirty.
  - `test_page_note_rewritten`: the old sentence "it cannot create files for you" is gone; the new note says the page saves or downloads the file and the user puts it in the `source` folder and rebuilds.
- [ ] **Step 2: Run**. Expected: FAIL.
- [ ] **Step 3: Implement** per spec ED-10; `Blob` type `text/markdown;charset=utf-8`; `URL.revokeObjectURL` after the click. Copy writes the same normalised text.
- [ ] **Step 4: Run**. Expected: PASS.
- [ ] **Step 5: CHANGELOG** (ED-10) and commit: `feat(editor): save or download the new document`.

### Task 11: Documentation and final checks (ED-11, ED-12)

**Files:**
- Modify: `help/source/reference-theme-techdoc.md`, `AGENTS.md`, `README.md`, `CHANGELOG.md`
- Create: `help/source/howto-write-document-editor.md` (`DocType: How-to guide`, frontmatter like `help/source/howto-write-documents.md`)

- [ ] **Step 1: Write the docs** per spec ED-11. The reference page covers the editor, completion and lint (with the reason table), the property pane, the toolbar, saving and browser support (Chromium: save dialog; Firefox and Safari: download). `AGENTS.md`: `kb4it/resources/editor/`, `scripts/devel/editor/build.sh`, `deploy_editor_assets()`, the bundle and KB4IT code split (D-3), the browser test command. `README.md`: one line in the techdoc features.
- [ ] **Step 2: Run** `kb4it verify help/config/repo.json`, `./scripts/devel/test.sh`, the browser suite, `./scripts/devel/check_themes.sh`, `uv run --no-project python scripts/devel/smoke_build.py`. Expected: all pass. Check by hand once in Firefox from `file://` that Save downloads.
- [ ] **Step 3: Commit**: `docs: describe the techdoc markdown editor`.

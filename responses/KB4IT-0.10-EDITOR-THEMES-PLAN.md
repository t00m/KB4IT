---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-23 08:40
DocType: How-to guide
OS: Linux, macOS, Windows
Product: KB4IT
Scope: Development
Status: Draft
Tag: implementation-plan, editor, theme, configuration
Topic: Architecture, Development
---

# KB4IT 0.10 editor in every theme: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the techdoc Add page and its Markdown editor available to every theme, turned on and off with `"editor"` in `repo.json`.

**Architecture:** The editor script drops UIkit and uses a native `<dialog>`, its own toasts and inline SVG icons. The page builder moves from techdoc into a core `AddPageMixin` on `Builder`, with a shared dialog template, a common cards template, and skeleton sets looked up in the repository overrides, then the theme, then common. Each bundled theme calls `create_page_add()` and links to `add.html` when `var['editor']` is true.

**Tech Stack:** Python, Mako, plain ES2017 classic scripts, CodeMirror 6 bundle (unchanged), pytest, Playwright with Chromium.

**Spec:** `responses/KB4IT-0.10-EDITOR-THEMES-SPEC.md` (ET-xx, D-x). The earlier `responses/KB4IT-0.10-EDITOR-SPEC.md` (ED-xx) still binds everything not changed here.

## Global Constraints

- All constraints of the ED plan stay: offline, classic scripts, no `innerHTML` for document data, `encoding="utf-8"` on every text read or write, JSON in `<script>` with `<` as `<`, no Python module over 600 lines.
- No `UIkit` reference and no `uk-` class anywhere in `kb4it/resources/editor/*.js`.
- `KB4ITEditor` and `KB4ITFrontmatter` stay the only globals the editor scripts define.
- Element ids of the dialog stay: `modal-add-<cat>`, `kb-editor-<cat>`, `kb-toolbar-<cat>`, `kb-props-<cat>`, `kb-save-<cat>`, `kb-add-keys`, `kb-add-skeletons`.
- Category id pattern: `^[a-z][a-z0-9-]*$`.
- Exact texts: `repo.json 'editor' must be true or false`; "Add document" (page title and link text in techdoc, blog, bookshelf); apphelp label `add` = "Add a page".
- Log events: `[BUILDER] ADD_PAGE enabled=<bool> skeletons=<overrides|theme|common> categories=<n>`, `[BUILDER] SKELETON_UNLISTED file=<name>`.
- techdoc behaviour does not change: every existing browser test keeps its assertion, only selectors move to the new markup.
- Each task updates `CHANGELOG.md` under `## [Unreleased]` where the user sees a change, with its ET IDs, and the documentation files its **Docs** line names (from the ET-12 tables).
- A new log event is documented in `help/source/reference-log-codes.md` in the task that adds it.
- Commits: one line, Conventional Commits, no trailers. Never push, never branch. No em dashes anywhere.

## Review Focus

1. **Turning the editor off after a build with it on**, incremental build: `add.html` and `resources/editor/` are gone and no page links to `add.html`. Test in Task 2 (`test_editor_off_removes_page_and_link`).
2. **Escape with unsaved edits**: one confirm; Cancel keeps the dialog open and the text; Escape inside the editor never closes it, in Chromium where `cancel` cannot always be prevented. Test in Task 1 (`test_escape_dirty_asks_once`, `test_escape_in_editor_keeps_dialog`).
3. **A broken override skeleton set** (bad id, listed file missing, invalid JSON): the build fails with a `ThemeError` that names the file, and an empty overrides folder falls through to the theme's set. Test in Task 3.
4. **apphelp with versions on**: `add.html` and `resources/editor/` sit in the version folder and the page loads its scripts. Test in Task 6 (`test_apphelp_versions_add_page`).
5. **Dark page in a theme without UIkit** (apphelp in dark mode): the dialog gets `kb-dialog-dark` and the toasts and cards keep readable contrast. Test in Task 7 (`test_dark_page_all_themes`).

---

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `kb4it/resources/editor/kb4it-editor.js` | Dialog, toasts, SVG icons, delegated buttons, `close()`, `notify()`, `init()` | 1 |
| `kb4it/resources/editor/kb4it-editor.css` | Dialog, panes, cards, toasts, buttons, light and dark | 1 |
| `kb4it/resources/editor/THIRD-PARTY-NOTICES.txt` | UIkit icon notice | 1 |
| `kb4it/resources/themes/techdoc/framework/kb4it/css/screen.css` | Loses the Add page and dialog rules | 1 |
| `kb4it/services/addpage.py` | `AddPageMixin`: `editor_enabled`, `create_page_add`, `editor_keys`, `skeleton_set` | 2, 3, 4 |
| `kb4it/services/builder.py` | `Builder` gains `AddPageMixin`; `var['editor']` | 2 |
| `kb4it/services/backend.py`, `kb4it/services/workflow.py` | `editor` validation at build and in `verify` | 2 |
| `kb4it/resources/common/templates/PAGE_ADD.tpl`, `EDITOR_DIALOGS.tpl` | Cards page and shared dialogs | 4 |
| `kb4it/resources/common/templates/skeletons/DOCUMENT-SKELETON.md` | Generic skeleton | 3 |
| `kb4it/resources/themes/techdoc/templates/skeletons/skeletons.json` | techdoc categories | 3 |
| `kb4it/resources/themes/techdoc/logic/techdoc_addpage.py` | Deleted | 4 |
| `kb4it/resources/themes/{blog,bookshelf}/...` | Build call, link, skeleton | 5 |
| `kb4it/resources/themes/apphelp/...` | `_emit` route, label, sidebar link, skeletons, `editor_keys` | 6 |
| `tests/browser/conftest.py` | Sites per theme, dialog helpers | 1, 7 |

---

### Task 1: Editor without UIkit (ET-01, ET-02, ET-03)

techdoc only. At the end the techdoc Add page works as before, with no UIkit in the editor.

**Files:**
- Modify: `kb4it/resources/editor/kb4it-editor.js`, `kb4it-editor.css`, `THIRD-PARTY-NOTICES.txt`
- Modify: `kb4it/resources/themes/techdoc/templates/PAGE_ADD.tpl`, `kb4it/resources/themes/techdoc/framework/kb4it/css/screen.css`, `kb4it/resources/themes/techdoc/logic/techdoc_addpage.py` (skeleton JSON shape only)
- Modify: `tests/browser/conftest.py`, `tests/browser/test_add_editor.py`, `tests/browser/test_save.py`, `tests/browser/test_toolbar.py`, `tests/core/test_editor_assets.py`, `tests/themes/test_techdoc_add.py`

**Interfaces:**
- Produces: `KB4ITEditor.open(cat)`, `KB4ITEditor.close(cat) -> bool` (true when closed), `KB4ITEditor.notify(message, status, timeout)`, `KB4ITEditor.init()` (binds the delegated listener once; called by the script on `DOMContentLoaded`, or at once if the document is already loaded).
- Produces: `kb-add-skeletons` JSON shape `{cat: {"name": str, "text": str}}`.
- Produces: button attributes `data-kb-open`, `data-kb-save`, `data-kb-copy`, `data-kb-close`, each with the category id.
- Produces, for later tasks: browser helpers in `tests/browser/conftest.py`: `open_dialog(page, cat)`, `close_dialog(page, cat)`, `dialog_open(page, cat) -> bool`, `TOAST = "#kb-toasts .kb-toast"`.

- [ ] **Step 1: Move the browser tests to the new markup first.** Replace every UIkit selector with the helpers: `.uk-open` becomes `dialog_open(page, cat)` (`document.getElementById('modal-add-'+cat).open`); `UIkit.modal(...).hide()` becomes a click on `[data-kb-close="<cat>"]`; `.uk-notification-message` becomes `TOAST`; `button[onclick="kbAddCopy('note')"]` becomes `[data-kb-copy="note"]`. Keep every assertion. Run `KB4IT_BROWSER_TESTS=required ... -m browser tests/browser`; expected: failures on the new selectors.

- [ ] **Step 2: Add the new tests** in `tests/browser/test_add_editor.py`:
  - `test_escape_dirty_asks_once`: type a character, press Escape on the dialog header; one `dialog` event with "You have unsaved changes. Close and lose them?"; dismiss; `dialog_open` is true and the character is still in the text.
  - `test_escape_in_editor_keeps_dialog`: focus the editor, press Escape twice; `dialog_open` is true and no confirm appeared.
  - `test_body_does_not_scroll_while_open`: `getComputedStyle(document.body).overflow == "hidden"` while open, restored after close.
  - `test_toolbar_icons_are_svg`: every `[data-action] svg` exists for bold, italic, code, link, ul, quote, hr, table, image; no element in the page has an attribute `uk-icon` inside `#kb-toolbar-note`.
  - `test_toast_copy`: Copy shows a `TOAST` with "Copied to clipboard" and class `kb-toast-success`.

  In `tests/core/test_editor_assets.py`, `test_editor_js_has_no_uikit`: no `UIkit` and no `uk-` in `kb4it-editor.js`; and `test_notices_name_uikit`: `THIRD-PARTY-NOTICES.txt` contains "UIkit" and "MIT".

- [ ] **Step 3: Implement** in `kb4it-editor.js`: `<dialog>` open with `showModal()`, `close(cat)` with the UNSAVED confirm, the Escape `keydown` handler on the dialog with `preventDefault()`, body `overflow: hidden` while any dialog is open, `notify()` with the `#kb-toasts` container, SVG icons with `createElementNS` (path data from UIkit 3 icons, MIT), `kb-*` classes on every created control, the delegated click listener in `init()`, skeleton title from `name`. Remove `beforehide` and every `UIkit` call.

- [ ] **Step 4: Update the templates and styles.** `PAGE_ADD.tpl`: each modal becomes `<dialog id="modal-add-${cat['id']}" class="kb-dialog-modal">`; buttons use the data attributes; the inline `<script>` with `kbAddOpen` goes. Cards keep UIkit (they are techdoc's page, not the editor). Move the "Add document page" and "Add page (PAGE_ADD.tpl)" rule blocks from `screen.css` into `kb4it-editor.css`, rename any `uk-` dependency to `kb-`, and add light and dark rules for `.kb-toast`, `.kb-btn`, `.kb-input`, `.kb-select`. `techdoc_addpage.py` writes `{"name": cat.capitalize(), "text": skeleton}`.

- [ ] **Step 5: Run** `./scripts/devel/test.sh -q` and the browser suite. Expected: all pass, the earlier 129 browser tests included.

- [ ] **Step 6: Commit** `refactor(editor): use a native dialog and drop UIkit from the editor`.

### Task 2: The `editor` setting (ET-04)

**Files:**
- Create: `kb4it/services/addpage.py`
- Modify: `kb4it/services/builder.py`, `kb4it/services/backend.py`, `kb4it/services/workflow.py` (verify), `kb4it/resources/themes/techdoc/theme.json`, `kb4it/resources/themes/techdoc/logic/theme.py`, `kb4it/resources/themes/techdoc/templates/HTML_HEADER_COMMON.tpl`
- Test: `tests/core/test_editor_setting.py`
- Docs: `help/source/reference-log-codes.md` (`[BUILDER] ADD_PAGE`), `help/source/reference-repo-json.md` (`editor` row)

**Interfaces:**
- Produces: `check_editor_setting(repo: dict) -> None` in `addpage.py` (raises `ConfigError` with the exact text), `AddPageMixin.editor_enabled(self) -> bool`, `var['editor']: bool` in `get_theme_var()`.
- Produces: `AddPageMixin.remove_stale_add_page(self) -> None`, used by Task 4's `create_page_add()`.

- [ ] **Step 1: Write the tests** in `tests/core/test_editor_setting.py`:
  - `test_editor_must_be_bool`: `"editor": "yes"` makes `kb4it build` exit non-zero with `repo.json 'editor' must be true or false` in the output, and `kb4it verify` lists the same text.
  - `test_default_comes_from_theme`: techdoc without the key builds `add.html`; blog without the key builds none.
  - `test_repo_overrides_theme`: techdoc with `"editor": false` builds no `add.html` and `index.html` has no `href="add.html"`.
  - `test_editor_off_removes_page_and_link`: build techdoc, set `"editor": false`, build again without `--force`; `add.html` and `resources/editor/` are gone and no `*.html` in the target contains `add.html`.
  - `test_add_page_log`: the build log has `[BUILDER] ADD_PAGE enabled=False` for blog.

- [ ] **Step 2: Run them**; expected: failures.

- [ ] **Step 3: Implement.** `AddPageMixin` in `addpage.py`; `class Builder(AddPageMixin, Service)` or the equivalent position in its bases. `editor_enabled()`: `repo["editor"]` when present, else `theme.get("editor") is True`. Call `check_editor_setting` in `Backend._validate_config` and in the verify problem list next to `load_settings`. techdoc `theme.json` gets `"editor": true`; its `build()` calls `build_page_add()` only when `editor_enabled()`, otherwise `remove_stale_add_page()`; its header link to `add.html` is wrapped in `% if var['editor']:`.

- [ ] **Step 4: Run** the new tests and the full suite; expected: pass.

- [ ] **Step 5: Commit** `feat(editor): turn the add page on or off with the editor setting`.

### Task 3: Skeleton sets (ET-05)

**Files:**
- Modify: `kb4it/services/addpage.py`
- Create: `kb4it/resources/common/templates/skeletons/DOCUMENT-SKELETON.md`, `kb4it/resources/themes/techdoc/templates/skeletons/skeletons.json`
- Test: `tests/core/test_skeleton_sets.py`
- Docs: `help/source/reference-log-codes.md` (`[BUILDER] SKELETON_UNLISTED`)

**Interfaces:**
- Produces: `AddPageMixin.skeleton_set(self) -> tuple[str, list[dict]]`: `source` is `"overrides"`, `"theme"` or `"common"`; each dict has `id`, `name`, `description`, `color`, `icon`, `text` (missing optional fields are `""`).
- Consumes: `self.srvbes.overrides_dir`, `runtime["theme"]["templates"]`, `ENV["GPATH"]["TEMPLATES"]`.

- [ ] **Step 1: Write the tests**, calling `skeleton_set()` on a builder set up the way `tests/core/test_themekit.py` sets one up:
  - `test_theme_set_with_json`: techdoc gives source `"theme"`, 8 categories in the order change, incident, meeting, note, post, procedure, report, task, with the names, colours, icons and descriptions now in `PAGE_ADD.tpl`.
  - `test_set_without_json`: a folder with `B-SKELETON.md` and `A-SKELETON.md` gives ids `a`, `b`, names `A`, `B`, empty descriptions.
  - `test_overrides_win_and_do_not_merge`: an overrides set with one skeleton gives exactly that one, source `"overrides"`.
  - `test_empty_overrides_fall_through`: an empty `overrides/templates/skeletons/` gives the theme's set.
  - `test_common_fallback`: a theme with no `skeletons/` gives source `"common"` and one category `document`.
  - `test_bad_id`, `test_listed_file_missing`, `test_invalid_json`: `ThemeError` whose message contains the path of `skeletons.json`.
  - `test_unlisted_file_logged`: an extra file gives `[BUILDER] SKELETON_UNLISTED file=EXTRA-SKELETON.md`.
  - `test_skeleton_text_utf8`: a skeleton with `ñ` and `日本` comes back unchanged.

- [ ] **Step 2: Run them**; expected: failures.

- [ ] **Step 3: Implement** `skeleton_set()` as specified in ET-05. `DOCUMENT-SKELETON.md`:

  ```markdown
  ---
  Date: YYYY-MM-DD
  Tag:
  ---

  # Title of the document

  Write here.
  ```

  Copy techdoc's `CATEGORIES` from `PAGE_ADD.tpl` into `skeletons.json` with the keys `id`, `name`, `description`, `color`, `icon`.

- [ ] **Step 4: Run** the tests; expected: pass.

- [ ] **Step 5: Commit** `feat(editor): look up skeleton sets in overrides, theme and common`.

### Task 4: Core Add page (ET-06, ET-07)

**Files:**
- Modify: `kb4it/services/addpage.py`
- Create: `kb4it/resources/common/templates/PAGE_ADD.tpl`, `kb4it/resources/common/templates/EDITOR_DIALOGS.tpl`
- Modify: `kb4it/resources/themes/techdoc/templates/PAGE_ADD.tpl`, `kb4it/resources/themes/techdoc/logic/theme.py`
- Delete: `kb4it/resources/themes/techdoc/logic/techdoc_addpage.py`
- Test: `tests/themes/test_techdoc_add.py`, `tests/core/test_add_page_core.py`
- Docs: `help/source/reference-theme-techdoc.md`, `kb4it/resources/themes/techdoc/README.md`

**Interfaces:**
- Consumes: `editor_enabled()`, `remove_stale_add_page()` (Task 2), `skeleton_set()` (Task 3).
- Produces: `AddPageMixin.create_page_add(self) -> None`; `AddPageMixin.add_page_html(self) -> str` (the rendered page body, used by apphelp in Task 6); `AddPageMixin.editor_keys(self) -> dict`.
- Produces: `var['page']` keys `categories`, `editor_dialogs`, `keys_json`, `skeletons_json`.

- [ ] **Step 1: Write the tests**:
  - `tests/themes/test_techdoc_add.py` keeps its tests, and adds `test_dialogs_from_shared_template`: `add.html` has 8 `<dialog` elements and exactly one `kb-add-keys` block.
  - `tests/core/test_add_page_core.py`:
    - `test_common_page_has_no_framework`: rendering the common `PAGE_ADD.tpl` gives no `uk-` class.
    - `test_hostile_category_text_escaped`: an overrides `skeletons.json` with `"name": "<b>x</b>"` and `"description": "</script>"` shows both as text in `add.html`.
    - `test_editor_keys_counts`: `editor_keys()` on the techdoc sample gives `{"v": "Note", "c": 2}` under `Category` for `ADD_DOCS`.
    - `test_system_page`: `add.md` has `Title` "Add document" and `SystemPage` "Yes".

- [ ] **Step 2: Run them**; expected: failures.

- [ ] **Step 3: Implement.** Move the body of `build_page_add()` into `create_page_add()` and `add_page_html()`; `editor_keys()` keeps today's counting. `EDITOR_DIALOGS.tpl` holds the CSS link, both JSON blocks, the dialogs from Task 1 and the three script tags. techdoc's `PAGE_ADD.tpl` reads `var['page']['categories']` instead of `CATEGORIES` and prints `editor_dialogs` once. Log `ADD_PAGE` with the source and count. Delete `techdoc_addpage.py` and its mixin from techdoc's `Theme`.

- [ ] **Step 4: Run** the full suite and the browser suite; expected: pass.

- [ ] **Step 5: Commit** `refactor(editor): build the add page in core for every theme`.

### Task 5: blog and bookshelf (ET-08, ET-09)

**Files:**
- Modify: `kb4it/resources/themes/blog/logic/theme.py`, `templates/HTML_FOOTER.tpl`, `theme.json`
- Create: `kb4it/resources/themes/blog/templates/skeletons/POST-SKELETON.md`
- Modify: `kb4it/resources/themes/bookshelf/logic/theme.py`, `templates/HTML_HEADER_COMMON.tpl`, `theme.json`
- Create: `kb4it/resources/themes/bookshelf/templates/skeletons/CHAPTER-SKELETON.md`
- Modify: `kb4it/resources/themes/apphelp/theme.json` (`kb4it` floor only)
- Test: `tests/themes/test_editor_themes.py`
- Docs: `help/source/reference-theme-blog.md`, `help/source/reference-theme-bookshelf.md`, `kb4it/resources/themes/blog/README.md`, `kb4it/resources/themes/bookshelf/README.md`

**Interfaces:**
- Consumes: `create_page_add()`, `var['editor']`.

- [ ] **Step 1: Write the tests** in `tests/themes/test_editor_themes.py`, parametrized over blog and bookshelf:
  - `test_on_builds_page_and_link`: `"editor": true` builds `add.html` with one dialog (`modal-add-post` for blog, `modal-add-chapter` for bookshelf), and `index.html` links to `add.html`.
  - `test_off_by_default`: no key, no `add.html`, no link.
  - `test_skeleton_keys`: the blog skeleton has `Author`, `Category: Post`, `Date`, `Tag`, `Topic`; the bookshelf one has `Author`, `Book`, `Part`, `Chapter`, `Date`, `Status`.
  - `test_kb4it_floor`: every bundled `theme.json` has `"kb4it": ">=0.10.0"`.

- [ ] **Step 2: Run them**; expected: failures.

- [ ] **Step 3: Implement**: `self.create_page_add()` in each `build()` after `create_page_search()`; the blog footer link "Add document" and the bookshelf plus icon button, both inside `% if var['editor']:`; the two skeletons (Date as `YYYY-MM-DD`, first heading `# Title of the post` / `# Title of the chapter`); floors to `>=0.10.0`.

- [ ] **Step 4: Run** the tests, `./scripts/devel/check_themes.sh` and `uv run --no-project python scripts/devel/smoke_build.py`; expected: pass.

- [ ] **Step 5: Commit** `feat(editor): add the editor page to the blog and bookshelf themes`.

### Task 6: apphelp (ET-10)

**Files:**
- Modify: `kb4it/resources/themes/apphelp/logic/theme.py`, `logic/apphelp_config.py` (label), `templates/HTML_BODY.tpl` (sidebar link)
- Create: `kb4it/resources/themes/apphelp/templates/skeletons/{TUTORIAL,HOWTO,REFERENCE,EXPLANATION}-SKELETON.md`, `skeletons.json`
- Test: `tests/apphelp/test_apphelp_editor.py`
- Docs: `help/source/reference-theme-apphelp.md`, `kb4it/resources/themes/apphelp/README.md`

**Interfaces:**
- Consumes: `add_page_html()`, `editor_keys()`, `editor_enabled()`, `remove_stale_add_page()`.

- [ ] **Step 1: Write the tests**:
  - `test_apphelp_add_page`: `"editor": true` gives `add.html` wrapped by apphelp's `HTML_BODY` (it has the `ah-sidebar` element) and four dialogs `modal-add-tutorial`, `modal-add-howto`, `modal-add-reference`, `modal-add-explanation`.
  - `test_apphelp_sidebar_link`: the sidebar of a content page links to `add.html` with the text "Add a page"; with a `labels.add` of "Nueva página" the text follows.
  - `test_apphelp_skeletons_pass_verify`: each skeleton, with its placeholders filled (Section, Order `100`, Summary, a Feature from the vocabulary), passes `kb4it verify` with `strict: true`.
  - `test_apphelp_editor_keys`: `editor_keys()` includes every vocabulary value, every `DocType` name and every `Layout` name, unused ones with `c == 0`.
  - `test_apphelp_versions_add_page`: with versions on, `<target>/<version>/add.html` and `<target>/<version>/resources/editor/kb4it-editor.js` exist.
  - `test_apphelp_off_by_default`.

- [ ] **Step 2: Run them**; expected: failures.

- [ ] **Step 3: Implement**: override `create_page_add()` to `_emit("add", "Add document", self.add_page_html())` when on, else `remove_stale_add_page()`; call it from `build()`; add `add` to `DEFAULT_LABELS` and the sidebar link; write the four skeletons with `DocType`, `Section`, `Order`, `Summary`, `Feature`, `Level`; override `editor_keys()` to add the allowed values with count 0.

- [ ] **Step 4: Run** the tests and the apphelp suite; expected: pass.

- [ ] **Step 5: Commit** `feat(editor): add the editor page to the apphelp theme`.

### Task 7: Browser tests on every theme (ET-11)

**Files:**
- Modify: `tests/browser/conftest.py`
- Create: `tests/browser/test_themes.py`
- Modify: `.github/workflows/kb4it.yml` only if the job command must change (it should not)

**Interfaces:**
- Consumes: the helpers from Task 1; `build_techdoc` and the build helpers in `tests/helpers.py`.
- Produces: a session fixture `theme_site(theme)` for `techdoc`, `blog`, `bookshelf`, `apphelp`, each built with `"editor": true` and two documents that share a property value.

- [ ] **Step 1: Write** `tests/browser/test_themes.py`, each test parametrized over the four themes:
  - `test_open_and_type`, `test_completion_offers_repo_value`, `test_properties_form_edits_text`, `test_save_downloads_file` (no `showSaveFilePicker`, as in `test_save.py`), `test_copy_toast`, `test_close_prompt`, `test_no_network_request` (the route records no request outside `file://`).
  - `test_dark_page_all_themes`: set the page background to `#111` before opening; the dialog has `kb-dialog-dark`; a toast's text and background contrast ratio is at least 4.5.

- [ ] **Step 2: Run** the browser suite; fix only test plumbing here. A failure in product code goes back to the task that owns it, as a fix commit with the task's scope.

- [ ] **Step 3: Commit** `test(editor): run the editor browser tests on every theme`.

### Task 8: Application documentation (ET-12)

The theme pages were updated in Tasks 4 to 6. This task covers the application pages and checks the whole set.

**Files:**
- Modify: `help/source/howto-write-document-editor.md`, `help/source/explanation-themes.md`, `help/source/howto-create-theme.md`, `help/source/howto-customize-templates.md`, `help/source/tips.md`, `help/source/index.md`, `README.md`, `AGENTS.md`, `CHANGELOG.md`
- Regenerate: `kb4it/resources/help/` with `scripts/help/build_offline.py`

- [ ] **Step 1: Write** each change in the "Application" table of ET-12:
  - `howto-write-document-editor.md`: intro for every theme; "Turn it on" (`"editor": true`, and `false` to remove it from techdoc); "Use your own skeletons" (`overrides/templates/skeletons/`, `skeletons.json` fields, no merging); dialog wording without UIkit.
  - `explanation-themes.md`: one line per bundled theme on whether the Add page is on by default.
  - `howto-create-theme.md`: `editor` in "Options in theme.json"; a section "Add the editor page" with `create_page_add()`, the `var['editor']` link, a `templates/skeletons/` set, and the `<!-- kb4it:theme-html -->` wrapping rule.
  - `howto-customize-templates.md`: replacing the skeletons; `PAGE_ADD.tpl` may be replaced, `EDITOR_DIALOGS.tpl` not; a 0.9.x `PAGE_ADD.tpl` override has no editor and should be deleted or rebased.
  - `tips.md`, `index.md`, `README.md`: drop "techdoc" from the editor lines and name the setting.
  - `AGENTS.md`: rewrite "Techdoc editor" as "Editor" with `AddPageMixin`, the shared templates, the skeleton lookup, no UIkit, and the new test files; drop `techdoc_addpage.py`; update the `templates/skeletons/` line of the theme layout.

- [ ] **Step 1b: Check** with `grep -rn "techdoc Add page\|techdoc only\|kbAddOpen\|uk-modal\|techdoc_addpage" help/source README.md AGENTS.md kb4it/resources/themes/*/README.md`; expected: no line left that describes the editor as techdoc-only or names removed code.

- [ ] **Step 2: Run** `uv run --no-project --with-requirements requirements.txt python -m kb4it.core.main verify help/config/repo.json`, the offline help build, `./scripts/devel/test.sh -q` (help and README tests included); expected: pass, and `git status` shows the regenerated help files.

- [ ] **Step 3: Commit** `docs: describe the editor setting and skeleton sets`.

---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-23 08:40
DocType: Reference
OS: Linux, macOS, Windows
Product: KB4IT
Scope: Development
Status: Draft
Tag: specification, editor, theme, configuration
Topic: Architecture, Documentation
---

# KB4IT 0.10 specification: the Markdown editor in every theme

## Overview

KB4IT 0.10.0 adds a Markdown editor to the techdoc Add page (`add.html`), defined in `KB4IT-0.10-EDITOR-SPEC.md` (ED-01 to ED-12). This specification makes the same page available to every bundled theme (techdoc, blog, bookshelf, apphelp) and to custom themes. A `repo.json` key turns it on or off.

The base is branch `0.10.0` at `c65db8e`. Requirement IDs are `ET-01`, `ET-02`, ...; the plan, commits and CHANGELOG refer to them. Everything in "Hard constraints" and "Conventions for all changes" of the ED spec still applies.

### What changes for the user

- A new `repo.json` key, `"editor": true | false`.
- techdoc keeps its Add page by default. blog, bookshelf and apphelp get one when `"editor": true` is set.
- The page offers one card per skeleton. Each theme ships skeletons that fit its own metadata, and a repository can replace them with its own.
- The editor works the same in every theme: completion, lint, the properties form, the toolbar, Save, Copy.

### Phases

| Phase | Name | IDs | Depends on |
|---|---|---|---|
| 1 | Editor without UIkit | ET-01 to ET-03 | none |
| 2 | Setting and core page | ET-04 to ET-07 | 1 |
| 3 | Themes | ET-08 to ET-10 | 2 |
| 4 | Tests and documentation | ET-11, ET-12 | all |

### Non-goals

- Editing existing documents, live preview, writing through `kb4it serve`: still out, as in the ED spec.
- Checking theme-specific metadata rules in the editor (for example apphelp's required `Summary`). `kb4it verify` and the build stay the authority.
- A per-theme look for the dialog. The dialog has one look, light or dark, in every theme.

## Phase 1: Editor without UIkit

Today `kb4it-editor.js` calls UIkit for the dialog, the notifications and the toolbar icons. bookshelf and apphelp do not load UIkit. The editor drops UIkit completely, so one code path serves every theme.

### ET-01 Native dialog

- Each category's dialog is a `<dialog>` element, opened with `showModal()`. It fills the viewport (`width: 100vw; height: 100vh; max-width: none; max-height: none; margin: 0`).
- Its id stays `modal-add-<cat>`. The ids `kb-editor-<cat>`, `kb-toolbar-<cat>`, `kb-props-<cat>` and `kb-save-<cat>` stay as they are.
- Closing goes through one function, `KB4ITEditor.close(cat)`. With unsaved edits it asks "You have unsaved changes. Close and lose them?"; Cancel keeps the dialog open.
- **Escape.** A `keydown` listener on the dialog calls `preventDefault()` on Escape, so the browser's own `cancel` never fires, then calls `close(cat)`. Escape inside the editor host does not reach that listener (it stops propagation, as today): it belongs to CodeMirror, and "Escape then Tab leaves the editor" keeps working.
- `KB4ITEditor.open(cat)` keeps its current rules: first open builds the view; a later open asks "Discard your changes and start again?" when the text was edited.
- The page body does not scroll while a dialog is open.

### ET-02 Notifications and icons

- `KB4ITEditor.notify(message, status, timeout)` shows a message in a fixed container `#kb-toasts` (`role="status"`, `aria-live="polite"`) that the script creates on first use. `status` is `"success"` or `"danger"`. Default timeout 5000 ms; the Copy message keeps 2000 ms. A click removes a message.
- The toolbar icons are inline SVG, built with `document.createElementNS`, never `innerHTML`. Path data is taken from the UIkit 3 icons the toolbar shows today (bold, italic, code, link, list, quote-right, minus, table, image), so techdoc looks the same. The UIkit MIT notice is added to `kb4it/resources/editor/THIRD-PARTY-NOTICES.txt`.
- No `uk-*` class is set by the script. Buttons, inputs and selects get `kb-*` classes styled in `kb4it-editor.css`.

### ET-03 Markup contract and styles

- Buttons carry data attributes instead of inline handlers: `data-kb-open="<cat>"`, `data-kb-save="<cat>"`, `data-kb-copy="<cat>"`, `data-kb-close="<cat>"`. `kb4it-editor.js` binds them with one delegated `click` listener on `document`. The global functions `kbAddOpen`, `kbAddSave` and `kbAddCopy` go away.
- The data blocks stay `<script type="application/json">` elements: `kb-add-keys` as today, and `kb-add-skeletons`, whose value per category becomes `{"name": <display name>, "text": <Markdown>}`. The title placeholder becomes `# <name> title`; for techdoc that is the same text as today.
- Every rule for the dialog, the panes, the cards and the toasts moves from techdoc's `screen.css` to `kb4it-editor.css`. The rules use only `kb-*` classes and must stay readable on a light and on a dark page. The dark look keys off the existing `pageIsDark()` check, which sets `kb-dialog-dark` on the dialog.

## Phase 2: Setting and core page

### ET-04 The `editor` setting

- `repo.json` key `editor`, `true` or `false`. Any other value is a `ConfigError` at build start (`repo.json 'editor' must be true or false`) and a problem line in `kb4it verify`.
- `theme.json` key `editor`, `true` or `false`, is the theme's default. A missing key means `false`. techdoc ships `"editor": true`; blog, bookshelf and apphelp do not set it.
- `Builder.editor_enabled()` returns `repo["editor"]` when set, otherwise the theme default (decision D-1).
- `get_theme_var()` adds `var["editor"]` (bool), so templates can show or hide the link to `add.html`.
- When the editor is off, the build writes no `add.html`, and an `add.html` left by an earlier build is removed from the target. The deployer already removes `resources/editor/` when no page loads it.
- Changing the key rebuilds every page, because the link appears in each page's navigation. This already happens: `repo.json` keys outside `NON_PAGE_KEYS` are in the core signature.
- Log: `[BUILDER] ADD_PAGE enabled=<bool> skeletons=<overrides|theme|common> categories=<n>`.

### ET-05 Skeleton sets

A skeleton set is a folder named `skeletons/` holding `<ID>-SKELETON.md` files and an optional `skeletons.json`.

- **Lookup.** The first of these folders that holds at least one `*-SKELETON.md` file is the set; sets are never merged:
  1. `<overrides>/templates/skeletons/` of the repository
  2. the theme's `templates/skeletons/`
  3. the common `kb4it/resources/common/templates/skeletons/`, which holds one generic `DOCUMENT-SKELETON.md`
- **`skeletons.json`** is a list of objects: `id` (required), `name`, `description`, `color`, `icon`. Its order is the order of the cards. `id` must match `^[a-z][a-z0-9-]*$`, because it ends up in element ids. Each `id` needs `<ID upper>-SKELETON.md` in the same folder. An unknown id, a missing file, a bad id or invalid JSON is a `ThemeError` that names the file. A skeleton file not listed is ignored, with `[BUILDER] SKELETON_UNLISTED file=<name>`.
- **Without `skeletons.json`**, each file is a category: `id` is the file name before `-SKELETON.md`, lower case; `name` is the id with its first letter in upper case; `description` is empty; the order is by id.
- `color` is a CSS colour used for the card's top border, and `icon` a UIkit icon name. Only techdoc's own template uses `icon`. Both are optional.
- The skeleton text is read with `encoding="utf-8"` and printed as is. The editor fills `Date` with today and replaces the first heading, as today.

### ET-06 Core Add page

- The page builder moves out of techdoc. A new mixin, `AddPageMixin` in `kb4it/services/addpage.py`, is part of `Builder`. It provides:
  - `create_page_add()`: builds `add.html` when `editor_enabled()` is true, or removes the stale page;
  - `editor_keys() -> dict`: the completion data `{Key: [{"v": value, "c": count}]}`, built as today from the repository's documents. Themes may override it.
  - `skeleton_set() -> (source, categories)`: implements ET-05.
- **Templates.** Two new common templates:
  - `PAGE_ADD.tpl`: the cards page, plain HTML with `kb-*` classes, no framework. A theme may replace it with its own `PAGE_ADD.tpl`, as techdoc does.
  - `EDITOR_DIALOGS.tpl`: the data blocks, the CSS link, one `<dialog>` per category and the three script tags. No theme replaces it. Every `PAGE_ADD.tpl` prints it once with `${var['page']['editor_dialogs'] | n}`.
- `var['page']` carries `categories` (the list from ET-05), `editor_dialogs` (rendered HTML), `keys_json` and `skeletons_json`. JSON inside `<script>` replaces `<` with `<`, as today.
- The page is a system page: `Title` "Add document", `SystemPage` "Yes".
- `techdoc_addpage.py` is deleted. techdoc's `PAGE_ADD.tpl` keeps its UIkit cards, icons and notes; its `CATEGORIES` move into `templates/skeletons/skeletons.json`. Its dialogs come from `EDITOR_DIALOGS.tpl`.

### ET-07 Custom themes

A custom theme gets the Add page by calling `self.create_page_add()` in `build()` and linking to `add.html` when `var['editor']` is true. Its `build_page()` must wrap theme-made pages (the `<!-- kb4it:theme-html -->` ones), as it already does for `search.html`. Nothing else is needed. Themes that do not call it never get the page, whatever `repo.json` says.

## Phase 3: Themes

### ET-08 blog

- `build()` calls `create_page_add()`.
- `HTML_FOOTER.tpl` shows an "Add document" link when `var['editor']` is true, next to the other site links.
- Skeleton set: `POST-SKELETON.md`, with the keys of the sample post: `Author`, `Category: Post`, `Date`, `Tag`, `Topic`.
- Uses the common `PAGE_ADD.tpl`.

### ET-09 bookshelf

- `build()` calls `create_page_add()`.
- `HTML_HEADER_COMMON.tpl` shows an icon button (a plus sign, inline SVG like its neighbours, title "Add document") when `var['editor']` is true.
- Skeleton set: `CHAPTER-SKELETON.md` with `Author`, `Book`, `Part`, `Chapter`, `Date`, `Status`.
- Uses the common `PAGE_ADD.tpl`.

### ET-10 apphelp

- `build()` adds the page through its own `_emit()`, so `build_page()` wraps it like the other theme pages: apphelp overrides `create_page_add()` to call the shared builder for the HTML, then `_emit("add", ...)`.
- A new label `add` ("Add a page") in `DEFAULT_LABELS`, translatable like the others. The sidebar shows it under the Topics link when the editor is on.
- Skeleton set: `TUTORIAL`, `HOWTO`, `REFERENCE` and `EXPLANATION` skeletons, each with `DocType` set and the required keys `Section`, `Order`, `Summary`, `Feature`, plus `Level`.
- `editor_keys()` adds the allowed values that no document uses yet: the `vocabulary` lists of `repo.json`, the four `DocType` names and the `Layout` names, each with count 0.
- With versions on, `add.html` and `resources/editor/` live in the version folder, like the other pages.

## Phase 4: Tests and documentation

### ET-11 Tests

- Python: the setting and its validation, `verify`, skeleton lookup and `skeletons.json` errors, stale `add.html` removal, the page in each theme, and the nav link on and off.
- Browser: the existing techdoc suite runs against the `<dialog>` markup. A shared subset (open, type, completion, properties form, Save with a download, Copy, close prompt, no network request, dark page) runs on all four themes.

### ET-12 Documentation

- `help/source/reference-repo-json.md`: the `editor` key.
- `help/source/howto-write-document-editor.md`: no longer techdoc-only; how to turn it on; how to replace the skeletons.
- Theme references and the theme authoring page: `theme.json` `editor`, skeleton sets, `create_page_add()` for custom themes.
- `AGENTS.md`, `README.md`, each theme's `README.md`, `CHANGELOG.md` under `## [Unreleased]`.
- The offline help in `kb4it/resources/help/` is regenerated with `scripts/help/build_offline.py`.

## Compatibility

- techdoc sites: no change in behaviour. The Add page stays on unless `"editor": false` is set.
- blog, bookshelf and apphelp sites: no change unless `"editor": true` is set.
- A repository override of techdoc's `PAGE_ADD.tpl` from 0.9.x still renders, but has no editor; the help says to delete it or base it on the new template.
- Every bundled `theme.json` requires `"kb4it": ">=0.10.0"`, since they call `create_page_add()`.

## Decisions

- **D-1 Default.** The theme decides the default (`theme.json`), `repo.json` overrides it. techdoc is on, the rest off, so no existing site changes. Same pattern as `search` and `feed`.
- **D-2 No UIkit in the editor.** One code path with a native `<dialog>` instead of an adapter with UIkit and plain versions. Two code paths would double the browser tests and drift apart.
- **D-3 Sets are not merged.** A repository that ships its own skeletons replaces the theme's set completely. Merging would make the order and the names unpredictable.
- **D-4 One shared dialog template.** Themes may replace the cards page but not the dialogs, so the markup contract of ET-03 has a single source.

## Related Topics

- `responses/KB4IT-0.10-EDITOR-SPEC.md`
- `responses/20261023_081000_EDITOR-FOR-ALL-THEMES-ANALYSIS.md`

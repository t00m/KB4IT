# Content blocks: code, tables, back-to-top, author tabs and collapsible notes (WP6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the document body comfortable to read: a copy button and language label on code, long code folded, wide tables scrolling and long tables with a sticky header, a back-to-top button after one screen, author tabs and collapsible notes styled like the rest of techdoc, and a help page that teaches both extensions.

**Architecture:** A new pure theme module, `techdoc_blocks.py`, rewrites the compiled body with lxml in `build_page`, next to `enhance_images`: it wraps code blocks and tables, adds the copy and "Show all" buttons, and inserts a print-only label in every author tab panel. CSS in `screen.css` and `print.css` styles the new markup; one small script, `blocks.js`, copies code, unfolds long blocks, shows the back-to-top button and opens notes for printing. The back-to-top link lives in `HTML_BODY.tpl`. The help gains one page and a line in the techdoc reference.

**Tech Stack:** Python 3.11, lxml, Mako, UIkit 3.21.13, `pymdownx.tabbed` / `pymdownx.details` (optional extra), pytest.

**Spec:** `docs/superpowers/specs/2026-10-24-document-quality-design.md`: D4 (author tabs, collapsible notes), D6 (print table), E2 (code), E3 (tables), E4 (back to top). Order: `docs/superpowers/specs/2026-10-24-open-items-design.md`, WP6.

## Global Constraints

- techdoc only, no core change. Run `python3 -m pytest tests/themes tests/help tests/core -q && scripts/devel/check_themes.sh` before every commit.
- No browser tests. A Playwright look goes in the response file when the user asks for it.
- `pymdown-extensions` stays optional: a repository without the extensions keeps building exactly as today. The enhancer never assumes the extension is installed.
- HTML stays W3C valid. Generated markup carries no `NAME :: START/END` comments (they are inside the body). New page block comments, if any, are paired.
- Print: no copy button, language label or "Show all" button; folded code prints in full; every author tab panel prints with its label as a bold line; collapsible notes print open; back-to-top is not printed (`kb-noprint`).
- JS is classic ES2017, no network, works from `file://`. Clipboard uses `navigator.clipboard` with the `execCommand` fallback.
- Comments one line, plain English, no em dash. One-line Conventional Commits, no trailers, never push, never branch.

## Review Focus

- **A page with no code, no table and no tabs:** the enhancer returns the HTML untouched (fast path), so ordinary documents pay nothing. Test in Task 1.
- **A `pre` that is not a code block:** Mermaid diagrams (`pre.mermaid`) are left alone, or the diagram would get a copy button. Test in Task 1.
- **Code with no language:** the bar still holds the copy button, with no label, and no empty label is printed. Test in Task 1.
- **A table inside a block that already scrolls:** never wrapped twice. Test in Task 1.
- **Tabs without JavaScript:** the radio and CSS mechanism of `pymdownx.tabbed` keeps working; our CSS must not hide the checked panel. Test in Task 3 by inspection of the selectors, and in Task 2 on the built HTML.
- **Print of a closed note:** `beforeprint` opens the notes and `afterprint` closes them again; without JS the note prints closed. Test the script is present in Task 3.
- **`check_themes.sh`:** it builds from a `git archive` of HEAD, so every new theme file must be committed with the code that imports it.

---

### Task 1: Content block enhancer

**Files:** create `kb4it/resources/themes/techdoc/logic/techdoc_blocks.py`; modify `kb4it/resources/themes/techdoc/logic/theme.py` (import and call after `enhance_images`); create `tests/themes/test_techdoc_blocks.py`.

**Interfaces:**
- `enhance_blocks(html: str) -> str`: parse the body fragment, rewrite it, return the HTML. Idempotent enough for one call.
- `LONG_CODE_LINES = 30`, `FOLDED_CODE_LINES = 20` module constants, used for the fold and the button label.
- Code block, for every `<pre>` that is not `pre.mermaid` and not already inside `.kb-code`:
  - wrapper `<div class="kb-code">` (plus `kb-code-long` when lines > 30);
  - bar `<div class="kb-code-bar">` with `<span class="kb-code-lang">python</span>` when the `code` child has `language-python` (also read `language-*` from the `pre` class and from a parent `div.highlight` or `div.codehilite`), then `<button type="button" class="kb-code-copy kb-noprint" aria-label="Copy code">` with the UIkit copy icon and the text `Copy`;
  - long blocks get `<button type="button" class="kb-code-show kb-noprint" data-lines="42">Show all 42 lines</button>` after the `pre`.
- Table, for every `<table>` not already inside `.kb-table`: `<div class="kb-table uk-overflow-auto">`, plus `kb-table-sticky` when the table has more than 15 body rows.
- Author tabs, for every `.tabbed-set` from `pymdownx.tabbed`: read `.tabbed-labels > label` and prepend `<p class="kb-tab-print">Label</p>` to the matching `.tabbed-block`, so print can show every panel with its label.

- [ ] Unit tests: code wrapper, language label, copy button; no label without a language; `pre.mermaid` untouched; 42-line block gets `kb-code-long` and `Show all 42 lines`, a 5-line block does not; table wrapper, `kb-table-sticky` at 16 rows and not at 15; tab labels inserted in order; text after a `pre` and after a `table` keeps its place; empty input returns unchanged.
- [ ] RED, implement, GREEN; run the theme test file; commit `feat(techdoc): wrap code blocks and tables and label author tabs`.

### Task 2: Integration with the build

**Files:** `tests/themes/test_techdoc_blocks.py` or `tests/themes/test_techdoc_page.py`; `theme.py` hook.

- Build a repo with `markdown.extensions` set to `pymdownx.tabbed` and `pymdownx.details` and `alternate_style: true`; a document with a Python fence, a 2-row table, a 16-row table and one tabbed set with Linux and Windows.
- Assert the built page has `kb-code`, `kb-code-lang`, `kb-code-copy`, `kb-table uk-overflow-auto`, `kb-table-sticky`, `tabbed-set`, the print labels and `<details class="note">`.
- Assert a second build does not double-wrap (`html.count('class="kb-code"') == code_fences`).
- [ ] RED, implement, GREEN; commit with Task 1 if the split is not clean.

### Task 3: Screen styles, print rules, script and back-to-top link

**Files:** create `kb4it/resources/themes/techdoc/framework/kb4it/js/blocks.js`; modify `.../css/screen.css`, `.../css/print.css`, `templates/HTML_HEADER_COMMON.tpl` (script tag), `templates/HTML_BODY.tpl` (back-to-top after `</main>`); tests in `tests/themes/test_techdoc_blocks.py` and `tests/themes/test_techdoc_page.py`.

- Screen CSS: code bar (dark, language small caps, copy at the right), folded code `max-height` for 20 lines with a fade, "Show all" button; `.kb-table` margin and sticky `thead th`; `.tabbed-set` as a UIkit-like tab bar with 10 label/panel pairs driven by `input:checked`; `details` (not `.kb-toc-panel`) as an admonition with a chevron; `.kb-totop` fixed bottom right, hidden until `.kb-totop-visible`; `.kb-tab-print` hidden on screen.
- Print CSS: hide `.kb-code-bar`, `.kb-code-show`, `.kb-totop`, `.tabbed-labels` and the radios; unfold `pre`; show every `.tabbed-block` with `.kb-tab-print`; show closed `details` content; release `.kb-table` overflow and sticky headers.
- `blocks.js`: copy (clipboard, fallback textarea, "Copied" for two seconds), fold toggle, back-to-top toggle after `window.innerHeight` and smooth scroll, `beforeprint` opens closed notes and `afterprint` restores them.
- `HTML_BODY.tpl`: after `</main>`, a `BACK TO TOP :: START/END` pair with `<a class="kb-totop kb-noprint" href="#" data-uk-icon="icon: totop" aria-label="Back to top"></a>`.
- Tests: the page has the link and the script tag; `blocks.js` exists, has no `http://`/`https://` and no `innerHTML`; CSS has the fold, sticky, tab and print selectors.
- [ ] RED, implement, GREEN; commit `feat(techdoc): style code, tables, author tabs and back to top`.

### Task 4: Help and reference

**Files:** create `help/source/howto-content-blocks.md`; modify `help/source/index.md` (Write card), `help/source/reference-theme-techdoc.md` (Document pages section).

- Page frontmatter: `DocType: How-to guide`, `Feature: Writing`, `HelpId: content-blocks`, `Keyword: code, copy, language, fold, table, sticky, tabs, details, note, back to top`, `Level: basic`, `Order: 260`, `Related: howto-write-documents.md, reference-theme-techdoc.md`, `Section: Guides`, `Summary: ...`.
- Content: code copy, language label and folded code; wide and long tables; author tabs (the `pymdownx.tabbed` Markdown, the `repo.json` block, the `alternate_style` requirement); collapsible notes (`pymdownx.details`); back to top. Examples as fenced Markdown so the help site does not need `pymdown-extensions`.
- Reference: one paragraph under Document pages with the same facts.
- [ ] `kb4it verify help/config/repo.json` with the working-tree KB4IT or, when unavailable, `python -m kb4it verify help/config/repo.json`; check the page builds in `pytest tests/help -q`.
- [ ] Commit `docs(help): document code blocks, tables, author tabs and notes`.

### Task 5: Full check and changelog

- [ ] `python3 -m pytest tests/themes tests/help tests/core -q` and `scripts/devel/check_themes.sh`.
- [ ] `uv run --no-project --with-requirements requirements.txt --with html5validator python scripts/devel/validate_html.py` if Java is available; otherwise note it in the response.
- [ ] `CHANGELOG.md` under `## [Unreleased] / ### Added`: copy button, language label, folded long code, table wrapper and sticky header, back-to-top, author tabs and collapsible note styles, help page.
- [ ] Commit `feat(techdoc): improve code blocks, tables, back to top and author tabs` (or reuse Task 3's commit and add only the changelog).

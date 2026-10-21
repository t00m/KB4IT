# 404 Page, Favicon, Diagrams and Math Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every theme gets a favicon, techdoc/blog/bookshelf get a 404 page, and all four themes draw Mermaid diagrams and KaTeX formulas, all working from `file://`.

**Architecture:** A core python-markdown extension (`kb4it/core/mdrich.py`) turns `mermaid` fences and `$...$`/`$$...$$` into marked elements. The deployer copies one bundled copy of Mermaid, KaTeX and a small init script to `target/resources/render/` for every theme. The existing head-meta injection (`HTML_HEAD_META.tpl`, Deployer step 05) adds the favicon link to every page, and the render scripts only to pages that contain a diagram or formula. A themekit mixin builds `404.html` for the three document themes.

**Tech Stack:** Python 3.11+, python-markdown, Mako, Mermaid (browser build), KaTeX, pytest via `./scripts/devel/test.sh`.

**Spec:** `docs/superpowers/specs/2026-10-21-404-favicon-diagrams-math-design.md`

## Global Constraints

- Everything works from `file://` with no network, and on a web server. No CDN.
- Mermaid is the classic single-file browser build loaded with `<script>`, never an ES module.
- `source/` is only read; nothing writes, moves or renames files there.
- No new required dependency; no Node at build time. Formulas work without the `extras` group.
- Formulas are always on; no `repo.json` setting turns them off.
- Pages without a diagram or formula reference no Mermaid or KaTeX file.
- Text inside fenced code, indented code and inline code never changes.
- Favicon = `repo.json` `logo`; without it, the theme's own logo. No new `repo.json` key.
- No module under `kb4it/` over 600 lines (`tests/test_module_size.py`). `builder.py` is at 594 today.
- Bundled themes keep `"autoescape": true`; raw `| n` only for HTML KB4IT built.
- Every bundled template is used; no template byte-identical in two themes of the same base.
- No em dash anywhere (code, comments, docs, commit messages).
- Commits: one-line Conventional Commits, no trailers, stage files by name, never push or branch.

## Review Focus

1. **`$` in a link destination** (`[pay](https://x.org/?a=$1&b=$2)`): the link must stay intact. Pinned in Task 2 (`test_dollar_in_link_url_is_not_math`).
2. **A `mermaid` fence shown as an example inside a longer fence** (````` ````markdown ````` blocks in the help): it must stay a code example. Pinned in Task 2 (`test_mermaid_fence_inside_longer_fence_stays_code`).
3. **Unclosed delimiters** (`$$` with no closing line, a lone `$`): text stays as written, no crash. Pinned in Task 2 (`test_unclosed_display_math_is_text`).
4. **HTML characters in a formula or diagram** (`$a<b$`, `A-->B & C`): escaped in the page, the original text reaches the script. Pinned in Task 2 (`test_math_source_is_escaped`).
5. **`logo` set to a full URL**: the favicon uses it as given. Pinned in Task 4 (`test_favicon_full_url_logo`).

---

### Task 1: Move head-meta code out of `builder.py`

No behaviour change. Frees room in `builder.py` for later tasks.

**Files:**
- Create: `kb4it/services/headmeta.py`
- Modify: `kb4it/services/builder.py` (methods `page_meta`, `inject_head_meta` and their imports)
- Test: existing suite

**Interfaces:**
- Produces: `class HeadMetaMixin` with `page_meta(self, page_name: str, html: str) -> dict` and `inject_head_meta(self, html: str, page_name: str) -> str`, same behaviour as today. `Builder` inherits it, so `theme.inject_head_meta(...)` and `META_START`/`META_END` keep working for callers.

- [ ] **Step 1:** Move both methods and the names only they use into `HeadMetaMixin` in `kb4it/services/headmeta.py`; make `Builder` inherit it. Keep `from kb4it.services.builder import META_START, META_END` working if anything imports them (grep first).
- [ ] **Step 2:** Run `./scripts/devel/test.sh -q`. Expected: same result as before (775 passed, 1 skipped), `tests/test_module_size.py` passes.
- [ ] **Step 3:** Add `kb4it/services/headmeta.py` to `scripts/devel/typecheck.sh` only if it passes `mypy --strict`; otherwise leave the list alone.
- [ ] **Step 4: Commit** `refactor(builder): move head meta injection into a mixin`

---

### Task 2: Core Markdown extension for diagrams and formulas

**Files:**
- Create: `kb4it/core/mdrich.py`
- Modify: `kb4it/core/mdconfig.py` (`MarkdownSettings.all_extensions`)
- Test: `tests/core/test_mdrich.py`

**Interfaces:**
- Produces:
  - `class RichContentExtension(markdown.Extension)` in `kb4it/core/mdrich.py`.
  - Output markup, relied on by Tasks 3 and 4:
    - diagram: `<pre class="mermaid">ESCAPED_SOURCE</pre>`
    - inline formula: `<span class="kb4it-math">ESCAPED_TEX</span>`
    - display formula: `<div class="kb4it-math kb4it-math-display">ESCAPED_TEX</div>`
  - Constants `MERMAID_MARK = 'class="mermaid"'` and `MATH_MARK = 'class="kb4it-math'` (prefix match covers both formula forms), used to detect pages that need scripts.
  - `MATH_EXTENSIONS = ("pymdownx.arithmatex", "markdown_katex")`: when any of these is in `settings.extensions`, the core extension is not added.

- [ ] **Step 1: Write the failing tests** in `tests/core/test_mdrich.py`, converting with `MarkdownSettings(...).new_markdown().convert(text)`:

```python
def test_mermaid_fence_becomes_diagram():           # "```mermaid\ngraph LR\n  A-->B\n```" -> '<pre class="mermaid">graph LR\n  A--&gt;B</pre>'
def test_mermaid_in_every_highlight_mode():          # parametrize highlight in client, pygments, none -> same <pre class="mermaid">, no "highlight" div around it
def test_mermaid_with_superfences():                 # extensions=["pymdownx.superfences"] (skip if not installed) -> same markup
def test_mermaid_fence_inside_longer_fence_stays_code():  # "````markdown\n```mermaid\nA\n```\n````" -> no class="mermaid"
def test_inline_math():                              # "The area is $A = \\pi r^2$." -> '<span class="kb4it-math">A = \\pi r^2</span>'
def test_display_math_multiline():                   # "$$\nE = mc^2\n$$" -> '<div class="kb4it-math kb4it-math-display">E = mc^2</div>'
def test_math_protects_emphasis_chars():             # "$a_1 * b_2$ and $c_3$" -> no <em>, both spans contain the raw text
def test_escaped_dollar_is_literal():                # "Price \\$5." -> "<p>Price $5.</p>", no kb4it-math
def test_dollars_in_code_untouched():                # inline `$HOME`, fenced bash "echo $A $B", indented "    $x$" -> no kb4it-math, text unchanged
def test_space_after_opening_dollar_is_not_math():   # "5 $ each and 6 $ more" -> no kb4it-math
def test_plain_prices_become_math():                 # "costs $5 and $10" -> kb4it-math present (documented behaviour)
def test_dollar_in_link_url_is_not_math():           # "[pay](https://x.org/?a=$1&b=$2)" -> href unchanged, no kb4it-math
def test_unclosed_display_math_is_text():            # "$$\nE = mc^2\n" and "a $ b" -> no exception, no kb4it-math
def test_math_source_is_escaped():                   # "$a<b \\& c$" -> "a&lt;b \\&amp; c" inside the span
def test_user_math_extension_disables_core():        # extensions=["markdown_katex"] config -> RichContentExtension not in all_extensions() (check by type)
def test_sanitize_keeps_rich_markup():               # sanitize_html() on each of the three markups returns them unchanged
```

- [ ] **Step 2:** Run `./scripts/devel/test.sh tests/core/test_mdrich.py -q`. Expected: FAIL (`ModuleNotFoundError: kb4it.core.mdrich`).
- [ ] **Step 3: Implement `RichContentExtension`** with three processors, registered in `extendMarkdown(md)`:
  - `md.ESCAPED_CHARS.append("$")` so `\$` renders `$`.
  - **Mermaid preprocessor**, priority 30 (before `fenced_code` and superfences at 25). Scan lines tracking the open fence (its character and length): only a fence that opens at column 0 with exactly the info string `mermaid` and is not inside another open fence is replaced, up to its matching closing fence, by `md.htmlStash.store(markup)`. All other lines pass through.
  - **Display math preprocessor**, priority 20 (after fences are stashed, so fenced code is already out of reach). A line that is exactly `$$` (column 0) opens a block that ends at the next line that is exactly `$$`; a single line `$$...$$` also counts. Replace with a stashed `<div>`; with no closing line, leave the lines unchanged.
  - **Inline math processor** (`InlineProcessor`), priority 155: after backticks (190), escapes (180) and links (160), before emphasis. Pattern: `(?<!\$)\$(?=\S)(.+?)(?<=\S)\$(?!\$)` on one paragraph's text; return an `etree` `span` with the text set (etree escapes it).
  - Escape diagram and display source with `html.escape(text, quote=False)` before stashing.
- [ ] **Step 4:** In `MarkdownSettings.all_extensions()`, append `RichContentExtension()` unless any name in `MATH_EXTENSIONS` is in `self.extensions`.
- [ ] **Step 5:** Run `./scripts/devel/test.sh tests/core/test_mdrich.py tests/core/test_markdown_config.py tests/core/test_sanitize.py tests/core/test_superfences.py -q`. Expected: PASS.
- [ ] **Step 6:** Run the full suite. Expected: PASS. (The core signature already rebuilds pages after a version change; no cache work needed.)
- [ ] **Step 7: Commit** `feat(markdown): render mermaid fences and dollar formulas as marked elements`

---

### Task 3: Bundled Mermaid, KaTeX and the init script

**Files:**
- Create: `scripts/devel/fetch_render_assets.sh` (downloads pinned versions into the folder below; run once by the implementer)
- Create: `kb4it/resources/render/` with `mermaid/mermaid.min.js`, `mermaid/LICENSE`, `katex/katex.min.js`, `katex/katex.min.css`, `katex/fonts/*`, `katex/LICENSE`, `VERSIONS` (one line per library: name and version), `kb4it-render.js`
- Modify: `kb4it/services/deployer.py` (`step_08_copy_global_resources_to_target`), `THANKS`
- Test: `tests/core/test_render_assets.py`

**Interfaces:**
- Consumes: markup from Task 2.
- Produces: deployed paths, relative to the target root, used by Task 4:
  - `resources/render/mermaid/mermaid.min.js`
  - `resources/render/katex/katex.min.css`, `resources/render/katex/katex.min.js`
  - `resources/render/kb4it-render.js`

- [ ] **Step 1: Write the failing tests:**

```python
@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf", "apphelp"])
def test_render_assets_deployed(tmp_path, home, theme):   # build a one-page site (reuse _app_conf pattern of test_highlight.py) -> all four paths above exist in target
def test_render_assets_in_package():                       # the four files exist under kb4it/resources/render and VERSIONS names mermaid and katex
def test_katex_css_fonts_are_relative():                   # every url(...) in katex.min.css starts with "fonts/" and the file exists
def test_mermaid_is_not_an_es_module():                    # mermaid.min.js contains no top-level "export " / "import " statement (regex ^\s*(export|import)\s)
```

- [ ] **Step 2:** Run them. Expected: FAIL (files missing).
- [ ] **Step 3:** Write `fetch_render_assets.sh`: takes `MERMAID_VERSION` and `KATEX_VERSION` (latest stable at implementation time), downloads `mermaid@V/dist/mermaid.min.js` and the KaTeX release archive (`katex.min.js`, `katex.min.css`, `fonts/`) plus both licenses, and writes `VERSIONS`. Run it and commit the files.
- [ ] **Step 4:** Write `kb4it-render.js` (classic script, no modules): on `DOMContentLoaded`, if `window.mermaid` exists, `mermaid.initialize({startOnLoad: false, theme: matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'default'})` then `mermaid.run({querySelector: 'pre.mermaid'})`; if `window.katex` exists, for each `.kb4it-math` call `katex.render(el.textContent, el, {displayMode: el.classList.contains('kb4it-math-display'), throwOnError: false})`.
- [ ] **Step 5:** In `step_08_copy_global_resources_to_target`, next to the `pygments.css` block and for every theme regardless of `deploy_dirs`, `copydir(<package>/resources/render, target/resources/render)`. Use the `ENV["GPATH"]["RESOURCES"]` path.
- [ ] **Step 6:** Credit Mermaid and KaTeX (MIT) in `THANKS`.
- [ ] **Step 7:** Run the new tests and `python3 scripts/devel/check_wheel_themes.py` after `uv build` (or the CI wheel check command). Expected: PASS, and the wheel contains `kb4it/resources/render/`.
- [ ] **Step 8: Commit** `feat(deploy): bundle mermaid and katex for offline rendering`

---

### Task 4: Favicon and render scripts in every page head

**Files:**
- Modify: `kb4it/services/headmeta.py` (`page_meta`), `kb4it/resources/common/templates/HTML_HEAD_META.tpl`
- Modify: `kb4it/resources/themes/{techdoc,blog,bookshelf,apphelp}/theme.json` (add `"favicon"`, raise `"kb4it"` to `">=0.9.1"`)
- Modify: `kb4it/resources/themes/techdoc/templates/HTML_HEADER_COMMON.tpl:58` (header fallback)
- Modify: `kb4it/resources/themes/techdoc/logic/theme.py` (`build_page_admin`)
- Test: `tests/core/test_favicon_render_head.py`

**Interfaces:**
- Consumes: `MERMAID_MARK`, `MATH_MARK` (Task 2); deployed paths (Task 3).
- Produces: new optional `theme.json` key `"favicon"`: a path relative to the theme folder. The deployed href is `resources/themes/<id>/<favicon>`. Values: techdoc, blog, bookshelf, apphelp all `"images/logo.svg"` (all four have it; apphelp deploys `images`).
- New `page_meta` keys: `favicon: str` (empty when no logo and no theme favicon), `mermaid: bool`, `math: bool`.

- [ ] **Step 1: Write the failing tests** (build each theme's default app with one extra page; parametrize over the four themes where marked):

```python
@pytest.mark.parametrize("theme", THEMES)
def test_favicon_uses_repo_logo(...):          # every .html in target has <link rel="icon" href="<repo logo>">
@pytest.mark.parametrize("theme", THEMES)
def test_favicon_falls_back_to_theme_logo(...):# repo.json without "logo" -> href == f"resources/themes/{theme}/images/logo.svg" and that file exists in target
def test_favicon_full_url_logo(...):           # logo "https://example.org/logo.png" -> href is exactly that
@pytest.mark.parametrize("theme", THEMES)
def test_render_scripts_only_where_needed(...):# page with a diagram has mermaid.min.js and kb4it-render.js and no katex; page with a formula has katex.min.css, katex.min.js, kb4it-render.js and no mermaid; a plain page references none of "resources/render/"
def test_techdoc_header_logo_fallback_exists(...):  # techdoc without "logo": header <img src> points to a file that exists in target
def test_admin_page_has_favicon(...):          # techdoc with "admin": true -> admin/index.html has <link rel="icon" href="../resources/...">
```

- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** In `page_meta`, add `favicon` (`repo["logo"]` if set, else `resources/themes/<id>/<theme.json favicon>` if the theme declares one, else `""`), `mermaid` (`MERMAID_MARK in html`) and `math` (`MATH_MARK in html`). Read the theme's `theme.json` values from `self.srvbes.get_dict("theme")`; if `favicon` is not already carried there, have `Frontend.theme_load()` keep it.
- [ ] **Step 4:** In `HTML_HEAD_META.tpl`, inside the markers: `<link rel="icon" href="${m['favicon']}">` when set; when `math`, the KaTeX stylesheet and `<script defer src=...>` for `katex.min.js`; when `mermaid`, `<script defer src=...>` for `mermaid.min.js`; when either, `<script defer src="resources/render/kb4it-render.js">` last.
- [ ] **Step 5:** Add `"favicon": "images/logo.svg"` to the four `theme.json` files and raise `"kb4it"` to `">=0.9.1"`. Run `./scripts/devel/check_themes.sh`. Expected: PASS.
- [ ] **Step 6:** techdoc header fallback: replace `'resources/images/logo.png'` with `'resources/themes/techdoc/images/logo.svg'` (the old path does not exist in a built site).
- [ ] **Step 7:** In techdoc `build_page_admin`, pass the rendered page through `self.inject_head_meta(html, "admin/index.html")` before `relocate_links()`, so the favicon gets the `../` prefix like the other links.
- [ ] **Step 8:** Run the new tests and the full suite. Expected: PASS.
- [ ] **Step 9: Commit** `feat(themes): add a favicon and load render scripts only on pages that need them`

---

### Task 5: 404 page for techdoc, blog and bookshelf

**Files:**
- Create: `kb4it/services/themekit/notfound.py` (mixin), `kb4it/resources/bases/uikit/templates/PAGE_404.tpl` (techdoc, blog), `kb4it/resources/themes/bookshelf/templates/PAGE_404.tpl`
- Modify: `kb4it/services/themekit/__init__.py` (mix into `DocumentTheme`), each document theme's `build()` (call it), `kb4it/services/headmeta.py` (`<base>` for 404), `kb4it/services/processor.py` (`step_00_extraction`) and `kb4it/services/workflow.py` (`verify_sources`) for the reserved name
- Test: `tests/themes/test_page_404.py`

**Interfaces:**
- Produces: `NotFoundMixin.build_page_404(self) -> None` (renders `PAGE_404` in the theme shell, title "Page not found", one sentence, a link to `index.html`, the search box `${var['search_box'] | n}`, then `self.distribute_md("404", html)`). `DocumentTheme.reserved_pages: tuple[str, ...] = ("404.md",)`; `Builder` gets no attribute (read with `getattr(theme, "reserved_pages", ())`).

- [ ] **Step 1: Write the failing tests:**

```python
@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf"])
def test_404_page_written(...):            # target/404.html exists, contains 'href="index.html"' and the theme's search box markup
@pytest.mark.parametrize("theme", ["techdoc", "blog", "bookshelf"])
def test_404_not_listed(...):               # "404" absent from sitemap.xml, search index file, feed.xml (if any), all.html / datatable pages
def test_404_base_with_site_url(...):       # site_url "https://ex.org/kb" -> 404.html has <base href="https://ex.org/kb/"> right after <head...>; without site_url no <base>
def test_document_named_404_is_reserved(...):  # source/404.md in techdoc -> build logs DOC_NAME_RESERVED for it, target/404.html is the generated page; kb4it verify exits 1 naming 404.md
def test_apphelp_404_unchanged(...):        # apphelp still emits its own 404.html (no duplicate distribute)
```

- [ ] **Step 2:** Run them. Expected: FAIL.
- [ ] **Step 3:** Implement `NotFoundMixin` and the two `PAGE_404.tpl` templates (escaped by default; only `search_box` raw). Call `self.build_page_404()` from the `build()` of techdoc, blog and bookshelf.
- [ ] **Step 4:** In `HeadMetaMixin.inject_head_meta`, when `page_name == "404.html"` and the backend has `site_url`, insert `<base href="{site_url.rstrip('/')}/">` immediately after the opening `<head ...>` tag (not inside the meta markers; replace an existing one on rebuild).
- [ ] **Step 5:** Reserved name: in `Processor.step_00_extraction`, next to the Windows-name check, a docId in `getattr(theme, "reserved_pages", ())` is invalid with reason `reserved_name` (logged `DOC_NAME_RESERVED`, as today). In `Workflow.verify_sources`, report it the same way.
- [ ] **Step 6:** Run the new tests, `tests/core/test_themekit.py` and `tests/themes/test_templates_used.py`. Expected: PASS.
- [ ] **Step 7: Commit** `feat(themes): add a 404 page to techdoc, blog and bookshelf`

---

### Task 6: `kb4it serve` answers missing pages with `404.html`

**Files:**
- Modify: `kb4it/core/webserver.py` (`_make_handler`)
- Test: `tests/serve/test_webserver_404.py`

- [ ] **Step 1: Write the failing tests:**

```python
def test_missing_page_serves_site_404(tmp_path):   # directory with 404.html; GET /nope.html -> status 404, body is 404.html (with the reload script when reload=True)
def test_missing_page_without_404_html(tmp_path):  # no 404.html -> status 404, standard error body
```

- [ ] **Step 2:** Run them. Expected: FAIL (body is the standard error page).
- [ ] **Step 3:** Override `send_error(self, code, message=None, explain=None)` in the handler: for code 404 with `<directory>/404.html` present, send it through `_send(404, "text/html; charset=utf-8", body)` (with `inject_reload` when reload is on); otherwise call the parent.
- [ ] **Step 4:** Run the tests and `tests/serve/`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(serve): answer missing pages with the site's 404 page`

---

### Task 7: Help, changelog and AGENTS.md

**Files:**
- Modify: `help/source/troubleshooting.md`, `help/source/howto-write-documents.md`, `help/source/reference-document-format.md`, `help/source/reference-repo-json.md`, `help/source/reference-theme-{techdoc,blog,bookshelf,apphelp}.md`, `help/source/howto-publish-web-server.md`, `help/source/howto-create-theme.md` (new `favicon` key), `CHANGELOG.md`, `AGENTS.md`

- [ ] **Step 1:** Write the pages as listed in spec section 6. Troubleshooting entry heading: "Text between dollar signs shows as a formula" (anchor `{#dollar-sign}`), cause and fix as in the spec. Show the syntax examples inside four-backtick fences so they stay examples. Write any literal dollar sign in prose as `\$`.
- [ ] **Step 2:** `howto-create-theme.md`: the optional `theme.json` key `favicon` (path inside the theme folder).
- [ ] **Step 3:** `CHANGELOG.md` under `## [Unreleased]`: `### Added` (diagrams, formulas, favicon, 404 page, serve 404) and `### Fixed` (techdoc header logo fallback).
- [ ] **Step 4:** `AGENTS.md`: `mdrich.py` in the module table, `RichContentExtension` and the `$` rule under Builder hooks and core behaviour, `resources/render/` deployment, `favicon` in the optional `theme.json` keys, `reserved_pages`, 404 page in the themes section.
- [ ] **Step 5:** Run `kb4it verify help/config/repo.json` (from the checkout: `uv run --no-project --with-requirements requirements.txt python -m kb4it.core.main verify help/config/repo.json`) and `tests/help/`. Expected: exit 0, PASS.
- [ ] **Step 6: Commit** `docs(help): document diagrams, formulas, the favicon and the 404 page` (and `docs: update changelog and agents reference` if split)

---

### Task 8: Whole-feature verification

- [ ] **Step 1:** Full suite: `./scripts/devel/test.sh -q`. Expected: all pass.
- [ ] **Step 2:** `uv run -q --no-project --with-requirements requirements.txt python scripts/devel/theme_snapshot.py --content DIR` on this branch and on the commit before Task 1; `diff -r`. Expected: pages without diagrams or formulas differ only by the favicon line (and the techdoc header logo), plus the new `404.html`.
- [ ] **Step 3:** `uv run --no-project --with-requirements requirements.txt --with html5validator python scripts/devel/validate_html.py`. Expected: no new errors.
- [ ] **Step 4:** Manual, by the user: build a sample site of each theme with one diagram and one formula, turn networking off, open `target/index.html` from disk in Firefox and Chrome. Expected: diagram, formula and favicon visible.

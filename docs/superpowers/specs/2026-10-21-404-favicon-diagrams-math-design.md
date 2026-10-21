# 404 page, favicon, diagrams and math design

Status: draft, waiting for approval.
Date: 2026-10-21
Release: 0.9.1
Roadmap: `tmp/KB4IT-SSG-ROADMAP.md`, Plan B (publishing basics) and Plan D (diagrams and math)

## Intent

Two small plans from the static site generator roadmap, built together in 0.9.1:

- **Plan B, reduced:** every theme gets a 404 page and a favicon.
- **Plan D:** authors can write Mermaid diagrams and math formulas in Markdown, and all four bundled themes draw them.

## Why

- A KB4IT site shows the browser's blank icon in the tab. The `logo` in `repo.json` already identifies the site in the header; it should also identify it in the tab.
- On a web server, a missing page shows the server's bare error page. Only apphelp has its own 404 page.
- Technical documentation needs diagrams and formulas. GitHub, GitLab, MkDocs and Obsidian already render the same syntax, so authors expect it to work.

## Goals

1. techdoc, blog and bookshelf publish a `404.html` page in the site's style, with a link back to the home page.
2. All four themes (techdoc, blog, bookshelf, apphelp) put a favicon in every page they write.
3. A fenced code block with the language `mermaid` renders as a diagram in all four themes.
4. Text between `$...$` (inline) and `$$...$$` (display) renders as a formula in all four themes.
5. All of it works when the site is opened from disk (`file://`) with no network, and the same way on a web server.
6. The help explains the new syntax, the favicon, the 404 page, and what happens to a plain `$` in text.

## Non-goals

These were in the roadmap's Plan B and were dropped on purpose:

- **Drafts.** `Draft` is an ordinary value of a property like `Status`. A draft is built and published like any other document, with no label. No change.
- **Future dates.** A document with a future `Date` is published right away like any other. No change.
- **`Updated` key.** `Date` stays the only date property. An author who updates a document changes its `Date`. No change.

Also out of scope:

- Loading Mermaid or KaTeX from a CDN.
- Rendering diagrams or formulas at build time (that would need Node or a headless browser on the build machine).
- A setting to turn formulas or diagrams off.
- Plan A (page identity, nested folders), Plan C (asset fingerprinting, minification) and the 0.9.2 name-collision fix.
- New `kb4it verify` rules.

## Anti-goals

The work fails, even if it technically works, when any of these happens:

- KB4IT writes, moves or renames anything in `source/`. That folder belongs to the user and KB4IT only reads it.
- A site needs a web server or a network connection to show diagrams, formulas or the favicon.
- Pages without diagrams or formulas download the Mermaid or KaTeX files.
- The text inside code blocks or inline code changes. `$HOME` in a shell example stays `$HOME`.
- A user has to install an extra package (the `extras` group, Node, anything else) to get diagrams or formulas.

## Decisions made with the user

1. **Syntax.** Diagrams are fenced code blocks with the language `mermaid`:

   ````markdown
   ```mermaid
   graph LR
     Source --> Build --> Site
   ```
   ````

   Formulas use `$...$` inside a sentence and `$$...$$` on their own lines:

   ```markdown
   The area is $A = \pi r^2$.

   $$
   E = mc^2
   $$
   ```

2. **Formulas are always on.** There is no setting. Documents should not use `$` as plain text outside code. The help explains this case in `help/source/troubleshooting.md`, with the way to write a literal dollar sign.
3. **Bundled, rendered in the browser.** Mermaid and KaTeX (scripts, CSS, fonts) ship inside the KB4IT package and are deployed with the site. No CDN.
4. **Favicon = the `logo` from `repo.json`.** When `logo` is not set, the favicon is the theme's own logo, the same image the techdoc header already falls back to. No new `repo.json` key.
5. **`source/` is never touched.** See the anti-goals.

## Design

### 1. Favicon

Every page a theme writes gets one line in its `<head>`:

```html
<link rel="icon" href="...">
```

- `href` is the `logo` value from `repo.json` when set, exactly as the header uses it (a path relative to the site root, or a full URL).
- Without `logo`, `href` points to the theme's logo in the deployed resources:

  | Theme | Fallback |
  |---|---|
  | techdoc | `resources/images/logo.png`, the header's current fallback |
  | blog | the theme's `logo.svg` or `logo.png` |
  | bookshelf | the theme's `logo.svg` |
  | apphelp | the theme's `images/logo.svg` (deployed, since `deploy_dirs` includes `images`) |

- The link is relative, so it works from `file://`. techdoc's `admin/` page gets the right path through `relocate_links()`, like its other links. In apphelp versioned sites (`target/<version>/`), it must resolve like the other resource links of the page.
- A change of `logo` already rebuilds every page (it is part of the `repo.json` hash in the core signature, and of apphelp's `SIGNATURE_REPO_KEYS`), so every page gets the new favicon.
- The `type` attribute is optional. Browsers accept SVG and PNG favicons.

`help/source/reference-repo-json.md` says that `logo` is also the favicon. The theme reference pages say what the fallback is.

### 2. 404 page (techdoc, blog, bookshelf)

apphelp already has one (`PAGE_404.tpl`, emitted in `apphelp/logic/theme.py`) and does not change.

For the three document themes:

- The build writes `404.html` at the site root on every build, through the shared code in `kb4it/services/themekit/` (one implementation, a template per theme or in the `uikit` base for techdoc and blog).
- The page uses the theme's normal page shell (header, menu, footer), a short title such as "Page not found", one sentence, and a link to `index.html`, and the search box (all three themes have `"search": true`).
- It is a system page, not a document: it is not in the database, the datatables, the property pages, the event pages, the search index, the feed, the menu or the "all documents" page. `Builder.sitemap_exclude()` already leaves `404.html` out of the sitemap.
- **Links.** A web server shows `404.html` for any missing URL, at any depth, so relative links only resolve when the missing URL is at the site root. The rule:
  - When `site_url` is set in `repo.json`, the page's links and resource paths are absolute URLs built from `site_url` (my call: this is the only case where KB4IT knows where the site lives, and it keeps GitHub Pages project subpaths working).
  - When `site_url` is not set, links stay relative. They work for missing pages at the site root and when the file is opened from disk.
- Web servers need to be told to use the page (GitHub Pages does it on its own). `help/source/howto-publish-web-server.md` gets the nginx (`error_page 404 /404.html;`) and Apache (`ErrorDocument 404 /404.html`) lines. `kb4it serve` answers a missing page with the site's `404.html` and status 404 when the site has one (my call; `kb4it/core/webserver.py` has no 404 handling today).
- **Name.** A document named `404.md` in these themes would collide with the page. Until the 0.9.2 collision fix lands, the build and `kb4it verify` report a `404.md` document in these themes the way apphelp reports its reserved names, and leave it out (my call: the smallest step that does not make the collision bug worse). The 0.9.2 fix then takes this name into its general rule.

### 3. Mermaid diagrams

- **Where the files live.** One pinned Mermaid release, the single-file browser build (`mermaid.min.js`, loaded with a classic `<script>` tag). ES module builds are not allowed, because browsers block modules opened from `file://`. Include Mermaid's license file next to it and credit it in `THANKS`.
- **Markup.** python-markdown turns a `mermaid` fence into `<pre><code class="language-mermaid">`. The exact markup differs with `markdown.highlight` (`client`, `pygments`, `none`) and with `pymdownx.superfences`. The compiler must turn every one of these forms into the same plain block before the theme sees the page, for example `<pre class="mermaid">source</pre>`, with the diagram source HTML-escaped. Pygments and highlight.js must not colour it.
- **Loading.** A page loads `mermaid.min.js` and calls Mermaid once, only when it contains a diagram block. Pages without a diagram load nothing new.
- **Errors.** Invalid diagram source does not fail the build. Mermaid shows its own error message in place of the diagram.
- **Dark mode.** If a theme switches between light and dark, Mermaid uses its matching theme (`default` or `dark`) at page load. A switch after load does not need to redraw (builder's call whether to do more).

### 4. Math formulas

- **Files.** One pinned KaTeX release: `katex.min.js`, `katex.min.css`, the `auto-render` extension if used, and the `fonts/` folder, with its license file, credited in `THANKS`. The CSS loads the fonts with relative URLs, so they load from disk.
- **Protecting formulas from Markdown.** Without help, Markdown reads `_` and `*` inside `$a_1 * b_2$` as emphasis. KB4IT adds a small python-markdown extension to the core (in `kb4it/core/`, always on, part of `BASE_EXTENSIONS` or loaded next to it in `kb4it/core/mdconfig.py`). It runs before inline formatting, finds `$...$` and `$$...$$` outside code, and stores each formula so that Markdown does not change it. The output is a marked element that KaTeX renders in the browser, for example `<span class="kb4it-math">` for inline and `<div class="kb4it-math kb4it-math-display">` for display, with the TeX source HTML-escaped inside.
- **Matching rules** (my calls, following the usual Markdown math conventions):
  - `$$...$$` may span lines. `$...$` stays inside one paragraph.
  - Inline `$...$` needs a non-space character right after the opening `$` and right before the closing `$`. So `costs $5 and $10` still turns into a formula (that is the documented case), but `5 $ each` does not.
  - `\$` writes a literal dollar sign and is never a delimiter.
  - Nothing inside fenced code, indented code or inline code is touched.
- **Loading.** A page loads the KaTeX CSS and scripts, and renders, only when it contains a formula.
- **Errors.** A formula KaTeX cannot parse does not fail the build. KaTeX shows the source in its error colour (`throwOnError: false`).
- **Interaction with user extensions.** If a user already enables `pymdownx.arithmatex` or `markdown_katex` in `markdown.extensions`, the two must not both process the same `$`. Builder's call: skip the core extension when one of those is configured, and say so in the help.

### 5. Shared rules for diagrams and formulas

- **Where the assets go.** One copy of Mermaid and KaTeX in the package, not one per theme (they add several megabytes). Builder's call where: `kb4it/resources/common/` is deployed by techdoc, blog and bookshelf; apphelp deploys only `framework/` and `images/` (`deploy_dirs`), so apphelp needs a way to get the same files into its output without a second copy in the wheel.
- **Which pages need them.** The decision "this page has a diagram" or "this page has a formula" is made from the compiled HTML of the page, so it also covers pages that embed document bodies (for example a blog listing that shows full posts).
- **`markdown.sanitize`.** When `sanitize` is on, nh3 must keep the diagram and formula elements and their classes. Add them to the allow-list in `mdconfig` (`SANITIZE_TAGS`, `SANITIZE_ATTRIBUTES`).
- **Escaping.** Diagram and formula source taken from a document is HTML-escaped in the page. The scripts read it as text.
- **Search and feed.** The search index and the Atom feed keep the formula and diagram source as plain text. Feed readers show the source, not the drawing. That is accepted.
- **Rebuilds.** A new KB4IT version already turns on `force_all`, so existing sites rebuild every page with the new extension the first time they build with 0.9.1.
- **Theme requirement.** Each bundled theme that uses the new features raises its `kb4it` requirement in `theme.json` to `">=0.9.1"`.

### 6. Help pages

| Page | Change |
|---|---|
| `help/source/troubleshooting.md` | New entry: "Text between dollar signs shows as a formula". Cause: `$...$` is formula syntax. Fix: write `\$` for a literal dollar sign, or put the text in inline code. |
| `help/source/howto-write-documents.md` | How to add a diagram and a formula, with the examples above. |
| `help/source/reference-document-format.md` | The exact syntax and matching rules of section 4, and the `mermaid` fence. |
| `help/source/reference-repo-json.md` | `logo` is also the favicon. |
| `help/source/reference-theme-*.md` (four pages) | Favicon fallback; 404 page (techdoc, blog, bookshelf); diagrams and formulas supported. |
| `help/source/howto-publish-web-server.md` | Serving `404.html` on nginx and Apache. |

`kb4it verify help/config/repo.json` passes. Today no help page and no sample document of any theme uses `$` outside code (checked on 2026-10-21), so the new syntax changes none of them. New help text that shows a dollar sign as text writes `\$`.

## Constraints

- Works from `file://` and on a web server, offline, in current Firefox, Chrome and Safari.
- No new required dependency, Python or otherwise. No Node at build time.
- All links relative, except the 404 page with `site_url` (section 2).
- Bundled themes keep `"autoescape": true`. Raw output (`| n`) only for HTML KB4IT built.
- No module under `kb4it/` over 600 lines. Annotated modules stay `mypy --strict` clean.
- Every bundled template is used (`tests/themes/test_templates_used.py`), and no template is byte-identical in two themes of the same base.
- No em dash in code, comments or docs.

## Done means

The roadmap's checklist:

- Tests, including:
  - the math extension: inline, display, multi-line display, `\$`, `$` inside fenced code, indented code and inline code, `_` and `*` inside a formula, the "costs $5 and $10" case
  - diagrams with `markdown.highlight` set to `client`, `pygments` and `none`, and with `pymdownx.superfences`
  - `markdown.sanitize: true` keeps diagrams and formulas
  - pages without diagrams or formulas reference no Mermaid or KaTeX file
  - favicon link on every page of every theme, with and without `logo`
  - `404.html` in techdoc, blog and bookshelf; absent from the sitemap, search index, feed and datatables; absolute links with `site_url`
  - `scripts/devel/theme_snapshot.py` diffs on every sample site, where the only change to pages without diagrams or formulas is the favicon line
- A clean `scripts/devel/validate_html.py` run.
- A manual check: open a sample site of each theme from disk with networking off, and see a diagram, a formula and the favicon.
- Updated help pages (section 6).
- A `CHANGELOG.md` entry under `## [Unreleased]`.
- An `AGENTS.md` update (math extension, 404 page, favicon, bundled assets).

## Left to the builder

- Mermaid and KaTeX versions (latest stable at build time, pinned).
- Where the shared assets live and how apphelp deploys them (section 5).
- The exact element names and classes for diagrams and formulas.
- The text of the 404 page.
- How a theme's templates add the scripts only to pages that need them.
- Whether to skip the core math extension when a user extension already handles `$`.

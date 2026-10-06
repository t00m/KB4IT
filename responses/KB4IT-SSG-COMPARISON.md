---
Author: Tomás Vírseda
Category: Report
Date: 2026-10-06
DocType: Explanation
Language: Go, JavaScript, Python, Ruby, Rust, TypeScript
Product: Docusaurus, Eleventy, Hugo, Jekyll, KB4IT, MkDocs Material, Pelican, Quartz, Starlight, VitePress, Zensical
Scope: Knowledge Management
Tag: comparison, markdown, static-site-generator
Topic: Analysis, Documentation
---

# KB4IT compared with other Markdown static site generators

## Background

KB4IT 0.8.0 turns a folder of Markdown files with YAML frontmatter into a static website. Its core idea is that metadata drives the site: every frontmatter property becomes a set of index pages, and the build is incremental, driven by blake2b hashes of each document body and each key/value pair.

This report compares KB4IT with the Markdown generators most often used for documentation, knowledge bases and blogs. It lists where each tool is strong, where it is weak, and where KB4IT is behind. The KB4IT facts come from the code in this repository (branch at release 0.8.0). The facts about the other tools come from their public documentation and recent release notes, checked on 2026-10-06.

## The field

| Tool | Language | Template engine | Main use | State in 2026 |
|---|---|---|---|---|
| KB4IT | Python | Mako | Metadata-driven knowledge base, blog, study notes, app help | Active, single maintainer, 4 bundled themes |
| Hugo | Go | Go templates | Anything: docs, blogs, large sites | Very active, 0.163.x in June 2026 |
| Jekyll | Ruby | Liquid | Blogs, GitHub Pages | Mature, slow release pace |
| Pelican | Python | Jinja2 | Blogs | Mature, 4.12 current |
| MkDocs + Material | Python | Jinja2 | Project documentation | Material in maintenance mode, bug and security fixes until 2026-11-05 |
| Zensical | Rust + Python | Jinja2 (MkDocs compatible) | Project documentation | Successor to Material, alpha, MIT |
| Docusaurus | JavaScript (React) | MDX / React | Product documentation | Very active, widest plugin set |
| Starlight | JavaScript (Astro) | Astro / MDX | Product documentation | Fast growing, accessibility first |
| VitePress | JavaScript (Vue) | Vue / Markdown | Library documentation | Active |
| Eleventy | JavaScript | Many (Nunjucks, Liquid, ...) | Flexible sites | Active |
| Quartz v4 | TypeScript | Preact components | Obsidian vaults, digital gardens | Active |

## Strongest and weakest features per tool

### KB4IT

Strongest:

- **Automatic faceted navigation.** Every frontmatter key gets a page, and every key/value pair gets a page, with no configuration. No other tool here does this for arbitrary keys. Hugo taxonomies come closest but must be declared in config and need templates per taxonomy.
- **Incremental builds on two levels.** Only changed documents and only the affected key/value pages are recompiled (`kbdict.json` cache). Most competitors either rebuild everything (Pelican, MkDocs) or only do incremental work in the dev server.
- **Metadata quality control.** `kb4it verify` exits 1 on non-conformant files, invalid frontmatter is reported (`DOC_INVALID`), `fail_on_invalid` can stop the build, and the `apphelp` theme enforces a controlled vocabulary and a Diátaxis `DocType`. For a knowledge base this is rare and valuable.
- **Application help features.** The `apphelp` theme has offline full-text search, help ids with a contract file checked at build time, and works from `file://`, a GitHub Pages subpath, or embedded in an app. Only Docusaurus and Starlight come close, and neither checks a help-id contract.
- **Terminal UI.** A Textual TUI to create, build, browse metadata (keys, values, documents), read logs and serve the site. None of the others ship a TUI.
- **Usable as a library.** `theme_path` lets an application embed KB4IT and ship its own theme.
- **Extras in techdoc.** Event calendar from `Date`, DataTables listings, admin page with source and site backup zips.
- **Plain Markdown sources.** Files stay readable in any editor and in git.

Weakest: see the gap analysis below.

### Hugo

Strongest: build speed (single Go binary, thousands of pages per second), no runtime dependencies, taxonomies, multilingual sites, image processing, asset pipeline (Sass, minify, fingerprinting), custom output formats (RSS, JSON, sitemap), render hooks and shortcodes, `hugo server` with live reload, hundreds of themes.

Weakest: Go template syntax is hard to learn and debug, theme upgrades break often, no built-in search.

### Jekyll

Strongest: native on GitHub Pages, simple Liquid templates, large theme and plugin catalogue, collections and data files.

Weakest: slow on large sites, Ruby toolchain on the build machine, development has slowed.

### Pelican

Strongest: Python, Jinja2, Markdown and reStructuredText, RSS/Atom feeds, Pygments highlighting, content caching, importers (WordPress, RSS), plugin system, i18n subsites plugin.

Weakest: blog oriented, weak for structured documentation, small theme catalogue of uneven quality.

### MkDocs + Material, and Zensical

Strongest: polished UI out of the box, client-side full-text search, dark mode, navigation tabs and sections, tags plugin, admonitions, content tabs, Mermaid, math, code annotations, social cards, versioning with `mike`, 60+ languages, `mkdocs serve` live reload, `gh-deploy`, `mkdocstrings` for API docs. Zensical keeps that and adds a Rust incremental engine (reported 5x faster rebuilds) and native plugins.

Weakest: Material is frozen for features and ends maintenance in November 2026; Zensical is still alpha. Tags are a single flat dimension, not arbitrary properties. MkDocs core rebuilds the whole site.

### Docusaurus

Strongest: versioned docs with one command, mature i18n, blog included, MDX (React components in Markdown), large plugin ecosystem, Algolia DocSearch integration.

Weakest: heavy JavaScript bundle, Node toolchain, React knowledge needed for customization, slow builds on large sites.

### Starlight and VitePress

Strongest: near zero JavaScript (Starlight), accessible defaults, Pagefind (Starlight) or built-in local search (VitePress), i18n, very fast dev servers, clean sidebar navigation.

Weakest: Node toolchain, documentation-only scope, limited metadata navigation.

### Eleventy

Strongest: maximum flexibility, many template languages, data cascade, collections from any frontmatter field, fast.

Weakest: no batteries, everything (search, navigation, feeds) must be built or added by plugins.

### Quartz v4

Strongest: Obsidian compatibility, wikilinks, backlinks, graph view, transclusion, popover previews, full-text search, tags, LaTeX, i18n.

Weakest: Node toolchain, tied to the Obsidian note model, less suited to formal documentation.

## Feature matrix

Legend: **Yes** built in, **Plugin** via an official or common plugin, **Partial** limited or theme-dependent, **No** absent.

| Feature | KB4IT | Hugo | Jekyll | Pelican | MkDocs Material / Zensical | Docusaurus | Starlight | Quartz |
|---|---|---|---|---|---|---|---|---|
| Arbitrary metadata facets | **Yes** | Partial (declared taxonomies) | Partial | Partial (tags, categories) | Partial (tags) | Partial (tags) | No | Partial (tags) |
| Incremental build | **Yes** (doc + key/value) | Dev server | Partial (`--incremental`) | Partial (caching) | Zensical only | Dev server | Dev server | Dev server |
| Metadata validation | **Yes** (`verify`, strict mode) | No | No | No | No | Partial (frontmatter schema) | Yes (content collections schema) | No |
| Live-reload dev server | No | Yes | Yes | Plugin | Yes | Yes | Yes | Yes |
| Full-text search | Partial (apphelp only) | No | Plugin | Plugin | Yes | Plugin (Algolia) / local plugin | Yes (Pagefind) | Yes |
| RSS / Atom feed | No | Yes | Plugin | Yes | Plugin | Yes (blog) | Plugin | Yes |
| sitemap.xml | No | Yes | Plugin | Plugin | Yes | Yes | Yes | Yes |
| SEO and social meta (Open Graph) | No | Yes | Plugin | Partial | Yes | Yes | Yes | Partial |
| Multilingual (i18n) | No | Yes | Plugin | Plugin | Yes | Yes | Yes | Partial (UI only) |
| Versioned docs | No | No | No | No | Plugin (`mike`) | Yes | Plugin | No |
| Server-side syntax highlighting | No (highlight.js in browser) | Yes (Chroma) | Yes (Rouge) | Yes (Pygments) | Yes (Pygments) | Yes (Prism) | Yes (Expressive Code) | Yes (Shiki) |
| Diagrams (Mermaid) and math | No | Partial | Plugin | Plugin | Yes | Plugin | Plugin | Yes |
| Content tabs, includes, transclusion | No | Yes (shortcodes) | Yes (includes) | Partial | Yes (snippets, tabs) | Yes (MDX) | Yes (components) | Yes |
| Wikilinks and backlinks | No | No | Plugin | No | Plugin | No | No | Yes |
| Broken link check | **Yes** (`LINK_BROKEN`) | Partial | Plugin | No | Yes (warnings) | Yes | Plugin | No |
| Configurable Markdown extensions | No (hard coded) | Yes (Goldmark options) | Yes | Yes | Yes | Yes (remark/rehype) | Yes | Yes |
| Plugin API | No (themes only) | No (modules) | Yes | Yes | Yes | Yes | Yes | Yes |
| Override one template, keep the theme | No | Yes | Yes | Yes | Yes (`overrides/`) | Yes (swizzle) | Yes | Yes |
| Image processing, asset pipeline | No | Yes | Plugin | Plugin | Partial | Yes | Yes | Partial |
| One-command deploy | No | Partial | Native on GitHub Pages | Partial | Yes (`gh-deploy`) | Yes | Partial | Yes |
| Works from `file://` | **Yes** (apphelp) | Partial | Partial | Partial | Partial | No | No | No |
| TUI or GUI | **Yes** (TUI) | No | No | No | No | No | No | No |
| Platforms | GNU/Linux only | All | All | All | All | All | All | All |
| Theme catalogue size | 4 | Hundreds | Hundreds | Dozens | 1 theme, highly configurable | Dozens | Few | Few |

## Where KB4IT is behind

The gaps are ordered by impact on a typical KB4IT user (an IT team writing a knowledge base or a blog).

### 1. No live-reload dev server

Every competitor has `serve` with file watching and browser reload. KB4IT has a web server in the TUI, but no watch loop and no CLI command. Authors must rebuild by hand after each edit. The incremental engine already exists, so a `kb4it serve <config>` that watches `source/` and triggers a normal build is mostly glue code.

### 2. Full-text search only in apphelp

`techdoc` and `blog` offer DataTables filtering on titles and metadata, not on body text. Material, Starlight, VitePress and Quartz all search the content. The `apphelp` search code (`apphelp_search.py`) could be moved to a common module, or the build could generate a Pagefind index as a post-activity.

### 3. No feeds, sitemap or SEO metadata

The `blog` theme has no RSS or Atom feed. No theme writes `sitemap.xml`, canonical URLs or Open Graph tags. For a blog this is the most visible gap; Hugo, Pelican, Jekyll and Docusaurus give feeds by default.

### 4. Fixed Markdown dialect

`compiler.py` hard codes the extensions `extra`, `admonition`, `toc`, `sane_lists`. Users cannot enable `pymdownx` (tabs, task lists, details, snippets, superfences for Mermaid), `codehilite` with Pygments, or math. MkDocs users can do this from `mkdocs.yml`. A `markdown_extensions` list (and `markdown_extension_configs`) in `repo.json` would close most of this gap in one change.

### 5. Code highlighting runs in the browser

`techdoc` and `blog` ship highlight.js. Every other tool in the table highlights at build time, which means no JavaScript, no flash of unstyled code, and correct output from `file://` and in print.

### 6. No i18n and no versioning

There is no way to build a site in several languages or to keep docs for several releases. For an internal knowledge base this matters less; for `apphelp`, which documents an application, versioned help per release is a natural next step.

### 7. Customizing a theme means copying it

Template lookup is theme folder, then common folder. There is no cross-theme inheritance and no per-repository override folder. To change one template, a user must copy and maintain the whole theme. Hugo, Jekyll, MkDocs (`custom_dir`) and Docusaurus (swizzle) let a site override a single template. A `<repo>/overrides/` folder checked first in `_template_candidates()` would fix this.

### 8. No plugin system

Themes are the only extension point. There are no build hooks (on page, on build end) that a repository can add without writing a theme. Pelican and MkDocs show how small such an API can be.

### 9. GNU/Linux only

The package declares POSIX Linux only, and a global process lock allows only one KB4IT run per user. Hugo, Pelican, MkDocs and the Node tools run on Windows and macOS. Many IT teams author on Windows laptops, so this limits adoption.

### 10. No asset pipeline

No image resizing, no CSS or JS minification, no fingerprinted file names for cache busting. Large theme frameworks (UIKit, DataTables, highlight.js with all languages) are copied to every target.

### 11. No cross-document features

No includes or transclusion, no wikilinks, no backlinks or "what links here". Metadata pages give related documents by property, but explicit links between notes are not indexed. Quartz shows the value of backlinks for a knowledge base.

### 12. Small ecosystem

Four themes, one maintainer, few users. Competitors have large communities, many themes and fast answers to questions. This is not a code problem, but it affects every choice a new user makes.

## Where KB4IT is ahead

These are the features to protect and to market:

- Automatic faceted navigation for any frontmatter key, with no configuration.
- Hash-based incremental compilation of documents and key/value pages, used for every build, not only in a dev server.
- Metadata validation and controlled vocabularies (`verify`, `fail_on_invalid`, `apphelp` strict mode, Diátaxis `DocType`).
- Broken link detection between Markdown sources at build time.
- Help ids with a contract file, and help sites that work offline and embedded.
- A TUI for non-developers to create, build, explore and serve sites.
- Event calendar and backup zips in `techdoc`.

No single competitor combines these. The closest are Hugo (taxonomies) plus a custom validation script, or MkDocs Material with the tags plugin and a schema check in CI.

## Suggested priorities

| Priority | Change | Effort | Closes gap |
|---|---|---|---|
| 1 | `kb4it serve` with file watching and incremental rebuild | Medium | 1 |
| 2 | `markdown_extensions` in `repo.json`, plus Pygments `codehilite` | Small | 4, 5 |
| 3 | Shared full-text search (reuse apphelp or Pagefind) for techdoc and blog | Medium | 2 |
| 4 | RSS/Atom for blog, `sitemap.xml` and Open Graph for all themes | Small | 3 |
| 5 | Per-repository template override folder | Small | 7 |
| 6 | Build hooks API (on document, on build end) | Medium | 8 |
| 7 | Backlinks page per document, built from the existing link rewrite | Medium | 11 |
| 8 | macOS support, then Windows; per-repository lock instead of global | Medium to large | 9 |
| 9 | Versioned help for `apphelp` | Large | 6 |

Items 2, 4 and 5 are small and would remove the most common reasons a technical user would pick another tool.

## Related Topics

- [Hugo taxonomies](https://gohugo.io/content-management/taxonomies/)
- [Material for MkDocs maintenance mode](https://github.com/squidfunk/mkdocs-material/issues/8523)
- [Zensical roadmap](https://zensical.org/about/roadmap/)
- [Zensical overview (LinuxLinks)](https://www.linuxlinks.com/zensical-modern-static-site-generator/)
- [Docusaurus vs VitePress vs Nextra vs Starlight 2026](https://www.pkgpulse.com/guides/docusaurus-vs-vitepress-vs-nextra-vs-starlight-2026)
- [Starlight vs Docusaurus](https://docsio.co/blog/starlight-vs-docusaurus)
- [Quartz overview (LinuxLinks)](https://www.linuxlinks.com/quartz-batteries-included-static-site-generator/)
- [Pelican documentation](https://docs.getpelican.com/)
- [Hugo releases (pkg.go.dev)](https://pkg.go.dev/github.com/gohugoio/hugo@v0.162.1)

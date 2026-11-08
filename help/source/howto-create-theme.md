---
DocType: How-to guide
Feature: Themes, Development
HelpId: create-theme
Keyword: custom theme, new-theme, starter, template, mako, theme.json, Builder, DocumentTheme, themekit, kit, template_base, build_page, page_pipeline, page_context, add_system_page, config_class, assets, checks, verify.py, autoescape, escaping, THEME_AUTOESCAPE_OFF
Level: advanced
Order: 560
Related: explanation-themes.md, reference-theme-hooks.md, dev-architecture.md
Section: Guides
Summary: Make your own theme with kb4it new-theme, then add kits, settings, shared libraries and checks.
---

# Create your own theme

A theme is a folder with a description, some Python and some templates. The quickest start is a copy of a starter theme, made by `kb4it new-theme`.

## Start from a starter theme {#start}

1. Create the theme. `mytheme` is its id: lower-case letters, digits, `-` and `_`.

        kb4it new-theme mytheme

    It copies `starter-docs` into `~/.kb4it/opt/resources/themes/mytheme/` and sets the id. Add `--plain` to start from `starter-plain` instead.

2. Make a site from its sample app and build it:

        kb4it create mytheme default ~/my-site
        kb4it build ~/my-site/config/repo.json

3. Open `~/my-site/target/index.html`. Change the templates and `logic/theme.py` of the theme step by step and build again.

`kb4it themes` lists the theme with `scope=user`, its version, its fingerprint and its folder. A normal build is enough after a change: when any file of the theme changes, its fingerprint changes and the next build rebuilds every page. See [Theme version and fingerprint](#version).

The two starters:

| Starter | Built on | What it has |
|---|---|---|
| `starter-docs` | `DocumentTheme` and the `uikit` template base | Home page with the latest documents, a page per property and per value, all documents, properties, search, 404 page |
| `starter-plain` | `Builder` | Home page listing every document, one plain page per document, search. No property pages (`"metadata_pages": false`) |

To start from a bundled theme instead, copy its folder (`kb4it themes` shows it after `path=`) into `~/.kb4it/opt/resources/themes/`, and set a new `id`, `name` and `version` in its `theme.json`.

## What a theme contains {#layout}

```text
mytheme/
├── theme.json        # id, name, version, the KB4IT it needs, the libraries it uses
├── logic/theme.py    # class Theme: builds the pages
├── templates/*.tpl   # Mako templates
│   └── skeletons/    # optional: skeletons of the Add page
├── framework/        # the theme's own CSS, JavaScript, fonts, images
└── apps/default/     # optional sample knowledge base for kb4it create
```

KB4IT copies the theme folder to `target/resources/themes/<id>/`, so templates link the theme's files from there: `resources/themes/${var['theme']['id']}/framework/style.css`. Libraries such as UIkit are not in the theme: list them in `assets` (see [Shared libraries](#assets)).

## How the pieces fit {#hooks}

`logic/theme.py` holds a class `Theme`. With `page_pipeline = True` (the starters have it), KB4IT builds every page the same way: it reads the compiled document, fills `var` with the title (`var['page']['title']`), the body (`var['source_html']`), the properties (`var['keys']`) and more, calls your hooks, and renders `HTML_HEADER_COMMON`, the body template and `HTML_FOOTER`.

| Part | Role |
|---|---|
| `build()` | Builds the pages that do not come from a document, with `add_system_page(name, title, html)`: home, lists, calendars |
| `page_context(doc_id, var)` | Adds the theme's own data to `var` for one page; returns `var` |
| `body_transforms(doc_id, var)` | Functions from HTML to HTML applied to the body in order; by default the heading and section wrappers (see `heading_classes` in [Options](#options)) |
| `page_body_template(doc_id, var)`, `render_page(doc_id, var)` | The body template (default `HTML_BODY`) and the whole page |
| `finalize_html(html)` | A last change to the whole page, such as pretty printing |
| `build_page(path_md)` | Override it only to build the page completely yourself; the hooks above then do not run |
| `post_activities()`, `post_deploy_activities()` | Run after compilation and after the copy to `target/` |
| `site_signature()` | Returns a value that changes when every page must be rebuilt, for example when the navigation changes |
| `self.srvdtb` | The documents and their properties: `get_documents()`, `get_values(doc, key)` |
| `self.template(name)` | Loads a template from `templates/`, then from the theme's `template_base`, then from KB4IT's shared ones |

[Theme hooks](reference-theme-hooks.md) lists every hook and helper, generated from the KB4IT code.

Templates use [Mako](https://www.makotemplates.org/): `${var['repo']['title']}` prints a value, and `% for` ... `% endfor` repeats a block. `var['repo']` holds every key of `repo.json`.

## Build on the document themes {#document-theme}

techdoc, blog and bookshelf share their code and part of their templates. A theme that looks like them can use both, and hold only what it does differently.

For the code, subclass `DocumentTheme` instead of `Builder`:

```python
from kb4it.services.themekit import DocumentTheme

class Theme(DocumentTheme):
    datatable_link_template = 'LINK'
```

It brings the pages per property and per value, the properties, stats, bookmarks and "all documents" pages, the document table, the day, month and year event pages, the table of contents and the metadata section of a page. Where the bundled themes differ, it takes a class attribute or a small method that your theme sets:

| Hook | Default | Sets |
|---|---|---|
| `properties_title` | `'Properties'` | Title of the properties page |
| `reuse_unchanged_pages` | `False` | Keep the cached properties, stats, bookmarks and all-documents pages when nothing they show changed |
| `tagcloud_scale_skips_empty` | `False` | Leave documents without the property out of a tag cloud's scale |
| `cloud_measure(frequency, max_frequency)` | `count` and `weight` | The size fields of a property button or a tag cloud word |
| `frequency_keys()`, `stats_keys()` | Every property not ignored | The properties that size the buttons, and those the stats page lists |
| `stats_skip_keys` | `('Summary',)` | Properties left out of the stats page, such as free text |
| `datatable_link_template` | `'LINK_DATATABLE'` | Template of a value link in the document table |
| `datatable_default_headers` | `('Date', 'Title')` | Columns when neither the page nor `repo.json` `"datatable"` names them |
| `datatable_date_cell(timestamp)`, `datatable_title_cell(doc, properties)`, `datatable_value_link(properties, key, value)` | UIkit cells | The cells of the document table |

The stats page template, `PAGE_STATS`, gets `var['stats']`, built by `collect_stats()` in `kb4it/services/themekit/stats.py`: the totals (`documents`, `properties`, `values`, `dated_pct`, `bookmarks`, `links`), the activity (`oldest`, `newest`, `undated`, and `years` and `months`, lists of bars with `label`, `count`, `pct` and `url`), `coverage` (one row per property with `key`, `url`, `docs`, `pct`, `values` and `top`), the health lists (`duplicates`, `rare_keys`, `sparse_docs`) and the links (`most_linked`, `orphans`, `no_outgoing`). The health lists and `orphans` hold at most ten `items` and say how many more there are in `more` (`total` is both). For a section's summary line it also gives `dated`, `busiest_year`, `full_coverage`, `least_covered` and `health_issues`. Content documents only: system pages never count. The page is kept from the cache only when no document and no property changed.

A document theme writes a `404.html` page at the end of its build: call `self.build_page_404()` from `build()` and give the theme a `PAGE_404` template. To keep a source file name for itself, a theme lists it in `reserved_pages`, a tuple that is empty by default. A theme that writes the 404 page sets `reserved_pages = ("404.md",)`; a document with that name is then reported with `DOC_NAME_RESERVED` and left out.

You can still override any method. KB4IT's own themes start the docstring of such an override with `Override:` and say why; a test checks it.

For the templates, set `"template_base": "uikit"` in `theme.json` (see [Options in theme.json](#options)) and delete from `templates/` the ones you have not changed: they come from the base. techdoc and blog use it.

A theme that looks nothing like them keeps subclassing `Builder`, as apphelp does.

## Add a kit {#kits}

Some features of techdoc are kits: mixins in `kb4it/services/themekit/` that any theme adds to its class line. A kit needs no other kit.

```python
from kb4it.services.themekit import DocumentTheme
from kb4it.services.themekit.navigation import NavigationMixin

class Theme(NavigationMixin, DocumentTheme):
    def ordered_pages(self, doc_id):
        """Override: every document, sorted by file name."""
        return sorted(d for d in self.srvdtb.get_documents() if not self.srvdtb.is_system(d))
```

| Kit | Module | What it adds |
|---|---|---|
| Navigation | `navigation` | `neighbours(doc_id)`: previous and next page of the order `ordered_pages(doc_id)` gives |
| Table filter | `filters` | A filter bar over the document tables; needs a `DATATABLE_FILTER.tpl` and `"tablefilter"` in `assets` |
| Related | `related` | `related_docs(doc_id)`: documents that share rare property values |
| TOC sidebar | `tocsidebar` | `toc_sidebar(source_html)`: whether a page gets a second, sticky table of contents |
| Gallery | `gallery` | The Gallery page of every image; needs `"gallery"` in `assets` |
| Diagrams | `diagrams` | The Diagrams page of every Mermaid diagram |

## Theme settings {#settings}

A setting the users of your theme may change goes into a dataclass, named in the class attribute `config_class`:

```python
from dataclasses import dataclass

from kb4it.services.builder import Builder

@dataclass
class MySettings:
    show_dates: bool = True

class Theme(Builder):
    config_class = MySettings
```

`self.config.show_dates` is then the field default, replaced by `"show_dates"` in `theme.json`, replaced by the block named after the theme in `repo.json`: `"mytheme": {"show_dates": false}`. A value of the wrong type stops the build with a message naming the key; an unknown key in the block logs `THEME_SETTING_UNKNOWN` and makes `kb4it verify` fail. Without `config_class`, `self.config.get("name")` reads `theme.json`.

## Shared libraries {#assets}

UIkit, highlight.js, DataTables and the search engine come with KB4IT, one copy each. List the ones your pages load in `theme.json`:

```json
"assets": ["uikit", "search"]
```

Each is copied to `resources/vendor/<name>/` in the website, so templates link `resources/vendor/uikit/css/uikit.min.css`. The names are `highlight`, `uikit`, `datatables`, `search`, `tablefilter` and `gallery`. An unknown name stops the build.

## Checks after the build {#checks}

After every build KB4IT reads the pages of the website and logs each link to a missing page or section as `[CHECK] ANCHOR_MISSING`. A theme adds its own checks by overriding `checks(target)`, which returns a list of `Problem` (from `kb4it.core.checks`):

```python
import os

from kb4it.core.checks import Problem

def checks(self, target):
    """Override: the shared link check, then mine."""
    problems = super().checks(target)
    if not os.path.isfile(os.path.join(target, "index.html")):
        problems.append(Problem("HOME_MISSING", "", "page=index.html", severity="error"))
    return problems
```

An `error` stops the build; with `"strict": true` in `repo.json`, a warning does too. See [Post-build checks](reference-log-codes.md#checks).

## Escaping {#escaping}

Titles, property values and `repo.json` settings are written by people, and may hold `<`, `"` or a whole `<script>`. With `"autoescape": true` in `theme.json`, every `${...}` is HTML-escaped, so such text shows as text. A value that is HTML on purpose, such as the compiled body of a document or a fragment your `theme.py` built, must be printed raw with `| n`:

```html
<title>${var['title']}</title>       <!-- escaped -->
<main>${var['body'] | n}</main>      <!-- HTML, printed as it is -->
```

Only use `| n` for HTML that KB4IT or your theme built; never for a value taken from a document as it is. `scripts/devel/escape_audit.py mytheme --raw` (in the KB4IT sources) lists the raw expressions of a theme for review. KB4IT's shared templates are always escaped.

A theme without `"autoescape": true` prints values as they are, and every build warns with `[BUILDER] THEME_AUTOESCAPE_OFF`. The bundled themes all escape.

`HTML_BODY` and `PAGE_INDEX` are always required, and `PAGE_KEY` and `PAGE_KEY_VALUE` too unless `metadata_pages` is `false`. A missing one stops the build with `TEMPLATE_MISSING`.

## Clean, valid HTML {#html}

The bundled themes follow these rules, and a theme you share should too:

- **Mark the blocks of a page.** Put a pair of comments around each part a reader looks for: `<!-- NAME :: START -->` and `<!-- NAME :: END -->`, with the name in capitals (`TOP BAR`, `MAIN CONTENT`, `TABLE OF CONTENTS`, `FOOTER`). Pairs nest like the markup. Every page has at least `PAGE METADATA`, `STYLESHEETS`, `MAIN CONTENT` and `FOOTER`. Put a pair inside a `% if` together with its block, so a page never has a `START` without its `END`. Do not write values from documents inside a comment: a `--` in a title would end it.
- **Write UIkit components as `data-uk-*` attributes** (`data-uk-icon`, `data-uk-toggle`, `data-uk-modal`). UIkit reads them the same way, and `uk-*` is not valid HTML.
- **Give every `<section>` and `<article>` a heading.** When the design shows none, use a heading only screen readers see (`class="uk-hidden-visually"` with UIkit).
- **Check the result** with the W3C checker: `uv run --no-project --with-requirements requirements.txt --with html5validator python scripts/devel/validate_html.py <target folder>` (it needs Java). The bundled themes have no error and no warning.

## Options in theme.json {#options}

| Key | Meaning |
|---|---|
| `version` | The theme's own version, `X.Y.Z`. Raise it when you change the theme. Without it the theme loads and is shown as `unversioned` (`THEME_VERSION_MISSING`); another form, such as `1.0` or `2.1-beta`, logs `THEME_VERSION_INVALID` and the theme is shown as `unversioned`. |
| `favicon` | Path of the theme's icon inside the theme folder, such as `images/logo.svg`. Pages use it when `repo.json` has no `logo`. The folder must be in `deploy_dirs` if you set that list |
| `kb4it` | The KB4IT versions the theme works with, such as `">=X.Y.Z"` or `">=X.Y.Z, <A.B.C"` |
| `metadata_pages` | `false` skips the pages per property and per value |
| `deploy_dirs` | Only these folders of the theme are copied to the website, for example `["framework"]` |
| `assets` | Shared libraries bundled with KB4IT that the theme's pages load, such as `["uikit", "search"]`. Each one is copied to `resources/vendor/<name>/` in the website, so templates link, for example, `resources/vendor/uikit/js/uikit.min.js`. The names are `highlight` (highlight.js), `uikit` (UIkit), `datatables` (jQuery and DataTables), `search` (the search engine and search box), `tablefilter` (the table filter kit) and `gallery` (the gallery kit). An unknown name stops the build. A theme with `"search": true` gets `search` without listing it. See [Shared libraries](#assets) |
| `autoescape` | `true` escapes every value the templates print, except those marked raw. See [Escaping](#escaping) |
| `editor` | `true` or `false`: whether the Add page is on when `repo.json` has no `editor` key. Without it, the page is off. See [Add the editor page](#editor) |
| `template_base` | Name of a set of templates bundled with KB4IT that the theme builds on, such as `"uikit"`, the UIkit layout techdoc and blog share. A template is looked up in the repository's overrides, then the theme, then its base, then KB4IT's shared templates, so the theme only holds the ones it changes |
| `heading_classes` | Classes of the headings and section wrappers of a document page: keys `h2`, `h3`, `h4` and `sect1` to `sect4`, for example `{"h2": "uk-card-title"}`. A key you leave out keeps its default: `kb-h2` ... `kb-sect4`, or techdoc's UIkit classes with `"template_base": "uikit"`. For other markup, ship your own `HTML_TAG_H2_NEW.tpl` and the like in `templates/` |

## Theme version and fingerprint {#version}

A theme is identified by its `version` and by a fingerprint: 12 characters computed from every file of the theme folder (except `apps/`), its template base and KB4IT's shared templates. A file changed, added or renamed gives another fingerprint, even when you forget to raise the version.

The pair shows as `mytheme 1.0.0+3f9a1c0b7e21`:

- in `kb4it themes` and `kb4it doctor`, with the folder the theme is loaded from;
- in the `[WORKFLOW] SUMMARY` line of every build, as `theme=mytheme/1.0.0+3f9a1c0b7e21`;
- in the `generator` meta tag of the pages of the bundled themes.

The fingerprint is part of the build cache. When it changes, the next build rebuilds every page, so you never need `--force` after editing a theme.

## Add the editor page {#editor}

The [Add page](howto-write-document-editor.md) is built by KB4IT. `Builder` includes it through `AddPageMixin`, so any theme can have it with four steps.

1. Set the class attribute `add_page = True` on your `Theme` class. Without it the editor is off, whatever `repo.json` says, and `add.md` stays a normal page:

        class Theme(Builder):
            add_page = True

2. Call `self.create_page_add()` in `build()`. It builds `add.html` when the editor is on and removes a stale one when it is off:

        def build(self):
            ...
            self.create_page_add()

3. Link to `add.html` where your layout shows its links, only when `var['editor']` is true:

        % if var['editor']:
        <a href="add.html">Add document</a>
        % endif

4. Let the page pipeline wrap the page like any other (`page_pipeline = True`), or make your own `build_page()` wrap it like it wraps `search.html`. The page starts with `<!-- kb4it:theme-html -->`, which marks HTML the theme made itself. A theme that wraps its own pages in another way can override `register_add_page(html)`; apphelp does.

Optionally, ship skeletons in `templates/skeletons/`: `*-SKELETON.md` files and a `skeletons.json`, as described in [Use your own skeletons](howto-write-document-editor.md#skeletons). Without them the cards come from the common set. Set `"editor": true` in `theme.json` to have the page on by default, and require `"kb4it": ">=0.10.0"`.

The page uses the common `PAGE_ADD.tpl`; put a `PAGE_ADD.tpl` in `templates/` to replace the cards. Do not replace `EDITOR_DIALOGS.tpl`. To offer more values in completion, override `editor_keys()`.

A theme that does not set `add_page = True` and call `create_page_add()` never gets the page, whatever `repo.json` says.

## Check the sources with kb4it verify {#verify}

A file `logic/verify.py` with a function `verify(repo, docs)` runs during `kb4it verify`. `docs` maps each file name to its properties. Return a list of problem messages, empty when all is well.

## Share it {#share}

- Put the theme in `source/resources/themes/<name>/` of a knowledge base to ship it with the documents.
- Or point `"theme_path"` in `repo.json` at its folder.
- Or pack it as a zip that others install with `kb4it install-theme`.

### Pack a theme as a zip {#zip}

The zip holds one top folder, the theme folder itself, with `theme.json` and the theme's folders in it:

```text
mytheme.zip
└── mytheme/
    ├── theme.json        "id": "mytheme"
    ├── templates/
    ├── framework/
    ├── logic/
    └── apps/
```

**The top folder name must be exactly the `id` in `theme.json`.** A zip whose folder and id differ is refused, and nothing is installed. The id has 1 to 64 characters: lowercase letters, digits, `-` and `_`, starting with a letter or a digit.

Pack it from the folder that holds the theme:

```bash
cd ~/work/themes
zip -r mytheme.zip mytheme -x '*/__pycache__/*'
```

The users install it from the file or from an `https://` address:

```bash
kb4it install-theme mytheme.zip
kb4it install-theme https://example.org/themes/mytheme.zip
```

`kb4it install-theme` also refuses a zip with more than one top folder, with files at its root, with paths that leave the folder or symbolic links, with no `theme.json` in the top folder, or with a `kb4it` requirement this KB4IT does not meet. Set a new `version` in `theme.json` for every zip you publish, so users see which one they have; see [Command line](reference-command-line.md#themes).

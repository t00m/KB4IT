---
DocType: How-to guide
Feature: Themes, Development
HelpId: create-theme
Keyword: custom theme, template, mako, theme.json, Builder, DocumentTheme, themekit, template_base, build_page, verify.py, autoescape, escaping, THEME_AUTOESCAPE_OFF
Level: advanced
Order: 560
Related: explanation-themes.md, dev-architecture.md
Section: Guides
Summary: Make your own theme, starting from a bundled one or from a small working example.
---

# Create your own theme

A theme is a folder with a description, some Python and some templates. Start from a copy of a bundled theme, or from the small example below.

## Start from a bundled theme {#copy}

1. Find where KB4IT keeps its themes:

        kb4it -L DEBUG themes 2>&1 | grep THEME_SEARCH_GLOBAL

2. Copy one into your own themes folder under a new name, replacing `<path>` with the folder the first command printed:

        mkdir -p ~/.kb4it/opt/resources/themes
        cp -r <path>/techdoc ~/.kb4it/opt/resources/themes/mytheme

3. In `mytheme/theme.json`, set `"id": "mytheme"`, a new `name` and `"version": "1.0.0"`.
4. Set `"theme": "mytheme"` in the `repo.json` of a knowledge base and build it with `--force`.

`kb4it themes` now lists it with `scope=user`, its version, its fingerprint and its folder. Change the templates and CSS step by step and rebuild. A normal build is enough: when any file of the theme changes, its fingerprint changes and the next build rebuilds every page (`CORE_SIGNATURE_CHANGED` in the log). See [Theme version and fingerprint](#version).

## What a theme contains {#layout}

```text
mytheme/
├── theme.json        # id, name, version, description, KB4IT it needs
├── logic/theme.py    # class Theme: builds the pages
├── templates/*.tpl   # Mako templates
│   └── skeletons/    # optional: skeletons of the Add page
├── framework/        # CSS, JavaScript, fonts, images
└── apps/default/     # optional sample knowledge base for kb4it create
```

## A small working theme {#example}

This theme, `plain`, makes a home page that lists every document and wraps each document in a simple layout. Create these files in `~/.kb4it/opt/resources/themes/plain/`.

`theme.json`:

```json
{
    "id": "plain",
    "name": "Plain",
    "author": "Ann Lopez",
    "email": "ann@example.com",
    "website": "",
    "description": "One page per document and a list of them",
    "kb4it": ">=X.Y.Z",
    "metadata_pages": false,
    "autoescape": true
}
```

`"metadata_pages": false` skips the pages per property and per value, so the theme needs no templates for them. `"autoescape": true` escapes every value the templates print; see [Escaping](#escaping).

`logic/theme.py`:

```python
"""Plain theme: a home page listing every document, and one page per document."""

import os

from kb4it.core.util import html_id_for
from kb4it.services.builder import Builder


class Theme(Builder):

    def build(self):
        """Build the pages that do not come from a document: here, the home page."""
        var = self.get_theme_var()
        var["docs"] = [
            {"url": html_id_for(doc), "title": self.srvdtb.get_values(doc, "Title")[0]}
            for doc in self.srvdtb.get_documents()
            if not self.srvdtb.is_system(doc)
        ]
        self.distribute_md("index", self.template("PAGE_INDEX").render(var=var))
        self.srvdtb.add_document("index.md")
        self.srvdtb.add_document_key("index.md", "Title", var["repo"]["title"])
        self.srvdtb.add_document_key("index.md", "SystemPage", "Yes")

    def build_page(self, path_md):
        """Wrap each compiled page in the layout of HTML_BODY.tpl."""
        path_html = html_id_for(path_md)
        with open(path_html, encoding="utf-8") as fh:
            body = fh.read()
        var = self.get_theme_var()
        var["body"] = body
        var["title"] = self.srvdtb.get_values(os.path.basename(path_md), "Title")[0]
        with open(path_html, "w", encoding="utf-8") as fh:
            fh.write(self.template("HTML_BODY").render(var=var))
```

`templates/HTML_BODY.tpl`, the layout of every page:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>${var['title']} · ${var['repo']['title']}</title>
  <link rel="stylesheet" href="resources/themes/plain/framework/plain.css">
</head>
<body>
  <header><a href="index.html">${var['repo']['title']}</a></header>
  <main>${var['body'] | n}</main>
</body>
</html>
```

`templates/PAGE_INDEX.tpl`, the home page:

```html
<h1>${var['repo']['title']}</h1>
<ul>
% for doc in var['docs']:
  <li><a href="${doc['url']}">${doc['title']}</a></li>
% endfor
</ul>
```

`framework/plain.css`:

```css
body { max-width: 46rem; margin: 2rem auto; font-family: sans-serif; line-height: 1.6; }
header a { font-weight: bold; text-decoration: none; }
```

KB4IT copies the theme folder to `target/resources/themes/plain/`; that is why the layout links the CSS from there.

## How the pieces fit {#hooks}

| Part | Role |
|---|---|
| `build()` | Builds the pages that do not come from a document: home, lists, calendars |
| `build_page(path_md)` | Receives each compiled document and writes its final HTML |
| `build_page_key(key, values)`, `build_page_key_value(kvpath)` | Build the pages per property and per value, unless `metadata_pages` is `false` |
| `post_activities()`, `post_deploy_activities()` | Run after compilation and after the copy to `target/` |
| `site_signature()` | Returns a value that changes when every page must be rebuilt, for example when the navigation changes |
| `self.srvdtb` | The documents and their properties: `get_documents()`, `get_values(doc, key)` |
| `self.distribute_md(name, html)` | Adds a page the theme rendered |
| `self.template(name)` | Loads a template from `templates/`, then from the theme's `template_base`, then from KB4IT's shared ones |

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
| `datatable_link_template` | `'LINK_DATATABLE'` | Template of a value link in the document table |
| `datatable_default_headers` | `('Date', 'Title')` | Columns when neither the page nor `repo.json` `"datatable"` names them |
| `datatable_date_cell(timestamp)`, `datatable_title_cell(doc, properties)`, `datatable_value_link(properties, key, value)` | UIkit cells | The cells of the document table |

A document theme writes a `404.html` page at the end of its build: call `self.build_page_404()` from `build()` and give the theme a `PAGE_404` template. To keep a source file name for itself, a theme lists it in `reserved_pages`, a tuple that is empty by default. A theme that writes the 404 page sets `reserved_pages = ("404.md",)`; a document with that name is then reported with `DOC_NAME_RESERVED` and left out.

You can still override any method. KB4IT's own themes start the docstring of such an override with `Override:` and say why; a test checks it.

For the templates, set `"template_base": "uikit"` in `theme.json` (see [Options in theme.json](#options)) and delete from `templates/` the ones you have not changed: they come from the base. techdoc and blog use it.

A theme that looks nothing like them keeps subclassing `Builder`, as apphelp does.

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
| `version` | The theme's own version, `X.Y.Z`. Raise it when you change the theme. Without it the theme loads and is shown as `unversioned` (`THEME_VERSION_MISSING`); another form, such as `1.0` or `2.1-beta`, logs `THEME_VERSION_INVALID` and the theme is shown as `unversioned`. From the next minor release that form stops the build |
| `favicon` | Path of the theme's icon inside the theme folder, such as `images/logo.svg`. Pages use it when `repo.json` has no `logo`. The folder must be in `deploy_dirs` if you set that list |
| `kb4it` | The KB4IT versions the theme works with, such as `">=X.Y.Z"` or `">=X.Y.Z, <A.B.C"` |
| `metadata_pages` | `false` skips the pages per property and per value |
| `deploy_dirs` | Only these folders of the theme are copied to the website, for example `["framework"]` |
| `autoescape` | `true` escapes every value the templates print, except those marked raw. See [Escaping](#escaping) |
| `editor` | `true` or `false`: whether the Add page is on when `repo.json` has no `editor` key. Without it, the page is off. See [Add the editor page](#editor) |
| `template_base` | Name of a set of templates bundled with KB4IT that the theme builds on, such as `"uikit"`, the UIkit layout techdoc and blog share. A template is looked up in the repository's overrides, then the theme, then its base, then KB4IT's shared templates, so the theme only holds the ones it changes |

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

4. Make `build_page()` wrap the page like it wraps `search.html`. The page starts with `<!-- kb4it:theme-html -->`, which marks HTML the theme made itself. A theme that wraps its own pages in another way can override `register_add_page(html)`; apphelp does.

Optionally, ship skeletons in `templates/skeletons/`: `*-SKELETON.md` files and a `skeletons.json`, as described in [Use your own skeletons](howto-write-document-editor.md#skeletons). Without them the cards come from the common set. Set `"editor": true` in `theme.json` to have the page on by default, and require `"kb4it": ">=0.10.0"`.

The page uses the common `PAGE_ADD.tpl`; put a `PAGE_ADD.tpl` in `templates/` to replace the cards. Do not replace `EDITOR_DIALOGS.tpl`. To offer more values in completion, override `editor_keys()`.

A theme that does not set `add_page = True` and call `create_page_add()` never gets the page, whatever `repo.json` says.

## Add your own checks {#verify}

A file `logic/verify.py` with a function `verify(repo, docs)` runs during `kb4it verify`. `docs` maps each file name to its properties. Return a list of problem messages, empty when all is well.

## Share it {#share}

- Put the theme in `source/resources/themes/<name>/` of a knowledge base to ship it with the documents.
- Or point `"theme_path"` in `repo.json` at its folder.

---
DocType: How-to guide
Feature: Themes, Development
HelpId: create-theme
Keyword: custom theme, write a theme, new-theme, starter, template, mako, theme.json, kb4it.theme, BaseTheme, Site, Doc, Table, feature, features, options, hooks, prepare, build, page_context, site.page, render, config_class, assets, checks, verify.py, theme-info, autoescape, escaping, THEME_AUTOESCAPE_OFF, THEME_HOOK_UNUSED
Level: advanced
Order: 560
Related: reference-theme-hooks.md, dev-theme-internals.md, explanation-themes.md
Section: Guides
Summary: "Write your own theme with kb4it.theme: start from a starter, switch on features, fill a few hooks and write your pages."
---

# Write a theme

A theme is a folder with a description, some Python and some templates. The Python imports from one module, `kb4it.theme`, and the theme class switches on the parts it wants by name. The quickest start is a copy of a starter theme.

## Start from a starter theme {#start}

1. Create the theme. `mytheme` is its id: lower-case letters, digits, `-` and `_`.

        kb4it new-theme mytheme

    It copies `starter-docs` into `~/.kb4it/opt/resources/themes/mytheme/` and sets the id. Add `--plain` to start from `starter-plain` instead.

2. Make a site from its sample app and build it:

        kb4it create mytheme default ~/my-site
        kb4it build ~/my-site/config/repo.json

3. Open `~/my-site/target/index.html`. Change the templates and `logic/theme.py` step by step and build again.

A normal build is enough after a change: when any file of the theme changes, the next build rebuilds every page. See [Theme version and fingerprint](#version).

| Starter | Features | What it has |
|---|---|---|
| `starter-docs` | `documents`, `search`, on the `uikit` template base | Home page with the latest documents, a page per property and per value, all documents, properties, search, 404 page |
| `starter-plain` | `search` | Home page listing every document, one plain page per document, search. No property pages |

To start from a bundled theme instead, copy its folder (`kb4it themes` shows it after `path=`) into `~/.kb4it/opt/resources/themes/`, and set a new `id`, `name` and `version` in its `theme.json`.

## What a theme contains {#layout}

```text
mytheme/
├── theme.json        # id, name, version, the KB4IT it needs
├── logic/
│   ├── __init__.py   # optional, empty: lets your editor resolve the imports below
│   └── theme.py      # class Theme(BaseTheme)
├── templates/*.tpl   # Mako templates
│   └── skeletons/    # optional: skeletons of the Add page
├── framework/        # the theme's own CSS, JavaScript, fonts, images
└── apps/default/     # optional sample knowledge base for kb4it create
```

`logic/` is a Python package of its own: a second module next to `theme.py` is imported relatively, `from .helpers import shorten`. KB4IT copies the theme folder to `target/resources/themes/<id>/`, so templates link the theme's files from there: `resources/themes/${var['theme']['id']}/framework/style.css`.

## A theme in twenty lines {#hello}

`logic/theme.py` of a theme with a home page, search and the tags of each document:

```python
from kb4it.theme import BaseTheme


class Theme(BaseTheme):
    features = ("search",)

    def build(self, site):
        """The home page: every document, newest first."""
        items = [{"title": doc.title, "url": doc.url} for doc in site.documents]
        site.page("index", "Home", self.render("PAGE_INDEX", documents=items))

    def page_context(self, doc, var):
        """The tags of the document, for HTML_BODY."""
        var["tags"] = doc.links("Tag")
        return var
```

With `templates/HTML_BODY.tpl` and `templates/PAGE_INDEX.tpl` (plus `HTML_HEADER_COMMON.tpl` and `HTML_FOOTER.tpl` when the pages share a header and a footer), that is a whole theme. `PAGE_INDEX.tpl` reads `var['documents']`; `HTML_BODY.tpl` reads `var['source_html']`, the compiled document, and `var['tags']`.

## How a build calls the theme {#stages}

Every hook is optional. KB4IT calls them in this order:

| Hook | When | Use it to |
|---|---|---|
| `setup()` | Once per build, first | Reset the theme's own per-build state |
| `generate_sources(site)` | Before KB4IT reads `source/` | Write documents into `source/` |
| `prepare(site)` | After the documents are read, before any page is built | Compute what your pages need, once |
| `build(site)` | After the features wrote their pages | Write your own pages with `site.page()` |
| `page_context(doc, var)` and the other page hooks | For every page | Add data to `var`, rewrite the body, choose the template |
| `after_build(site)` | After every page is compiled | Work on the compiled pages |
| `after_deploy(site)` | After the site is in `target/` | Copy or package files in `site.paths.target` |
| `checks(site)` | After deployment | Return the problems of the built site |
| `after_checks(site)` | After the checks passed | Publish, copy, notify |

For a document page, KB4IT reads the compiled document, fills `var` with the title (`var['page']['title']`), the body (`var['source_html']`), the properties (`var['keys']`) and more, then calls `page_var()`, `page_context(doc, var)`, `body_transforms(doc, var)`, `render_page(doc, var)` (which renders `HTML_HEADER_COMMON`, the template `page_template(doc, var)` names, by default `HTML_BODY`, and `HTML_FOOTER`) and `finalize_html(html)`.

## Read the knowledge base {#site}

`site` is a read-only view of the knowledge base. Nothing it returns changes the build: values are tuples and settings refuse changes.

| You want | Write |
|---|---|
| Every document, newest first | `for doc in site.documents:` |
| The ten newest | `site.documents.latest(10)` |
| The documents with a value | `site.documents.with_value("Tag", "backup")` |
| One document | `site.documents.get("note.md")` |
| The properties that get pages, and the values of one | `site.properties.keys()`, `site.properties.values("Tag")` |
| A setting of `repo.json` or `theme.json` | `site.repo.get("title")`, `site.theme["id"]` |
| Whether this build compiles a document | `site.build.changed(doc)` |
| The folders | `site.paths.source`, `site.paths.target` (complete after deployment) |
| An enabled feature | `site.features.events` |

A `doc` has `doc.id` (`note.md`), `doc.title`, `doc.url` (`note.html`), `doc.date`, `doc.values("Tag")`, `doc.value("Status", "Draft")`, `doc.links("Tag")` (`[{name, url}]`, each value with its page), `doc.backlinks`, `doc.source()` (the Markdown) and `doc.template_keys()` (the `var['keys']` of its page). [Theme API reference](reference-theme-hooks.md#site) lists every member.

## Write pages {#pages}

- `self.render("NAME", **values)` renders `templates/NAME.tpl` with the variables every template gets (`var['repo']`, `var['theme']`, `var['page']`, `var['search_box']`...) plus `values`, all under `var`.
- `site.page(name, title, html)` adds `name.html` to the site. `markdown=True` sends the text through the Markdown converter like a document; `listing=True` marks a page that only lists documents (search engines get `noindex, follow`).
- `site.keep(name)` keeps `name.html` of the previous build while no document changed (`unless="properties"`: while no property changed) and returns `True`; build the page only when it returns `False`.
- `site.table(Table(documents=docs, columns=("Date", "Title")))` is the HTML of a table of documents; the `table` feature draws it.

To add the same variables to every template, override `base_var()`, call `super().base_var()` and add yours.

## Switch on features {#features}

A feature is a part of a theme that KB4IT has ready: list its name in `features`.

| Feature | What it brings |
|---|---|
| `documents` | A bundle: `toc`, `metadata`, `property_pages`, `all_documents` and `not_found` (and `table`, which they need) |
| `table` | Tables of documents: `site.table()` |
| `toc` | `var['toc']`, the table of contents of each page, and `menu_contents(var)` |
| `metadata` | The page actions of each page, and `section(doc)`, the property links of a document |
| `property_pages` | `properties.html`, one page per property and one per value |
| `all_documents`, `bookmarks`, `stats` | `all.html`, `bookmarks.html`, `stats.html` |
| `events` | One page per day, month and year of the event documents; dates in tables link there |
| `table_filter` | A filter bar over the tables of the list pages |
| `related` | `related(doc)`: the documents that share rare values with a document |
| `navigation` | `neighbours(doc)`: previous and next document in the theme's reading order |
| `toc_sidebar` | `wanted(html)`: whether a page gets a second, sticky table of contents |
| `gallery`, `diagrams` | `gallery.html` with every image and `diagrams.html` with every Mermaid diagram |
| `search` | `search.html`, the search box and the search index |
| `editor` | The Add page, an editor for new documents in the browser |
| `about` | The About KB4IT and About this app pages |
| `not_found` | `404.html` |

A feature comes with the features it requires, and runs after them: `events` needs `table`, so `features = ("events",)` has both. A feature writes its pages before your `build()`. It also sets what it needs in `theme.json`: `search` sets `"search": true`, `property_pages` sets `"metadata_pages"`, and each adds its shared library to `assets`. A `theme.json` value that says the opposite, such as `"search": false` with the `search` feature, stops the build with a message that names both.

`kb4it theme-info mytheme` shows the features a theme has, in the order they run. [Theme API reference](reference-theme-hooks.md#features) lists the options, hooks and templates of each one.

## Change what a feature does {#customize}

**Options** are class attributes, with the defaults the reference lists:

```python
class Theme(BaseTheme):
    features = ("documents", "search")
    properties_cloud = False           # property_pages: a table instead of tag clouds
    datatable_link_template = "LINK"   # table: the template of a value link
```

**Hooks** are methods named like the hook. The feature calls yours instead of its own. To build on the default, call it on the feature:

```python
    def datatable_date_cell(self, doc):
        """The date cell gets a class of its own."""
        cell = self.site.features.table.datatable_date_cell(doc)
        return cell.replace('<td class="uk-text-left">', '<td class="uk-text-left my-date">', 1)

    def event_documents(self):
        """Only the documents with a Category of Meeting get events pages."""
        return self.site.documents.with_value("Category", "Meeting")
```

A method named like a hook of a feature the theme does not switch on is never called; the build logs `THEME_HOOK_UNUSED` with the feature to add.

## Write a feature of your own {#own-feature}

When a part of your theme has its own pages, its own per-build data or its own work after deployment, make it a feature: a `Feature` subclass in `logic/`, listed as a class in `features`.

```python
from kb4it.theme import BaseTheme, Feature


class Glossary(Feature):
    name = "glossary"
    requires = ("table",)
    reserves = ("glossary.md",)

    def prepare(self, site):
        self.terms = site.documents.with_value("Category", "Term")

    def pages(self, site):
        site.page("glossary", "Glossary", self.theme.render("PAGE_GLOSSARY", terms=self.terms))


class Theme(BaseTheme):
    features = ("documents", Glossary)
```

`prepare`, `pages`, `page_context(doc, var)`, `after_build` and `after_deploy` run at the same stages as the theme's hooks; the other features read yours as `site.features.glossary`.

## Theme settings {#settings}

A setting the users of your theme may change goes into a dataclass, named in `config_class`:

```python
from dataclasses import dataclass

from kb4it.theme import BaseTheme


@dataclass
class MySettings:
    show_dates: bool = True


class Theme(BaseTheme):
    config_class = MySettings
```

`self.config.show_dates` is then the field default, replaced by `"show_dates"` in `theme.json`, replaced by the block named after the theme in `repo.json`: `"mytheme": {"show_dates": false}`. A value of the wrong type stops the build with a message naming the key; an unknown key in the block logs `THEME_SETTING_UNKNOWN` and makes `kb4it verify` fail. Without `config_class`, `self.config.get("name")` reads `theme.json`.

## Templates {#templates}

Templates use [Mako](https://www.makotemplates.org/): `${var['repo']['title']}` prints a value, and `% for` ... `% endfor` repeats a block. `var['repo']` holds every key of `repo.json`. A template is looked up in the site's overrides, then the theme, then its `template_base`, then KB4IT's shared templates, so a theme on the `uikit` base only holds the templates it changes.

`HTML_BODY` and `PAGE_INDEX` are always required, `PAGE_KEY` and `PAGE_KEY_VALUE` too with `property_pages`, and each feature needs the templates the reference lists. A missing one stops the build with `TEMPLATE_MISSING`. `kb4it theme-info mytheme` shows where each template comes from.

## Escaping {#escaping}

Titles, property values and `repo.json` settings are written by people, and may hold `<`, `"` or a whole `<script>`. With `"autoescape": true` in `theme.json`, every `${...}` is HTML-escaped, so such text shows as text. A value that is HTML on purpose, such as the compiled body of a document or a fragment your `theme.py` built, must be printed raw with `| n`:

```html
<title>${var['title']}</title>       <!-- escaped -->
<main>${var['body'] | n}</main>      <!-- HTML, printed as it is -->
```

Only use `| n` for HTML that KB4IT or your theme built; never for a value taken from a document as it is. `scripts/devel/escape_audit.py mytheme --raw` (in the KB4IT sources) lists the raw expressions of a theme for review. KB4IT's shared templates are always escaped. A theme without `"autoescape": true` prints values as they are, and every build warns with `[BUILDER] THEME_AUTOESCAPE_OFF`.

## Shared libraries {#assets}

UIkit, highlight.js, DataTables and the search engine come with KB4IT, one copy each. The features add the ones they use; list the others your pages load in `theme.json`:

```json
"assets": ["uikit", "highlight"]
```

Each is copied to `resources/vendor/<name>/` in the website, so templates link `resources/vendor/uikit/css/uikit.min.css`. The names are `highlight`, `uikit`, `datatables`, `search`, `tablefilter` and `gallery`. An unknown name stops the build.

## Checks after the build {#checks}

After every build KB4IT reads the pages of the website and logs each link to a missing page or section as `[CHECK] ANCHOR_MISSING`. Add your own checks in `checks(site)`, which returns a list of `Problem`:

```python
import os

from kb4it.theme import Problem

    def checks(self, site):
        """The shared link check, then mine."""
        problems = super().checks(site)
        if not os.path.isfile(os.path.join(site.paths.target, "index.html")):
            problems.append(Problem("HOME_MISSING", "", "page=index.html", severity="error"))
        return problems
```

An `error` stops the build; with `"strict": true` in `repo.json`, a warning does too. `after_checks(site)` runs only when the checks pass. See [Post-build checks](reference-log-codes.md#checks).

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
| `kb4it` | The KB4IT versions the theme works with, such as `">=X.Y.Z"` or `">=X.Y.Z, <A.B.C"` |
| `favicon` | Path of the theme's icon inside the theme folder, such as `images/logo.svg`. Pages use it when `repo.json` has no `logo`. The folder must be in `deploy_dirs` if you set that list |
| `deploy_dirs` | Only these folders of the theme are copied to the website, for example `["framework"]` |
| `assets` | Shared libraries the theme's pages load besides the ones its features add. See [Shared libraries](#assets) |
| `autoescape` | `true` escapes every value the templates print, except those marked raw. See [Escaping](#escaping) |
| `editor` | `true` or `false`: whether the Add page is on when `repo.json` has no `editor` key (feature `editor`) |
| `template_base` | Name of a set of templates bundled with KB4IT that the theme builds on, such as `"uikit"`, the UIkit layout techdoc and blog share |
| `heading_classes` | Classes of the headings and section wrappers of a document page: keys `h2`, `h3`, `h4` and `sect1` to `sect4`, for example `{"h2": "uk-card-title"}`. A key you leave out keeps its default |

`search`, `metadata_pages` and the `assets` of the features come from the features; leave them out of `theme.json`.

## Theme version and fingerprint {#version}

A theme is identified by its `version` and by a fingerprint: 12 characters computed from every file of the theme folder (except `apps/`), its template base and KB4IT's shared templates. A file changed, added or renamed gives another fingerprint, even when you forget to raise the version.

The pair shows as `mytheme 1.0.0+3f9a1c0b7e21`:

- in `kb4it themes` and `kb4it doctor`, with the folder the theme is loaded from;
- in the `[WORKFLOW] SUMMARY` line of every build, as `theme=mytheme/1.0.0+3f9a1c0b7e21`;
- in the `generator` meta tag of the pages of the bundled themes.

The fingerprint is part of the build cache. When it changes, the next build rebuilds every page, so you never need `--force` after editing a theme.

## Look inside a theme {#theme-info}

`kb4it theme-info mytheme` (or the theme's folder) prints, without building a site, the features in the order they run, every hook the theme fills with its file and line, the options it sets, where each template comes from and its settings. Use `--repo` with a site's `repo.json` to see that site's template overrides and settings. See [Look inside a theme](reference-command-line.md#theme-info).

## Add the editor page {#editor}

The [Add page](howto-write-document-editor.md) is the `editor` feature:

1. Add `"editor"` to `features`.
2. Link to `add.html` where your layout shows its links, only when `var['editor']` is true:

        % if var['editor']:
        <a href="add.html">Add document</a>
        % endif

3. Set `"editor": true` in `theme.json` to have the page on by default; `repo.json` `"editor"` wins.

Optionally, ship skeletons in `templates/skeletons/`: `*-SKELETON.md` files and a `skeletons.json`, as described in [Use your own skeletons](howto-write-document-editor.md#skeletons). The page uses the common `PAGE_ADD.tpl`; put a `PAGE_ADD.tpl` in `templates/` to replace the cards. Do not replace `EDITOR_DIALOGS.tpl`. The hooks `editor_keys()` (more values for completion) and `register_add_page(html)` (wrap the page your way) change it; `profile_skeleton = False` leaves out the Person profile skeleton.

## Check the sources with kb4it verify {#verify}

A file `logic/verify.py` with a function `verify(repo, docs)` runs during `kb4it verify`. `docs` maps each file name to its properties. Return a list of problem messages, empty when all is well. It imports the theme's other modules relatively, like `theme.py`.

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

## A theme on Builder or DocumentTheme {#legacy}

Themes written before `kb4it.theme` subclass `Builder` or `DocumentTheme` and add mixins to their class line. They keep working, and a build logs `THEME_API_LEGACY` for them. [Theme internals](dev-theme-internals.md#migrate) says what replaces each part, step by step.

---
DocType: Reference
Feature: Configuration
HelpId: repo-json
Keyword: settings, config, repo.json, version, sanitize, nh3, title, theme, source, target, workers, ignored_keys, publish_sources, fail_on_invalid, theme_path, force, search, site_url, sitemap, robots.txt, feed, atom, rss, overrides, hooks, backlinks, linked from, og_image, open graph, description, seo, json-ld, schema.org, structured data, lang, language, index, noindex, noindex_keys, robots, search engines, Modified, dateModified, markdown, extensions, pymdownx, highlight, pygments, syntax highlighting
Level: basic
Order: 620
Section: Reference
Summary: Every setting of config/repo.json shared by all themes, with its default.
---

# Repository settings

Each knowledge base has its settings in `config/repo.json`. `kb4it create` writes a complete one for the theme you chose.

```json
{
    "title": "Ops Knowledge Base",
    "tagline": "Runbooks, incidents and changes",
    "theme": "techdoc",
    "source": "source",
    "target": "target"
}
```

## Required {#required}

| Key | Meaning |
|---|---|
| `title` | Name of the site, shown in the header and the browser tab |
| `theme` | Theme name, see [Themes](explanation-themes.md) |
| `source` | Folder with the documents |
| `target` | Folder where the website is written |

A missing key stops the build with `CONFIG_KEY_MISSING key=...`.

`source` and `target` are relative to the knowledge base folder, the one that holds `config/`. Absolute paths, `~` and `$VARIABLES` also work.

KB4IT removes from `target` the pages of documents you deleted. It only removes pages it wrote itself, so other files you keep in `target` stay; still, `target` must be a folder of its own. The build stops with an error when `target` is the knowledge base folder, `source`, `config/`, `var/`, your home folder or a filesystem root, when it holds any of them, or when it lies inside `source`.

## Optional {#optional}

| Key | Default | Meaning |
|---|---|---|
| `tagline` | | Short subtitle |
| `logo`, `logo_alt` | theme logo | Logo image, relative to the website, and its text for screen readers; empty uses the site `title`. The logo is also the favicon of every page; without `logo`, the page uses the theme's own logo |
| `workers` | half the processor cores | Documents converted at the same time |
| `force` | `false` | Rebuild everything on every build, like `--force` |
| `ignored_keys` | `[]` | Properties that get no pages; see [properties](explanation-properties.md#excluded) |
| `publish_sources` | `true` | Copy the `.md` files to the website, in `target/sources/` |
| `fail_on_invalid` | `false` | Stop the build when a document cannot be read |
| `theme_path` | | Use the theme in this folder instead of searching by name |
| `site_url` | | Public address of the site, such as `https://me.github.io/kb/`. Needed for `sitemap.xml`, the feed and canonical links; changing it rebuilds every page |
| `seo` | | Language of the pages and structured data for search engines; see [structured data](#seo) |
| `og_image` | | Image shown when a page is shared on social networks, a path inside the website such as `resources/share.png`; needs `site_url` |
| `sitemap` | `true` | With `site_url`, write `sitemap.xml` and `robots.txt`; a `robots.txt` in `source/` is used instead of the generated one. See [Search engines](#indexing) for `seo.index` |
| `backlinks` | `true` | At the end of each document, list the documents that link to it ("Linked from"); `false` hides the list |
| `feed` | blog: on; techdoc, bookshelf: off | Atom feed `feed.xml`, see [feed](#feed) |
| `hooks` | | Python file with build hooks, such as `hooks/hooks.py`; see [Run your own code during a build](howto-hooks.md) |
| `overrides` | `overrides` | Folder with templates and files that replace or extend the theme's; see [Change one template of a theme](howto-customize-templates.md) |
| `search` | `true` | Full-text search in techdoc, blog and bookshelf; `false` removes the search box, `search.html` and `search-index.js`. See [search](#search) |
| `editor` | techdoc: on; blog, bookshelf, apphelp: off | Add page (`add.html`) with a Markdown editor for new documents. `true` or `false`; any other value stops the build. `false` removes the page and the link to it |
| `git`, `git_server`, `git_user`, `git_repo`, `git_branch`, `git_path` | `false` | Edit links to your git server; see each theme for the format. They appear only with `"git": true` and `git_server`, `git_user`, `git_repo` and `git_branch` all set; `git_path` may stay empty |

## Markdown {#markdown}

The optional `markdown` block adds python-markdown extensions to the built-in ones (`extra`, `admonition`, `toc`, `sane_lists`).

```json
"markdown": {
    "extensions": ["pymdownx.tasklist", "pymdownx.details", "nl2br"],
    "extension_configs": {
        "pymdownx.tasklist": {"custom_checkbox": true}
    }
}
```

| Key | Default | Meaning |
|---|---|---|
| `extensions` | `[]` | Extension names, as python-markdown expects them. Extensions that ship with python-markdown work right away; others must be installed where KB4IT runs |
| `extension_configs` | `{}` | Settings per extension |
| `highlight` | `client` | How code blocks are coloured: `client` (highlight.js in the browser, as before), `pygments` (at build time, no JavaScript), or `none` |
| `pygments_style` | `default` | [Pygments style](https://pygments.org/styles/) for light colour schemes, with `pygments` |
| `pygments_style_dark` | `monokai` | Pygments style for dark colour schemes, with `pygments` |
| `sanitize` | `false` | `true` removes scripts, event handlers, `javascript:` links and any other markup Markdown does not make from each document. Needs nh3, part of the extras. See [Raw HTML](reference-document-format.md#raw-html) |

With `"highlight": "pygments"` the build writes `resources/pygments.css`, and the pages no longer load highlight.js. Code blocks without a language are left plain.

With `pymdownx.superfences` (or `pymdownx.highlight`), code blocks follow `highlight` too: KB4IT sets `use_pygments` of `pymdownx.highlight` to `true` only in `pygments` mode, so in `client` mode highlight.js colours them. A `use_pygments` of your own in `extension_configs` wins.

Changing the block rebuilds every page. An extension that is not installed stops the build with `MD_EXTENSION_MISSING name=... hint=pip install ...`; `kb4it verify` reports it too.

The [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/) (task lists, tabs, details, keys and more) install with KB4IT. The sample repositories of every theme turn on `pymdownx.tasklist`, so `kb4it create` makes a repository with task lists. The extras, `uv tool install "KB4IT[extras]"` or `pipx install "KB4IT[extras]"`, bring [nh3](https://nh3.readthedocs.io/), which `sanitize` needs.

## Search {#search}

techdoc, blog and bookshelf build `search-index.js` with the text of every document, split by section, and a `search.html` page. Search runs in the browser, so it also works when you open the site from disk. Results link to the section that matched. The search page offers filters by `Category`, `WorkType` and `Tag`, for the keys your documents use.

The index grows with your documents; above 5 MB the build warns with `[SEARCH] INDEX_LARGE`. Turn it off with `"search": false`. apphelp has its own search, configured in its `apphelp` block.

## Page metadata {#metadata}

Every page gets a short description and [Open Graph](https://ogp.me/) tags, so links shared in chats and social networks show a title and a summary. The description is the document's `Summary` property, or its first lines cut to 160 characters; pages that are not documents use `tagline`. With `site_url` set, each page also gets a canonical link and its full address, and `og_image` adds a preview image.

The tags come from the template `HTML_HEAD_META.tpl`, which a theme can replace.

## Language and structured data {#seo}

Every page also carries structured data: a [schema.org](https://schema.org/) description in JSON-LD that search engines, enterprise search tools and link previews read. A document becomes an article whose type follows its `DocType` (`How-to guide` is a how-to, `Reference` a technical article, `Explanation` an article), with its title, `Summary`, `Date`, author and the properties listed below. The home page describes the website and, when the site has a search page, how to search it. Absolute addresses need `site_url`; without it the data is still written, without them.

```json
"seo": {
  "lang": "es",
  "index": true,
  "noindex_keys": true,
  "structured_data": true,
  "map": {"Team": "contributor:Organization", "Scope": null}
}
```

| Key | Default | Meaning |
|---|---|---|
| `lang` | `en` | Language of the pages: `<html lang>` and the structured data. A language tag such as `en`, `es` or `pt-BR`. apphelp's own `apphelp.lang` wins when both are set. A tag with a region (`es-ES`) also gives the Open Graph locale (`es_ES`) |
| `index` | not set | `true`: search engines may index the site. `false`: they may not. Not set: as `true`, and the build reminds you to decide. See [Search engines](#indexing) |
| `noindex_keys` | `true` | Asks search engines not to list the pages that only list documents: property, value, event, stats, bookmarks and all-documents pages |
| `structured_data` | `true` | `false` leaves the JSON-LD out of every page |
| `map` | | Changes which properties go into the structured data: `"Property": "schemaProperty"`, `"Property": "schemaProperty:Type"` for a typed value, or `null` to leave a property out |

Properties KB4IT maps by default:

| Property | schema.org | Themes |
|---|---|---|
| `Author` | `author` (Person) | all |
| `Tag` | `keywords` | all |
| `Topic` | `about` | all |
| `Category` | `genre`; in blog, `articleSection` | all |
| `WorkType` | `genre` | all |
| `Scope` | `audience` | all |
| `Product`, `OS`, `Database` | `mentions` (SoftwareApplication) | all |
| `Protocol` | `mentions` (DefinedTerm) | all |
| `Project` | `isPartOf` (CreativeWorkSeries) | all |
| `Status` | `creativeWorkStatus`; not in bookshelf, where it is reading progress | all |
| `Book`, `Chapter`, `Command` | `isPartOf` (Book), `position`, `mentions` (DefinedTerm) | bookshelf |
| `Feature`, `Level`, `Platform`, `Since`, `Keyword`, `Plugin`, `Section` | `about`, `educationalLevel`, `audience`, `version`, `keywords`, `mentions`, `articleSection` | apphelp |

A document with no known `DocType` is a technical article in techdoc and apphelp, a blog post in blog and a chapter in bookshelf. `Title`, `Summary`, `Date`, `Modified` and `DocType` are always used and cannot be mapped; properties in `ignored_keys` are never written. A malformed `seo` block stops the build with a message naming the entry. Changing `seo` rebuilds every page.

The date a document last changed (`dateModified` in the structured data, `article:modified_time` in the Open Graph tags and `<lastmod>` in `sitemap.xml`) is, in this order:

1. The document's [`Modified`](reference-document-format.md#dates) property.
2. The date of the last commit that changed the file, when the knowledge base is in a git repository. KB4IT reads all dates with one `git log` per build and keeps them in `var/db/gitdates.json` until the next commit. Without git, it goes on to the next step.
3. The time the file was last saved.

The value is never older than `Date`; when it would be, `Date` is used. A page is rebuilt when this date changes, for example after a commit, so the page and the sitemap always agree.

Document pages also get the Open Graph article tags: `article:published_time` from `Date`, `article:modified_time`, one `article:author` per `Author`, `article:section` from the first `Category` and one `article:tag` per `Tag`.

### Search engines {#indexing}

`seo.index` decides, for the whole site, whether search engines may index it. There is no setting per document.

| `seo.index` | Pages | `robots.txt` | `sitemap.xml` |
|---|---|---|---|
| `false` | Every page has `<meta name="robots" content="noindex, nofollow">` | `Disallow: /` for every crawler, even without `site_url` | Not written; an old one is removed |
| `true` | Indexable | With `site_url`, allows everything and names the sitemap | With `site_url` |
| not set | As `true` | As `true` | As `true` |

While `seo.index` is not set, every build logs `[SEO] INDEX_UNSET` and `kb4it verify` shows a notice asking you to decide. It is not an error. `kb4it create --index yes|no` and the **Allow search engines** choice of the [terminal interface](howto-use-tui.md#add) write it for you.

With `noindex_keys` on (the default), the pages that only list documents carry `noindex, follow`: search engines follow their links to the documents but do not list the pages themselves, and the pages leave `sitemap.xml`. These are the property, value, properties, event (day, month and year), stats, bookmarks and all-documents pages of techdoc, blog and bookshelf. apphelp has none; its `topics.html` stays indexable.

The `404.html` page, the Add page (`add.html`) and the techdoc `admin/` page always carry `noindex`. A template or an override that writes its own `<meta name="robots">` tag wins over the one KB4IT adds.

A `robots.txt` in `source/` is always used instead of the generated one. KB4IT never replaces or deletes a `robots.txt` in `target/` that it did not write; the build logs `ROBOTS_KEPT` instead.

## Feed {#feed}

With `site_url` set, the blog theme writes an Atom feed, `feed.xml`, with the newest dated documents. techdoc and bookshelf write one when you turn it on:

```json
"feed": {"enabled": true, "limit": 20, "categories": ["Post", "Note"], "full_content": true}
```

| Key | Default | Meaning |
|---|---|---|
| `enabled` | blog `true`, others `false` | Write the feed |
| `limit` | `20` | Number of entries, newest first |
| `categories` | all | Only documents with one of these `Category` or `WorkType` values |
| `full_content` | `true` | The whole document in each entry; `false` uses `Summary` or the first lines |

Documents without a `Date` are not in the feed.

## Theme settings {#theme}

Each theme reads its own keys as well:

- [techdoc](reference-theme-techdoc.md#settings): `datatable`, `events`, `admin`, `quality`
- [blog](reference-theme-blog.md#settings): `index_posts`, `strict`, `datatable`
- [bookshelf](reference-theme-bookshelf.md#settings): `datatable`
- [apphelp](reference-theme-apphelp.md#settings): the `apphelp` block and `version`

`version` is the version of the application the help describes. apphelp shows it on the home page, next to the pages new in that version, and uses it to name the folder of each version; see [versions](reference-theme-apphelp.md#versions). The value `"kb4it"` stands for the version of the installed KB4IT. The other themes ignore it.

Sample apps from older versions also contain `menu`, `sort`, `timeline` and `webserver`. KB4IT no longer reads them; you can leave them or delete them.

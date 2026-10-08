---
DocType: Reference
Feature: Configuration
HelpId: repo-json
Keyword: settings, config, repo.json, title, theme, source, target, workers, ignored_keys, publish_sources, fail_on_invalid, theme_path, force, search, site_url, sitemap, robots.txt, feed, atom, rss, markdown, extensions, pymdownx, highlight, pygments, syntax highlighting
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

## Optional {#optional}

| Key | Default | Meaning |
|---|---|---|
| `tagline` | | Short subtitle |
| `logo`, `logo_alt` | theme logo | Logo image, relative to the website, and its text |
| `workers` | half the processor cores | Documents converted at the same time |
| `force` | `false` | Rebuild everything on every build, like `--force` |
| `ignored_keys` | `[]` | Properties that get no pages; see [properties](explanation-properties.md#excluded) |
| `publish_sources` | `true` | Copy the `.md` files to the website, in `target/sources/` |
| `fail_on_invalid` | `false` | Stop the build when a document cannot be read |
| `theme_path` | | Use the theme in this folder instead of searching by name |
| `site_url` | | Public address of the site, such as `https://me.github.io/kb/`. Needed for `sitemap.xml`, the feed and canonical links; changing it rebuilds every page |
| `sitemap` | `true` | With `site_url`, write `sitemap.xml` and `robots.txt`; a `robots.txt` in `source/` is used instead of the generated one |
| `feed` | blog: on; techdoc, bookshelf: off | Atom feed `feed.xml`, see [feed](#feed) |
| `search` | `true` | Full-text search in techdoc, blog and bookshelf; `false` removes the search box, `search.html` and `search-index.js`. See [search](#search) |
| `git`, `git_server`, `git_user`, `git_repo`, `git_branch`, `git_path` | `false` | Edit links to your git server; see each theme for the format |

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

With `"highlight": "pygments"` the build writes `resources/pygments.css`, and the pages no longer load highlight.js. Code blocks without a language are left plain.

Changing the block rebuilds every page. An extension that is not installed stops the build with `MD_EXTENSION_MISSING name=... hint=pip install ...`; `kb4it verify` reports it too.

The [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/) (task lists, tabs, details, keys and more) install with KB4IT when you ask for its extras: `uv tool install "KB4IT[extras]"` or `pipx install "KB4IT[extras]"`.

## Search {#search}

techdoc, blog and bookshelf build `search-index.js` with the text of every document, split by section, and a `search.html` page. Search runs in the browser, so it also works when you open the site from disk. Results link to the section that matched.

The index grows with your documents; above 5 MB the build warns with `[SEARCH] INDEX_LARGE`. Turn it off with `"search": false`. apphelp has its own search, configured in its `apphelp` block.

## Feed {#feed}

With `site_url` set, the blog theme writes an Atom feed, `feed.xml`, with the newest dated documents. techdoc and bookshelf write one when you turn it on:

```json
"feed": {"enabled": true, "limit": 20, "categories": ["Post", "Note"], "full_content": true}
```

| Key | Default | Meaning |
|---|---|---|
| `enabled` | blog `true`, others `false` | Write the feed |
| `limit` | `20` | Number of entries, newest first |
| `categories` | all | Only documents with one of these `Category` values |
| `full_content` | `true` | The whole document in each entry; `false` uses `Summary` or the first lines |

Documents without a `Date` are not in the feed.

## Theme settings {#theme}

Each theme reads its own keys as well:

- [techdoc](reference-theme-techdoc.md#settings): `datatable`, `events`, `admin`
- [blog](reference-theme-blog.md#settings): `index_posts`, `strict`, `datatable`
- [bookshelf](reference-theme-bookshelf.md#settings): `datatable`
- [apphelp](reference-theme-apphelp.md#settings): the `apphelp` block

Sample apps from older versions also contain `menu`, `sort`, `timeline` and `webserver`. KB4IT no longer reads them; you can leave them or delete them.

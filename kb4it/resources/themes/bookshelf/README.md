# Bookshelf theme

The bookshelf theme builds a study library. It arranges your notes as books, parts and chapters on a shelf. Create a site with `kb4it create bookshelf <path>`.

## Minimum core

A new `config/repo.json` needs these four keys:

```json
{
    "source": "source",
    "target": "target",
    "theme": "bookshelf",
    "title": "My Study Library"
}
```

| Key | Meaning |
| --- | --- |
| `source` | Folder with your Markdown documents |
| `target` | Folder where the site is written |
| `theme` | Must be `bookshelf` |
| `title` | Library name, shown in the header and the browser tab |

Tested: these four keys and one plain document build with exit code 0.

## Document properties

Bookshelf places each document with these properties:

| Property | Used for |
| --- | --- |
| `Book` | The book the note belongs to |
| `Part` | The part of the book |
| `Chapter` | The chapter of the part |
| `PartTitle` | Name of the part, shown in the book overview |
| `Status` | Reading progress: `Done`, `Reading` or nothing for to do |
| `Command` | Commands the chapter teaches; each one gets its own page |

Documents without these properties still build, but they may show up in the wrong place or not at all. Set them for every note you want on the shelf.

## Configuration file

Every setting lives in `config/repo.json`. `kb4it create` writes a complete one. The [repository settings](../../../../help/source/reference-repo-json.md) page explains each key in more detail.

### Required keys

| Key | Values | Meaning |
|---|---|---|
| `title` | Text | Library name, shown in the header and the browser tab |
| `theme` | `bookshelf` | Theme of the site |
| `source` | Folder path | Folder with your Markdown documents |
| `target` | Folder path | Folder where the site is written; it must be a folder of its own |

`source` and `target` are relative to the knowledge base folder, the one that holds `config/`. Absolute paths, `~` and `$VARIABLES` also work. A missing key stops the build with `CONFIG_KEY_MISSING`.

### Common keys

These keys are optional. Add one only to change its default.

| Key | Values | Default | Meaning |
|---|---|---|---|
| `tagline` | Text | empty | Short subtitle |
| `logo` | Path inside the website | theme logo | Logo image; also the favicon of every page |
| `logo_alt` | Text | empty | Text of the logo for screen readers; empty uses `title` |
| `workers` | Integer, 1 or more | half the processor cores | Documents converted at the same time |
| `force` | `true`, `false` | `false` | Rebuild everything on every build, like `--force` |
| `ignored_keys` | List of property names | `[]` | Properties that get no pages |
| `hidden_properties` | List of property names | `[]` | Properties left out of the properties page; they keep their pages |
| `publish_sources` | `true`, `false` | `true` | Copy the `.md` files to `target/sources/` |
| `fail_on_invalid` | `true`, `false` | `false` | Stop the build when a document cannot be read |
| `theme_path` | Folder path | empty | Use the theme in this folder instead of searching by name |
| `overrides` | Folder path | `overrides` | Templates and files that replace or extend the theme's |
| `hooks` | Path to a Python file | empty | Build hooks, such as `hooks/hooks.py` |
| `site_url` | URL ending in `/` | empty | Public address of the site. Needed for `sitemap.xml`, the feed, canonical links and absolute addresses in the structured data; changing it rebuilds every page |
| `og_image` | Path inside the website | empty | Image for links shared on social networks; needs `site_url` |
| `sitemap` | `true`, `false` | `true` | With `site_url`, write `sitemap.xml` and `robots.txt`. A `robots.txt` in `source/` wins |
| `backlinks` | `true`, `false` | `true` | List the documents that link to each document ("Linked from") |
| `search` | `true`, `false` | `true` | Full-text search; `false` removes the search box, `search.html` and `search-index.js` |
| `editor` | `true`, `false` | `false` | Add page (`add.html`) with a Markdown editor; any other value stops the build |
| `timezone` | IANA zone name, such as `Europe/Madrid` | the computer's zone | Zone of every date written without an offset. An unknown name falls back to the computer's zone |
| `git` | `true`, `false` | `false` | Edit links to your git server. They appear only with `git_server`, `git_user`, `git_repo` and `git_branch` all set |
| `git_server` | Full URL, such as `https://github.com` | empty | Git server of the edit links |
| `git_user` | Text | empty | User or organisation on the git server |
| `git_repo` | Text | empty | Repository name |
| `git_branch` | Text | empty | Branch the edit links open |
| `git_path` | Folder path inside the repository | empty | Folder that holds the documents; empty for the repository root |

#### `markdown` block

Adds python-markdown extensions to the built-in ones (`extra`, `admonition`, `toc`, `sane_lists`). Changing it rebuilds every page.

```json
"markdown": {
    "extensions": ["pymdownx.tasklist"],
    "extension_configs": {"pymdownx.tasklist": {"custom_checkbox": true}},
    "highlight": "client"
}
```

| Key | Values | Default | Meaning |
|---|---|---|---|
| `extensions` | List of extension names | `[]` | Extensions to load; one that is not installed stops the build with `MD_EXTENSION_MISSING` |
| `extension_configs` | Object: extension name to settings | `{}` | Settings per extension |
| `highlight` | `client`, `pygments`, `none` | `client` | Code colouring: highlight.js in the browser, Pygments at build time, or none |
| `pygments_style` | Pygments style name | `default` | Style for light colour schemes, with `pygments` |
| `pygments_style_dark` | Pygments style name | `monokai` | Style for dark colour schemes, with `pygments` |
| `sanitize` | `true`, `false` | `false` | Remove scripts, event handlers and other raw markup from each document; needs nh3 (`KB4IT[extras]`) |

#### `seo` block

Language of the pages and structured data (JSON-LD) for search engines. Changing it rebuilds every page.

```json
"seo": {"lang": "es", "index": true, "noindex_keys": true, "structured_data": true, "map": {"Team": "contributor:Organization"}}
```

| Key | Values | Default | Meaning |
|---|---|---|---|
| `lang` | Language tag (`en`, `es`, `pt-BR`) | `en` | `<html lang>` and the language of the structured data |
| `index` | `true`, `false` | not set (acts as `true`, with a reminder) | `false` asks search engines not to index the site: `noindex` on every page, `Disallow: /` in `robots.txt`, no sitemap |
| `noindex_keys` | `true`, `false` | `true` | Keep the pages that only list documents out of search engines and the sitemap |
| `structured_data` | `true`, `false` | `true` | `false` leaves the JSON-LD out of every page |
| `map` | Object: property to `"schemaProperty"`, `"schemaProperty:Type"` or `null` | built-in map | Changes which properties go into the structured data; `null` leaves one out |

#### `feed` block

Atom feed `feed.xml` with the newest dated documents. Needs `site_url`. Documents without `Date` are left out.

```json
"feed": {"enabled": true, "limit": 20, "categories": ["Post", "Note"], "full_content": true}
```

| Key | Values | Default | Meaning |
|---|---|---|---|
| `enabled` | `true`, `false` | `false` | Write the feed |
| `limit` | Integer | `20` | Number of entries, newest first |
| `categories` | List of `Category` or `WorkType` values | all | Only documents with one of these values |
| `full_content` | `true`, `false` | `true` | The whole document in each entry; `false` uses `Summary` or the first lines |

#### `profiles` block

Says what the profiles of each property do. A profile is a source named `PROFILE-<NAME>.md` with `ProfileOf: <Property>`. Without the block, `Author` is a person with the defaults below.

```json
"profiles": {
    "Author": {"type": "Person", "contact_keys": ["Email", "Phone", "Chat", "Url"], "missing": "penalty"},
    "Team": {"type": "Organization", "missing": "notice"}
},
"profiles_private": ["Phone"]
```

| Key | Values | Default | Meaning |
|---|---|---|---|
| `type` | schema.org type | `Thing` | `Person` makes the values people, with person pages |
| `contact_keys` | List of profile properties | none | Properties that tell readers how to reach it |
| `missing` | `penalty`, `notice`, `none` | `none` | What a value without a profile does; for now only `notice` acts (`VALUE_NO_PROFILE` in `kb4it verify`) |
| `tip` | List of profile properties | none | Reserved for value tooltips; not used yet |
| `map` | Same syntax as `seo.map` | none | Profile property to schema.org property |

`profiles_private` (list of profile properties, default `[]`) keeps those properties out of the pages and the structured data. The older `people` block (`keys`, `contact_keys`, `private`, `map`) is still read when `profiles` is absent, with a `PEOPLE_BLOCK_DEPRECATED` warning.

#### `dates` block

Declares more date properties. The built-in ones are `Date`, `Modified`, `Start`, `End`, `ScheduledStart`, `ScheduledEnd`, `DowntimeStart`, `DowntimeEnd`, `DetectedDate`, `ResolvedDate`, `DueDate`, `ExpiryDate` and `ReviewDate`.

```json
"dates": {
    "WarrantyStart": {"group": "start"},
    "WarrantyEnd": {"group": "end", "closes": "WarrantyStart"}
}
```

| Key | Values | Default | Meaning |
|---|---|---|---|
| `group` | `start`, `end` | required | Whether the property opens or closes a period |
| `closes` | A start property | `Date` | The start this end belongs to |
| `supersedes` | `true`, `false` | `false` | The pair overrides `Start` and `End`, like `ScheduledStart` |

A bad entry is ignored and logged under `[DATES]`; it never stops the build.

### bookshelf keys

| Key | Values | Default | Meaning |
|---|---|---|---|
| `datatable` | List of property names | `["Date", "Title", "Chapter"]` | Columns of the document tables. The `default` app adds Author and Status |

With `editor` on, the Add page offers `CHAPTER-SKELETON.md` (`Author`, `Book`, `Part`, `Chapter`, `Date`, `Status`). Put your own in `templates/skeletons/` of the repository overrides to replace it.

### Keys no longer read

Older sample apps also hold `sort`, `timeline` and `webserver`, and `menu`. KB4IT ignores them; you can delete them.

## Sample app

The `default` app has five sample chapters in two books. `Sample Book` explains the properties in two parts. `Linux Basics` shows a study book with `Command` values. Copy a chapter to start your own, or delete them.

See [reference-theme-bookshelf.md](../../../../help/source/reference-theme-bookshelf.md) for the full theme reference.

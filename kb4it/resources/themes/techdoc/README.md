# Techdoc theme

Techdoc builds a site for technical documents: runbooks, changes, incidents, meetings and notes. Create a site with `kb4it create techdoc <path>`.

## Minimum core

A new `config/repo.json` needs these four keys:

```json
{
    "source": "source",
    "target": "target",
    "theme": "techdoc",
    "title": "My Knowledge Base"
}
```

| Key | Meaning |
| --- | --- |
| `source` | Folder with your Markdown documents |
| `target` | Folder where the site is written |
| `theme` | Must be `techdoc` |
| `title` | Site name, shown in the header and the browser tab |

Tested: a folder with these four keys and one valid document builds.

## Document properties

Techdoc uses these properties from each document:

| Property | Used for |
| --- | --- |
| `Category` | The form of the document: `Procedure`, `Note`, `Report`, `Template`, `Post`, `Record` or `Minutes` |
| `WorkType` | `Knowledge` for a knowledge document, or the type of work a record holds: `Change`, `Incident`, `Task` or `Meeting`. Drives the latest changes and incidents, **Open items** and the calendar |
| `Date` | Dates the document; it appears in the calendar when its `WorkType` (or, without one, its `Category`) is listed in `events` |
| `DocType` | `Tutorial`, `How-to guide`, `Reference` or `Explanation`; fills the dashboard cards and the quality score |
| `Status` | `Draft` shows a draft banner; `Obsolete`, `Deprecated`, `Withdrawn` and `Rejected` mark the document as retired |
| `Summary` | One line shown under the title |

`WorkType: Knowledge` goes with `Category: Procedure`, `Note`, `Post`, `Report` or `Template`; a change, incident or task record has `Category: Record`; meeting notes have `Category: Minutes`. The quality score checks the pair (`work_categories` in the `quality` block of `theme.json`). Every other property is optional. Add `Tag`, `Topic`, `Scope`, `Priority` and the rest when you need them.

## Configuration file

Every setting lives in `config/repo.json`. `kb4it create` writes a complete one. The [repository settings](../../../../help/source/reference-repo-json.md) page explains each key in more detail.

### Required keys

| Key | Values | Meaning |
|---|---|---|
| `title` | Text | Site name, shown in the header and the browser tab |
| `theme` | `techdoc` | Theme of the site |
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
| `editor` | `true`, `false` | `true` | Add page (`add.html`) with a Markdown editor; any other value stops the build |
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

### techdoc keys

| Key | Values | Default | Meaning |
|---|---|---|---|
| `datatable` | List of property names, plus `Quality` | `["Date", "Title"]` | Columns of the document tables. A column empty in every row of a table is left out. `Scope` is never shown. `Quality` adds the quality meter and tier |
| `events` | List of `WorkType` values, or `Category` values for documents without a `WorkType` | `[]` | Documents that count as events: calendar, events archive and the Activity card |
| `admin` | `true`, `false` | `false` | `true` builds the `admin/` page with the source and site backup zips |
| `quality` | `true`, `false` | `true` | `false` removes the quality score, the Quality tab, the search chip and `quality-index.js` |
| `toc_sidebar` | `true`, `false` | `toc_sidebar` of `theme.json` (`false`) | Second table of contents in a right column, with Expand all and Collapse all, for documents with four or more sections on screens 1400 pixels or wider |
| `menu` | List of property names | `[]` | Order of the property buttons on the Gallery and Diagrams pages: listed keys first, the rest by name. The navigation menu is not set here: it is built from the properties your documents use |

The `default` app sets `datatable` to Date, Title, Category, WorkType, Priority, Status and Topic, and lists every work type and category in `events`.

The document page also reads `header_keys`, `info_groups`, `info_tabs`, `table_filter`, `toc_sidebar` and the `quality` block from the theme's own `theme.json`. Those are theme settings, not `repo.json` keys: to change them, copy the theme.

### Keys no longer read

Older sample apps also hold `sort`, `timeline` and `webserver`. KB4IT ignores them; you can delete them.

## Sample apps

`kb4it create techdoc <path>` starts from the `default` app; `kb4it create techdoc sapbasis <path>` from `sapbasis`. Every sample uses the sections of its skeleton on the Add page, so each one is also a model of a well-scored document. Names, hosts and system ids in them are made up.

| App | Samples |
|---|---|
| `default` | A daily backup check (procedure), a disk full incident, the change that followed it, the weekly operations meeting, an open certificate renewal task, a note on RAID levels and a draft capacity report |
| `sapbasis` | Checking failed background jobs (`SM37`), analysing a short dump (`ST22`), a memory dump incident in a nightly job, a planned kernel update and a note on the transport landscape (`STMS`). The menu adds SAP properties such as `SID`, `Transaction`, `Job` and `Dump` |

Copy a sample to start a new document, or delete the samples once you have your own.

See [reference-repo-json.md](../../../../help/source/reference-repo-json.md) for every key.

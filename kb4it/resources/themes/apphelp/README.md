# AppHelp theme

AppHelp builds a help site for an application. The site works when opened from disk (`file://`), when served from a subpath such as GitHub Pages, and inside the application's own web view (`?embed=1`).

Create a site with `kb4it create apphelp <path>`; the sample in `apps/default/` shows every page type.

## Minimum core

A new `config/repo.json` needs these four keys, plus an `apphelp` block that lists the allowed `Feature` values:

```json
{
    "source": "source",
    "target": "target",
    "theme": "apphelp",
    "title": "My App Help",
    "apphelp": {
        "vocabulary": {
            "Feature": ["Getting started", "Documents", "Search", "Settings", "Plugins"]
        }
    }
}
```

| Key | Meaning |
| --- | --- |
| `source` | Folder with your Markdown pages |
| `target` | Folder where the site is written |
| `theme` | Must be `apphelp` |
| `title` | Application name, shown in the header and the browser tab |
| `apphelp.vocabulary.Feature` | The only values a page may use for `Feature` |

Without the `apphelp` block the build fails with `META_CONFIG reason=missing_feature_vocabulary`. This is because `strict` is on by default.

Tested: this file with one page from the sample builds with exit code 0.

Every page needs these properties: `DocType`, `Feature`, `Order`, `Section` and `Summary`. A page with a missing or unknown value fails the build while `strict` is on.

`Level` and `Platform` are optional. They are checked only when you list their values in `apphelp.vocabulary`.

## Type of document

AppHelp follows the [Diátaxis](https://diataxis.fr/) framework, like the `techdoc` theme. Every page has exactly one type of document, set with the `DocType` key:

| `DocType` | What the page is |
|---|---|
| `Tutorial` | A lesson that takes the reader through a series of steps |
| `How-to guide` | A recipe that solves one specific problem |
| `Reference` | A dry, structured description (settings, shortcuts, plugins) |
| `Explanation` | Background that clarifies how or why something works |

The value must be spelled exactly as above. A page without a valid `DocType` is never published: it is left out of the site, the navigation, the search and the help ids. The build reports it as `DOCTYPE_MISSING` or `DOCTYPE_INVALID` and fails when `strict` is on (the default).

The generated site calls this "Type of document". The word Diátaxis appears only in this documentation.

## Layout

`Layout` is optional and changes how a page is rendered, on top of its type:

| `Layout` | Rendering | Typical `DocType` |
|---|---|---|
| `faq` | Every `##` heading is a question, shown as a collapsible item with its own anchor | `Reference` |
| `tips` | Every `##` heading is one tip, shown as a card | `How-to guide` |
| `troubleshooting` | Every `##` heading is a problem; `### Cause` and `### Fix` are styled | `How-to guide` |

Tutorials number their `##` steps automatically.

## Page properties

| Key | Required | Meaning |
|---|---|---|
| `DocType` | yes | Type of document, see above |
| `Section` | yes | Sidebar group |
| `Order` | yes | Integer position in the section; sections are ordered by their lowest `Order` |
| `Summary` | yes | One sentence, at most 160 characters; shown in search results, cards and the Topics page |
| `Feature` | yes | One or more values from the `Feature` vocabulary in `repo.json` |
| `Layout` | no | `faq`, `tips` or `troubleshooting` |
| `Keyword` | no | Words readers search for that the text does not use |
| `Level` | no | From the `Level` vocabulary, for example `basic`, `advanced` |
| `Platform` | no | From the `Platform` vocabulary |
| `Since` | no | Application version that introduced the feature; quote it (`"0.10"`) |
| `Plugin` | no | Plugin name, shown in a page header |
| `HelpId` | no | Stable ids the application opens with `go.html?id=<id>`; `id=#anchor` points to a section |
| `Related` | no | File names of pages listed first under "Related pages" |
| `Tag` | no | Free tags, used by search only |
| `Date` | no | Shown as "Last updated" |

`index.md` is the landing page and needs none of these. `search.md`, `topics.md`, `go.md` and `404.md` are reserved names.

## Configuration file

Every setting lives in `config/repo.json`. `kb4it create` writes a complete one. The [repository settings](../../../../help/source/reference-repo-json.md) page explains each key in more detail.

### Required keys

| Key | Values | Meaning |
|---|---|---|
| `title` | Text | Application name, shown in the header and the browser tab |
| `theme` | `apphelp` | Theme of the site |
| `source` | Folder path | Folder with your Markdown pages |
| `target` | Folder path | Folder where the site is written; it must be a folder of its own |

`source` and `target` are relative to the knowledge base folder, the one that holds `config/`. Absolute paths, `~` and `$VARIABLES` also work. `kb4it create` writes absolute paths. When the knowledge base is kept in git or built on another computer, change them to `"source": "source"` and `"target": "target"`. A missing key stops the build with `CONFIG_KEY_MISSING`.

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
| `editor` | `true`, `false` | `false` | Add page (`add.html`) with a Markdown editor; any other value stops the build. Top-level key, not part of the `apphelp` block |
| `timezone` | IANA zone name, such as `Europe/Madrid` | the computer's zone | Zone of every date written without an offset. An unknown name falls back to the computer's zone |
| `git` | `true`, `false` | `false` | Edit links to your git server. They appear only with `git_server`, `git_user`, `git_repo` and `git_branch` all set |
| `git_server` | Host name without scheme, such as `github.com` | empty | Git server of the edit links |
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
| `lang` | Language tag (`en`, `es`, `pt-BR`) | `en` | `<html lang>` and the language of the structured data; `apphelp.lang` wins |
| `index` | `true`, `false` | not set (acts as `true`, with a reminder) | `false` asks search engines not to index the site: `noindex` on every page, `Disallow: /` in `robots.txt`, no sitemap |
| `noindex_keys` | `true`, `false` | `true` | Keep the pages that only list documents out of search engines and the sitemap |
| `structured_data` | `true`, `false` | `true` | `false` leaves the JSON-LD out of every page |
| `map` | Object: property to `"schemaProperty"`, `"schemaProperty:Type"` or `null` | built-in map | Changes which properties go into the structured data; `null` leaves one out |

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

### apphelp keys

`version` is a top-level key. Everything else lives in the `apphelp` block:

```json
"version": "0.3",
"apphelp": {
    "strict": true,
    "lang": "en",
    "accent": "#3584e4",
    "about": false,
    "contract": "config/contract.txt",
    "vocabulary": {
        "Feature": ["Getting started", "Documents", "Settings"],
        "Level": ["basic", "advanced"],
        "Platform": ["Linux", "Windows"]
    },
    "labels": {"add": "New page"},
    "versions": {"enabled": true, "latest": "0.3"}
}
```

| Key | Values | Default | Meaning |
|---|---|---|---|
| `version` | Text, or `"kb4it"` for the installed KB4IT version | empty | Version of the application the help describes. Shown on the home page, next to the pages new in it, and used as the folder name with `versions` |
| `apphelp.strict` | `true`, `false` | `true` | Metadata problems and help ids pointing nowhere fail the build |
| `apphelp.lang` | Language tag (`en`, `es`, `pt-BR`) | `seo.lang`, else `en` | Language of the pages |
| `apphelp.accent` | Hex colour: `#rgb`, `#rgba`, `#rrggbb` or `#rrggbbaa` | `#3584e4` | Accent colour. Any other value falls back to the default |
| `apphelp.about` | `true`, `false` | `false` | Adds an about page |
| `apphelp.contract` | File path | `config/contract.txt` | File with the help ids and anchors the application opens, one per line. A missing id fails the build. The build fails when you set this key and the file is missing |
| `apphelp.vocabulary` | Object: property name to list of values | `{}` | Allowed values. `Feature` is required while `strict` is on; `Level` and `Platform` are checked only when listed |
| `apphelp.labels` | Object: label name to text | English texts | Your own interface texts. Unknown names are ignored. Names: `home`, `menu`, `breadcrumb`, `search`, `search_placeholder`, `filters`, `results`, `no_results`, `topics`, `add`, `topics_intro`, `on_this_page`, `previous`, `next`, `related`, `edit`, `updated`, `built_with`, `theme_toggle`, `skip`, `new_in`, `plugin`, `copy`, `copied`, `go_title`, `go_unknown`, `not_found_title`, `not_found_text`, `ts_cause`, `ts_fix`, `doctypes`, `doctype_tutorial`, `doctype_howto`, `doctype_reference`, `doctype_explanation`, `doctype_tutorial_title`, `doctype_howto_title`, `doctype_reference_title`, `doctype_explanation_title`, `doctype_tutorial_desc`, `doctype_howto_desc`, `doctype_reference_desc`, `doctype_explanation_desc`, `facet_DocType`, `facet_Feature`, `facet_Level`, `facet_Platform`, `facet_Plugin`, `facet_Since` |
| `apphelp.versions.enabled` | `true`, `false` | `false` | Builds into `<target>/<version>/` and keeps the folders of other versions, with a version selector |
| `apphelp.versions.latest` | A version | the highest version | Version the site root and `latest/` point to |

### Keys no longer read

Older sample apps also hold `sort`, `timeline` and `webserver`, and `menu`. KB4IT ignores them; you can delete them.

## Add page

Set `"editor": true` in `repo.json` (off by default) to build `add.html`, a Markdown editor for new pages, with a Tutorial, How-to guide, Reference and Explanation skeleton. The sidebar links to it with the `add` label ("Add a page"). Completion offers the `vocabulary` values.

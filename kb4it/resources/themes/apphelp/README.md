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

## Settings

The `apphelp` block of `repo.json` holds `strict`, `lang`, `accent`, `about`, `contract`, `vocabulary` and `labels`. See `AGENTS.md` in the repository root.

## Add page

Set `"editor": true` in `repo.json` (off by default) to build `add.html`, a Markdown editor for new pages, with a Tutorial, How-to guide, Reference and Explanation skeleton. The sidebar links to it with the `add` label ("Add a page"). Completion offers the `vocabulary` values.

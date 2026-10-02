# AppHelp theme

AppHelp builds a help site for an application. The site works when opened from disk (`file://`), when served from a subpath such as GitHub Pages, and inside the application's own web view (`?embed=1`).

Create a site with `kb4it create apphelp <path>`; the sample in `apps/default/` shows every page type.

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

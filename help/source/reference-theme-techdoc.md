---
DocType: Reference
Feature: Themes, Configuration
HelpId: techdoc
Keyword: dashboard, incident, change, meeting, procedure, priority, status, periodicity, monitoring, bookmark, gallery, image, backup, admin, datatable
Level: basic
Order: 520
Section: Reference
Summary: The techdoc theme for team knowledge bases, the properties it reacts to and its settings.
---

# techdoc

techdoc turns a folder of runbooks, incident reports, changes and notes into a team knowledge base with a dashboard.

![The techdoc dashboard](resources/images/techdoc.webp)

## Properties it reacts to {#properties}

| Property | Values | Effect |
|---|---|---|
| `Category` | The form of the document: `Procedure`, `Note`, `Report`, `Template`, `Post`, `Record`, `Minutes` | Groups documents |
| `WorkType` | `Knowledge` for a knowledge document; for a record, the type of work it holds: `Change`, `Incident`, `Task`, `Meeting` | Drives the latest changes and incidents, **Open items** and the calendar: dated documents whose work type (or, without one, whose Category) is in `events` appear in the calendar |
| `DocType` | `Tutorial`, `How-to guide`, `Reference`, `Explanation` | Counted in the four cards of the dashboard |
| `Priority` | `Critical`, `Very high`, `High`, `Medium`, `Normal`, `Low`, `Unknown` | Coloured label; open items are sorted by it |
| `Status` | Open: `New`, `Open`, `Draft`, `Planned`. Closed: `Completed`, `Finished`, `Released`, `Successful`. Faded: `Deprecated`, `Obsolete` | Coloured label; open values put incidents, changes and tasks under **Open items** |
| `Topic` + `Periodicity` | `Topic: Monitoring` with `Periodicity: Daily`, `Weekly`, ... | Listed in the **Monitoring** panel by periodicity |
| `Bookmark` | `Yes` | Listed on the **Bookmarks** page |
| `Date` | any [date](reference-document-format.md#dates) | Sorting, calendar, upcoming and recent events |

Any other property gets its own pages, as in every theme.

Every document carries a `WorkType`, and its `Category` must go with it:

| WorkType | Category |
|---|---|
| `Knowledge` | `Procedure`, `Note`, `Post`, `Report`, `Template` |
| `Change`, `Incident`, `Task` | `Record` |
| `Meeting` | `Minutes` |

A document whose `WorkType` is `Change`, `Incident`, `Task` or `Meeting` is a record; a document with `WorkType: Knowledge` is a knowledge document. The quality score takes a point when `WorkType` is missing and three when the `Category` does not go with it. A document with no `WorkType` is still read as a knowledge document, unless its `Category` holds an older type of work (see [Upgrading](#upgrade)).

### Upgrading an older repository {#upgrade}

Older repositories put the type of work in `Category` (`Category: Change`). They keep working: when a document has no `WorkType` and its `Category` is `Change`, `Incident`, `Task` or `Meeting`, techdoc reads that value as the work type.

To move them to the new keys, run `scripts/conv/split_category.py` from a copy of the KB4IT source. First check what it would change:

```bash
python scripts/conv/split_category.py source --csv split.csv --dry-run
```

`split.csv` lists every document it would change. Then run it for real:

```bash
python scripts/conv/split_category.py source --csv split.csv
```

It only rewrites the `Category` line of the frontmatter and adds `WorkType` below it. `Category: Change` becomes `Category: Record` with `WorkType: Change`; `Category: Meeting` becomes `Category: Minutes` with `WorkType: Meeting`; in `Category: Report, Incident` the `Report` stays, so check those documents by hand. A document whose `Category` is only `Procedure`, `Note`, `Post`, `Report` or `Template` gets `WorkType: Knowledge`; any other `Category` is left alone. Running it twice changes nothing. Back up the `source` folder first if it is not under version control.

## Dashboard {#dashboard}

The home page shows, from top to bottom:

- Counts of documents, authors, categories, events and bookmarks, and the number of Exemplary documents (a link to the Quality page).
- The four types of document, with counts and, under each, a bar with the mix of quality tiers ("22 exemplary, 113 complete of 230").
- **Best documents**: up to three Exemplary or Complete documents per type, best first.
- **Open items and activity**: one card with two tabs.
    - **Open items**: incidents, changes and tasks with an open status, highest priority first.
    - **Activity**: a tab each for the latest changes, the latest incidents, events (this month and the next, then the last month) and monitoring (recurring checks by periodicity).

  A tab without entries is not shown. Each tab bar opens on the tab you chose last.

Every section except the counts and the four document types folds when you click its title. The browser remembers which sections you folded.

## Document pages {#document}

![A techdoc document](resources/images/techdoc-page.webp)

The top bar holds the logo menu on the left, the page title in the middle and a search icon on the right:

- The logo menu links to the dashboard (click the logo), the Add page, Search, Events, Bookmarks, Gallery, Properties, Stats, Quality, Reload page, Help (the KB4IT help site, in a new window), About this app and About KB4IT (the KB4IT README).
- A long title ends in an ellipsis; hover over it to read it whole. On a document, hovering over the title opens the title menu: one row of buttons at the top (edit on the git server with `"git": true`, edit in the editor when the [editor](#editor) is on, document properties, document source, print), then the table of contents.
- The search icon, `/` or `Ctrl+K` opens the search dialog, which shows the best matches as you type. The Search entry of the logo menu opens `search.html`, the full page with filters. The keys do nothing while you type in a field. Each result shows the quality tier of the document, and the score breaks a tie between matches of the same relevance.

Below the top bar, a document page shows:

- **A header strip** with the DocType, Status and Priority badges, then Date (day and time), WorkType, Topic and Product as links to their pages. Keys a document does not have are left out.
- **The Summary**, when the document has a `Summary` key, as an opening line.
- **Banners** for documents that need care: red when `Environment` is `Production` ("This document changes production systems", with the `SID` values), grey when `Status` is `Obsolete`, `Deprecated`, `Withdrawn` or `Rejected` ("Do not follow this document"), amber when `Status` is `Draft`.
- **An info card** with two tabs. **Details** lists every property in groups (Classification, Systems, Technical objects, Organisation, Lifecycle, Other); technical objects such as transactions and commands show as chips, and SAP notes named in the text ("note 736902") link to the SAP support portal. **History** shows the date, the source file with a link to view it, an edit link with `"git": true`, and the build time. The card starts closed when the document has a Summary and open on Details when it does not. Click a tab to open it, click the open tab or the arrow to close it; the card remembers your last tab. The document properties button in the title menu, or `#kb-info-details` at the end of the address, opens Details. `#details` does too, unless the document has a section with that name, which keeps the link.

Each document gets a table of contents, sections that fold when you click their heading, and buttons in the title menu to show the properties and the Markdown source and to print. With `"toc_sidebar": true` in the theme's `theme.json`, a document with four or more sections gets a second table of contents in a right column on screens 1400 pixels or wider. It stays in view while you scroll and marks the section you are reading. It is left out of print; the inline table of contents and the title menu still hold it on narrower screens. Every heading level folds. The table of contents and the first section start open, with its subsections; every other section starts folded, subsections too. A link to a section, from the table of contents or another page, unfolds it. Printing shows every section, and each printed page (documents and the other techdoc pages) ends with the page title on the left and the page number (`3/8`) on the right. The footer needs a browser that supports CSS page-margin boxes, such as Chrome or Edge; turn off the browser's own headers and footers in the print dialog to avoid a second footer. With `"git": true`, an edit button opens the file in your git server. The **Related** tab of the info card lists the documents that link to this one (**Linked from**) and up to five **Related documents**: documents that share a SID, Product, Transaction, Component or Tag, the rarest shared values first. Each line shows the quality tier of the document.

Images in a document:

- Get their width and height from the file, so the page does not jump while they load. Images below the first one load when you scroll to them.
- Become figures with a light frame. When the alt text describes the image (`![User list in SU01](...)`), it becomes a numbered caption ("Figure 1. User list in SU01"); an alt text that looks like a file name (`SAP-BC-00`, `image12`) gives no caption.
- Open full size when you click them, with previous and next for the other images of the document.
- Three or more images in a row, with no text between them, become a grid of thumbnails.
- Stay as they are when they are inside a link, narrower than 64 pixels, or part of a sentence.
- Show a grey box with the path when the file is missing, and the build warns [IMAGE_MISSING](troubleshooting.md#image-missing).

Content blocks:

- Code blocks have a bar with a language label and a **Copy** button; a block over 30 lines shows the first 20 and a **Show all N lines** button. Both buttons are left out of print, and a long block prints in full.
- Tables get the UIkit table style. Wide tables scroll sideways; a table over 15 rows keeps its header visible and gets a search box and sortable columns (see [content blocks](howto-content-blocks.md)). Print shows the whole table.
- With `pymdown-extensions` and `alternate_style`, `pymdownx.tabbed` sets show a tab bar that works without JavaScript; all panels print with their label. See [Make code, tables and notes easier to read](howto-content-blocks.md).
- `pymdownx.details` notes fold; they print open.
- After one screen of scrolling, a **Back to top** button appears at the bottom right. It is not printed.

## Quality score {#quality}

Every document gets a score from 0 to 100. A ring in the header strip shows it; click it, or the star button in the title menu, to open the **Quality** tab of the info card. The tab shows five bars, a list of what the document has, and the next steps with the points each one adds. A black tick on each bar marks the median of the documents of the same kind. Hover over any item for a tip on what to do; click it to open the **Quality guide** (`quality-guide.html`), a system page that explains every check with the Markdown to write, and lists the skeleton of each Category and WorkType.

| Dimension | Points | What counts |
|---|---|---|
| Findable | 15 | Author, Date, DocType, Category, WorkType, Status, Tag, Topic, Scope and Product (1 each); known values for Status, Priority, DocType, Category and WorkType (2); a `Summary` (3). A Category that does not go with the WorkType costs 3 |
| Structured | 25 | Two or more sections; a first section that gives context (Description, Introduction, Overview); the shape of its DocType (steps for a how-to guide, a table or list for a reference); the sections of its skeleton. Empty sections and skeleton text left in cost points |
| Complete | 25 | Words against a target: how-to guide 150, reference 200, explanation 500, tutorial 800 |
| Connected | 15 | Linked from another document; links to a document; cites a source; a References section; an image or a diagram. Each broken link and each missing image costs 3 |
| Current | 20 | A final status (Released, Completed, Finished, Successful); a recent `Date` (the points halve every 3 years for how-to guides and tutorials, 4 for references, 8 for explanations) |

The score gives a tier: **Exemplary** (75 and up, gold ring and a note under the top bar), **Complete** (60 to 74, green), **Basic** (40 to 59) and **Stub** (under 40), both grey. Documents with the Status `Obsolete`, `Deprecated`, `Withdrawn` or `Rejected` are **Retired** and get no score.

Records (documents whose `WorkType` is Change, Incident, Task or Meeting) are short by nature and are scored on a lighter scale: the sections of their WorkType skeleton instead of a DocType shape, a 60-word target, and a final status instead of freshness. A record is compared with records of the same WorkType.

The skeletons of the Add page are written to this standard. Each one has every core key in alphabetical order, with its Category and WorkType already set (empty keys to fill: Author, Summary, Tag, Topic, Scope, Product), a first section that gives context, the shape of its type (numbered steps and a command for a procedure, a table for a report, three sections for a note or a post) and a References section with an example source. A document that keeps that structure, replaces the example text and reaches the word target scores Exemplary. Each example line says what to write; one left unchanged costs points as skeleton text. To have an AI assistant write documents to the same standard, give it the [kb4itdoc skill](howto-write-with-ai-assistant.md).

| Skeleton | Sections |
|---|---|
| Procedure | Introduction, Prerequisites, Steps, Verification, References |
| Note, Post | Overview, Details, References |
| Report | Executive Summary, Findings, Recommendations, References |
| Change | Overview, Impact, Rollback, References |
| Incident | Summary, Timeline, Root Cause, Resolution, References |
| Task | Objective, Acceptance Criteria, Notes, References |
| Meeting | Objective, Attendees, Agenda, Notes, Action Items, References |

Ranks and medians are in `quality-index.js`, written at every build.

Add `"Quality"` to the `datatable` list of `repo.json` to get a Quality column in the document tables: five squares (one per 20 points) and the tier; the column sorts by score, retired documents last.

The **Quality page** (`quality.html`, in the logo menu) is for maintainers: the tier mix per type, the Exemplary documents, quick wins (documents within 5 points of the next tier, with the one change that gets them there), broken links, missing images, documents without a Summary and possible duplicates (titles that share most words; journal titles that differ only by a date are left out). The score does not check that the content is correct.

Turn it off with `"quality": false` in `repo.json`. The `quality` block of the theme's `theme.json` sets the tiers, the word targets, the half-lives and the statuses that count as final, retired or known.

## Add page and editor {#editor}

`add.html` writes new documents in a Markdown editor (CodeMirror 6, bundled, no network). Click **Create** on a category card to open its skeleton. The page is built by KB4IT itself and follows the `editor` setting of `repo.json`, which is on by default for techdoc. The cards come from `templates/skeletons/skeletons.json`; a repository can replace them with its own `overrides/templates/skeletons/` folder. For a walk-through see [Write a document in the editor](howto-write-document-editor.md).

| Part | What it does |
|---|---|
| Editor | Line numbers, Markdown and frontmatter highlighting, undo, search (`Ctrl+F`), lists and quotes continued on Enter. Tab indents (four spaces), Shift-Tab outdents, `Escape` then `Tab` leaves the editor |
| Completion | In the frontmatter: property names, and values of the repository, most used first. Values that YAML needs quoted are quoted |
| Lint | A gutter with the diagnostics below |
| Properties pane | One row per property: value chips, suggestions with counts, a property selector with "New property...", and a word cloud per property |
| Toolbar | Bold, italic, code, link, headings H2 to H4, lists, quote, code block, rule, table, image, admonitions, Mermaid diagram, formulas. Disabled while the cursor is in the frontmatter |
| Save and Copy | Save a file or download it; Copy writes the text to the clipboard |

On open, the text of the H1 title is selected, so typing replaces it.

**Edit in the editor**, on every document page (title menu and History tab), opens the same editor on the document's Markdown; **Save** suggests its own file name. See [Edit an existing document](howto-write-document-editor.md#edit).

### Checks {#lint}

The gutter uses the reason names of the build. Errors stop the document from building; warnings and info do not.

| Reason | Level | Meaning |
|---|---|---|
| `missing_frontmatter` | error | The text does not start with `---` |
| `missing_frontmatter_close` | error | The frontmatter has no closing `---` |
| `yaml_error` | error | The YAML has a syntax error |
| `invalid_frontmatter` | error | The frontmatter is not a key/value mapping |
| `missing_h1_title` | error | There is no `#` title |
| `title_in_frontmatter_ignored` | warning | A `Title:` property is ignored; the title comes from the H1 |
| `bad_property_name` | error | The property name is not valid |
| `bad_property_value` | error | The value is not valid |
| `duplicate_property` | warning | The property appears twice; the build keeps the last |
| `new_property`, `new_value` | info | The name or value is not used in the repository yet |

The editor's YAML check can miss some malformed nested values, for example `A:` followed by `  b: [x`. `kb4it build` and `kb4it verify` remain the authority.

### Properties pane {#pane}

- Values cannot contain commas, because KB4IT splits on commas.
- Complex properties (block lists, several lines, anchors) are read-only and say "Edit this property in the text". Numbers, dates, `yes` and `no` are text like any other value and can be edited.
- A repeated property is edited at its last occurrence.
- When one of several values needs quotes, the line is written as a flow list: `Key: [a, "b: c"]`.
- The pane follows the text 300 ms after the last edit. While the frontmatter has an error, its inputs are disabled.

### Saving and browsers {#save}

| Browser | Save |
|---|---|
| Chromium-based (Chrome, Edge, ...) | System save dialog; later saves reuse the file and the button reads `Save (<name>)` |
| Firefox, Safari | Downloads the file |

If the dialog is cancelled or the write fails, the page offers a download. A document with errors asks for confirmation. The text is saved as UTF-8 with LF line endings and one final newline. Everything works offline, from `file://` or `kb4it serve`; the editor files are copied to `resources/editor/` only in sites that have the Add page.

## Other pages {#pages}

| Page | Shows |
|---|---|
| `all.html` | Every document in a sortable, searchable table |
| `events.html` | A calendar per year and a table of events |
| `properties.html` | Every property, one per line, with its number of values and of documents; each links to the property's page. A property's page (such as `Author.html`) shows its values as a cloud or as a table |
| `stats.html` | Totals, then one card per section with a summary line; its Details button opens the section in a modal: activity (documents per year and per month), property coverage with the most used values, metadata health (similar values, properties used once, documents with little metadata) and links (most linked documents, documents nothing links to) |
| `bookmarks.html` | Documents with `Bookmark: Yes` |
| `gallery.html` | The images of every document. See [Gallery](#gallery) |
| `add.html` | A Markdown [editor](#editor) with a ready-made skeleton per category; saves a new file |
| `search.html` | Full-text search over every document, with filters by Category, WorkType and Tag; the search dialog in the top bar shows the best matches as you type, with the quality tier of each document. See [search](reference-repo-json.md#search) |
| `404.html` | "Page not found", in the theme's layout, with a link home and the search box. A web server shows it for a missing address; see [serving it](howto-publish-web-server.md#not-found). A document named `404.md` is left out with `DOC_NAME_RESERVED` |

## Gallery {#gallery}

`gallery.html`, in the logo menu, shows the images of your documents. It opens empty, so a large knowledge base loads nothing until you ask:

1. The filter panel on the right has one button per document property, plus **Year** (from `Date`). The button shows how many values the property has.
2. Click a button to open its values in a dialog and tick the ones you want. Each value shows how many images it adds to the filters already chosen; a value that would add none is greyed out. A property with many values gets a search box. **None** clears the property; **Show images** closes the dialog.
3. The images appear as thumbnails in a masonry grid, newest document first, each with its document title (a link) and its caption. Values of one property widen the choice; values of two properties narrow it (`Product` Linux or SAP, and `Tag` backup).
4. Click a thumbnail to enlarge the original. Previous and next follow the filters, and the caption links to the document.

The text box above the buttons matches words of the document title or the image caption. Each chosen value shows as a chip under the buttons; click it to remove it, or **Clear all**. The choice is kept in the address, such as `gallery.html#Product=SAP&Tag=backup`, so you can bookmark or link a view.

The build makes a thumbnail of each image 480 pixels wide, in WebP, keeps it in `var/thumbs/` and makes it again only when the image changes. The site gets the ones in use in `resources/kb4it-thumbs/`. SVG images, images no wider than a thumbnail and files the build cannot read are shown as they are; remote images too. Missing images and images inside code are left out. `Summary`, `Bookmark` and the keys of `ignored_keys` are not offered as filters. A document named `gallery.md` is left out with `DOC_NAME_RESERVED`.

## Icon, diagrams and formulas {#render}

- The icon of the browser tab is `logo` from `repo.json`; without it, the theme's own logo (`images/logo.svg`).
- Documents can hold [Mermaid diagrams and formulas](reference-document-format.md#diagrams).

## Settings {#settings}

Keys in `repo.json` that techdoc reads, on top of the [common ones](reference-repo-json.md):

| Key | Default | Meaning |
|---|---|---|
| `datatable` | `["Date", "Title"]` | Columns of the document tables; a column that is empty in every row of a table is left out of it |
| `events` | `[]` | Work types (or, for documents without one, categories) that count as events |
| `editor` | `true` | Builds the Add page; `false` removes `add.html` and the link to it |
| `admin` | `false` | Builds the backup page, see below |
| `quality` | `true` | Scores every document, see [quality score](#quality); `false` removes the score, the Quality tab, the search chip and `quality-index.js` |
| `git`, `git_server`, `git_user`, `git_repo`, `git_branch`, `git_path` | | Edit links; `git_server` is a full URL such as `https://github.com` |

The `default` app sets `datatable` to Date, Title, Category, WorkType, Priority, Status, Scope and Topic, and lists every work type and category in `events`.

The document page reads these keys of the theme's `theme.json`. To change them, copy the theme (see [create a theme](howto-create-theme.md)):

| Key | Meaning |
|---|---|
| `header_keys` | `badges` and `links`: the keys shown in the header strip, in order |
| `info_groups` | The groups of the Details tab: `name`, `keys`, and `"chips": true` for the group shown as chips. Keys in no group go to Other |
| `info_tabs` | `details` and `history`, each with `print`: whether the tab is printed. By default Details is printed and History is not |
| `table_filter` | `true`: tables with more than 15 rows and a plain grid get a search box and sortable columns; `false` keeps only the style and the scrolling |
| `toc_sidebar` | `false`: show a second table of contents in a right column on screens 1400 pixels or wider, for documents with four or more sections |

On paper, the header strip is one line of text, banners have a border instead of a colour, Details follows the title under the heading "Document details" in two columns, and the tab bar is left out.

## Backups page {#admin}

With `"admin": true`, every build writes `target/admin/index.html` with two downloads:

| File | Holds |
|---|---|
| `<title>_sources.zip` | Every `.md` file of `source/` |
| `<title>_site.zip` | The whole website, without the admin folder |

The zips are rebuilt only when something changed. The page is not linked from the menu, but anyone who knows the address can open it: on a public server, protect `admin/` or leave this off.

## Sample apps {#apps}

| App | Starts you with |
|---|---|
| `default` | Seven sample documents: a backup check procedure, a disk full incident and the change that followed it, a weekly operations meeting, an open task, a note on RAID levels and a draft report |
| `sapbasis` | The same settings with a menu of SAP properties (`SID`, `Transaction`, `Job`, `Dump`, ...) and five SAP Basis samples: two procedures (`SM37`, `ST22`), an incident, a planned kernel update and a note on the transport landscape |

Each sample follows the sections of its skeleton and scores Exemplary. Names, hosts and system ids are made up. Copy a sample to start a document, or delete them.

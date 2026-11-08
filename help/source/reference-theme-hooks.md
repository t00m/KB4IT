---
DocType: Reference
Feature: Themes, Development
HelpId: theme-hooks
Keyword: theme hooks, kb4it.theme, BaseTheme, Site, Doc, Table, feature, features, options, prepare, build, page_context, config_class, checks
Level: advanced
Order: 645
Related: howto-create-theme.md, dev-theme-internals.md
Section: Reference
Summary: Every hook, option and feature of kb4it.theme, the public theme API, generated from the KB4IT code.
---

# Theme API reference

A theme is a `Theme` class in `logic/theme.py` that subclasses `kb4it.theme.BaseTheme`. It switches on
features by name in `features`, sets their options as class attributes and fills a hook by defining a
method with the same name. The tables below come from the KB4IT source (`scripts/devel/theme_hooks_doc.py`),
so they match the installed version. See [Write a theme](howto-create-theme.md) for a walk through.

`kb4it.theme` exports `BaseTheme`, `Site`, `Doc`, `Table`, `Feature`, `FEATURES`, `Problem`, `ThemeError`,
`page_name`, `slugify` and `q`; `kb4it.theme.html` has the body rewrites `enhance_images`, `enhance_blocks`,
`lazy_images` and `wrap_code`. Anything else is internal.

## BaseTheme

The base class of every theme.

| Class attribute | Default | Meaning |
|---|---|---|
| `features` | `()` | Features to switch on: names of built-in features or bundles, or Feature subclasses. |
| `config_class` | `None` | Dataclass of the theme's settings (theme.json and the repo.json block named after the theme). |
| `reserved_pages` | `()` | Source file names the build refuses because the theme writes a page with that name. |
| `untitled_label` | `''` | Title of a page whose document has no Title. |
| `ellipsize_titles` | `True` | Cut long titles (True) or leave them whole (False, when the CSS cuts them). |
| `log_area` | `'THEME'` | Area of the theme's log lines, such as [THEME] HTML_MISSING. |
| `person_pages` | `True` | The site has a page per person (Author_<name>.html) that the structured data links to; False describes each person in the home page instead. |

KB4IT sets `self.site` (the [Site](#site)), `self.config` (the settings), `self.log` and `self.internals` (unstable, see [Theme internals](dev-theme-internals.md)) before the first hook.

### Lifecycle

Called once per build, in this order. Every one is optional.

| Hook | What it does |
|---|---|
| `setup() -> None` | Once per build, before anything else: reset the theme's own per-build state. |
| `generate_sources(site: Site) -> None` | Write documents into the source folder before KB4IT reads it. |
| `prepare(site: Site) -> None` | After the documents are read, before any page is built: compute what the pages need. |
| `build(site: Site) -> None` | Write the theme's own pages with site.page(). The features' pages are already written. |
| `after_build(site: Site) -> None` | After every document page is compiled, before the site is deployed. |
| `after_deploy(site: Site) -> None` | After the site is in target (site.paths.target): copy or package files there. |
| `checks(site: Site) -> list[Problem]` | Problems of the built site; default: links to missing pages and anchors. |
| `after_checks(site: Site) -> None` | After the checks passed: publish, copy, notify. |

### Document pages

Called for every page, in this order: `page_var`, `page_context`, `body_transforms`, `page_template` (through `render_page`), `finalize_html`. `backlinks_html` adds the block after the body.

| Hook | What it does |
|---|---|
| `page_var() -> dict[str, Any]` | The starting var of a document page; default: base_var(). |
| `page_context(doc: Doc, var: dict[str, Any]) -> dict[str, Any]` | Add the theme's data to var before the body is rewritten and the page rendered. |
| `body_transforms(doc: Doc, var: dict[str, Any]) -> list[Callable[[str], str]]` | Functions from HTML to HTML applied in order to the compiled body. |
| `page_template(doc: Doc, var: dict[str, Any]) -> str` | Name of the template that renders the body of the page. |
| `render_page(doc: Doc, var: dict[str, Any]) -> str` | The whole page: page_template() between HTML_HEADER_COMMON and HTML_FOOTER when they exist. |
| `finalize_html(html: str) -> str` | Last change to the whole page before it is written. |
| `backlinks_html(doc: Doc) -> str` | The block after the body that lists the documents linking here (HTML_BACKLINKS); '' for none. |

### Site-wide

Values that hold for the whole site.

| Hook | What it does |
|---|---|
| `site_signature() -> str` | A value that changes when every page must be rebuilt (site-wide navigation...); '' for none. |
| `target_subdir() -> str \| None` | Folder inside target to build into, or None. |
| `page_lang() -> str` | Language of the pages (<html lang>); default: repo.json seo.lang. |
| `structured_defaults() -> dict[str, Any]` | Schema.org defaults of the theme's documents: {'type': ..., 'map': {property: schema field}}. |
| `search_page() -> str` | The search page of the site, for the structured data of the home page. |

### Rendering

Helpers to call from the hooks.

| Hook | What it does |
|---|---|
| `render(name: str, **values: Any) -> str` | Render template `name` with the base variables plus values, all under `var`. |
| `template(name: str) -> Any` | The compiled template `name`; call .render(var=...) on it. |
| `has_template(name: str) -> bool` | True when a template named `name` exists (site override, theme, base or common). |
| `base_var() -> dict[str, Any]` | A new dict of the variables every template gets: repo, theme, page, lang, search_box... |

## Site

The knowledge base being built, read-only. `site.page()`, `site.keep()` and `site.table()` write through KB4IT.

| Member | What it is |
|---|---|
| `site.documents` | The documents of the site (no system pages), newest first, undated ones last. |
| `site.properties` | The properties used by the documents and their values. |
| `site.people` | The person profiles of the site. |
| `site.build` | What this build compiles. |
| `site.paths` | Folders of the site. |
| `site.features` | The enabled features, by name: `site.features.events`, `site.features['table']` |
| `doc(doc_id: str) -> Doc` | The Doc of an id, also for a system page. |
| `keep(name: str, unless: str = 'documents') -> bool` | Reuse name.html of the previous build when nothing it shows changed; True if kept. |
| `page(name: str, title: str, html: str, *, markdown: bool = False, listing: bool = False) -> None` | Add a page to the site: name.html with this title and content. |
| `repo` | repo.json, read-only. |
| `table(table: Table) -> str` | The HTML of a document table. |
| `theme` | theme.json of the theme being built, read-only. |

### site.documents

| Member | What it does |
|---|---|
| `by_date() -> list[Doc]` | Every document, newest first, undated ones last. |
| `filter(test: Callable[[Doc], bool]) -> list[Doc]` | The documents for which test(doc) is true, newest first. |
| `get(doc_id: str) -> Doc \| None` | The document with this id ('note.md'), system pages included, or None. |
| `latest(n: int) -> list[Doc]` | The n newest documents. |
| `with_value(key: str, value: str) -> list[Doc]` | Documents that have value among the values of key, newest first. |

### site.properties

| Member | What it does |
|---|---|
| `all_keys() -> tuple[str, ...]` | Every key of the documents except the blocked ones (Title, SystemPage, dates). |
| `blocked` | Keys that never get a page: Title, SystemPage and the date keys. |
| `documents(key: str, value: str) -> list[Doc]` | The documents with a value of a property, newest first. |
| `hidden` | Keys left out of the properties page (repo.json hidden_properties). |
| `ignored` | Keys left out of every page (repo.json ignored_keys). |
| `keys() -> tuple[str, ...]` | The properties that get pages: every key but the blocked and the ignored ones. |
| `values(key: str) -> tuple[str, ...]` | Every value of a property in the site, sorted without case. |

### site.people

| Member | What it does |
|---|---|
| `keys` | The properties that name people (Author by default). |
| `lookup(name: str) -> Any` | The profile of a person by name or alias, or None. |
| `status(name: str) -> str` | 'ok', 'missing' or 'no_contact': whether the person has a profile with contact details. |
| `tip(name: str) -> str` | Role and team of a person, for a tooltip; '' without a profile. |

### site.build

| Member | What it does |
|---|---|
| `changed(doc: Doc \| str) -> bool` | True when the document is compiled in this build (new or changed, or a full build). |
| `documents_changed` | How many documents this build compiles. |
| `force` | True for a full build (--force, or nothing cached). |
| `invalid` | (source file, reason) of each document KB4IT could not read; they are not in the site. |
| `keys_changed` | The properties whose pages this build rebuilds. |

### site.paths

| Member | What it does |
|---|---|
| `source` | The folder of the Markdown documents. |
| `target` | The published site; only complete after deployment (after_deploy). |

## Doc

One document of the knowledge base, read-only.

| Member | What it does |
|---|---|
| `id` | The file name in `source/`, such as `note.md` |
| `backlinks` | {title, url} of the documents that link to this one. |
| `date` | The Date property as written, or None. |
| `datetime` | The Date property as a datetime, or None when missing or unreadable. |
| `is_system` | True for a page KB4IT or the theme generates (property pages, index, about...). |
| `keys() -> tuple[str, ...]` | The properties of the document, sorted, without the ones KB4IT ignores (Title...). |
| `links(key: str) -> list[dict[str, str]]` | {name, url} of each value of a property, url being the value's page. |
| `modified` | When the document last changed (Modified property, git or file time), or None. |
| `name` | The file name without .md. |
| `properties` | Every property of the document and its values. |
| `source() -> str` | The Markdown text of the document ('' for a page without a source file). |
| `template_keys() -> dict[str, Any]` | The var['keys'] of the document's page: {key: [values]}, 'Title' as a string, and the |
| `title` | The Title (the first heading of the document), or ''. |
| `url` | The page of the document, relative to the site root. |
| `value(key: str, default: str = '') -> str` | The first value of a property, or default. |
| `values(key: str) -> tuple[str, ...]` | The values of a property, () when the document does not have it. |

## Table

A table of documents, as site.table() renders it. columns: property names; 'Date' and 'Title' get their own cells. None: the repo.json "datatable" setting, else the theme's default. id: the HTML id of the table. filterable: the table filter bar may attach to it (feature table_filter). dates: {doc id: 'YYYY-MM-DD'}, the event day of each row, for a calendar panel that filters the table.

Fields: `documents`, `columns`, `id`, `filterable`, `dates`.

## Features

Switch a feature on by listing its name in `features`; a feature that another one `requires` comes with it, and a feature runs after the ones it requires or uses. Set an option as a class attribute of the theme. Fill a hook by defining a method with its name; to call the default from it, use the feature: `self.site.features.table.datatable_date_cell(doc)`.

| Bundle | Features |
|---|---|
| `documents` | `toc`, `metadata`, `property_pages`, `all_documents`, `not_found` |

### about

about_kb4it.html, and about_app.html unless the site has its own about_app.md.

- Templates: `PAGE_ABOUT_KB4IT`, `PAGE_ABOUT_APP`

| Hook | Default |
|---|---|
| `about_pages() -> bool` | Whether this build writes the About pages; a theme may leave them out by a setting. |

### all_documents

all.html.

- Requires: `table`
- Templates: `PAGE_ALL`

| Option | Default |
|---|---|
| `reuse_unchanged_pages` | `False` |

What `site.features.all_documents` offers:

| Method | What it does |
|---|---|
| `write() -> str \| None` | Write all.html; the page, or None when the cached one is kept. |

### bookmarks

bookmarks.html.

- Requires: `table`
- Templates: `PAGE_BOOKMARKS`

| Option | Default |
|---|---|
| `reuse_unchanged_pages` | `False` |

What `site.features.bookmarks` offers:

| Method | What it does |
|---|---|
| `write() -> str \| None` | Write bookmarks.html; the page, or None when the cached one is kept. |

### diagrams

diagrams.html: the Gallery page, with the Mermaid diagrams of the documents instead of their images.

- Templates: `PAGE_GALLERY`
- Assets: `gallery`
- Reserves: `diagrams.md`

What `site.features.diagrams` offers:

| Method | What it does |
|---|---|
| `html_of(doc_id: str) -> str` | The HTML of a document body with a mermaid fence, as the compiler makes it, so the heading ids match; else ''. |
| `items(doc_id: str) -> list[dict[str, Any]]` | The diagrams of one document, each linked to its section. |
| `write() -> None` | diagrams.html: no diagram at first; the browser draws the ones the filters choose. |

### editor

add.html when the editor setting is on (repo.json "editor", default theme.json "editor").

- Templates: `PAGE_ADD`, `EDITOR_DIALOGS`

| Option | Default |
|---|---|
| `profile_skeleton` | `True` |

| Hook | Default |
|---|---|
| `editor_keys() -> dict[str, Any]` | Completion data {Key: [{"v": value, "c": count}]} for the properties pane. |
| `register_add_page(html: str) -> None` | Write the Add page and register it as a system page. |

What `site.features.editor` offers:

| Method | What it does |
|---|---|
| `enabled() -> bool` | True when this build has the Add page (the editor setting is on). |

### events

events_YYYYMMDD.html, events_YYYYMM.html and events_YYYY.html of the event documents.

- Requires: `table`
- Templates: `EVENTCAL_PAGE_EVENTS_DAYS`, `EVENTCAL_PAGE_EVENTS_MONTHS`, `EVENTCAL_PAGE_EVENTS_YEARS`

| Hook | Default |
|---|---|
| `event_documents() -> list[Any]` | Default: every dated document. A theme returns the ones that are events (Docs or ids). |

What `site.features.events` offers:

| Method | What it does |
|---|---|
| `build_pages(doclist: list[str], *, collect: bool = True) -> set[str]` | Create the day, month and year pages of the dated documents in doclist. |
| `calendar(days: dict[str, str] \| None = None) -> str` | The JSON a calendar panel reads, {"days": {"YYYY-MM-DD": count}}, safe inside <script>. |
| `collect(doclist: list[str]) -> None` | Add the dated documents of doclist to index and dey. |
| `day_url(doc: Doc) -> str \| None` | events_YYYYMMDD.html of the document, or None when it is not on a day page. |
| `days() -> dict[str, str]` | {doc id: 'YYYY-MM-DD'} of every event. |
| `has_day_page(doc: Doc) -> bool` | True when the document is on a day page of this build, so its date may link there. |

### gallery

gallery.html: property buttons, a value chooser, a masonry grid of thumbnails, a lightbox.

- Templates: `PAGE_GALLERY`
- Assets: `gallery`
- Reserves: `gallery.md`

What `site.features.gallery` offers:

| Method | What it does |
|---|---|
| `data() -> MediaData` | The documents with images, newest first, their images and the filters they can be narrowed by. |
| `deploy_thumbs() -> None` | Copy the thumbnails the Gallery uses into the site and drop the others, there and in var/thumbs. |
| `image(src: str, local: str \| None) -> dict[str, Any]` | The entry of one image: what the grid shows (a thumbnail or the original) and its size. |
| `items(doc_id: str) -> list[dict[str, Any]]` | The images one document shows, each with its thumbnail, size and caption. |
| `theme_image(src: str, local: str \| None) -> dict[str, Any]` | A legacy theme may override gallery_image(); a BaseTheme theme gets image(). |
| `thumb_dir() -> str` | Thumbnails made by earlier builds: <repo>/var/thumbs. |
| `write() -> None` | gallery.html: no image at first; the property buttons on the right choose which ones to show. |

### metadata

section(doc): the METADATA_SECTION of a document; actions(var): its SECTION_ACTIONS.

- Templates: `SECTION_ACTIONS`

| Hook | Default |
|---|---|
| `build_metadata_section(doc: Doc) -> str` | Default of the hook: the metadata section of a document. |

What `site.features.metadata` offers:

| Method | What it does |
|---|---|
| `actions(var: dict[str, Any]) -> str` | The html of the page actions (SECTION_ACTIONS). |
| `labels(values: list[tuple[str, str]]) -> str` | The html links of (page, text) pairs; empty texts are left out. |
| `section(doc: Doc) -> str` | The metadata section of a document, through the theme's hook when it has one. |
| `section_html(doc_id: str) -> str` | The METADATA_SECTION block of a document (keys and values). |
| `values_of(doc_id: str, key: str) -> list[tuple[str, str]]` | (page, value) pairs of a property of a document; a date key has no page. |

### navigation

neighbours(doc): the previous and next document of the reading sequence doc belongs to.

| Hook | Default |
|---|---|
| `ordered_pages(doc: Doc) -> list[Any]` | The reading sequence doc belongs to, in order (Docs or ids); default none. |

What `site.features.navigation` offers:

| Method | What it does |
|---|---|
| `neighbours(doc: Doc) -> tuple[Doc \| None, Doc \| None]` | The previous and next Doc of doc; None at either end or when doc is not in a sequence. |

### not_found

The page web servers show for a missing page.

- Templates: `PAGE_404`
- Reserves: `404.md`

### property_pages

The pages built from the properties of the documents.

- Requires: `table`
- Templates: `PAGE_PROPERTIES`, `PAGE_KEY`, `PAGE_KEY_VALUE`, `WORDCLOUD`

| Option | Default |
|---|---|
| `properties_title` | `'Properties'` |
| `properties_cloud` | `True` |
| `reuse_unchanged_pages` | `False` |
| `tagcloud_scale_skips_empty` | `False` |

| Hook | Default |
|---|---|
| `cloud_measure(frequency: int, max_frequency: int) -> dict[str, Any]` | The size fields of a property button or a tag cloud word. |
| `frequency_keys() -> list[str]` | The properties whose value count sizes the property buttons. |
| `value_page(key: str, value: str, docs: list[Doc]) -> None` | Write the page of a property value (Key_Value.html): the table of its documents. |

What `site.features.property_pages` offers:

| Method | What it does |
|---|---|
| `max_values() -> int` | The highest number of values of a property. |
| `reuse(name: str, counter: str, reason: str, func: str) -> bool` | Keep the cached page when reuse_unchanged_pages is on and nothing it shows changed. |
| `tagcloud(key: str) -> str` | A tag cloud of the values of a property, or '' when it has none. |
| `value_page_of(kvpath: tuple[str, str, bool]) -> None` | The pipeline's call for one value: the theme's value_page() hook when the page is rebuilt. |
| `write_key_page(key: str, values: list[str]) -> None` | Key.html: the tag cloud of a property and the count of each value. |
| `write_properties_page() -> None` | properties.html: every property with its numbers of values and documents, and with |
| `write_value_page(kvpath: tuple[str, str, bool]) -> None` | Key_Value.html: the documents that have a value (written only when compile is True). |

### related

related(doc): the documents that share the rarest values with doc, best first.

| Option | Default |
|---|---|
| `related_keys` | `('SID', 'Product', 'Transaction', 'Component', 'Tag')` |

| Hook | Default |
|---|---|
| `related_candidates() -> list[Any]` | Documents that may be listed as related (Docs or ids); default: every document. |

What `site.features.related` offers:

| Method | What it does |
|---|---|
| `meta() -> dict[str, dict[str, list[str]]]` | {doc id: {key: [values]}} of the candidates, read once per build. |
| `related(doc: Doc, limit: int = 5) -> list[dict[str, Any]]` | [{doc, score, shared}] of the documents related to doc, best first; doc is a document id. |
| `related_ids(doc_id: str, limit: int = 5) -> list[dict[str, Any]]` | related() of a document id over the candidates; [] when it is not one. |

### search

Full-text search over the documents, in the browser.

- Templates: `PAGE_SEARCH`, `HTML_SEARCH_BOX`
- Assets: `search`
- Sets in theme.json: `"search": true`

| Option | Default |
|---|---|
| `search_index_var` | `'KB4IT_INDEX'` |
| `search_index_warn_bytes` | `2097152` |
| `search_own_page` | `False` |
| `search_optional` | `True` |

| Hook | Default |
|---|---|
| `search_documents() -> list[Any]` | The documents of the index, in index order (Docs or ids). |
| `search_record(doc: Doc) -> dict[str, Any] \| None` | The index record of one document; None leaves it out. |
| `search_sections(doc: Doc) -> list[Any]` | [[anchor, heading, text], ...] of one document. |

What `site.features.search` offers:

| Method | What it does |
|---|---|
| `enabled() -> bool` | True when this build has search: always when search_optional is False. |
| `write_index() -> None` | Stage 8: target/search-index.js (removed with search.html when search is off). |

### stats

stats.html; with the events feature on, its year and month bars link the archive pages.

- Uses: `events`
- Templates: `PAGE_STATS`

| Option | Default |
|---|---|
| `stats_skip_keys` | `('Summary',)` |
| `reuse_unchanged_pages` | `False` |

| Hook | Default |
|---|---|
| `stats_keys() -> list[str]` | The properties listed on the stats page. |

What `site.features.stats` offers:

| Method | What it does |
|---|---|
| `events_index() -> Any` | {year: {month: {day: [docs]}}} of the events pages, or None. |

### table

Tables of documents: a date, a title and one column per property.

- Templates: `DATATABLE`, `DATATABLE_HEADER_ITEM`, `DATATABLE_BODY_ITEM`

| Option | Default |
|---|---|
| `datatable_link_template` | `'LINK_DATATABLE'` |
| `datatable_default_headers` | `('Date', 'Title')` |

| Hook | Default |
|---|---|
| `datatable_date_cell(doc: Doc) -> str` | The <td> of the date column. |
| `datatable_title_cell(doc: Doc) -> str` | The <td> of the Title column. |
| `datatable_custom_cell(doc: Doc, key: str) -> str \| None` | The whole <td> of a column the theme draws itself, or None for a plain property cell. |
| `datatable_value_link(doc: Doc, key: str, value: str) -> dict[str, str]` | The variables of LINK_DATATABLE for one value of a cell. |
| `datatable_columns(columns: list[str], docs: list[Doc]) -> list[str]` | The columns of a table of these documents; a theme may drop or add some. |

What `site.features.table` offers:

| Method | What it does |
|---|---|
| `date_cell_html(timestamp: str \| None, doc_id: str \| None) -> str` | The date cell; the date links to its events day page when the document is on one. |
| `has_day_page(doc_id: str) -> bool` | True when the document is on an events day page (feature events). |
| `legacy_date_cell(timestamp: str \| None, doc_id: str) -> str` | A legacy theme's datatable_date_cell(); an override written before doc_id existed gets the date only. |
| `render(headers: list[str] \| None = None, doclist: list[str] \| None = None, table_id: str = 'kb4it-datatable', row_attrs: Any = None) -> str` | The HTML of a table of documents; the first column is the date when headers has 'Date'. |
| `render_table(table: TableSpec) -> str` | The HTML of a Table (public API): its columns, the theme's hooks and the features' extensions. |
| `title_cell_html(doc_id: str, properties: dict[str, Any]) -> str` | The title cell: the title, shortened, with a tooltip. |

### table_filter

The filter bar of the tables of all.html, bookmarks.html, the value pages and the events pages.

- Requires: `table`
- Templates: `DATATABLE_FILTER`
- Assets: `tablefilter`

| Option | Default |
|---|---|
| `datatable_filter_keys` | `('WorkType', 'DocType', 'Category', 'Topic', 'Status', 'P...` |
| `datatable_filter_min_rows` | `10` |

What `site.features.table_filter` offers:

| Method | What it does |
|---|---|
| `bar(groups: list[dict[str, Any]], **where: str) -> str` | The DATATABLE_FILTER bar: where is table_id=... for a table, list=... for a plain list. |
| `list_filter(docs: Iterable[str], list_id: str) -> tuple[str, Callable[[Any], str]]` | The filter bar of a plain document list, and the attributes of each document. |
| `table_extension(table: Table, columns: list[str], doc_ids: list[str]) -> tuple[str, Callable[[str], str]] \| None` | The bar and row attributes of a filterable table with a Title column. |

### toc

var['toc'] of every document page, and the Contents menu of the header.

- Templates: `HTML_TOC_LI`, `HTML_TOC_SECTLEVEL1`, `HTML_TOC_SECTLEVEL2`, `HTML_TOC_SECTLEVEL3`, `HTML_TOC_SECTLEVEL4`

What `site.features.toc` offers:

| Method | What it does |
|---|---|
| `extract(source: str) -> str` | The TOC of compiled HTML in the theme's markup; '' when the source has none. |
| `menu_contents(var: dict[str, Any]) -> str` | The header's Contents menu: disabled on a system page, the document's TOC otherwise. |

### toc_sidebar

wanted(html): whether a document page shows the side table of contents.

- Requires: `toc`

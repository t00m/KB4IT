---
DocType: Reference
Feature: Themes, Development
HelpId: theme-legacy
Keyword: Builder, DocumentTheme, themekit, kit, mixin, srvdtb, page_pipeline, deprecated, THEME_API_LEGACY
Level: advanced
Order: 646
Related: dev-theme-internals.md, reference-theme-hooks.md
Section: Reference
Summary: The theme API before kb4it.theme (Builder, DocumentTheme and the kits), deprecated, generated from the KB4IT code.
---

# Theme hooks of the legacy API

**Deprecated.** A theme on `Builder` or `DocumentTheme` keeps working, and a theme outside KB4IT that
uses them logs `THEME_API_LEGACY`. New themes use `kb4it.theme`: see [Theme API reference](reference-theme-hooks.md)
and [Theme internals](dev-theme-internals.md), which says what replaces each part.

A legacy theme subclasses `Builder`, or `DocumentTheme` for a theme with property pages, and adds the kits
it wants to its class line. A method that replaces a shared one starts its docstring with `Override:`. The
tables below come from the KB4IT source (`scripts/devel/theme_hooks_doc.py`).

## Page pipeline

With `page_pipeline = True`, `build_page()` runs these hooks for every document page, in this order: `page_var`, `page_toc`, `page_context`, `body_transforms`, `page_actions`, `render_page`, `finalize_html`.

| Method | What it does | Defined in |
|---|---|---|
| `add_system_page(name: str, title: str, html: str \| None = None, as_html: bool = True, listing: bool = False) -> None` | Add a page the theme generates: write it (unless html is None) and register it as a system page. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `body_transforms(doc_id: str, var: dict) -> list` | Functions from HTML to HTML applied in order to the compiled body. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `build_page(path_md: str) -> None` | Turn the compiled body of a document into its final page and overwrite the HTML file. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `edit_url(doc_id: str = '') -> str` | Link to edit doc_id on the git server, or to the source folder without doc_id; '' when git is off. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `finalize_html(html: str) -> str` | Last change to the whole page before it is written. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `git_repo_url() -> str` | Link to the repository on the git server, such as https://github.com/user/repo; '' when git is off. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `git_url(action: str, path: str = '') -> str` | Link to <server>/<user>/<repo>/<action>/<branch>/<git_path>/<path>; '' when git is off. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `has_template(name: str) -> bool` | True when the lookup of template() finds a file for name (override, theme, base or common). | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `page_actions(var: dict) -> str` | HTML of the page actions (edit, properties...); '' when the theme has none. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `page_body_template(doc_id: str, var: dict) -> str` | Name of the template that renders the body of the page. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `page_context(doc_id: str, var: dict) -> dict` | Add the theme's own data to var before the body is rewritten and the page rendered. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `page_title(doc_id: str) -> str` | Title of a document page, or untitled_label when the document has none. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `page_toc(source_html: str) -> str` | Table of contents of the page; document themes extract it from the compiled body. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `page_var() -> dict` | Base var of a document page: get_theme_var(); a theme whose templates do not use it may return less. | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `render_page(doc_id: str, var: dict) -> str` | Whole page: the body template, between HTML_HEADER_COMMON and HTML_FOOTER when the theme has them. | `kb4it.services.pagepipeline.PagePipelineMixin` |

| Attribute | Default | Defined in |
|---|---|---|
| `ellipsize_titles` | `True` | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `log_area` | `'THEME'` | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `page_pipeline` | `False` | `kb4it.services.pagepipeline.PagePipelineMixin` |
| `untitled_label` | `''` | `kb4it.services.pagepipeline.PagePipelineMixin` |

## Settings, checks and search

Theme settings (`config_class`), the post-build checks and the search index.

| Method | What it does | Defined in |
|---|---|---|
| `checks(target) -> list` | Problems of the built site in target; default: broken links to pages and anchors of the target root. | `kb4it.services.builder.Builder` |
| `run_checks(target=None) -> list` | Log every problem of checks(); an error, or any problem with repo.json "strict": true, fails the build. | `kb4it.services.builder.Builder` |
| `search_documents() -> list` | Doc ids of the search index, in index order; default: the source documents, sorted. | `kb4it.services.builder.Builder` |
| `search_enabled() -> bool` | Full-text search is on when the theme supports it ("search": true in theme.json) | `kb4it.services.builder.Builder` |
| `search_record(doc_id) -> dict` | Index record of one document; themes may override to add facets or a summary. | `kb4it.services.builder.Builder` |
| `search_sections(doc_id) -> list` | [[anchor, heading, text], ...] of one document; default: the sections the compiler recorded. | `kb4it.services.builder.Builder` |
| `write_index_file(target) -> list` | Write target/search-index.js: search_record() of each search_documents() id, None skipped; return the ids. | `kb4it.services.builder.Builder` |
| `write_search_index()` | Write target/search-index.js from the sections the compiler recorded; remove it when search is off. | `kb4it.services.builder.Builder` |

| Attribute | Default | Defined in |
|---|---|---|
| `config_class` | `None` | `kb4it.services.builder.Builder` |
| `search_index_var` | `'KB4IT_INDEX'` | `kb4it.services.builder.Builder` |
| `search_index_warn_bytes` | `5242880` | `kb4it.services.builder.Builder` |

## Generated pages and helpers

What `Builder` offers every theme: pages it can write, templates and shared data.

| Method | What it does | Defined in |
|---|---|---|
| `after_checks()` | After the post-build checks passed (stage 8); themes on BaseTheme use it. | `kb4it.services.builder.Builder` |
| `apply_transformations(content)` | Apply CSS transformations to the compiled page. | `kb4it.services.builder.Builder` |
| `backlinks(doc_id) -> list` | [{title, href}] of the documents that link to doc_id; [] when "backlinks" is false. | `kb4it.services.builder.Builder` |
| `backlinks_html(doc_id) -> str` | The HTML_BACKLINKS block of the documents that link to doc_id; '' when none does. | `kb4it.services.builder.Builder` |
| `build_page_key(key, values)` | Create page for a key. | `kb4it.services.builder.Builder` |
| `build_page_key_value(kvpath)` | Build the final HTML Page for a document key-value. | `kb4it.services.builder.Builder` |
| `create_page_about_app()` | About this app page, generated only when the user repo has no about_app.md. | `kb4it.services.builder.Builder` |
| `create_page_about_kb4it()` | About KB4IT page. | `kb4it.services.builder.Builder` |
| `create_page_add() -> None` | Build add.html when the editor is on, otherwise remove the page an earlier build left. | `kb4it.services.addpage.AddPageMixin` |
| `create_page_help()` | Help page,  generated only when the user repo has no help.md. | `kb4it.services.builder.Builder` |
| `create_page_search()` | Search page (search.html), built only when search is on. | `kb4it.services.builder.Builder` |
| `distribute_html(mdId, htmlId)` | Add compiled page to the target list. | `kb4it.services.builder.Builder` |
| `distribute_md(name, content, as_html=True, listing=False)` | Distribute a theme-rendered system page to the temporary directory. | `kb4it.services.builder.Builder` |
| `editor_enabled() -> bool` | True when the theme class supports the Add page and the editor setting is on. | `kb4it.services.addpage.AddPageMixin` |
| `editor_keys() -> dict` | Completion data {Key: [{"v": value, "c": count}]} from the repository's documents. | `kb4it.services.addpage.AddPageMixin` |
| `feed_enabled() -> bool` | True when the feed is on and repo.json has the site_url its links need. | `kb4it.services.builder.Builder` |
| `feed_settings()` | Feed settings, or None when the theme has no feed. theme.json "feed": true turns it on by default. | `kb4it.services.builder.Builder` |
| `generate_sources()` | Generate sources. | `kb4it.services.builder.Builder` |
| `get_services()` | Get services. | `kb4it.services.builder.Builder` |
| `get_theme_var()` | Create a new variable for rendering templates. | `kb4it.services.builder.Builder` |
| `inject_head_meta(html, page_name) -> str` | Insert (or replace) the HTML_HEAD_META block before </head>. | `kb4it.services.headmeta.HeadMetaMixin` |
| `is_listing_page(page_name) -> bool` | True for a page that lists documents (property, value, event, stats pages), not content. | `kb4it.services.indexing.IndexingMixin` |
| `modified_date(doc_id) -> str` | dateModified of a document, as the processor resolved it (Modified, git, file time). | `kb4it.services.indexing.IndexingMixin` |
| `page_dates() -> dict` | 'page.html' -> dateModified of each content document, the value its page head carries. | `kb4it.services.indexing.IndexingMixin` |
| `page_lang() -> str` | Language of the generated pages: repo.json seo.lang, else English. | `kb4it.services.headmeta.HeadMetaMixin` |
| `page_meta(page_name, html) -> dict` | Values for HTML_HEAD_META: description, Open Graph and canonical link of one page. | `kb4it.services.headmeta.HeadMetaMixin` |
| `page_robots(page_name) -> str` | Content of the robots meta tag of a page, or empty when it may be indexed. | `kb4it.services.indexing.IndexingMixin` |
| `people_settings() -> kb4it.core.people.PeopleSettings` | The checked repo.json "people" block (Backend loads it with the configuration). | `kb4it.services.profilecard.ProfileCardMixin` |
| `person_category() -> dict` | The Person profile skeleton, added to every skeleton set (see core/people.py). | `kb4it.services.addpage.AddPageMixin` |
| `person_data(profile) -> dict` | The schema.org Person of a profile; private keys are left out. | `kb4it.services.headmeta.HeadMetaMixin` |
| `person_iri(name) -> str` | The @id of a person: <site_url>Author_Jane_Doe.html#person, or <site_url>#person-Jane_Doe without person pages. | `kb4it.services.headmeta.HeadMetaMixin` |
| `person_tip(key: str, value: str) -> str` | Role and team of the person a people key value names, for the tooltip of the name on document pages. | `kb4it.services.profilecard.ProfileCardMixin` |
| `post_activities()` | Theme post activities. | `kb4it.services.builder.Builder` |
| `post_deploy_activities()` | Theme activities executed after the site has been deployed. | `kb4it.services.builder.Builder` |
| `prepare()` | After the documents are read and before any page is built (stage 3); themes on BaseTheme use it. | `kb4it.services.builder.Builder` |
| `profile_actions(value: str, profile: kb4it.core.people.Profile \| None) -> dict` | Create and Edit links to the Add page, while the editor is on; the texts travel in the address. | `kb4it.services.profilecard.ProfileCardMixin` |
| `profile_card(key: str, value: str) -> str` | HTML of the profile card for a value page, or an empty string. | `kb4it.services.profilecard.ProfileCardMixin` |
| `profile_rows(profile: kb4it.core.people.Profile) -> list[dict]` | {key, value, href} of each visible profile key, in card order. | `kb4it.services.profilecard.ProfileCardMixin` |
| `register_add_page(html: str) -> None` | Write the Add page body and register it as a system page; a theme may override this only. | `kb4it.services.addpage.AddPageMixin` |
| `remove_stale_add_page() -> None` | Remove add.html left by an earlier build from the target and the cache. | `kb4it.services.addpage.AddPageMixin` |
| `render_template(name, var=None)` | Render template according to dict var values. | `kb4it.services.builder.Builder` |
| `reuse_cached_page(name, counter, reason, func)` | Keep the cached `name`.html of the previous build when the runtime counter (ncd or nck) is 0. | `kb4it.services.builder.Builder` |
| `search_box() -> str` | Search box markup for the theme's header, or '' when search is off. | `kb4it.services.builder.Builder` |
| `search_page() -> str` | Page that runs a search from ?q=, or empty when the site has none. | `kb4it.services.headmeta.HeadMetaMixin` |
| `seo_settings() -> kb4it.core.structured.SeoSettings` | The checked repo.json "seo" block (Backend loads it with the configuration). | `kb4it.services.headmeta.HeadMetaMixin` |
| `site_signature() -> str` | Return a value that changes when every page must be rebuilt; empty turns the check off. | `kb4it.services.builder.Builder` |
| `sitemap_exclude() -> set` | Pages left out of sitemap.xml; themes may add their own. | `kb4it.services.indexing.IndexingMixin` |
| `skeleton_set() -> tuple[str, list[dict]]` | Return (source, categories) of the first skeleton folder that holds a *-SKELETON.md file. | `kb4it.services.addpage.AddPageMixin` |
| `structured_data(page_name, doc_id, title, description) -> str` | JSON-LD of one page: the document node, and the WebSite node on the home page. | `kb4it.services.headmeta.HeadMetaMixin` |
| `structured_defaults() -> dict` | schema.org type of a document without a known DocType, and the frontmatter key map of the theme. | `kb4it.services.headmeta.HeadMetaMixin` |
| `target_subdir()` | Folder inside target to build into, or None. apphelp uses it for versioned help. | `kb4it.services.builder.Builder` |
| `template(template)` | Return Mako Template object. | `kb4it.services.builder.Builder` |
| `write_feed()` | feed.xml (Atom) with the newest dated documents. | `kb4it.services.builder.Builder` |
| `write_sitemap()` | sitemap.xml and robots.txt, following seo.index; "sitemap": false turns them off. | `kb4it.services.indexing.IndexingMixin` |

| Attribute | Default | Defined in |
|---|---|---|
| `add_page` | `False` | `kb4it.services.addpage.AddPageMixin` |
| `person_pages` | `True` | `kb4it.services.headmeta.HeadMetaMixin` |
| `profile_skeleton` | `True` | `kb4it.services.addpage.AddPageMixin` |

## DocumentTheme

What a `DocumentTheme` subclass gets on top of `Builder`: property pages, tables, events, the table of contents and the 404 page.

| Method | What it does | Defined in |
|---|---|---|
| `build_datatable(headers: list[str] \| None = None, doclist: list[str] \| None = None, table_id: str = 'kb4it-datatable') -> str` | Given a list of columns, it builds a datatable; the first column is the date when headers has 'Date'. | `kb4it.services.themekit.tables.TableMixin` |
| `build_events(doclist: list[str]) -> set[str]` | Create the day, month and year pages of the dated documents in `doclist`. | `kb4it.services.themekit.events.EventsMixin` |
| `build_metadata_section(docId: str) -> str` | Return a html block for displaying metadata (keys and values). | `kb4it.services.themekit.metadata.MetadataMixin` |
| `build_page_404() -> None` | Create the 404 page; as a system page it stays out of listings, search, feed and sitemap. | `kb4it.services.themekit.notfound.NotFoundMixin` |
| `build_page_bookmarks() -> str \| None` | Create the bookmarks page: documents with Bookmark set to Yes, True or On, in any case. | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `build_page_index_all() -> str \| None` | Create the page that lists every document. | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `build_page_key(key: str, values: list[str]) -> None` | Create the page of a property: its tag cloud and the count of each value. | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `build_page_key_value(kvpath: tuple[str, str, bool]) -> None` | Create the page of a property value: the documents that have it. | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `build_page_properties() -> None` | Create the properties page: every property with its numbers of values and documents, and with | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `build_page_stats() -> None` | Create the stats page of the repository. | `kb4it.services.themekit.stats.StatsMixin` |
| `build_tagcloud_from_key(key: str) -> str` | Return a tag cloud of the values of a property, or '' when it has none. | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `cloud_measure(frequency: int, max_frequency: int) -> dict[str, Any]` | Return the size fields of a property button or a tag cloud word. | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `datatable_custom_cell(doc_id: str, key: str) -> str \| None` | Return the whole <td> of a column the theme draws itself, or None for a plain property cell. | `kb4it.services.themekit.tables.TableMixin` |
| `datatable_date_cell(timestamp: str \| None, doc_id: str \| None = None) -> str` | Return the cell of the date column; `timestamp` is None when the document has none. | `kb4it.services.themekit.tables.TableMixin` |
| `datatable_title_cell(docId: str, properties: dict[str, Any]) -> str` | Return the cell of the Title column: the title, shortened, with a tooltip. | `kb4it.services.themekit.tables.TableMixin` |
| `datatable_value_link(properties: dict[str, Any], key: str, value: str) -> dict[str, str]` | Return the variables of the link to the page of a value; KeyError leaves the cell empty. | `kb4it.services.themekit.tables.TableMixin` |
| `date_cell(timestamp: str \| None, doc_id: str) -> str` | datatable_date_cell() of one row; a theme's override written before `doc_id` existed gets the date only. | `kb4it.services.themekit.tables.TableMixin` |
| `event_documents() -> list[str]` | Documents that get day, month and year pages; default none. | `kb4it.services.themekit.events.EventsMixin` |
| `extract_toc(source: str) -> str` | Extract the TOC from compiled HTML in the theme's markup; '' when the source has none. | `kb4it.services.themekit.toc.TocMixin` |
| `frequency_keys() -> list[str]` | Return the properties whose value count sizes the property buttons. | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `get_html_values_from_key(docId: str, key: str) -> list[tuple[str, str]]` | Return (page, value) pairs for the values of a property of a document; a date key has no page. | `kb4it.services.themekit.metadata.MetadataMixin` |
| `get_labels(values: list[tuple[str, str]]) -> str` | Return the html links for (page, text) pairs; empty texts are left out. | `kb4it.services.themekit.metadata.MetadataMixin` |
| `get_maxkv_freq() -> int` | Return the highest number of values of a property. | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `get_page_actions(var: dict[str, Any]) -> str` | Return the html of the page actions (SECTION_ACTIONS). | `kb4it.services.themekit.metadata.MetadataMixin` |
| `has_event_page(doc_id: str) -> bool` | True when doc_id is on an events day page of this build, so its date may link there. | `kb4it.services.themekit.events.EventsMixin` |
| `menu_contents(var: dict[str, Any]) -> str` | The header menu: disabled on a system page, the document contents otherwise. | `kb4it.services.themekit.page.DocumentPageMixin` |
| `page_actions(var: dict[str, Any]) -> str` | The page actions (SECTION_ACTIONS). | `kb4it.services.themekit.page.DocumentPageMixin` |
| `page_toc(source_html: str) -> str` | The TOC of the compiled body, in the theme's markup. | `kb4it.services.themekit.page.DocumentPageMixin` |
| `stats_keys() -> list[str]` | Return the properties listed on the stats page. | `kb4it.services.themekit.keypages.KeyPagesMixin` |

| Attribute | Default | Defined in |
|---|---|---|
| `datatable_default_headers` | `('Date', 'Title')` | `kb4it.services.themekit.tables.TableMixin` |
| `datatable_link_template` | `'LINK_DATATABLE'` | `kb4it.services.themekit.tables.TableMixin` |
| `page_pipeline` | `True` | `kb4it.services.themekit.page.DocumentPageMixin` |
| `properties_cloud` | `True` | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `properties_title` | `'Properties'` | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `reserved_pages` | `()` | `kb4it.services.themekit.notfound.NotFoundMixin` |
| `reuse_unchanged_pages` | `False` | `kb4it.services.themekit.keypages.KeyPagesMixin` |
| `stats_skip_keys` | `('Summary',)` | `kb4it.services.themekit.stats.StatsMixin` |
| `tagcloud_scale_skips_empty` | `False` | `kb4it.services.themekit.keypages.KeyPagesMixin` |

## Diagrams kit

The Diagrams page: every Mermaid diagram of the documents, with filters. Add `DiagramsMixin` from `kb4it.services.themekit.diagrams` to the class line.

| Method | What it does | Defined in |
|---|---|---|
| `build_page_diagrams() -> None` | The Diagrams page: no diagram at first; the browser draws the ones the filters choose. | `kb4it.services.themekit.diagrams.DiagramsMixin` |
| `diagram_html(doc_id: str) -> str` | The HTML of a document body with a mermaid fence, as the compiler makes it, so the heading ids match; else ''. | `kb4it.services.themekit.diagrams.DiagramsMixin` |
| `diagram_items(doc_id: str) -> list[dict[str, Any]]` | The diagrams of one document, each linked to its section. | `kb4it.services.themekit.diagrams.DiagramsMixin` |

## Gallery kit

The Gallery page: every image of the documents as thumbnails, with filters; needs the vendor library `gallery`. Add `GalleryMixin` from `kb4it.services.themekit.gallery` to the class line.

| Method | What it does | Defined in |
|---|---|---|
| `build_page_gallery() -> None` | The Gallery page: no image at first; the property buttons on the right choose which ones to show. | `kb4it.services.themekit.gallery.GalleryMixin` |
| `deploy_gallery_thumbs() -> None` | Copy the thumbnails the Gallery uses into the site and drop the others, there and in var/thumbs. | `kb4it.services.themekit.gallery.GalleryMixin` |
| `gallery_data() -> MediaData` | Return the documents with images, newest first, their images and the filters they can be narrowed by. | `kb4it.services.themekit.gallery.GalleryMixin` |
| `gallery_image(src: str, local: str \| None) -> dict[str, Any]` | The entry of one image: what the grid shows (a thumbnail or the original) and its size. | `kb4it.services.themekit.gallery.GalleryMixin` |
| `gallery_items(doc_id: str) -> list[dict[str, Any]]` | The images one document shows, each with its thumbnail, size and caption. | `kb4it.services.themekit.gallery.GalleryMixin` |
| `gallery_thumb_dir() -> str` | Thumbnails made by earlier builds: <repo>/var/thumbs. | `kb4it.services.themekit.gallery.GalleryMixin` |

## Navigation kit

Previous and next page in the reading order the theme gives. Add `NavigationMixin` from `kb4it.services.themekit.navigation` to the class line.

| Method | What it does | Defined in |
|---|---|---|
| `neighbours(doc_id: str) -> tuple[str \| None, str \| None]` | Previous and next doc id of doc_id in its sequence; (None, None) when it is not listed. | `kb4it.services.themekit.navigation.NavigationMixin` |
| `ordered_pages(doc_id: str) -> list[str]` | Doc ids of the reading sequence doc_id belongs to, in order (a whole help site, one book); default none. | `kb4it.services.themekit.navigation.NavigationMixin` |

## Related kit

Related documents: those that share rare property values. Add `RelatedMixin` from `kb4it.services.themekit.related` to the class line.

| Method | What it does | Defined in |
|---|---|---|
| `related_candidates() -> list[str]` | Documents that may be listed as related; default: every document that is not a system page. | `kb4it.services.themekit.related.RelatedMixin` |
| `related_docs(doc_id: str, limit: int = 5) -> list[dict[str, Any]]` | related() of doc_id over the candidates; [] when doc_id is not one. The metadata is read once per build. | `kb4it.services.themekit.related.RelatedMixin` |

| Attribute | Default | Defined in |
|---|---|---|
| `related_keys` | `('SID', 'Product', 'Transaction', 'Component', 'Tag')` | `kb4it.services.themekit.related.RelatedMixin` |

## TOC sidebar kit

A second, sticky table of contents for long documents. Add `TocSidebarMixin` from `kb4it.services.themekit.tocsidebar` to the class line.

| Method | What it does | Defined in |
|---|---|---|
| `toc_sidebar(source_html: str) -> bool` | True when repo.json (else the theme settings) asks for the sidebar and the page has four or more sections. | `kb4it.services.themekit.tocsidebar.TocSidebarMixin` |

## Table filter kit

A filter bar over the document tables; needs `DATATABLE_FILTER.tpl` and the vendor library `tablefilter`. Add `FilterMixin` from `kb4it.services.themekit.filters` to the class line.

| Method | What it does | Defined in |
|---|---|---|
| `build_datatable(headers: list[str] \| None = None, doclist: list[str] \| None = None, table_id: str = 'kb4it-datatable') -> str` | Put the filter bar, hidden, before the table; datatable-filter.js moves it below the search box. | `kb4it.services.themekit.filters.FilterMixin` |
| `build_events(doclist: Any) -> Any` | Archive pages of a year, month or day (events_YYYY*.html): their tables get the filter bar. | `kb4it.services.themekit.filters.FilterMixin` |
| `build_page_bookmarks() -> Any` | bookmarks.html: its table gets the filter bar. | `kb4it.services.themekit.filters.FilterMixin` |
| `build_page_index_all() -> Any` | all.html: its table gets the filter bar. | `kb4it.services.themekit.filters.FilterMixin` |
| `build_page_key_value(kvpath: Any) -> Any` | Property value pages: their table gets the filter bar. | `kb4it.services.themekit.filters.FilterMixin` |
| `datatable_title_cell(docId: str, properties: Any) -> str` | The Title cell of a table with the filter bar carries the values the bar matches on. | `kb4it.services.themekit.filters.FilterMixin` |
| `list_filter(docs: collections.abc.Iterable[str], list_id: str) -> tuple[str, collections.abc.Callable[[typing.Any], str]]` | The filter bar of plain document lists (Quality page), and the attributes of each document. | `kb4it.services.themekit.filters.FilterMixin` |

| Attribute | Default | Defined in |
|---|---|---|
| `datatable_filter_keys` | `('WorkType', 'DocType', 'Category', 'Topic', 'Status', 'P...` | `kb4it.services.themekit.filters.FilterMixin` |
| `datatable_filter_min_rows` | `10` | `kb4it.services.themekit.filters.FilterMixin` |

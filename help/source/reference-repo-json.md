---
DocType: Reference
Feature: Configuration
HelpId: repo-json
Keyword: settings, config, repo.json, version, sanitize, nh3, title, theme, source, target, workers, ignored_keys, hidden_properties, publish_sources, fail_on_invalid, theme_path, force, search, site_url, sitemap, robots.txt, feed, atom, rss, overrides, hooks, backlinks, linked from, og_image, open graph, description, seo, json-ld, schema.org, structured data, lang, language, index, noindex, noindex_keys, robots, search engines, people, person, profile, Alias, Modified, dateModified, markdown, extensions, pymdownx, highlight, pygments, syntax highlighting
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

| Key | Values | Meaning |
|---|---|---|
| `title` | Text | Name of the site, shown in the header and the browser tab |
| `theme` | `techdoc`, `blog`, `bookshelf`, `apphelp`, or the name of a theme of your own | Theme name, see [Themes](explanation-themes.md) |
| `source` | Folder path | Folder with the documents |
| `target` | Folder path | Folder where the website is written |

A missing key stops the build with `CONFIG_KEY_MISSING key=...`.

`source` and `target` are relative to the knowledge base folder, the one that holds `config/`. Absolute paths, `~` and `$VARIABLES` also work. `kb4it create` writes absolute paths. When the knowledge base is kept in git or built on another computer, change them to `"source": "source"` and `"target": "target"`.

KB4IT removes from `target` the pages of documents you deleted. It only removes pages it wrote itself, so other files you keep in `target` stay; still, `target` must be a folder of its own. The build stops with an error when `target` is the knowledge base folder, `source`, `config/`, `var/`, your home folder or a filesystem root, when it holds any of them, or when it lies inside `source`.

## Optional {#optional}

| Key | Values | Default | Meaning |
|---|---|---|---|
| `tagline` | Text | | Short subtitle |
| `logo` | Path inside the website | theme logo | Logo image, relative to the website. The logo is also the favicon of every page; without `logo`, the page uses the theme's own logo |
| `logo_alt` | Text | | Text of the logo for screen readers; empty uses the site `title` |
| `workers` | Integer, 1 or more | half the processor cores | Documents converted at the same time |
| `force` | `true`, `false` | `false` | Rebuild everything on every build, like `--force` |
| `ignored_keys` | List of property names | `[]` | Properties that get no pages; see [properties](explanation-properties.md#excluded) |
| `hidden_properties` | List of property names | `[]` | Properties left out of the properties page and the Properties menu; they keep their pages. See [properties](explanation-properties.md#excluded) |
| `publish_sources` | `true`, `false` | `true` | Copy the `.md` files to the website, in `target/sources/` |
| `fail_on_invalid` | `true`, `false` | `false` | Stop the build when a document cannot be read |
| `theme_path` | Folder path | | Use the theme in this folder instead of searching by name |
| `site_url` | URL ending in `/` | | Public address of the site, such as `https://me.github.io/kb/`. Needed for `sitemap.xml`, the feed and canonical links; changing it rebuilds every page |
| `seo` | Object | | Language of the pages and structured data for search engines; see [structured data](#seo) |
| `profiles` | Object: property name to settings | `Author` as a person | Which properties have profiles and what their profiles do; see [profiles](#people) |
| `profiles_private` | List of profile properties | `[]` | Profile properties kept out of the pages and the structured data; see [profiles](#people) |
| `people` | Object | | Old form of `profiles`, still read for this release; see [profiles](#people) |
| `timezone` | IANA zone name, such as `Europe/Madrid` | the computer's zone | Time zone of every date written without an offset; see [dates](#dates) |
| `dates` | Object: property name to settings | | More properties to read as dates; see [dates](#dates) |
| `og_image` | Path inside the website | | Image shown when a page is shared on social networks, such as `resources/share.png`; needs `site_url` |
| `sitemap` | `true`, `false` | `true` | With `site_url`, write `sitemap.xml` and `robots.txt`; a `robots.txt` in `source/` is used instead of the generated one. See [Search engines](#indexing) for `seo.index` |
| `backlinks` | `true`, `false` | `true` | At the end of each document, list the documents that link to it ("Linked from"); `false` hides the list |
| `feed` | Object | blog: on; techdoc, bookshelf: off | Atom feed `feed.xml`, see [feed](#feed) |
| `hooks` | Path to a Python file | | Python file with build hooks, such as `hooks/hooks.py`; see [Run your own code during a build](howto-hooks.md) |
| `overrides` | Folder path | `overrides` | Folder with templates and files that replace or extend the theme's; see [Change one template of a theme](howto-customize-templates.md) |
| `search` | `true`, `false` | `true` | Full-text search in techdoc, blog and bookshelf; `false` removes the search box, `search.html` and `search-index.js`. See [search](#search) |
| `editor` | `true`, `false` | techdoc: on; blog, bookshelf, apphelp: off | Add page (`add.html`) with a Markdown editor for new documents. Any other value stops the build. `false` removes the page and the link to it |
| `git` | `true`, `false` | `false` | Edit links to your git server. They appear only with `"git": true` and `git_server`, `git_user`, `git_repo` and `git_branch` all set |
| `git_server` | Full URL such as `https://github.com`; a host name such as `github.com` in apphelp | | Git server of the edit links |
| `git_user` | Text | | User or organisation on the git server |
| `git_repo` | Text | | Repository name |
| `git_branch` | Text | | Branch the edit links open |
| `git_path` | Folder path inside the repository | | Folder that holds the documents; may stay empty for the repository root |

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

| Key | Values | Default | Meaning |
|---|---|---|---|
| `extensions` | List of extension names | `[]` | Extension names, as python-markdown expects them. Extensions that ship with python-markdown work right away; others must be installed where KB4IT runs |
| `extension_configs` | Object: extension name to settings | `{}` | Settings per extension |
| `highlight` | `client`, `pygments`, `none` | `client` | How code blocks are coloured: `client` (highlight.js in the browser, as before), `pygments` (at build time, no JavaScript), or `none` |
| `pygments_style` | [Pygments style](https://pygments.org/styles/) name | `default` | Style for light colour schemes, with `pygments` |
| `pygments_style_dark` | Pygments style name | `monokai` | Style for dark colour schemes, with `pygments` |
| `sanitize` | `true`, `false` | `false` | `true` removes scripts, event handlers, `javascript:` links and any other markup Markdown does not make from each document. Needs nh3, part of the extras. See [Raw HTML](reference-document-format.md#raw-html) |

With `"highlight": "pygments"` the build writes `resources/pygments.css`, and the pages no longer load highlight.js. Code blocks without a language are left plain.

With `pymdownx.superfences` (or `pymdownx.highlight`), code blocks follow `highlight` too: KB4IT sets `use_pygments` of `pymdownx.highlight` to `true` only in `pygments` mode, so in `client` mode highlight.js colours them. A `use_pygments` of your own in `extension_configs` wins.

Changing the block rebuilds every page. An extension that is not installed stops the build with `MD_EXTENSION_MISSING name=... hint=pip install ...`; `kb4it verify` reports it too.

The [PyMdown Extensions](https://facelessuser.github.io/pymdown-extensions/) (task lists, tabs, details, keys and more) install with KB4IT. The sample repositories of every theme turn on `pymdownx.tasklist`, so `kb4it create` makes a repository with task lists. The extras, `uv tool install "KB4IT[extras]"` or `pipx install "KB4IT[extras]"`, bring [nh3](https://nh3.readthedocs.io/), which `sanitize` needs.

## Search {#search}

techdoc, blog and bookshelf build `search-index.js` with the text of every document, split by section, and a `search.html` page. Search runs in the browser, so it also works when you open the site from disk. Results link to the section that matched. The search page offers filters by `Category`, `WorkType` and `Tag`, for the keys your documents use.

The index grows with your documents; above 5 MB the build warns with `[SEARCH] INDEX_LARGE`. Turn it off with `"search": false`. apphelp has its own search, configured in its `apphelp` block.

## Profiles {#people}

A profile is a source whose file name starts with `PROFILE-` (any case), such as `PROFILE-SAP-BASIS.md`. `ProfileOf` names the property whose value it describes, and its title is that value, exactly as documents write it. A `PROFILE-` file without `ProfileOf` is left out with `PROFILE_INVALID`. A date property, `Title`, an ignored property, `Alias` and `ProfileOf` cannot have profiles.

```markdown
---
Email: sap-basis@example.org
Lead: Jane Doe
ProfileOf: Team
---

# SAP Basis

Runs the SAP landscape.
```

The `profiles` block says what the profiles of each property do:

```json
"profiles": {
  "Author": {"type": "Person", "contact_keys": ["Email", "Phone", "Chat", "Url"], "missing": "penalty", "tip": ["Role", "Team"]},
  "Team": {"type": "Organization", "missing": "notice"}
},
"profiles_private": ["Phone"]
```

| Setting | Values | Default | Meaning |
|---|---|---|---|
| `type` | schema.org type, such as `Person` or `Organization` | `Thing` | schema.org type of the described thing. Properties of type `Person` name people and share person profiles |
| `contact_keys` | List of profile properties | none | Profile properties that tell readers how to reach it |
| `missing` | `penalty`, `notice`, `none` | `none` | A value without a profile: `penalty` (quality points), `notice` (`VALUE_NO_PROFILE` in `kb4it verify`), `none`. For now only `notice` acts; people keep the techdoc `author_profiles` setting |
| `tip` | List of profile properties | none | Profile properties shown as the tooltip of the value on document pages. Not used yet: people show `Role` and `Team` |
| `map` | Object, with the syntax of `seo.map` | none | Profile property -> schema.org property |

Without `profiles`, `Author` is a person with the defaults shown above. The cards of profiles of other properties, such as `Team`, come in a later release; their profiles already load and are checked.

The old `people` block is read as the `Author` entries of `profiles` (`PEOPLE_BLOCK_DEPRECATED`). When `repo.json` has both blocks, `profiles` decides and `people` is not read (`PEOPLE_BLOCK_IGNORED`). A person profile is described below.

A person profile is a source such as `PROFILE-JANE-DOE.md` with `ProfileOf: Author`. A file named with the old `PERSON-` prefix is an ordinary document. A person profile describes one person that documents name in `Author`: its title holds the name exactly as documents write it, `Alias` the other spellings, and any other property (`Team`, `Role`, `Email`, `Phone`) says more about the person. A profile is not a document: it gets no page of its own, and a link to its file leads to the person's page, such as `Author_Jane_Doe.html`. That page shows the profile above the person's documents: the name, the properties (`Email` and `Phone` as links), and the text of the profile. A page for another spelling in `Alias` shows the same profile and links to the main page. A person with a profile and no document yet still gets a page.

The Add page offers a **Person profile** skeleton in every theme but apphelp. While the editor is on, the person's page shows **Edit profile**, or **Create profile** when the person has none. Edit profile carries the whole profile in its link, so a profile with a `private` property gets no Edit profile: edit its file instead. Create profile opens the skeleton with the name as its title, and proposes the file name `profile-<name>.md` (`profile-jane-doe.md`) in the dialog title and on **Save**: save it in the `source/` folder and rebuild. The techdoc, blog and bookshelf themes show the profile; a theme of your own shows it when its `PAGE_KEY_VALUE.tpl` prints `var['profile_card']`. On document pages, the name of a person with a profile shows the profile's `Role` and `Team` as a tooltip. See [Describe a person with a profile](howto-describe-person.md).

In the structured data, each person is one schema.org `Person`: documents point to it by `@id` (`<site_url>Author_Jane_Doe.html#person`, with aliases resolved to the profile name), and the person's page describes it as a `ProfilePage`, with `name`, `alternateName` (from `Alias`), `description` (the first paragraph of the profile text) and the mapped properties. apphelp has no person pages: the people go into the structured data of its home page, with the `@id` `<site_url>#person-Jane_Doe`.

```json
"people": {
  "keys": ["Author"],
  "contact_keys": ["Email", "Phone", "Chat", "Url"],
  "private": [],
  "map": {"Badge": "identifier"}
}
```

| Key | Values | Default | Meaning |
|---|---|---|---|
| `keys` | List of property names | `["Author"]` | Properties whose values are people. The first one names the person's page |
| `contact_keys` | List of profile properties | `["Email", "Phone", "Chat", "Url"]` | Profile properties that tell readers how to reach the person |
| `private` | List of profile properties | `[]` | Profile properties kept out of the pages, the tooltips and the structured data. A private property does not count as a contact detail |
| `map` | Object: property to `"schemaProperty"`, `"schemaProperty:Type"` or `null` | | Adds or changes the schema.org property of a profile property, with the syntax of `seo.map`. KB4IT maps `Role` to `jobTitle`, `Team` to `memberOf` (Organization), `Email` to `email`, `Phone` to `telephone`, `Location` to `workLocation` (Place) and `Url` to `url`; `name`, `alternateName` and `description` cannot be mapped |

`Alias` is reserved for profiles and cannot be listed here. A malformed `people` block stops the build with a message naming the entry. Changing `people` rebuilds every page.

## Dates {#dates}

These properties are dates: `Date`, `Modified`, `Start`, `End`, `ScheduledStart`, `ScheduledEnd`, `DowntimeStart`, `DowntimeEnd`, `DetectedDate`, `ResolvedDate`, `DueDate`, `ExpiryDate` and `ReviewDate`. Each takes a date (`2026-11-02`, a whole day) or a date and time (`2026-11-02 22:00`). Seconds and an offset (`2026-11-02T22:00:00+01:00`) are accepted. A date property gets no property page.

- `Date` is the start of the document. A document with `ScheduledStart`, or else `Start`, takes its `Date` from it; a `Date` that differs is replaced and reported.
- `ScheduledStart` and `ScheduledEnd` override `Start` and `End` when a document has both.
- A start without its end (`Start` without `End`, for example) ends at the start.
- `Downtime: Yes` expects `DowntimeStart` and `DowntimeEnd`, inside the scheduled window.

```json
"dates": {
  "WarrantyStart": {"group": "start"},
  "WarrantyEnd": {"group": "end", "closes": "WarrantyStart"},
  "RenewalDate": {"group": "end"}
},
"timezone": "Europe/Madrid"
```

| Setting | Values | Default | Meaning |
|---|---|---|---|
| `group` | `start`, `end` | | Whether the property opens or closes a period; required |
| `closes` | A start property | `Date` | The start an end belongs to |
| `supersedes` | `true`, `false` | `false` | The pair overrides `Start` and `End`, like `ScheduledStart` |

`timezone` is the zone of every date without an offset. Without it, KB4IT uses the zone of the computer that builds the site, so a build on a server in UTC can place an event on another day.

`dates` declares more date properties; the table above lists the settings of each entry. A name should end in `Date`, `Start` or `End`.

No date problem stops the build or fails `kb4it verify`: a value KB4IT cannot read is left out, a bad entry in `dates` is ignored, and an unknown `timezone` falls back to the computer's zone. The build log shows each one as `[DATES] <code>`, and `kb4it verify` lists them under "Dates". The codes are `DATE_INVALID`, `DATE_NOT_STANDARD`, `DATE_NOT_START`, `DATE_SUPERSEDED`, `DATE_SUPERSEDE_CONFLICT`, `DATE_END_MISSING`, `DATE_END_BEFORE_START`, `DATE_DOWNTIME_VALUE`, `DATE_DOWNTIME_MISSING`, `DATE_DOWNTIME_UNEXPECTED`, `DATE_DOWNTIME_OUTSIDE`, `DATE_KEY_NAME`, `DATES_BLOCK_INVALID`, `TIMEZONE_INVALID` and `TIMEZONE_UNSET`.

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

| Key | Values | Default | Meaning |
|---|---|---|---|
| `lang` | Language tag, such as `en`, `es` or `pt-BR` | `en` | Language of the pages: `<html lang>` and the structured data. apphelp's own `apphelp.lang` wins when both are set. A tag with a region (`es-ES`) also gives the Open Graph locale (`es_ES`) |
| `index` | `true`, `false` | not set | `true`: search engines may index the site. `false`: they may not. Not set: as `true`, and the build reminds you to decide. See [Search engines](#indexing) |
| `noindex_keys` | `true`, `false` | `true` | Asks search engines not to list the pages that only list documents: property, value, event, stats, bookmarks and all-documents pages |
| `structured_data` | `true`, `false` | `true` | `false` leaves the JSON-LD out of every page |
| `map` | Object: property to `"schemaProperty"`, `"schemaProperty:Type"` or `null` | | Changes which properties go into the structured data; `null` leaves a property out |

Properties KB4IT maps by default:

| Property | schema.org | Themes |
|---|---|---|
| `Author` | `author` (Person, with the `@id` of the person, see [people](#people)) | all |
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

| Key | Values | Default | Meaning |
|---|---|---|---|
| `enabled` | `true`, `false` | blog `true`, others `false` | Write the feed |
| `limit` | Integer | `20` | Number of entries, newest first |
| `categories` | List of `Category` or `WorkType` values | all | Only documents with one of these `Category` or `WorkType` values |
| `full_content` | `true`, `false` | `true` | The whole document in each entry; `false` uses `Summary` or the first lines |

Documents without a `Date` are not in the feed.

## Theme settings {#theme}

Each theme reads its own keys as well:

- [techdoc](reference-theme-techdoc.md#settings): `datatable`, `events`, `admin`, `quality`, `toc_sidebar`, `menu`
- [blog](reference-theme-blog.md#settings): `index_posts`, `strict`, `datatable`
- [bookshelf](reference-theme-bookshelf.md#settings): `datatable`
- [apphelp](reference-theme-apphelp.md#settings): the `apphelp` block and `version`

`version` is the version of the application the help describes. apphelp shows it on the home page, next to the pages new in that version, and uses it to name the folder of each version; see [versions](reference-theme-apphelp.md#versions). The value `"kb4it"` stands for the version of the installed KB4IT. The other themes ignore it.

Sample apps from older versions also contain `menu`, `sort`, `timeline` and `webserver`. KB4IT no longer reads them, except techdoc, which uses `menu` to order the filters of the Gallery and Diagrams pages; you can leave them or delete them.

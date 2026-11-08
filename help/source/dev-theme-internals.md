---
DocType: Explanation
Feature: Themes, Development
HelpId: theme-internals
Keyword: theme internals, ThemeEngine, internals, feature assembly, themeload, logic package, bare import, THEME_BARE_IMPORT, THEME_API_LEGACY, Builder, DocumentTheme, themekit, mixin, srvdtb, migrate, deprecated
Level: advanced
Order: 715
Related: howto-create-theme.md, reference-theme-hooks.md, reference-theme-legacy.md, dev-architecture.md
Section: Concepts
Summary: How KB4IT runs a theme, what stays internal, and how to move a theme from Builder or DocumentTheme to kb4it.theme.
---

# Theme internals

[Write a theme](howto-create-theme.md) covers the public API, `kb4it.theme`. This page is for the people who work on KB4IT, or who need more than the public API: how KB4IT runs a theme, what `self.internals` reaches, and the older API the bundled themes used before.

## Public and internal {#public}

The public API is what `kb4it.theme` exports (`tests/test_public_names.py` guards the list) and the members [Theme API reference](reference-theme-hooks.md) lists: `BaseTheme` and its hooks, `Site`, `Doc`, `Table`, `Feature`, the built-in features with their options and hooks. A change there goes through a deprecation period.

Everything else is internal and may change in any release: `Builder`, `DocumentTheme` and the themekit mixins, the `Database` and `Backend` services, the `runtime` dict, `kbdict`, `BuildPlan`, `distribute_md`, `distribute_html`, `add_target`, `get_theme_var` and the template lookup.

When the public API does not cover a need yet, `self.internals` reaches the services:

| Attribute | What it is |
|---|---|
| `self.internals.db` | The `Database` service: `get_values(doc, key)`, `get_doc_properties(doc)`, `get_docs_by_key_value(key, value)`... |
| `self.internals.backend` | The `Backend` service: `get_dict("repo")`, `get_path("tmp")`, `get_kb_dict()`, `get_plan()`... |
| `self.internals.builder` | The engine that runs the theme (a `Builder`): `distribute_html()`, `add_system_page()`, `inject_head_meta()`... |

techdoc uses it for its helper modules, which take a database (`logic/docpage.py`, `logic/records.py`, `logic/dashboard.py`), and apphelp for the front matter of the documents it leaves out of the site. Code that uses it may break with any KB4IT release; tell the KB4IT developers what you needed, so it can become public.

## How KB4IT runs a theme {#engine}

1. **Load.** `Frontend.theme_load()` loads `logic/` as a package named `kb4it_theme_<id>_<8 hex of the path>` (`kb4it/core/themeload.py`) and imports its `theme` module. A bare import of a sibling module (`from helpers import x`) still works: a finder limited to the files of `logic/` loads it as `<package>.helpers` and gives the bare name the same module. It logs `THEME_BARE_IMPORT`, a warning for themes outside KB4IT. Loading a theme again (terminal interface, `kb4it serve`) runs its files again.
2. **Assemble the features.** For a `BaseTheme` class, `resolve()` in `kb4it/theme/feature.py` expands bundles, adds what each feature `requires` before it, and orders the features so each runs after the ones it requires or uses; ties keep the order of `features`. The features' `theme_json` keys, `metadata_pages` and their `assets` are merged into the runtime copy of `theme.json` (`apply_theme_json()`); a key `theme.json` sets to another value stops the build. The theme's fingerprint is computed again with the added assets.
3. **Register the engine.** Frontend registers `ThemeEngine(Theme)` (`kb4it/services/themeengine.py`) as the theme service. The engine is a `Builder`: the pipeline calls it as it always called a theme. It owns the theme instance and one object per feature, copies the options it needs (`search_index_var`, `profile_skeleton`...) and sets `reserved_pages` (the theme's plus the features' `reserves`) and `add_page` (the `editor` feature). On its first start it makes the `Site`, sets `theme.site`, `theme.log` and `theme.internals`, logs `THEME_HOOK_UNUSED` for a theme method named like a hook of a feature that is off, and calls `theme.setup()`.
4. **Settings.** Frontend builds `self.config` from `config_class`, `theme.json` and the `repo.json` block named after the theme, and sets it on the engine, which hands it to the theme.

The stages of a build, and what the engine calls in each:

| Stage | Core call | Engine |
|---|---|---|
| 2 get_sources | `theme.generate_sources()` | `theme.generate_sources(site)` |
| 3 process_sources, after the analysis | `theme.prepare()` | each feature's `prepare(site)`, then `theme.prepare(site)` |
| 3 process_sources, transformation | `build_page_key()`, `build_page_key_value()` | the `property_pages` feature; a value page goes through the `value_page` hook |
| 4 process_theme | `theme.build()` | each feature's `pages(site)`, then `theme.build(site)` |
| 5 compilation | `build_page(path)` per page | `Builder.build_page()`, which calls the page hooks; the engine turns the doc id into a `Doc` |
| 6 theme_post | `theme.post_activities()` | features' `after_build(site)`, then `theme.after_build(site)` |
| 7 deploy | `inject_head_meta()` per page | `Builder`, with `page_lang()`, `structured_defaults()`, `search_page()` from the theme |
| 8 theme_post_deploy | `post_deploy_activities()`, `write_search_index()`, `write_sitemap()`, `write_feed()`, `run_checks()`, `after_checks()` | features' and theme's `after_deploy(site)`, the `search` feature's index, the theme's `checks(site)`, then `theme.after_checks(site)` |

The property and value pages are built in stage 3, before `build()`, so a theme that needs per-build data in them must not compute it in `build()`. Older themes computed it lazily, on first use; `prepare()` runs before those pages: compute there, never lazily.

## Features inside {#features}

A built-in feature lives in `kb4it/theme/features/`. It imports `kb4it.theme`, `kb4it.core` and its own helpers, never another feature module (`tests/core/test_feature_independence.py`); it reaches another feature through `requires`, `uses` and `self.feature(name)`. Code that two themes, or a theme and a starter, need becomes a built-in feature when it can be described without one theme's words; otherwise it stays in the theme, as a feature of its own when it has pages, per-build data or work after deployment (techdoc's `quality` and `admin`), or as a plain module when it only computes.

A feature reads its options with `self.option(name)` and calls a hook with `self.hook(name)`, which is the theme's method when the theme defines one and the feature's own method otherwise. Tables take extensions: a feature with `table_extension(table, columns, doc_ids)` returns HTML to put before the rows and the attributes of each row; `table_filter` adds its filter bar that way, for tables whose `Table.filterable` is true.

## The API before kb4it.theme {#legacy}

Before `kb4it.theme`, a theme subclassed `kb4it.services.builder.Builder`, or `kb4it.services.themekit.DocumentTheme` for a theme with property pages, and added kits (mixins) to its class line. It read the documents through `self.srvdtb`, wrote pages with `add_system_page()` and called the page builders in `build()`. [Theme hooks of the legacy API](reference-theme-legacy.md) lists every method.

This API is deprecated. It keeps working until it is removed, not before KB4IT 1.0 and at least two minor releases after the release that deprecated it, and a theme outside KB4IT that uses it logs `THEME_API_LEGACY` once per build. Inside, the mixins are thin: their code is in the features, and a mixin calls the feature with the legacy theme as both the theme and the engine; the feature then calls the theme's methods with their old arguments (doc ids, not `Doc` objects).

## Move a theme to kb4it.theme {#migrate}

1. Change the class line: `class Theme(BaseTheme)`, imported from `kb4it.theme`, and list the features the old class line and `build()` had:

    | Before | After |
    |---|---|
    | `DocumentTheme` | `"documents"` (and `"stats"`, `"bookmarks"`, `"events"` if `build()` built those pages) |
    | `FilterMixin` | `"table_filter"` |
    | `RelatedMixin`, `NavigationMixin`, `TocSidebarMixin` | `"related"`, `"navigation"`, `"toc_sidebar"` |
    | `GalleryMixin`, `DiagramsMixin` | `"gallery"`, `"diagrams"` |
    | `add_page = True` and `create_page_add()` | `"editor"` |
    | `create_page_search()` and `"search": true` | `"search"` |
    | `create_page_about_kb4it()`, `create_page_about_app()` | `"about"` |
    | `build_page_404()` and `reserved_pages = ("404.md",)` | `"not_found"`, in `"documents"` |

2. Delete from `build()` every call the features now make (`build_page_properties()`, `build_page_index_all()`, `build_page_stats()`...). What is left are your own pages: write them with `site.page()` and `self.render()`.
3. Give the hooks their new arguments: `doc` (a `Doc`) instead of `doc_id`, and `site` for the stage hooks. `page_body_template` is `page_template`, `post_activities` is `after_build`, `post_deploy_activities` is `after_deploy`, `_initialize` is `setup` (no `super()` call), and the publishing a theme did after `run_checks()` goes into `after_checks`.
4. Replace `self.srvdtb` with `site.documents`, `site.properties` and the `Doc` methods, `self.srvbes.get_dict("repo")` with `site.repo`, and `get_theme_var()` with `base_var()`.
5. Move what you computed on first use to `prepare(site)`.
6. Remove `"search"`, `"metadata_pages"` and the features' `assets` from `theme.json`.
7. Make the imports between the modules of `logic/` relative, and add an empty `logic/__init__.py`.
8. Run `kb4it theme-info` on the theme: the `api` line says `BaseTheme`, and no `THEME_HOOK_UNUSED` shows in a build.

The bundled themes moved this way, each with a site built before and after and compared page by page.

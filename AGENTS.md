# AGENTS.md

Full reference for AI coding assistants working in this repository. CLAUDE.md (and any other assistant-specific entry-point file) defers to this document; keep this file as the single source of truth and update it when the codebase changes.

## What is KB4IT

KB4IT is a static website generator for technical documentation. It reads Markdown source files with YAML frontmatter, computes per-document and per-key/value hashes, and incrementally compiles only what changed into HTML via `python-markdown` + Mako templates. Four themes ship with it: `techdoc`, `blog`, `bookshelf`, and `apphelp`. `manual`, `basico` and `kb4miaz` exist only in some local working trees and are not committed.

## Commands

**Install / build**

```bash
scripts/install/local/install_kb4it_from_source.sh   # Install this checkout (uv tool or pipx)
./scripts/devel/test.sh                              # Run the tests
./scripts/devel/check_themes.sh                      # Check every tracked theme is releasable
uv run --no-project --with-requirements requirements.txt --with html5validator python scripts/devel/validate_html.py  # Nu HTML Checker on every sample site (needs Java)
uv run -q --no-project --with-requirements requirements.txt python scripts/devel/theme_snapshot.py --content DIR  # Normalised pages of every sample site; diff -r two runs
python3 scripts/devel/escape_audit.py <theme> --raw  # List the template expressions printed raw (| n)
./scripts/devel/typecheck.sh                         # mypy --strict on the annotated modules (CI package job)
scripts/release.sh --dry-run                         # See what a release would do
```

**Versions and releases.** `kb4it/VERSION` names the release being built and only changes through `scripts/release.sh` (`pyproject.toml` is kept equal to it; a test fails when they differ). A development build is identified by `kb4it --version`, which adds `git describe` in a source checkout. Releases follow `RELEASING.md`: `scripts/release.sh` dates `CHANGELOG.md`, drafts `releases/X.Y.Z.md` and commits after the checks pass; the `vX.Y.Z` tag on the merged commit triggers `.github/workflows/publish.yml`, which checks the tag, publishes to PyPI, pushes the container image `ghcr.io/t00m/kb4it` (amd64, arm64), builds the `.deb` and `.rpm`, and creates the GitHub release with them. The other channels are built by `scripts/distribution/` (shared settings in `lib/common.sh`, offline package tests in `test/test_packages.sh`, see its `README.md`), checked by the CI job `packages`. The repository root is also a GitHub Action (`action.yml`, steps in `scripts/action/run.sh`), tested by `.github/workflows/action.yml` and used by `help.yml` to build the help. Every theme's `theme.json` declares the KB4IT it needs in `kb4it` (for example `">=0.7.9"`); KB4IT refuses a theme whose requirement it does not meet, and `check_themes.sh` must pass before a release.

**Run**

```bash
kb4it create <theme> [<app>] <repo_path>  # Initialize a new repository (app defaults to "default")
kb4it build <config>                      # Build the site from repo.json (use -f/--force to force recompilation); exits 1 when any page fails
kb4it serve <config>                      # Build, serve on 127.0.0.1:8642 with live reload, rebuild on change (kb4it/core/serve.py)
kb4it info <config>                       # Show repository info
kb4it themes                              # List installed themes
kb4it apps <theme>                        # List apps available for a theme
kb4it projects                            # List all projects created by the user
kb4it verify <config>                     # Verify sources are KB4IT conformant; exits 1 on any non-conformant file or theme problem
```

**Global flags (before subcommand):**

```bash
kb4it -L DEBUG <command>                  # Set log level (DEBUG/INFO/WARNING/ERROR, default INFO)
kb4it -v                                  # Print version and exit
```

CI (`.github/workflows/kb4it.yml`) runs a matrix of Linux, macOS and Windows with Python 3.11, 3.13 and 3.14: `kb4it --version`, the tests and `scripts/devel/smoke_build.py` (create and build every bundled theme's default app). Tests: `./scripts/devel/test.sh [--python X.Y]` (pytest via uv; add paths or pytest flags after it; Git Bash on Windows). CI also builds the wheel and runs `scripts/devel/check_wheel_themes.py`, which fails when a git-tracked theme is missing from `dist/*.whl` and prints a WARNING for themes that are in the wheel but not tracked in git.

## Architecture

Service-based: a central `KB4IT` controller in `kb4it/core/main.py` registers the long-lived services (`DB`, `Backend`, `Frontend`, `Builder`, `Workflow`, and `Theme` once loaded) and routes `get_service(name)` lookups. The services of one build, Processor, Compiler and Deployer, are not registered: `Backend.start_pipeline()` makes them together as `backend.pipeline` (`kb4it/services/pipeline.py`) at the end of stage 1, once the theme is loaded, and passes each its collaborators (backend, database, theme, processor, callbacks, log file) in its constructor. `KB4IT.get_service("Processor"|"Compiler"|"Deployer")` still answers from the current pipeline in 0.9.x and logs `[CONTROLLER] SERVICE_DEPRECATED name=... replacement=backend.pipeline` once per name; it goes in 0.10.0. Services share state through the `runtime` dict (held on `Backend`) and through explicitly-passed dataclasses; the global `ENV` (frozen after init) holds paths and immutable environment metadata. Nothing a build decides is written into `params` or `repo`: see `runtime["force_all"]` below.

A per-repository lock (`<repo>/var/kb4it.lock`, `kb4it/core/lock.py`, `flock` on POSIX and `msvcrt.locking` on Windows) stops two builds of the same repository; `create` locks under `~/.kb4it/var/`, and `projects.json` writes take `~/.kb4it/var/projects.lock`. Other actions and the TUI itself take no lock. When `kb4it` is run with no arguments in an interactive terminal, the Textual-based TUI launches instead of showing help.

### Execution flow

```
CLI args (or TUI)
  -> KB4IT.__init__()           # setup ENV, acquire lock, log file, register services
  -> KB4IT.run()                # dispatch by action
       -> Workflow.<action>()   # build_website / create_repository / info / list_* / verify_sources
            -> Backend.stage_01_check_environment       # paths, theme load, template validation, backend.pipeline
            -> theme.generate_sources()                 # generate system pages (about, help); nothing is written into source/
            -> Backend.stage_02_get_source_documents    # collect .md sources
            -> Backend.stage_03_process_sources         # pipeline.processor steps 00, 01, 02
            -> Backend.stage_04_process_theme           # theme.build()
            -> Backend.stage_05_compilation             # pipeline.compiler.execute() in parallel
            -> Theme.post_activities()                  # post-processing (stage 6)
            -> Backend.stage_06_deploy                  # pipeline.deployer.execute() (stage 7)
            -> Theme.post_deploy_activities()           # runs on the deployed target (stage 8)
```

Each `stage_*` method is decorated with `@timeit` so per-stage durations land in the `[PERFORMANCE]` debug log. Workflow emits a final `[WORKFLOW] SUMMARY` line with `docs_total`, `compiled`, `skipped`, `invalid` (documents whose frontmatter could not be read, see `BuildPlan.invalid_docs`), `keys_compiled`, `kv_pages_compiled`, `failed`, and `[WORKFLOW] TOTAL_TIME elapsed=...`.

**Build outcome.** A page that cannot be compiled or rendered is recorded in `Compiler.failed` (its partial page removed); a page missing from the cache at deploy time in `Deployer.missing`. Every other page is still deployed, then the workflow logs `[WORKFLOW] PAGES_FAILED n=... pages=...` and raises `CompilationError`: `kb4it build` exits 1 and `on_build_end` sees `failed` in its summary. `kbdict.json` is written only by `Backend.commit_kbdict()`, after a build without failures, so a failed or interrupted build leaves the previous cache and the next build compiles the same documents again.

### Modules

| Location                          | Role |
|---|---|
| `kb4it/core/main.py`              | Entry point, `KB4IT` controller, argparse, process lock, top-level exception catch, TUI auto-launch |
| `kb4it/core/env.py`               | `FrozenDict`-backed `ENV` (sealed after init), system paths, app metadata |
| `kb4it/core/exceptions.py`        | `KB4ITError`, `ConfigError`, `ThemeError`, `CompilationError` hierarchy |
| `kb4it/core/service.py`           | Base `Service` class all services inherit |
| `kb4it/core/types.py`             | `TypedDict` definitions: `Runtime`, `DirPaths`, `DocsInfo`, `KBDict`, `DocumentMeta`, `DBRecord` |
| `kb4it/core/util.py`              | `@timeit`, page names (`html_id_for`, `source_ext`, `page_name_clashes`), `slugify`, tag cloud sizes, `ellipsize_text`; imports and re-exports (`__all__`) every name of `dates.py`, `documents.py` and `files.py`, so `from kb4it.core.util import ...` keeps working in themes, hooks and templates |
| `kb4it/core/dates.py`             | `DateCache`, `guess_datetime`, the `get_human_*` and timestamp helpers |
| `kb4it/core/documents.py`         | Frontmatter and title: `get_document_attributes`, `first_heading` (title rule), `strip_first_heading`, `fences_in_blocks`, `raw_script_lines`, `extract_sections_from_md`, `get_hash_from_body` |
| `kb4it/core/files.py`             | `valid_filename`, `SOURCE_ENCODING`, copy and delete, `json_load`, `json_save` (atomic: temp file, fsync, `os.replace`), `quarantine` (keeps an unreadable file as `<name>.corrupt-<timestamp>`), blake2b hashes. `dates`, `documents` and `files` import nothing from `util` |
| `kb4it/core/paths.py`             | `resolve_repo_path` and `check_target`: the target may not be, or hold, the repository root, `source`, `config/`, `var/`, home or a filesystem root, nor lie inside `source` (`ConfigError` before anything touches the disk) |
| `kb4it/core/log.py`               | Logging setup, file redirection |
| `kb4it/services/workflow.py`      | Orchestrates build / create / info / list / verify actions |
| `kb4it/services/backend.py`       | Loads `repo.json`, owns `runtime` dict, exposes `get_plan()` proxy |
| `kb4it/services/database.py`      | In-memory document index keyed by docId, metadata caches |
| `kb4it/services/pipeline.py`      | `Pipeline`: the Processor, Compiler and Deployer of one build, made by `Backend.start_pipeline()` |
| `kb4it/services/processor.py`     | Frontmatter extraction, change detection, owns `BuildPlan` + `AnalysisResult` |
| `kb4it/services/compiler.py`      | Markdown -> HTML via `python-markdown` in a `ThreadPoolExecutor` |
| `kb4it/services/builder.py`       | Renders Mako templates (escaped when the theme opts in, see Escaping); defines `REQUIRED_TEMPLATES` + `_template_candidates()`, `template_base_dir()`, `git_ready()` |
| `kb4it/services/themekit/`        | `DocumentTheme(Builder)`, the base of techdoc, blog and bookshelf, from the mixins `metadata.py`, `keypages.py`, `tables.py`, `events.py`, `toc.py`; `host.py` declares for mypy what they use from `Builder` |
| `kb4it/services/frontend.py`      | Theme discovery, theme load, required-template validation |
| `kb4it/services/deployer.py`      | Copies the compiled output to `repo.target`; removes only pages listed in `kbdict.json` `deployed` by an earlier build (none on the first build after an upgrade) |
| `kb4it/core/serve.py`             | `kb4it serve`: build, serve, poll for changes, rebuild in-process (holds the repo lock; builds pass `lock_held`) |
| `kb4it/core/webserver.py`         | `SiteServer` (threaded `http.server`), `BuildStatus`, live reload script injection, `/__kb4it/status` |
| `kb4it/core/watch.py`             | `PollingWatcher`: stdlib polling with debounce, ignores editor scratch files |
| `kb4it/core/search.py`            | Search index: section extraction (also used by apphelp), per-document cache in `<repo>/var/search/` written by the compiler, `render_index_js`; browser engine `resources/common/js/kb4it-search.js` + UI `kb4it-search-ui.js`. `Builder.write_search_index()` runs after stage 8 for themes with `"search": true` in `theme.json` |
| `kb4it/core/publish.py`           | `site_url`, `sitemap.xml`/`robots.txt`, Atom feed; `Builder.write_sitemap()`/`write_feed()` run after stage 8; `Deployer.step_05_add_head_meta()` injects `HTML_HEAD_META.tpl` (description, Open Graph, canonical, feed link) into the pages built in this run, between `<!-- kb4it:meta -->` markers |
| `kb4it/core/hooks.py`             | Per-repository hooks named by `repo.json` `hooks`: `on_config` (Backend), `on_document` (Compiler, worker threads), `on_page` (Deployer step 5), `on_build_end` (Workflow); a failing hook raises `CompilationError`; the file hash is part of the core signature |
| `kb4it/core/lock.py`              | `FileLock` (flock / msvcrt), `repo_lock_path`, `registry_lock` |
| `kb4it/tui/`                      | Textual-based Terminal User Interface: `app.py` (`KB4ITTUI`, `run`, and every name it had before the split, re-exported), `projects.py` (registry, themes, apps, paths), `servers.py`, `clipboard.py`, `screens/` (one module per screen or pair of small screens) |

### Themes

Each theme lives under `kb4it/resources/themes/<name>/`:

- `logic/theme.py` -- `Theme` class that extends `Builder` and overrides `build_page`, `build_page_key`, `build_page_key_value`, etc. techdoc, blog and bookshelf extend `DocumentTheme` instead (`kb4it/services/themekit/`), which holds the code they share: the property, value, properties, stats, bookmarks and all-documents pages, the datatable, the day/month/year event pages, the TOC and the metadata section. Where they differ, the theme sets a class attribute or overrides a small hook (`properties_title`, `reuse_unchanged_pages`, `tagcloud_scale_skips_empty`, `cloud_measure`, `frequency_keys`, `stats_keys`, `datatable_link_template`, `datatable_default_headers`, `datatable_date_cell`, `datatable_title_cell`, `datatable_value_link`). A theme that overrides a shared method starts its docstring with `Override:` and says why; `tests/core/test_themekit.py` checks it. apphelp and custom themes keep extending `Builder`, which does not grow.
- Helper modules next to `theme.py` in `logic/` are imported by name, so they carry the theme's prefix: `apphelp_*.py`, `techdoc_dashboard.py` (home page) and `techdoc_addpage.py` (the "Add" page) hold mixins or functions of their theme.
- Mako `.tpl` files directly in `templates/` (flat, no subdirectories). Shared fallbacks live in `kb4it/resources/common/templates/`; templates shared by a family of themes live in a template base, `kb4it/resources/bases/<name>/templates/` (see `template_base`). No bundled template is byte-identical in two themes of the same base (`tests/themes/test_templates_used.py`).
- Optional `templates/skeletons/*.md` -- per-category Markdown document skeletons (used by the techdoc `PAGE_ADD` page).
- Optional `logic/verify.py` -- hook `verify(repo, docs) -> list[str]`, run by `kb4it verify` (`Workflow.verify_sources`); `docs` is `{file name: {key: [values]}}`; every returned string is reported as a problem.
- Static assets under `framework/` (CSS, JS, images, UIKit, DataTables).
- `apps/<app>/` repository scaffolds used by `kb4it create`, each holding `config/repo.json`, `source/`, and `target/`.

Optional `theme.json` keys:

- `metadata_pages` (default `true`): when `false`, the processor skips the per-key and per-key/value pages, and `PAGE_KEY` and `PAGE_KEY_VALUE` are no longer required templates.
- `template_base` (no default): the name of a folder under `kb4it/resources/bases/` whose templates the theme builds on; techdoc and blog use `"uikit"`. An unknown name raises `ThemeError` naming the key. Base templates compile with the theme's `autoescape`. The bases live outside `common/`, which is deployed into sites.
- `deploy_dirs` (default: the whole theme folder, plus `default` and `common`): list of plain folder names under the theme that are copied to the target. Names are validated (no paths, no `..`); an invalid entry raises `ThemeError`. An explicit list does not deploy the `default` theme or the common resources, so the theme must bring everything its pages need. The theme `id` must be a plain name (no path, not `.` or `..`). Themes without it deploy exactly as before.

Custom themes installable to `~/.kb4it/opt/resources/themes/<name>/`.

**Custom themes and about pages.** The backend no longer writes `about_kb4it.md` or `about_app.md` into `source/`. A custom theme gets about pages only if its `build()` calls `create_page_about_kb4it()` and `create_page_about_app()`. An untouched generated `source/about_kb4it.md` left by older versions is removed at stage 2.

**Clean tmp.** `var/tmp` is emptied at the start of every build (after stage 1, before `generate_sources()`), so a failed build cannot leak files into the next link check.

Required template names per theme: `HTML_BODY`, `PAGE_INDEX`, `PAGE_KEY`, `PAGE_KEY_VALUE`. Missing any of these raises `ThemeError` at `stage_01_check_environment`.

Template lookup (`_template_candidates`) resolves a name `<NAME>` to the first existing file among `<repo>/overrides/templates/<NAME>.tpl` (folder from `repo.json` `overrides`, default `overrides`; logged `[BUILDER] TEMPLATE_OVERRIDE`), `<theme>/templates/<NAME>.tpl`, the theme's template base (`kb4it/resources/bases/<base>/templates/<NAME>.tpl`) when it has one, then `kb4it/resources/common/templates/<NAME>.tpl`. There is no other cross-theme inheritance. Every bundled template is rendered by some code or is half of a transformation pair; `tests/themes/test_templates_used.py` fails on an unused one. `<repo>/overrides/static/` is copied into the target root; a hash of the overrides folder is part of the core signature.

**Built-in themes:**

| Theme | Description |
|---|---|
| `techdoc` | Full-featured technical documentation site with data tables, metadata navigation, event timeline, built-in web server |
| `blog` | Personal or team blog with post listings, tag/category navigation, and RSS-style layout |
| `bookshelf` | Study companion organised as Book, Part and Chapter for certification prep |
| `basico` | SAP-notes-style troubleshooting knowledge base with symptom/cause/resolution structure |
| `manual` | Chapter-based user manual with sequential prev/next navigation across documents |
| `apphelp` | Help site for an application: works from `file://`, from a GitHub Pages subpath and embedded; strict metadata, offline full-text search, help ids |
| `kb4miaz` | Browser for documents organised with the MiAZ seven-field scheme (`{date}-{country}-{group}-{sentby}-{purpose}-{concept}-{sentto}`); landing page with per-field facet cards, breakdown bars, and a recent-documents list |

### Builder hooks and core behaviour

- `Builder.create_page_about_app()` builds the about-app page into the build tree; the backend never writes into `source/`.
- `Processor.signature_parts()` lists core settings that shape every page (`markdown`, overrides, hooks, and a hash of the whole `repo.json` minus `NON_PAGE_KEYS` = `workers`, `force`, `fail_on_invalid`, `source`, `target`); their hash is stored as `core_signature` in `kbdict.json`, and a change rebuilds everything (`[PROCESSOR] CORE_SIGNATURE_CHANGED`).
- A template that exists but does not compile raises `ThemeError` (`[BUILDER] TEMPLATE_COMPILE_FAIL name= path= error=`, logged once per build); only missing candidates fall through to the next location.
- The title is the first `# ` line outside fenced and indented code (`util.first_heading`); the same line is left out of the page body and of the body hash.
- Page names from property names and values never start with a dot (`valid_filename`); a name or value that cleans to nothing makes the document invalid (`bad_property_name`, `bad_property_value`).
- `Builder.site_signature()` returns a value that changes when every page must be rebuilt (default empty, which turns the check off). The processor stores it in the database and forces a full recompile when it changes; themes that render site-wide content (navigation, related pages) into every page override it.
- Links between documents are scanned in stage 3 (`Processor.document_links()`, only for documents whose body changed) and stored in `kbdict.json` as `links`; `BuildPlan.backlinks` holds the inverse, a document whose backlinks changed is recompiled, and the compiler appends `HTML_BACKLINKS.tpl` ("Linked from") to each article unless `repo.json` has `"backlinks": false`. `kb4it verify` reports `LINK_BROKEN` and `ANCHOR_MISSING` and exits 1.
- Markdown links to other `.md` files (`[text](other.md#anchor)`) are rewritten to the generated `.html` page. A target that is not a source document logs `[COMPILER] LINK_BROKEN` (rewrite logic in `kb4it/core/mdlinks.py`).
- YAML frontmatter values that are null (`Tag:` with no value) become `[]`.
- In Mako templates that emit Markdown, write an H2 as `${'##'}` so Mako does not treat `##` as a comment.

### Template transformations

`Builder.apply_transformations()` (in `builder.py`) rewrites HTML from `python-markdown` using Mako template pairs. For each name in `Builder._XFORM_NAMES` (`HTML_TAG_TOC`, `HTML_TAG_SECT1` to `SECT4`, `HTML_TAG_SECTIONBODY`, `HTML_TAG_H2` to `H4`, `HTML_TAG_IMG`), a `_MD` template (source pattern, from common templates) and a `_NEW` template (replacement, from the active theme or its base) are loaded; `tests/core/test_transformations.py` checks that each `_MD` pattern occurs in python-markdown output. The theme supplies `_NEW` templates to override the default HTML wrappers. This system is used for element-level theming (e.g. wrapping tables, code blocks, or admonitions in theme-specific markup). It is plain string replacement on the page body, so a `_NEW` replacement must not add an attribute the matched element may already carry (the link transformation `HTML_TAG_A` was removed for that reason; style document links with CSS on the body container). Section wrappers use classes, never fixed ids, since they repeat on a page.

Additional system templates (not in the required set): `PAGE_ABOUT_KB4IT`, `PAGE_ABOUT_APP`, `PAGE_HELP`.

### Escaping

A theme with `"autoescape": true` in `theme.json` (all bundled themes) compiles its templates, and their overrides, with `default_filters=["h"]`: every `${...}` is HTML-escaped. Print HTML built by KB4IT or the theme raw with `${value | n}` (page bodies, TOC, datatables, metadata sections, the search box, JSON inside `<script>`), never a value taken from a document or `repo.json` as it is. KB4IT's common templates are always escaped. A custom theme without the key renders as before and logs `[BUILDER] THEME_AUTOESCAPE_OFF` once per build. HTML that theme logic builds in Python and passes to a raw expression must escape the values it holds (`html.escape`); JSON printed inside `<script>` must replace `<` with `\u003c`. `scripts/devel/escape_audit.py` lists every expression of a theme; `tests/themes/test_escaping.py` builds every bundled theme with hostile titles and properties.

Raw HTML written in a document reaches the page as written (the trust model is in `help/source/reference-document-format.md`). `"markdown": {"sanitize": true}` cleans each document's compiled HTML with nh3 (`mdconfig.sanitize_html`, allow-list in `SANITIZE_TAGS`/`SANITIZE_ATTRIBUTES`) in the compiler, before KB4IT adds its own markup.

### Mako templates

Templates use Mako syntax:

```mako
${var['repo']['title']}
% for item in var['page']['stats']:
    ${item['label']}: ${item['num']}
% endfor
```

Do not confuse with f-string-like `{var}` placeholders -- those are not interpreted.

### Repo config (`repo.json`)

Strictly required (validated in `Backend._validate_config`, raises `ConfigError` if missing): `source`, `target`, `theme`, `title`.

Common optional fields used by themes: `tagline`, `sort`, `force`, `workers`, `ignored_keys`, `events`, `logo`, `logo_alt`, `menu`, `datatable`, `webserver`, `admin`, `git`, `git_repo`, `git_server`, `git_user`, `git_branch`, `git_path`.

Core optional fields added in 0.9 (all part of `Processor.signature_parts()`, so changing them rebuilds every page): `markdown` (`extensions`, `extension_configs`, `highlight` = `client`|`pygments`|`none`, `pygments_style`, `pygments_style_dark`, `sanitize`), `search` (themes with `"search": true` in `theme.json`), `site_url`, `sitemap`, `feed` (`enabled`, `limit`, `categories`, `full_content`; themes declare `"feed": true|false` in `theme.json`), `og_image`, `overrides` (default `overrides`), `hooks`, `backlinks`.

`kbdict.json` fields added in 0.9: `core_signature`, `links` (`{docId: [[target docId, fragment], ...]}`), `deployed` (sorted list of the pages written into the target, kept across `--force` and version upgrades), `events` (`{event page: [docIds]}`; `DocumentTheme.build_events` rebuilds a day, month or year page only when one of its documents changed, its documents differ from this record, there is no record, or its cached copy is missing). An unreadable `kbdict.json` logs `[BACKEND] KBDICT_CORRUPT` and the build runs as a full rebuild; an unreadable `projects.json` is kept with `quarantine` (`PROJECTS_CORRUPT`).

Edit links (`git`, `git_*`) appear only when `git_ready(repo)` is true: `"git": true` and `git_server`, `git_user`, `git_repo`, `git_branch` set (no `{placeholder}`); templates test `var['git_ok']`. Sample `repo.json` files carry no placeholders other than `{source_directory}` and `{target_directory}`, which `create` fills.

`theme_path` (optional) overrides the name-based theme lookup with an explicit directory. When set, `Frontend.theme_search` skips the source-embedded, user-installed, and built-in lookup chain and uses this directory directly; it must contain a valid `theme.json`. Relative values are anchored to the repository root (the parent of the config file's parent), `~` and `$VARS` are expanded, and symlinks are resolved. Intended for applications that embed KB4IT as a library and ship their own theme without installing it under `~/.kb4it/`. The `theme` (name) field is still required and is used for identification and logging.

`source` and `target` are resolved like `theme_path`: relative values are anchored to the repository root (the parent of the config file's parent). If that path does not exist, the old behaviour (relative to the current directory, `PATH_CWD_RELATIVE`) is used as a fallback. `kb4it create` writes `"source"` and `"target"` into `repo.json`.

`publish_sources` (default `true`): when `false`, the Markdown sources are not copied to the target.

`fail_on_invalid` (default `false`): when `true`, any source document whose frontmatter cannot be read fails the build (`CompilationError` listing every invalid document). Without it, such documents are logged as `DOC_INVALID`, left out of the site and counted as `invalid` in the summary.

**`apphelp` block** (read by the `apphelp` theme only). The page names `search.md`, `topics.md`, `go.md` and `404.md` are reserved for theme pages; a user page with one of these names is reported as `META_INVALID reason=reserved_name`. `index.md` is the landing page and replaces the theme's own landing page:

| Key | Meaning |
|---|---|
| `strict` | Default `true`. Metadata problems (documents whose frontmatter cannot be read, `DOC_INVALID`; unknown vocabulary values, missing required properties, reserved page names) and help ids that point to a missing page or anchor fail the build. `LINK_BROKEN` and `ANCHOR_MISSING` are only warnings. Entries of the contract file that the site does not provide always fail the build |
| `lang` | Language of the generated pages (`<html lang>`) |
| `accent` | Accent colour (CSS value) |
| `about` | When `true`, the theme builds an about page |
| `versions` | `{"enabled": true, "latest": "<label>"}`: build into `target/<version>/` (version = top-level `version`); `Builder.target_subdir()` moves the target and `runtime['dir']['site_root']` keeps the root; `apphelp_versions.publish()` writes `latest/`, `versions.json`/`.js`, root `index.html` and `helpids.js` |
| `contract` | Path to a contract file with the help ids the application expects; checked against the documents. An explicit path that does not exist logs `[APPHELP] CONTRACT_FILE_MISSING` |
| `vocabulary` | Allowed values per property (`Feature`, `Level`, `Platform`, ...) |
| `labels` | Overrides of the UI texts (for example `ts_cause`, `ts_fix`) |

**Type of document (`apphelp`).** Every content page must be classified with `DocType`, the same key and values as `techdoc`, following the Diátaxis framework: exactly one of `Tutorial`, `How-to guide`, `Reference`, `Explanation` (exact spelling). A page without a valid `DocType` is never published: it is left out of the site, the navigation, the search index and `helpids.js` (`[APPHELP] DOC_LEFT_OUT`), and reported as `DOCTYPE_MISSING` or `DOCTYPE_INVALID`, which fails the build when `strict` is on. The optional `Layout` key (`faq`, `tips`, `troubleshooting`) selects a special rendering on top of the type. The old `Kind` key is reported as `META_INVALID reason=replaced_by_DocType_and_Layout`. In the generated site the classification is called "Type of document"; the theme never shows the word Diátaxis. See `kb4it/resources/themes/apphelp/README.md` for all page properties.

The `force` field can also be set per-build via `--force` (CLI) or the TUI; either one turns on `runtime["force_all"]` without changing `params` or `repo`.

### Admin area (`admin`, techdoc only)

`"admin": true` in `repo.json` makes the techdoc theme write an `admin/` subdirectory into the target after deployment. It holds a Backup page (`admin/index.html`) plus two zip files:

| File | Content |
|---|---|
| `<title-slug>_sources.zip` | Every `.md` in `source/`, flat, no assets |
| `<title-slug>_site.zip` | The whole compiled target tree, excluding `admin/` |

`<title-slug>` is `util.slugify(repo["title"])`, falling back to the repo directory name when the title slugifies to nothing. Rename the repository and the old zips are deleted on the next build.

Zips are rebuilt when the build compiled at least one document, when `--force` is used, or when a zip is missing; otherwise the step logs `[ADMIN] ZIP_SKIP` and keeps the existing files. They are written to `var/tmp` first and moved into place, so a half written file is never linked and the site zip never packs itself. The page itself is rewritten on every build and reads size and date off the zips on disk.

The page is written straight to disk by `Theme.build_page_admin()`, not through `distribute_md()`, so it never enters the database, the datatables, the search index or the menu. It is only reachable at `<site>/admin/`. Being unlisted is not access control: on a public server anyone who guesses the URL can download the backups.

Because the page lives one level down, `Theme.relocate_links()` rewrites every relative `href`/`src` in the rendered tree with a `../` prefix. Anchors (`#`), absolute paths and scheme URLs (`http:`, `javascript:`, ...) are left alone. The download links are authored as `admin/<file>.zip` in `PAGE_ADMIN.tpl` so they end up correct after the rewrite.

### Key data structures

- **`runtime`** -- the live build state, accessed via `backend.get_dict("runtime")` or `backend.get_value("runtime", key)`. Holds `theme`, `dir` (`DirPaths`, including `root`, the repository root), `docs` (`DocsInfo`), `logfile`, and `force_all`: the build rebuilds everything because `--force` or `repo.json` `force` asked for it, or because the cache was unreadable or from another version (`params` and `repo` stay as given; the processor reads `params["force"] or runtime["force_all"]`, techdoc's backups read `force_all`). **Does NOT hold** `ncd`, `nck`, `K_PATH`, `KV_PATH` anymore -- these moved to `BuildPlan`.
- **`BuildPlan`** (in `kb4it/services/processor.py`) -- dataclass produced by `Processor.step_01_analysis()`. Fields: `docs_to_compile`, `K_PATH` (`[(key, values, compile_flag), ...]`), `KV_PATH` (`[(key, value, compile_flag), ...]`), `force_kv_pairs`. Exposes `doc_count`, `key_count`, `kv_count` properties. Access via `backend.get_plan()`.
- **`AnalysisResult`** (in `kb4it/services/processor.py`) -- dataclass passed explicitly between `step_01_analysis` and `step_01_01_decide_keys_compilation`. Carries the `force_kv_pairs` set.
- **`kbdict`** (`KBDict` TypedDict) -- the persisted compilation cache at `<repo>/var/db/kbdict.json`. Maps docs to body/metadata hashes and metadata key/value indices for incremental compilation.
- **`Database` (`srvdtb`)** -- in-memory per-docId map of `{key: [values]}` plus `keys` (all / blocked / theme / ignored) and several lookup caches. `Title` is always ignored; `SystemPage`, `Date` are blocked.

### Backward-compat shim

`Backend.get_value("runtime", "ncd"|"nck"|"K_PATH"|"KV_PATH")` redirects to the BuildPlan so the techdoc/blog themes' existing reads keep working. New code should use `backend.get_plan()` directly.

Kept in 0.9.x, removed in 0.10.0: `KB4IT.get_service("Processor"|"Compiler"|"Deployer")` (use `backend.pipeline`), `compiler.set_progress_callback` and `set_compile_start_callback` (pass the callbacks to `KB4IT(params)`), and `var['repo']['updated']` (templates read `var['updated']`; `var['repo']` is a copy). `Builder.theme_var` is set per builder in `_initialize`; the shared class-level dict is gone.

### Error handling

Services raise typed exceptions (`ConfigError`, `ThemeError`, `CompilationError`, `KB4ITError`). `main.py:run()` catches them at the top level and calls `self.stop(error=True)` once. Services must **not** call `app.stop()` directly.

### Logging

Stage names and structured events use `[<COMPONENT>] EVENT key=value` form, e.g.:

- `[WORKFLOW] STAGE n=3 name=process_sources`
- `[PROCESSOR] ANALYZE doc=foo.md body=True meta=False title=False not_cached=True compile=True`
- `[BACKEND] CONFIG_LOADED`
- `[BUILDER] TEMPLATE_NOT_FOUND name=PAGE_KEY`

Performance log lines come from `@timeit` and look like `[PERFORMANCE] 0.1234s => Stage stage_03_process_sources`.

### Key runtime paths

| Path | Purpose |
|---|---|
| `~/.kb4it/` | Root of all per-user KB4IT data |
| `~/.kb4it/var/` | Var directory (lock, work, logs) |
| `~/.kb4it/var/log/` | Logs (rotated `kb4it.log.old` per run) |
| `~/.kb4it/var/projects.lock` | Registry lock, held while `projects.json` is written |
| `<repo>/var/kb4it.lock` | Build lock of one repository |
| `~/.kb4it/opt/` | Opt directory |
| `~/.kb4it/opt/resources/` | Local resources |
| `~/.kb4it/opt/resources/themes/` | User-installed themes |
| `~/.kb4it/projects.json` | TUI project registry |
| `<repo>/var/db/kbdict.json` | Per-repo compilation cache |
| `<repo>/var/tmp/` | Compiler scratch (Markdown -> HTML fragments) |
| `<repo>/var/cache/` | Hashed HTML cache for incremental builds |
| `kb4it/resources/` | Built-in assets relative to the installed package |
| `kb4it/resources/common/` | Common assets (templates, images, appdata) |
| `kb4it/resources/common/templates/` | Global template fallbacks |
| `kb4it/resources/common/images/` | Common images |
| `kb4it/resources/themes/` | Built-in themes |

## Terminal User Interface (TUI)

KB4IT ships with a full-featured TUI built on [Textual](https://textual.textualize.io/). It auto-launches when `kb4it` is run with no arguments in an interactive terminal.

### Screens

| Screen | Description |
|---|---|
| **Main** | Project list with actions: New, Import, Delete, Themes, Apps, Quit |
| **CreateProject** | Select theme, app template, enter name + path; runs `create` workflow |
| **ImportProject** | Browse to existing `repo.json`, assign display name, add to registry |
| **Project** | Per-project actions: Compile, Force Compile, Project Info, List Source Files, Explore Keys & Values, View Build Log, Browse Local, Browse via Web Server |
| **Build** | Live progress bar + real-time log output, copy-to-clipboard |
| **Explorer** | Three-pane metadata browser (Keys -> Values -> Documents) with document viewer |
| **LogViewer** | Build log with level filters (All / Info / Warnings+ / Errors only) |
| **Info** | Shows `repo.json` contents |
| **FileList** | Shows source documents with sizes |
| **Themes/Apps** | Browser for installed themes and their app templates |
| **WebServer** | Built-in HTTP server on `127.0.0.1` (auto port-scan from 8642) |

### Compiler callbacks

A build takes its callbacks as parameters: `KB4IT(argparse.Namespace(..., progress_callback=fn, compile_start_callback=fn))`. The controller moves them out of `params` into `KB4IT.callbacks` (`CALLBACK_PARAMS`), and the pipeline gives them to that build's Compiler:
- `progress_callback(basename, rc)` -- called per compiled doc
- `compile_start_callback(total)` -- called once with the number of documents

`compiler.set_progress_callback` / `set_compile_start_callback` are deprecated: what they register is used by the next build only, which logs `[COMPILER] CALLBACK_DEPRECATED`.

### Clipboard

`kb4it/tui/clipboard.py` uses the platform's tool found on `PATH` (`wl-copy`, `xclip`, `xsel` on Linux; `pbcopy` on macOS; `clip.exe` on Windows, fed UTF-16), falling back to the OSC 52 escape sequence. Screens call it as `clipboard._copy_to_clipboard`, so tests patch that one module.

### Project registry

The TUI reads/writes `~/.kb4it/projects.json`, a JSON file with:
```json
{"projects": [{"name": "My Project", "config": "/path/to/repo.json"}, ...]}
```

Projects are registered automatically by `kb4it create` and manually via ImportProjectScreen.

## Source documents

KB4IT consumes Markdown files only (`.md` / `.markdown`). Each must begin with a YAML frontmatter block, followed by an H1 heading used as the document title.

A document that does not meet this (`missing_frontmatter`, `missing_frontmatter_close`, `invalid_frontmatter`, `missing_h1_title`, `yaml_error line=<n> col=<n> <problem>`, `bad_property_name key=<k>`, `bad_property_value key=<k>`) is logged as `[UTIL] DOC_INVALID`, left out of the site and recorded in `BuildPlan.invalid_docs`. Quote values that contain `: ` (for example `Summary: "Plugins: how they load"`), otherwise YAML reads them as a nested mapping.

```markdown
---
Author: Tomas Virseda
Category: Procedure
Date: 2026-05-19
DocType: How-to guide
Tag: tag1, tag2
---

# Document Title

## Section
...
```

Frontmatter rules and the controlled vocabulary for `Category`, `DocType`, semantic properties (`OS`, `Product`, `Database`, ...) live in the `kb4itdoc_md` skill. Multi-value strings are comma-separated. `Title` must come from the `# H1`, not the frontmatter -- a warning logs and ignores any `Title:` key in frontmatter.

`Date` is optional. Undated documents are kept and sorted after the dated ones; the datatables list them with an empty date cell.

`Date` values are parsed by `guess_datetime` in `core/util.py`, which accepts the common separated forms (`YYYY-MM-DD`, `DD/MM/YYYY`, `YYYY.MM.DD`, ISO `T` variants, with optional time) plus the compact `YYYYMMDD` and `YYYYMMDDHHMMSS` forms used by the `kb4miaz` theme's MiAZ filenames. A `Date` that no pattern matches yields `None` and is treated as missing.

## Dependencies

- Python >= 3.11, < 4.0, on GNU/Linux, macOS and Windows (CI runs all three with 3.11, 3.13 and 3.14). Platform-specific code is limited to `kb4it/core/lock.py` (flock/msvcrt), `kb4it/core/env.py` (platform description) and the TUI clipboard; `KB4IT_HOME` relocates `~/.kb4it`.
- `Mako==1.3.12` -- templates.
- `Markdown>=3.5` -- Markdown -> HTML, with `extra`, `admonition`, `toc`, `sane_lists` extensions always on; `repo.json` `markdown.extensions`/`extension_configs` add more (`kb4it/core/mdconfig.py`, checked at config load). Optional extra `KB4IT[extras]` installs `pymdown-extensions` and `nh3` (for `markdown.sanitize`); with `pymdownx.superfences` or `pymdownx.highlight`, `all_configs()` sets `pymdownx.highlight.use_pygments` from `highlight`. `kb4it verify` warns `MD_FENCE_IN_BLOCK` (fence inside an indented block, without superfences) and, while `sanitize` is off, lists `DOC_RAW_SCRIPT` (information).
- `PyYAML>=6.0` -- frontmatter parsing.
- `Pygments>=2.15` -- build-time code highlighting (`markdown.highlight: pygments`).
- `lxml` -- XML parsing for post-processing.
- `rich>=13.0` -- terminal formatting (used by TUI and log output).
- `textual>=0.47.0` -- TUI framework.

## Conventions for contributions by AI assistants

- **Never use the em dash (`--`).** Use a comma, semicolon, colon, or rewrite the sentence.
- **Git workflow.**
  - Commit when a piece of work is done; do not wait to be asked.
  - One-line Conventional Commits message: `type(scope): description`, types `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `chore`, `build`; omit the scope for project-wide changes; description in lower case, imperative, no full stop, describing the change.
  - No trailer lines (no `Co-Authored-By`, no `Claude-Session`).
  - Never push and never create a branch (no `git branch <name>`, `checkout -b`, `switch -c`, `worktree add`); work on the checked-out branch. A PreToolUse hook (`.claude/hooks/git-guard.py`) enforces this.
  - Stage files by name, never `git add .` or a whole directory. Never commit `.claude/` (it is in `.gitignore`).
  - One commit per kind of change; a mixed commit takes the type of the main change, or is split if the split is clean.
  - After a fix or a feature, add an entry to `CHANGELOG.md` under `## [Unreleased]`, in Keep a Changelog format (`### Added`, `### Changed`, `### Fixed`, `### Removed`).
  - Never change anything on GitHub (settings, Pages, releases, issues, pull requests, comments) without asking first; explain the change and give the command.
  - If a hook or guard blocks a git command, do not work around it; use another way that respects the rule, or tell the user.
- **Save analysis responses and plans** under `/home/t00m/Documents/devel/github/KB4IT/responses/` using the `kb4itdoc_md` skill (KB4IT Markdown format).
- **Match KB4IT's existing log style** (`[<COMPONENT>] EVENT key=value`).
- **Prefer dataclasses + typed exceptions over runtime side-channels** when adding new cross-service communication. A service that belongs to one build takes its collaborators in its constructor (see `Pipeline`) instead of `get_service`; a build's decisions go into `runtime` or the build's objects, never into `params` or `repo`.
- **Module size.** No module under `kb4it/` is over 600 lines (theme `framework/` folders aside); `tests/test_module_size.py` enforces it. Split by concern, and when a name moves, keep the old import path working (`tests/test_public_names.py` lists the names of `kb4it.core.util` and `kb4it.tui.app`).
- **Types.** The modules that `scripts/devel/typecheck.sh` lists pass `mypy --strict`; keep them annotated, and add a module to the list when it is fully annotated.
- **Shared theme code.** Code that two document themes need goes into `kb4it/services/themekit/`, with a class attribute or hook method for each difference, not into a copy in each `theme.py`; templates two UIkit themes share go into `kb4it/resources/bases/uikit/templates/`.
- **Templates are Mako** -- `${var}` and `% for`/`% if`, never `{var}` or `{include:...}`.
- **`ENV` is frozen** after `env.py` finishes initializing. Do not attempt to write to it from services; raise an `ENV is frozen` error early at runtime.
- **`@timeit` everything that runs as a stage.** Visible per-stage timing is part of the public observability surface.
- **TUI screens** live in `kb4it/tui/screens/`, one module per screen or pair of small screens, as Textual `Screen` subclasses; a new screen is added to `kb4it/tui/app.py`'s imports and `__all__` only if outside code needs it by that path.
- **CLI actions** require three touches: (1) argparse subparser in `main.py`, (2) dispatch `elif` in `KB4IT.run()`, (3) method on `Workflow` service in `workflow.py`.
- **User help.** `help/` is the user documentation, an `apphelp` knowledge base published to https://t00m.github.io/KB4IT/ by `.github/workflows/help.yml`, which builds it with the KB4IT of the same commit. When a change alters what users see (commands, `repo.json` keys, document rules, theme behaviour, the TUI), update the matching page in `help/source/` in the same change, and check it with `kb4it verify help/config/repo.json`. `help/source/dev-help.md` describes how to write the pages.

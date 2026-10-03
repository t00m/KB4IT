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
scripts/release.sh --dry-run                         # See what a release would do
```

**Versions and releases.** `kb4it/VERSION` names the release being built and only changes through `scripts/release.sh` (`pyproject.toml` is kept equal to it; a test fails when they differ). A development build is identified by `kb4it --version`, which adds `git describe` in a source checkout. Releases follow `RELEASING.md`: `scripts/release.sh` dates `CHANGELOG.md`, drafts `releases/X.Y.Z.md` and commits after the checks pass; the `vX.Y.Z` tag on the merged commit triggers `.github/workflows/publish.yml`, which checks the tag, publishes to PyPI and creates the GitHub release. Every theme's `theme.json` declares the KB4IT it needs in `kb4it` (for example `">=0.7.9"`); KB4IT refuses a theme whose requirement it does not meet, and `check_themes.sh` must pass before a release.

**Run**

```bash
kb4it create <theme> [<app>] <repo_path>  # Initialize a new repository (app defaults to "default")
kb4it build <config>                      # Build the site from repo.json (use -f/--force to force recompilation)
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

CI runs a build + `kb4it --version` smoke test via `.github/workflows/kb4it.yml`. Tests: `./scripts/devel/test.sh` (pytest via uv; add paths or pytest flags after it). CI also builds the wheel and runs `scripts/devel/check_wheel_themes.py`, which fails when a git-tracked theme is missing from `dist/*.whl` and prints a WARNING for themes that are in the wheel but not tracked in git.

## Architecture

Service-based: a central `KB4IT` controller in `kb4it/core/main.py` registers services and routes `get_service(name)` lookups. Services share state through the controller's `runtime` dict (held on `Backend`) and through explicitly-passed dataclasses; the global `ENV` (frozen after init) holds paths and immutable environment metadata.

A process lock (`~/.kb4it/var/kb4it.lock`) prevents concurrent KB4IT instances. When `kb4it` is run with no arguments in an interactive terminal, the Textual-based TUI launches instead of showing help.

### Execution flow

```
CLI args (or TUI)
  -> KB4IT.__init__()           # setup ENV, acquire lock, log file, register services
  -> KB4IT.run()                # dispatch by action
       -> Workflow.<action>()   # build_website / create_repository / info / list_* / verify_sources
            -> Backend.stage_01_check_environment       # paths, theme load, template validation
            -> theme.generate_sources()                 # generate system pages (about, help); nothing is written into source/
            -> Backend.stage_02_get_source_documents    # collect .md sources
            -> Backend.stage_03_process_sources         # Processor steps 00, 01, 02
            -> Backend.stage_04_process_theme           # theme.build()
            -> Backend.stage_05_compilation             # Compiler.execute() in parallel
            -> Theme.post_activities()                  # post-processing (stage 6)
            -> Backend.stage_06_deploy                  # Deployer.execute() (stage 7)
            -> Theme.post_deploy_activities()           # runs on the deployed target (stage 8)
```

Each `stage_*` method is decorated with `@timeit` so per-stage durations land in the `[PERFORMANCE]` debug log. Workflow emits a final `[WORKFLOW] SUMMARY` line with `docs_total`, `compiled`, `skipped`, `invalid` (documents whose frontmatter could not be read, see `BuildPlan.invalid_docs`), `keys_compiled`, `kv_pages_compiled`, and `[WORKFLOW] TOTAL_TIME elapsed=...`.

### Modules

| Location                          | Role |
|---|---|
| `kb4it/core/main.py`              | Entry point, `KB4IT` controller, argparse, process lock, top-level exception catch, TUI auto-launch |
| `kb4it/core/env.py`               | `FrozenDict`-backed `ENV` (sealed after init), system paths, app metadata |
| `kb4it/core/exceptions.py`        | `KB4ITError`, `ConfigError`, `ThemeError`, `CompilationError` hierarchy |
| `kb4it/core/service.py`           | Base `Service` class all services inherit |
| `kb4it/core/types.py`             | `TypedDict` definitions: `Runtime`, `DirPaths`, `DocsInfo`, `KBDict`, `DocumentMeta`, `DBRecord` |
| `kb4it/core/util.py`              | File ops, hashing (blake2b), `exec_cmd`, `DateCache`, date helpers, `@timeit`, `get_document_attributes` |
| `kb4it/core/log.py`               | Logging setup, file redirection |
| `kb4it/services/workflow.py`      | Orchestrates build / create / info / list / verify actions |
| `kb4it/services/backend.py`       | Loads `repo.json`, owns `runtime` dict, exposes `get_plan()` proxy |
| `kb4it/services/database.py`      | In-memory document index keyed by docId, metadata caches |
| `kb4it/services/processor.py`     | Frontmatter extraction, change detection, owns `BuildPlan` + `AnalysisResult` |
| `kb4it/services/compiler.py`      | Markdown -> HTML via `python-markdown` in a `ThreadPoolExecutor` |
| `kb4it/services/builder.py`       | Renders Mako templates; defines `REQUIRED_TEMPLATES` + `_template_candidates()` |
| `kb4it/services/frontend.py`      | Theme discovery, theme load, required-template validation |
| `kb4it/services/deployer.py`      | Copies the compiled output to `repo.target` |
| `kb4it/tui/app.py`                | Textual-based Terminal User Interface (project CRUD, build, browse, explore metadata, log viewer, web server) |

### Themes

Each theme lives under `kb4it/resources/themes/<name>/`:

- `logic/theme.py` -- `Theme` class that extends `Builder` and overrides `build_page`, `build_page_key`, `build_page_key_value`, etc.
- Mako `.tpl` files directly in `templates/` (flat, no subdirectories). Shared fallbacks live in `kb4it/resources/common/templates/`.
- Optional `templates/skeletons/*.md` -- per-category Markdown document skeletons (used by the techdoc `PAGE_ADD` page).
- Optional `logic/verify.py` -- hook `verify(repo, docs) -> list[str]`, run by `kb4it verify` (`Workflow.verify_sources`); `docs` is `{file name: {key: [values]}}`; every returned string is reported as a problem.
- Static assets under `framework/` (CSS, JS, images, UIKit, DataTables).
- `apps/<app>/` repository scaffolds used by `kb4it create`, each holding `config/repo.json`, `source/`, and `target/`.

Optional `theme.json` keys:

- `metadata_pages` (default `true`): when `false`, the processor skips the per-key and per-key/value pages, and `PAGE_KEY` and `PAGE_KEY_VALUE` are no longer required templates.
- `deploy_dirs` (default: the whole theme folder, plus `default` and `common`): list of plain folder names under the theme that are copied to the target. Names are validated (no paths, no `..`); an invalid entry raises `ThemeError`. An explicit list does not deploy the `default` theme or the common resources, so the theme must bring everything its pages need. The theme `id` must be a plain name (no path, not `.` or `..`). Themes without it deploy exactly as before.

Custom themes installable to `~/.kb4it/opt/resources/themes/<name>/`.

**Custom themes and about pages.** The backend no longer writes `about_kb4it.md` or `about_app.md` into `source/`. A custom theme gets about pages only if its `build()` calls `create_page_about_kb4it()` and `create_page_about_app()`. An untouched generated `source/about_kb4it.md` left by older versions is removed at stage 2.

**Clean tmp.** `var/tmp` is emptied at the start of every build (after stage 1, before `generate_sources()`), so a failed build cannot leak files into the next link check.

Required template names per theme: `HTML_BODY`, `PAGE_INDEX`, `PAGE_KEY`, `PAGE_KEY_VALUE`. Missing any of these raises `ThemeError` at `stage_01_check_environment`.

Template lookup (`_template_candidates`) resolves a name `<NAME>` to the first existing file among `<theme>/templates/<NAME>.tpl` then `kb4it/resources/common/templates/<NAME>.tpl`. There is no cross-theme inheritance.

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
- `Builder.site_signature()` returns a value that changes when every page must be rebuilt (default empty, which turns the check off). The processor stores it in the database and forces a full recompile when it changes; themes that render site-wide content (navigation, related pages) into every page override it.
- Markdown links to other `.md` files (`[text](other.md#anchor)`) are rewritten to the generated `.html` page. A target that is not a source document logs `[COMPILER] LINK_BROKEN` (rewrite logic in `kb4it/core/mdlinks.py`).
- YAML frontmatter values that are null (`Tag:` with no value) become `[]`.
- In Mako templates that emit Markdown, write an H2 as `${'##'}` so Mako does not treat `##` as a comment.

### Template transformations

`Builder.apply_transformations()` (in `builder.py`) rewrites HTML from `python-markdown` using Mako template pairs. For each transformation name, a `_MD` template (source pattern, from common templates) and a `_NEW` template (replacement, from the active theme) are loaded. The theme supplies `_NEW` templates to override the default HTML wrappers. This system is used for element-level theming (e.g. wrapping tables, code blocks, or admonitions in theme-specific markup).

Additional system templates (not in the required set): `PAGE_ABOUT_KB4IT`, `PAGE_ABOUT_APP`, `PAGE_HELP`.

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
| `contract` | Path to a contract file with the help ids the application expects; checked against the documents. An explicit path that does not exist logs `[APPHELP] CONTRACT_FILE_MISSING` |
| `vocabulary` | Allowed values per property (`Feature`, `Level`, `Platform`, ...) |
| `labels` | Overrides of the UI texts (for example `ts_cause`, `ts_fix`) |

**Type of document (`apphelp`).** Every content page must be classified with `DocType`, the same key and values as `techdoc`, following the Diátaxis framework: exactly one of `Tutorial`, `How-to guide`, `Reference`, `Explanation` (exact spelling). A page without a valid `DocType` is never published: it is left out of the site, the navigation, the search index and `helpids.js` (`[APPHELP] DOC_LEFT_OUT`), and reported as `DOCTYPE_MISSING` or `DOCTYPE_INVALID`, which fails the build when `strict` is on. The optional `Layout` key (`faq`, `tips`, `troubleshooting`) selects a special rendering on top of the type. The old `Kind` key is reported as `META_INVALID reason=replaced_by_DocType_and_Layout`. In the generated site the classification is called "Type of document"; the theme never shows the word Diátaxis. See `kb4it/resources/themes/apphelp/README.md` for all page properties.

The `force` field can also be set per-build via `--force` (CLI) or the TUI; CLI/TUI takes priority over `repo.json`.

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

- **`runtime`** -- the live build state, accessed via `backend.get_dict("runtime")` or `backend.get_value("runtime", key)`. Holds `theme`, `dir` (`DirPaths`, including `root`, the repository root), `docs` (`DocsInfo`), `logfile`. **Does NOT hold** `ncd`, `nck`, `K_PATH`, `KV_PATH` anymore -- these moved to `BuildPlan`.
- **`BuildPlan`** (in `kb4it/services/processor.py`) -- dataclass produced by `Processor.step_01_analysis()`. Fields: `docs_to_compile`, `K_PATH` (`[(key, values, compile_flag), ...]`), `KV_PATH` (`[(key, value, compile_flag), ...]`), `force_kv_pairs`. Exposes `doc_count`, `key_count`, `kv_count` properties. Access via `backend.get_plan()`.
- **`AnalysisResult`** (in `kb4it/services/processor.py`) -- dataclass passed explicitly between `step_01_analysis` and `step_01_01_decide_keys_compilation`. Carries the `force_kv_pairs` set.
- **`kbdict`** (`KBDict` TypedDict) -- the persisted compilation cache at `<repo>/var/db/kbdict.json`. Maps docs to body/metadata hashes and metadata key/value indices for incremental compilation.
- **`Database` (`srvdtb`)** -- in-memory per-docId map of `{key: [values]}` plus `keys` (all / blocked / theme / ignored) and several lookup caches. `Title` is always ignored; `SystemPage`, `Date` are blocked.

### Backward-compat shim

`Backend.get_value("runtime", "ncd"|"nck"|"K_PATH"|"KV_PATH")` redirects to the BuildPlan so the techdoc/blog themes' existing reads keep working. New code should use `backend.get_plan()` directly.

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
| `~/.kb4it/var/kb4it.lock` | Process lock file |
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

The TUI hooks into the compiler via module-level callbacks in `compiler.py`:
- `set_progress_callback(fn)` -- called per compiled doc with `(current, total, filename)`
- `set_compile_start_callback(fn)` -- called when compilation starts

### Clipboard

Uses `wl-copy`, `xclip`, `xsel`, or OSC52 escape sequence (in order of preference) for copy-to-clipboard in the Build screen.

### Project registry

The TUI reads/writes `~/.kb4it/projects.json`, a JSON file with:
```json
{"projects": [{"name": "My Project", "config": "/path/to/repo.json"}, ...]}
```

Projects are registered automatically by `kb4it create` and manually via ImportProjectScreen.

## Source documents

KB4IT consumes Markdown files only (`.md` / `.markdown`). Each must begin with a YAML frontmatter block, followed by an H1 heading used as the document title.

A document that does not meet this (`missing_frontmatter`, `missing_frontmatter_close`, `invalid_frontmatter`, `missing_h1_title`, `yaml_error line=<n> col=<n> <problem>`) is logged as `[UTIL] DOC_INVALID`, left out of the site and recorded in `BuildPlan.invalid_docs`. Quote values that contain `: ` (for example `Summary: "Plugins: how they load"`), otherwise YAML reads them as a nested mapping.

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

- Python >= 3.11, < 4.0, GNU/Linux only.
- `Mako==1.3.12` -- templates.
- `Markdown>=3.5` -- Markdown -> HTML, with `extra`, `admonition`, `toc`, `sane_lists` extensions.
- `PyYAML>=6.0` -- frontmatter parsing.
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
- **Prefer dataclasses + typed exceptions over runtime side-channels** when adding new cross-service communication.
- **Templates are Mako** -- `${var}` and `% for`/`% if`, never `{var}` or `{include:...}`.
- **`ENV` is frozen** after `env.py` finishes initializing. Do not attempt to write to it from services; raise an `ENV is frozen` error early at runtime.
- **`@timeit` everything that runs as a stage.** Visible per-stage timing is part of the public observability surface.
- **TUI screens** live in `kb4it/tui/app.py` as Textual `Screen` subclasses. Add new screens by subclassing `Screen` and registering them in the app's screen map.
- **CLI actions** require three touches: (1) argparse subparser in `main.py`, (2) dispatch `elif` in `KB4IT.run()`, (3) method on `Workflow` service in `workflow.py`.
- **User help.** `help/` is the user documentation, an `apphelp` knowledge base published to https://t00m.github.io/KB4IT/ by `.github/workflows/help.yml`, which builds it with the KB4IT of the same commit. When a change alters what users see (commands, `repo.json` keys, document rules, theme behaviour, the TUI), update the matching page in `help/source/` in the same change, and check it with `kb4it verify help/config/repo.json`. `help/source/dev-help.md` describes how to write the pages.

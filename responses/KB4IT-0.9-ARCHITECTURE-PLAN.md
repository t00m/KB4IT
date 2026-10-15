---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-15
DocType: How-to guide
OS: Linux, macOS, Windows
Product: KB4IT
Scope: Development
Status: Done
Tag: implementation-plan, audit, architecture, refactoring, themes
Topic: Architecture, Development
---

# KB4IT architecture series implementation plan

## Problem

`responses/KB4IT-0.9-ARCHITECTURE-SPEC.md` (approved 2026-10-15) defines seven
requirements, AR-01 to AR-07, for the architecture findings of `AUDIT.md`. The
series ships in 0.9.0, before the tag (D-G1). Its rule is that nothing a user can
see changes. This plan turns the requirements into an ordered series of commits,
delivered as a zipped `git am` series on top of patch 0110 (this plan).

## Prerequisites

- Base: the branch after patch 0110, with the approved specification (0109) and
  this plan.
- Working branch here: `ccr-271d5ff1-h0hh01`; commits authored and committed as
  Tomás Vírseda, unsigned.
- Tools in this session: Python 3.11 to 3.14 through uv, Java 21 with the Nu HTML
  Checker, shellcheck and actionlint through `uvx`; mypy through `uvx`.
- Your side: as before, `git am`, a push for CI on macOS and Windows.

## Procedure

### Working rules for every commit

1. One commit per requirement or clean part of one; one-line Conventional Commits
   message without trailers; the requirement and finding IDs go in the
   `CHANGELOG.md` entry, under 0.9.0. Pure moves get a single changelog line per
   requirement, in its last commit, so the release notes stay readable.
2. Each commit holds its code, tests, help pages and changelog entry.
3. Before each commit, the four checks of the specification:
   `./scripts/devel/test.sh`; the content snapshot with no difference from the
   baseline; `scripts/devel/validate_html.py` with 0 errors besides UIkit; the
   escaping and HTML quality tests (part of the suite). Ruff reports no new issue
   in the changed files.
4. A move is a move: code is first moved unchanged, then adapted in a separate
   step inside the same commit only where the themes differ, so a reviewer can
   read the diff with `git show --color-moved`.
5. No em dashes.

### Baseline

Commit 111 extends the content snapshot to every sample app and records the
baseline from the tree of patch 0110, whose output equals that of 0107. Every
later commit compares against it. A difference is a bug of that commit, never a
reason to refresh the baseline; the one place the plan expects a difference is
named in Risks.

### Design choices inside the spec

| Topic | Choice |
|---|---|
| Snapshot coverage | `theme_snapshot.py --content` builds every app of every theme (`techdoc/default`, `techdoc/sapbasis`, blog, bookshelf, apphelp), as `validate_html.py` already does, and adds a second, incremental build of the blog and techdoc samples after touching one dated document, so the event pages' incremental path is compared too |
| Dead transformations (AR-04) | Removed: `HTML_TAG_PRE`, `HTML_TAG_TABLE`, `HTML_TAG_TABLE_KB4IT`, the five `HTML_TAG_ADMONITION_*` and the five `HTML_TAG_ADMONITION_ICON_*`: 13 `_MD` files in `common/templates/` and 39 `_NEW` files (13 per document theme). Kept: `TOC`, `SECT1` to `SECT4`, `SECTIONBODY`, `H2` to `H4`, `IMG` |
| Transformation test | `tests/core/test_transformations.py` compiles one document with every construct the default extensions and PyMdown produce (headings h2 to h5, tables, fenced and indented code, every admonition type, images, footnotes, task lists, TOC) through the compiler's own steps, and asserts that each `_MD` pattern in `_XFORM_NAMES` occurs in the output |
| Unreferenced templates (AR-04) | Found by a script that collects every template name from `self.template(...)`, `render_template(...)`, `_XFORM_NAMES`, f-strings and `%` formats in `kb4it/` and `.tpl` files; 62 at the base. `tests/themes/test_templates_used.py` runs the same search, so a new dead template fails the suite |
| Template base (AR-01) | `_template_candidates(name, theme_dir, common_dir, override_dir, base_dir)`: override, theme, base, common. `theme.json` key `template_base` names a folder under `kb4it/resources/common/bases/`; an unknown name stops the build with `ThemeError` naming the key. The base's templates compile with the theme's `autoescape` setting, like the theme's own |
| Shared templates | The techdoc and blog files that are byte-identical after AR-04 move to `common/bases/uikit/templates/`; both `theme.json` files get `"template_base": "uikit"`. Files that are almost identical stay in each theme |
| Shared code (AR-01) | `kb4it/services/themekit/__init__.py` exports `DocumentTheme`; one module per mixin (`metadata.py`, `keypages.py`, `tables.py`, `events.py`, `toc.py`). Each theme's `Theme` class subclasses `DocumentTheme` and keeps only overrides |
| Differences as hooks | Class attributes on `DocumentTheme` with the techdoc value as default, set by the theme that differs. Known so far: `datatable_link_template` (`LINK_DATATABLE`; blog and bookshelf `LINK`), `datatable_default_headers` (`["Date", "Title"]`), `datatable_title_cell` (a method: techdoc and blog render `DATATABLE_BODY_ITEM` with a tooltip, bookshelf a plain cell). bookshelf keeps `build_page_key_value` as an override that handles the Book overview and calls `super()` for the rest |
| Event pages | One `build_events` for techdoc and blog. The two differ only on incremental builds: techdoc rebuilds a day, month or year page whose cached copy is missing, blog only when a document changed. The shared method takes techdoc's rule, which gives the same pages whenever the cache is intact and repairs it when it is not; see Risks |
| Single definitions | `tests/core/test_themekit.py` parses the four `theme.py` files with `ast` and fails if a method of the AR-01 table is defined there without a docstring line starting `Override:` that says why |
| `core/util.py` split (AR-02) | New `core/dates.py`, `core/documents.py`, `core/files.py`; they import nothing from `core/util.py`. `core/util.py` does `from kb4it.core.dates import *` style explicit imports of every moved name, with `__all__`, so `from kb4it.core.util import guess_datetime` keeps working in themes, hooks, the TUI and the four templates that import it in `<%! %>` blocks |
| TUI split (AR-02) | `tui/projects.py` (`load_projects`, `save_projects`, `get_themes`, `get_apps`, path helpers), `tui/servers.py` (live and project web servers), `tui/clipboard.py`, `tui/screens/` with `build.py`, `logs.py`, `documents.py` (viewer and explorer), `project.py` (project, info and file list), `catalog.py` (themes and apps), `create.py` (create and import), `main.py`, `confirm.py`; `tui/app.py` keeps `KB4ITTUI` and `run` and re-exports the rest. Tests that patch `tui.webbrowser` or `tui.Path` move to the module that uses them |
| Module size test | `tests/test_module_size.py`: every `.py` under `kb4it/` except `resources/themes/*/framework/` has at most 600 lines |
| Import compatibility | `tests/test_public_names.py` holds the lists of names that `kb4it.core.util` and `kb4it.tui.app` export at patch 0110 and imports each one |
| Theme variables (AR-05) | `Builder.theme_var` assigned in `_initialize`; the class attribute goes |
| Callbacks (AR-05) | `KB4IT(params)` accepts `progress_callback` and `compile_start_callback` in `params`; the `Compiler` receives them from the pipeline. `set_progress_callback`, `set_compile_start_callback` and `clear_progress_callback` remain and store into a per-process default that the next build picks up once, with a `[COMPILER] CALLBACK_DEPRECATED` debug line; the TUI moves to the parameters |
| Build decisions (AR-05) | `runtime["force_all"]` replaces the writes to `params["force"]` in `Backend`; `Processor` reads `params["force"] or runtime["force_all"]`. The generation time moves from `repo["updated"]` to `theme_var["updated"]`, and `theme_var["repo"]` is a copy with `updated` added, so templates that read `var['repo']['updated']` keep working in 0.9.x while `Backend.repo` stays as loaded |
| Pipeline (AR-03) | `kb4it/services/pipeline.py`: `Pipeline(backend, db, theme, settings, callbacks)` creates `Processor`, `Compiler` and `Deployer` with explicit collaborators at the end of stage 1. Stages 3, 5 and 6 use `backend.pipeline`. The three classes stop calling `get_service`; their `_initialize` logic moves to `__init__` |
| Deprecated lookups (AR-03, D-G4) | `KB4IT.get_service` answers `Processor`, `Compiler` and `Deployer` from the current pipeline and logs `[CONTROLLER] SERVICE_DEPRECATED name=<name> replacement=backend.pipeline` once per build per name; removed in 0.10.0 |
| Types (AR-06) | Annotations on `core/paths.py`, `core/dates.py`, `core/documents.py`, `core/files.py`, `services/themekit/`, `services/pipeline.py`; `KB4IT.get_service` gets `typing.overload` signatures for the application-level names. `mypy --strict` on those modules, as a step of the CI `package` job; `scripts/devel/typecheck.sh` runs the same here |

### Commit series

Numbers continue after 0110. Counts are estimates; the order is fixed.

#### Phase A: plan and baseline

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 110 | `docs: add implementation plan for the architecture series` | | this file | |
| 111 | `build(devel): snapshot every sample app and an incremental build` | (support) | `scripts/devel/theme_snapshot.py`, `tests/core/test_theme_snapshot.py` | two runs on the same tree give no difference |

#### Phase B: remove before moving (G1)

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 112 | `refactor(builder): remove transformations that never match` | AR-04 (ARC-05) | `services/builder.py`, 13 `common/templates/HTML_TAG_*_MD.tpl`, 39 theme `_NEW` templates | new `tests/core/test_transformations.py`; snapshot |
| 113 | `refactor(themes): remove templates nothing uses` | AR-04 (ARC-05) | 62 templates in techdoc, blog and bookshelf | new `tests/themes/test_templates_used.py`; snapshot |
| 114 | `chore: remove the unused root index.html and pypi folder` | AR-07 (ARC-08) | `index.html`, `pypi/`, `tests/conftest.py` comment | `git ls-files` check in `tests/core/test_readme.py` |

#### Phase C: share and split (G2)

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 115 | `feat(builder): template bases for themes` | AR-01 (ARC-01) | `services/builder.py` (`_template_candidates`), `services/frontend.py` (key check), `scripts/devel/escape_audit.py`, theme how-to | lookup with and without `template_base`; unknown base refused |
| 116 | `refactor(themes): share the uikit templates of techdoc and blog` | AR-01 | `common/bases/uikit/templates/`, techdoc and blog `theme.json` and templates | no byte-identical template in two themes; snapshot; `test_escaping.py` covers the base |
| 117 | `refactor(themekit): add DocumentTheme with the metadata helpers` | AR-01 | new `services/themekit/` (`__init__`, `metadata.py`), the three document themes | snapshot; `tests/core/test_themekit.py` (starts with the metadata methods) |
| 118 | `refactor(themekit): share the property and value pages` | AR-01 | `themekit/keypages.py`, themes | snapshot; single-definition test extended |
| 119 | `refactor(themekit): share the datatable` | AR-01 | `themekit/tables.py`, themes | snapshot; the escaping test (titles in tables) |
| 120 | `refactor(themekit): share the events calendar` | AR-01 | `themekit/events.py`, techdoc and blog | snapshot including the incremental build; a test that deletes a cached month page and checks blog rebuilds it |
| 121 | `refactor(themekit): share the table of contents` | AR-01 | `themekit/toc.py`, themes | snapshot; single-definition test complete |
| 122 | `docs: document DocumentTheme and template bases` | AR-01 | `help/source/howto-create-theme.md`, `CHANGELOG.md` | help verify |
| 123 | `refactor(util): split util into dates, documents and files` | AR-02 (ARC-02) | `core/util.py`, new `core/dates.py`, `core/documents.py`, `core/files.py` | new `tests/test_public_names.py` (util part); snapshot |
| 124 | `refactor(tui): one module per screen` | AR-02 | `kb4it/tui/` | `tests/test_public_names.py` (TUI part); TUI tests with moved patch targets |
| 125 | `refactor(techdoc): split the dashboard and the add page out of the theme class` | AR-02 | `themes/techdoc/logic/` (new `techdoc_dashboard.py`, `techdoc_addpage.py`, imported by name like apphelp's `apphelp_*` helpers) | new `tests/test_module_size.py`; snapshot |

#### Phase D: explicit structure (G3)

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 126 | `refactor(builder): theme variables belong to one builder` | AR-05 (ARC-06) | `services/builder.py` | two builders do not share `theme_var` |
| 127 | `refactor(compiler): pass progress callbacks to the build` | AR-05 | `services/compiler.py`, `core/main.py`, `tui/screens/build.py` | two builds in one process with different callbacks |
| 128 | `refactor(backend): keep build decisions out of the settings` | AR-05 | `services/backend.py`, `services/processor.py`, `services/builder.py` | `on_build_end` sees `repo` as loaded; a corrupt cache still forces a full build; `var['repo']['updated']` still renders |
| 129 | `refactor(pipeline): build the processor, compiler and deployer once per build` | AR-03 (ARC-03) | new `services/pipeline.py`, `backend.py`, `processor.py`, `compiler.py`, `deployer.py`, `workflow.py`, `core/main.py` (deprecated lookups) | the existing build tests unchanged; `SERVICE_DEPRECATED` logged once |
| 130 | `test(pipeline): construct each pipeline service without the app` | AR-03 | new `tests/core/test_pipeline_units.py` | the change analysis, one compile and one deploy with stand-ins |
| 131 | `build(types): annotate the seams and type-check them in ci` | AR-06 (ARC-07) | the modules of the AR-06 row, `core/main.py` overloads, new `scripts/devel/typecheck.sh`, `.github/workflows/kb4it.yml` | mypy 0 errors; actionlint |

#### Phase E: notes

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 132 | `docs: update agents.md for the architecture series` | AR-03 | `AGENTS.md` (lifecycle, themekit, template bases, module layout, deprecations) | |
| 133 | `docs: record implementation notes in the architecture plan` | | this file, `AUDIT.md` status lines for ARC-01 to ARC-08 | |

### Delivery package

- `kb4it-architecture-plan.zip`: patches 0109 (approval) and 0110 (this plan), with
  readable copies, now.
- `kb4it-architecture-series.zip`: patches 0109 to 0133, `README-APPLY.md` and
  `SERIES.sha256`, at the end; it replaces the plan zip in the bundle.
- `kb4it-patch-bundle.zip` and `APPLY-ORDER.md` updated with each delivery; the
  apply script needs no change.

### Progress reporting

A short status after each phase. An interim zip after Phase C (sharing and
splitting) if you want CI on the moved code before the wiring changes of Phase D.

## Verification

| Check | Where | When |
|---|---|---|
| Full test suite | Here, Python 3.11 | Every commit |
| Content snapshot of every sample app, full and incremental build: no difference from the baseline | Here | Every commit |
| Nu HTML Checker on every sample app | Here and CI | Every commit |
| Structural tests (transformations, templates used, single definitions, module size, public names, two builds, pipeline units) | Here | From the commit that adds each |
| mypy on the AR-06 modules | Here and CI | From commit 131 |
| `git am` of 0109 to 0133 on a clean checkout of 0108 | Here | Before the zip |
| macOS and Windows | CI after you push | After applying |

## Implementation notes

The series is patches 0111 to 0133, as planned: the snapshot tool, 20 commits for
AR-01 to AR-07, the `AGENTS.md` update and these notes. At every commit the test
suite passed, the content snapshot of every sample app (full and incremental build)
was identical to the baseline, and the Nu HTML Checker reported 0 errors besides
UIkit attributes on 118 pages of the five sample sites. Differences from the plan,
decided while implementing:

| Item | Plan | Delivered | Why |
|---|---|---|---|
| Template bases (115) | `kb4it/resources/common/bases/` | `kb4it/resources/bases/` | `common/` is copied into the sites of themes without `deploy_dirs`; the bases would have been published with them |
| Unused templates (113) | 62 | 63 | Common `HTML_TAG_ADMONITION_MD` had no user once the admonition pairs of 112 were gone |
| Shared templates (116) | techdoc and blog, bookshelf if it shared any | 17 files to `uikit`; bookshelf has none of them and keeps no base | Byte-identical comparison after 112 and 113 |
| bookshelf metadata (117) | Shared method | An override that calls the shared one and leaves the section empty on failure | bookshelf has always built the page without its metadata instead of failing; a failure now also logs the shared `[THEME]` lines |
| Key pages (118) | Hooks for template names and a filter | Also `properties_title`, `reuse_unchanged_pages`, `tagcloud_scale_skips_empty`, `cloud_measure`, `frequency_keys`, `stats_keys`; bookshelf's `build_page_all` is now `build_page_index_all` | The three themes differ in the title, the cache reuse of four pages, the font size or weight of the clouds, and the keys they count |
| Tag cloud scale (118) | Not foreseen | Kept as it was: techdoc and blog count documents without the property (read as an empty value) in the scale; bookshelf does not | Changing it would change pages; a candidate fix for later |
| Datatable (119) | `datatable_link_template`, `datatable_default_headers`, `datatable_title_cell` | Also `datatable_date_cell` and `datatable_value_link` (techdoc's Priority and Status labels; bookshelf's `#` link) | Each theme renders the date and the value cells differently |
| blog `repo.json` without `datatable` (119) | Not foreseen | Falls back to Date and Title, like techdoc | blog read the key strictly and stopped with a `KeyError` |
| Event pages (120) | blog adopts techdoc's rule (rebuild on a changed document or a missing cache) | Shared method with techdoc's rule; blog sets `events_rebuild_all` | blog's day check started at `True`, so blog has always rebuilt every event page; adopting the rule would have made blog reuse cached pages, a change the plan did not intend. Whether blog should reuse them is a separate decision |
| Unused code in the moved methods (118, 120) | Not foreseen | Dropped: blog's `proportion` (could only raise), the month pages' `var['doclist']` (no template reads it), the `get_doc_properties` call in `build_events` | Found while unifying |
| `util.py` split (123) | `valid_filename` stays in `util` | `valid_filename`, `SOURCE_ENCODING` and `get_source_docs` in `files.py`; `get_hash_from_body` in `documents.py` | `documents.py` needs them, and the new modules import nothing from `util` |
| TUI split (124) | Patch targets move to the module that uses them | Screens call `clipboard._copy_to_clipboard` through the module, so tests patch one place; the registry warning logs as `kb4it.tui.projects` | Two screens copy text |
| techdoc split (125) | `techdoc_dashboard.py`, `techdoc_addpage.py` | Mixins (`DashboardMixin`, `AddPageMixin`) that `Theme` inherits; the Priority and Status tables moved with the dashboard | The methods move unchanged, with `self` |
| Callbacks (127) | In `params` | Taken out of `params` into `KB4IT.callbacks`, so they are neither logged as parameters nor passed to templates as `var['conf']` | `params` is data |
| Forced builds (128) | `Processor` reads `params["force"] or runtime["force_all"]` | As planned; before, it read `repo.json` `force` only | Same pages: `--force` and a bad cache already empty the cache; techdoc's backups now read `force_all` |
| Pipeline (129) | Made at the end of stage 1 | As planned; `kb4it info` no longer creates a Processor, which it never used, and the Compiler takes deprecated callbacks at stage 1 | The three classes keep `Service` for their logger but are not registered |
| Types (131) | mypy on the seams | 12 files, `mypy --strict` 0 errors; `ThemeHost` declares for mypy what the mixins use from `Builder`; event dates parse through a helper that raises `ValueError` on a bad date (never reached: the processor normalizes `Date` first); `string_timestamp` keeps raising `AttributeError` | CI pins mypy 2.4.0 and `types-PyYAML` |

Sizes after the series: techdoc `theme.py` 411 lines (1,273 at the base), blog 448
(971), bookshelf 526 (762), `tui/app.py` 133 (1,457), `core/util.py` 265 (754); the
largest module is `services/builder.py`, 594. `services/themekit/` holds 566 lines.

What ran here and what only CI can show:

- Ran here: the full test suite at every commit (702 tests at the end, Python 3.11);
  the content snapshot at every commit; the Nu HTML Checker at every commit;
  `scripts/devel/check_themes.py`; the help site's `verify` and build; mypy,
  shellcheck and actionlint.
- Only CI: macOS and Windows, the other Python versions of the matrix, and the new
  type-check step on GitHub's runner.

Follow-ups outside this series:

- Remove in 0.10.0 what 0.9.x keeps: `KB4IT.get_service` for the pipeline services,
  `compiler.set_progress_callback` and `set_compile_start_callback`, and
  `var['repo']['updated']`.
- Decide whether blog should reuse its cached event pages (`events_rebuild_all`).
- Decide whether a tag cloud's scale should leave out documents without the property
  in techdoc and blog, as bookshelf does.

## Troubleshooting

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| The snapshot covers full builds; the incremental paths of the shared code differ between themes (`build_events`) | A change that only shows on a second build | Commit 111 adds an incremental build to the snapshot; commit 120 adds a test for the missing-cache case |
| Unifying `build_events` on techdoc's rule changes blog when a cached event page is missing | The page is rebuilt instead of the build failing to copy it | This is the only expected behaviour change: it appears only with a damaged cache, and the snapshot of an intact build is unchanged. Recorded in the implementation notes |
| A template name built at run time escapes the unreferenced-template search | A page fails with `TEMPLATE_NOT_FOUND` after commit 113 | The search covers f-strings and `%` formats; the full suite and every sample app build after the commit; a removed file comes back in one line |
| Theme logic is loaded from its file, not as a package module | A relative import (`from .dashboard import ...`) in techdoc's `logic/` would not resolve, and `logic/` folders share one `sys.path` | The frontend loader puts the theme's `logic/` folder on `sys.path` (`frontend.py:157`); the new modules use plain imports and names prefixed with the theme, as apphelp's `apphelp_*` helpers do |
| `util` re-exports create an import cycle | Import error at start | The new modules import only the standard library, `yaml` and `kb4it.core.env`/`log`; a test imports each of them alone |
| Mako templates import from `kb4it.core.util` in `<%! %>` blocks | A template fails to compile after commit 123 | The public-names test covers `get_human_datetime`, `guess_datetime` and `valid_filename`; the snapshot builds every template that uses them |
| TUI tests patch module globals | Tests pass without exercising the patched path | Patch targets move to the module that uses each name; a TUI smoke test runs the app headless |
| Pipeline wiring changes the order services exist | A service used before stage 1 ends | The Pipeline is created at the end of stage 1, where the theme is loaded; `get_service` for the three names before that raises with a clear message |
| Size of the series (about 23 commits) | Review effort | Moves kept apart from adaptations (`--color-moved`); a status per phase; optional interim zip after Phase C |

## Open questions

None. The shared code was made byte-identical for every theme; where a theme's
behavior differed, a hook keeps it (see Implementation notes).

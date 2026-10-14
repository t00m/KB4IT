# KB4IT audit

Read-only audit of the KB4IT repository. Only this file is written. Work goes
phase by phase; each phase ends with a top-5 priority list, and the next phase
starts only after review.

- Audited tree: branch `ccr-271d5ff1-h0hh01`, commit `b5330aa` (0.8.0 plus the
  0.9 series and the distribution series, 68 commits on top of release `d026df3`).
- Date: 2026-10-14.

| Phase | Status |
|---|---|
| 0 Inventory | Done |
| 1 Automated baseline | Pending |
| 2 Correctness and robustness | Pending |
| 3 Security | Pending |
| 4 Architecture and maintainability | Pending |
| 5 Dependencies and packaging | Pending |
| 6 Tests and HTML output quality | Pending |

---

## Phase 0: Inventory

### Packages and size

Python lines (including comments and blank lines), counted with `wc -l`:

| Package | Files | Lines | Notes |
|---|---|---|---|
| `kb4it/core` | 18 | 2,597 | Controller, environment, utilities, server, watcher, search, hooks, lock |
| `kb4it/services` | 8 | 2,968 | The build pipeline services |
| `kb4it/tui` | 1 | 1,450 | Textual terminal interface, one module |
| `kb4it/resources/themes/*/logic` | 13 | 3,883 | Per-theme Python (`theme.py` subclasses of `Builder`) |
| `tests` | 56 test files | 4,324 | pytest |
| `scripts` (Python only) | | 721 | Dev and release helpers; shell scripts not counted |

Largest modules, the first places to look for god classes (Phase 4):

| Module | Lines |
|---|---|
| `kb4it/tui/app.py` | 1,449 |
| `kb4it/resources/themes/techdoc/logic/theme.py` | 1,269 |
| `kb4it/resources/themes/blog/logic/theme.py` | 949 |
| `kb4it/resources/themes/bookshelf/logic/theme.py` | 760 |
| `kb4it/core/util.py` | 617 |
| `kb4it/services/builder.py` | 533 |
| `kb4it/services/processor.py` | 493 |
| `kb4it/services/backend.py` | 456 |

Full module list with lines:

| Module | Lines | Role |
|---|---|---|
| `core/main.py` | 375 | CLI parser, `KB4IT` controller, service registry, `main()` |
| `core/service.py` | 84 | `Service` base class (start, end, `get_service`) |
| `core/env.py` | 168 | Paths (`GPATH`, `LPATH`), platform, `KB4IT_HOME` |
| `core/util.py` | 617 | Hashing, frontmatter parsing, file copy, dates, slugs |
| `core/types.py` | 69 | `BuildPlan`, `AnalysisResult` dataclasses |
| `core/log.py` | 88 | Logging setup |
| `core/exceptions.py` | 34 | `KB4ITError` hierarchy |
| `core/version.py` | 43 | Version string, `git describe` |
| `core/lock.py` | 141 | Per-repository file lock (flock/msvcrt) |
| `core/mdconfig.py` | 109 | python-markdown extension settings |
| `core/mdlinks.py` | 69 | Markdown link rewriter (`.md` to `.html`) |
| `core/search.py` | 141 | Search index sections and cache |
| `core/publish.py` | 101 | sitemap, robots.txt, Atom feed |
| `core/hooks.py` | 82 | Per-repository Python build hooks |
| `core/serve.py` | 197 | `kb4it serve` |
| `core/webserver.py` | 180 | Local HTTP server with live reload |
| `core/watch.py` | 99 | Polling file watcher |
| `services/backend.py` | 456 | Repository settings, paths, build stages 1 to 7, kbdict load/save |
| `services/processor.py` | 493 | Frontmatter extraction, change detection, `BuildPlan`, backlinks |
| `services/compiler.py` | 303 | Markdown to HTML in a thread pool |
| `services/database.py` | 304 | In-memory document/property index |
| `services/builder.py` | 533 | `Builder` base: Mako templates, page generation, search index |
| `services/deployer.py` | 235 | Copies output to `target/`, head metadata, cache |
| `services/frontend.py` | 238 | Theme discovery and loading (registers `Theme`) |
| `services/workflow.py` | 406 | Actions: build, create, info, verify, list |
| `tui/app.py` | 1,449 | 15 Textual screen/widget classes |
| `themes/apphelp/logic/*` | 905 | 9 modules: config, metadata checks, navigation, search, versions |
| `themes/blog/logic/theme.py` | 949 | Blog theme |
| `themes/bookshelf/logic/theme.py` | 760 | Bookshelf theme |
| `themes/techdoc/logic/theme.py` | 1,269 | Techdoc theme |

### Entry points

| Entry point | Location | Notes |
|---|---|---|
| `kb4it` console script | `pyproject.toml:59` -> `kb4it/core/main.py:224` (`main`) | Declared under `[tool.poetry.scripts]` |
| TUI | `kb4it/core/main.py:227-230` | Started when `kb4it` runs with no arguments and stdin/stdout are terminals |
| CLI actions | `kb4it/core/main.py:166-179` | `themes`, `projects`, `create`, `build`, `info`, `verify`, `apps`; `serve` goes to `core/serve.py:195` |
| GitHub Action | `action.yml`, `scripts/action/run.sh` | Composite action, bash steps |
| Build hooks | `kb4it/core/hooks.py:74` | Loads a repository-provided Python file and runs it in-process |

### Services and registration

Registered at start-up in `kb4it/core/main.py:109-115`: `DB`, `Backend`, `Frontend`, `Builder`, `Workflow`.
Registered later, during a build:

| Service | Registered at |
|---|---|
| `Theme` (a `Builder` subclass from the theme folder) | `kb4it/services/frontend.py:163` |
| `Processor` | `kb4it/services/backend.py:315` |
| `Compiler` | `kb4it/services/backend.py:447` |
| `Deployer` | `kb4it/services/backend.py:454` |

Services find each other by name through `Service.get_service` (`kb4it/core/service.py:82`), a service-locator pattern; coupling is reviewed in Phase 4.

### Templates and themes

| Theme | `.tpl` templates | Sample apps | Vendored front-end (`framework/`) |
|---|---|---|---|
| techdoc | 74 | `default`, `sapbasis` | UIkit, Highlight.js, DataTables, kb4it; 8.7 MB |
| blog | 105 | `default` | UIkit, Highlight.js, DataTables, TimelineJS, kb4it; 11 MB |
| bookshelf | 54 | `default` | bookshelf; 64 KB |
| apphelp | 6 | `default` | apphelp; 40 KB |
| common (shared by all) | 31 | | `kb4it-search.js`, `kb4it-search-ui.js` (255 lines), `kb4it-search.css` |

- 270 `.tpl` files in total; 797 vendored `.js` files under `themes/*/framework/`.
- Templates are compiled with `mako.template.Template(filename=...)` at `kb4it/services/builder.py:197`, with no `default_filters` and no `TemplateLookup`. Escaping is reviewed in Phase 3.
- Node/npm: there is no `package.json` in the project itself. Four `package.json` files exist only inside vendored, pre-built Highlight.js copies (`themes/{blog,techdoc}/framework/Highlight/package.json` and `.../es/package.json`, `"name": "@highlightjs/cdn-assets"`). Nothing in the build pipeline runs Node; whether these files should ship is reviewed in Phase 5.

### Main data flow

`kb4it build CONFIG` runs `Workflow.build_website` (`kb4it/services/workflow.py:312`) in eight logged stages:

1. **Check environment**: `Backend.stage_01_check_environment` (`backend.py:331`): reads and validates `repo.json`, resolves paths, loads the theme (`Frontend`, which registers `Theme`).
2. **Get sources**: `Theme.generate_sources` and `Backend.stage_02_get_source_documents` (`backend.py:389`): lists the `.md` files of `source/`.
3. **Process sources**: `Backend.stage_03_process_sources` (`backend.py:425`) runs the `Processor`:
    - `step_00_extraction` (`processor.py:86`): YAML frontmatter is parsed with `yaml.safe_load` (`core/util.py:362`), and each document is hashed with BLAKE2b, body and metadata separately (`core/util.py:307-338`, `432-442`).
    - `step_01_analysis` (`processor.py:236`): compares the hashes with the `kbdict.json` cache (`backend.py:277` load, `backend.py:300` save) and builds the `BuildPlan` (changed documents, keys and key/value pages). A version change discards the cache (`backend.py:284-291`).
    - Fills the in-memory `Database` (`services/database.py`).
4. **Process theme**: `Backend.stage_04_process_theme` (`backend.py:438`): the theme renders the index, key and key/value pages through Mako (`builder.py:178` `template`, `builder.py:210` `render_template`).
5. **Compilation**: `Backend.stage_05_compilation` (`backend.py:445`): `Compiler` converts Markdown to HTML with python-markdown in a `ThreadPoolExecutor` (`compiler.py:15`, `compiler.py:133` `_compile_md`; extensions from `core/mdconfig.py:51`), then wraps each page in the theme templates.
6. **Theme post**: `Theme.post_activities`.
7. **Deploy**: `Backend.stage_06_deploy` (`backend.py:452`) runs the `Deployer` (`deployer.py:28`): copies to `target/`, inserts head metadata (`deployer.py:85`), copies resources, and keeps a cache in `var/`.
8. **Theme post deploy**: search index, `sitemap.xml`, feed (`workflow.py:365-368`).

```text
source/*.md --(Processor: safe_load + BLAKE2b, compare kbdict.json)--> BuildPlan + Database
     --(Builder/Theme: Mako)--> index, key and key/value pages
     --(Compiler: python-markdown, threads)--> document HTML
     --(Deployer)--> target/ (+ var/ cache, kbdict.json)
```

### Concurrency

| Where | What |
|---|---|
| `services/compiler.py:15` | `ThreadPoolExecutor` for Markdown compilation (`workers` setting) |
| `core/webserver.py:172` | HTTP server thread (`serve`, TUI) |
| `core/serve.py:124` | Watcher thread (TUI live reload) |
| `tui/app.py:317` | Build thread in the TUI |
| `core/lock.py` | Cross-process lock per repository |

### Dependencies (first read; detail in Phase 5)

`pyproject.toml:44-53` and `requirements.txt:1-7` list the same seven runtime packages with the same constraints: `Mako` pinned to `1.3.12`, `lxml` unpinned, the rest with lower bounds. `pymdown-extensions` is an optional extra only in `pyproject.toml:52-56`, which is consistent. No drift found at this level; `tests/core/test_requirements.py` enforces it. `pixi.toml` and `pixi.lock` are a third dependency source, still to be checked in Phase 5.

### Other tracked items noticed

- `index.html` and `pypi/README.rst` at the repository root are tracked (`git ls-files`). Their purpose is to be checked in Phase 4 (possible leftovers).
- `kb4it/core/util.py:210-224` defines `exec_cmd`, which runs `subprocess.Popen([cmd], shell=True)`. A search finds no caller in `kb4it/`. Phases 3 and 4 cover it.

### Phase 0 top 5: where to look first

| # | Area | Location | Why first |
|---|---|---|---|
| 1 | Mako templates compiled without escaping filters | `kb4it/services/builder.py:197` | Document titles and property values from frontmatter end up in HTML; without `h` escaping that is a stored-XSS path (Phase 3) |
| 2 | `exec_cmd` with `shell=True` and no callers | `kb4it/core/util.py:219-220` | Dead code that runs a shell; remove or confirm unused (Phases 3, 4) |
| 3 | Incremental cache rules | `kb4it/services/processor.py:236`, `kb4it/services/backend.py:277-304` | Wrong invalidation means stale pages; check theme, template, hook and settings changes (Phase 2) |
| 4 | Size of the TUI and the theme modules | `kb4it/tui/app.py` (1,449 lines), `themes/techdoc/logic/theme.py` (1,269 lines) | Likely duplication between themes and a god-class TUI (Phase 4) |
| 5 | Vendored front-end assets with `package.json` | `kb4it/resources/themes/techdoc/framework/Highlight/package.json:2` | Check against the no-Node constraint and the licences of 19 MB of bundled JavaScript (Phase 5) |

Phase 0 is complete. I stopped here, waiting for your go-ahead before Phase 1.

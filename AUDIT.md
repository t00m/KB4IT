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
| 1 Automated baseline | Done |
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


---

## Phase 1: Automated baseline

All tools ran on `kb4it/` (the package, including theme logic and the TUI), not on
`tests/` or `scripts/`. `bandit`, `vulture`, `radon` and `pip-audit` were run with
`uvx` (isolated, nothing installed in the project). No project configuration
exists for any of them (`pyproject.toml` has no `[tool.ruff]`, `[tool.mypy]` or
`[tool.bandit]`), so each ran with its defaults.

| Tool | Version | Result |
|---|---|---|
| ruff check | 0.16.8 | 261 issues, 29 rules; 47 auto-fixable |
| mypy --ignore-missing-imports | 2.3.1 | 33 errors in 14 files (42 files checked); 24 are missing annotations |
| bandit -r | 1.9.4 | 20 issues over 8,928 lines: 1 high, 2 medium, 17 low |
| vulture (60% confidence) | 2.16 | 155 candidates; most are dynamic entry points (false positives) |
| radon cc -s -n C | 6.0.1 | 36 blocks at rank C or worse: 29 C (11-20), 7 D (21-30), none E/F |
| pip-audit | 2.10.1 | No known vulnerabilities (requirements.txt plus `pymdown-extensions>=10.0`) |

### ruff, grouped

| Group | Rules (count) | Comment |
|---|---|---|
| Broad exception handling | BLE001 (45), S110 (8), S112 (1) | 18 of the 45 are in `tui/app.py`; reviewed in Phase 2 |
| Dead code in functions | F841 (17), F401 (11), RUF059 (1) | Mostly theme modules and `tui/app.py`; see BASE-05 |
| Naive datetimes | DTZ005 (10), DTZ001 (5), DTZ006 (2), DTZ007 (2), DTZ901 (1) | Effect on feed and sitemap dates checked in Phase 2 |
| Style and modernisation | UP031 (61), UP009 (4), UP032 (3), I001 (14), SIM102 (4), SIM113 (1), RET501 (4), PIE790 (2), PLR1730 (3), PERF402 (2), PLC0206 (1), F541 (1), RUF100 (2) | Style only; not reported individually |
| Packaging hygiene | EXE001 (29) | Files with a shebang that are not executable (theme logic, modules); cosmetic |
| Class and argument defaults | RUF012 (22), B006 (3), RUF013 (1) | The three B006 cases were read and are safe (see below) |
| Subprocess | PLW1510 (1) | `core/version.py:39`, `git describe` with its error handled; harmless |

B006 check: `themes/blog/logic/theme.py:577` (`var={}`) replaces the empty default
before writing to it (`if len(var) == 0: var = self.get_theme_var()`), and
`themes/techdoc/logic/theme.py:91` (`headers=[]`, `doclist=[]`) reassigns
`headers` and never mutates either list. No shared-state bug.

### mypy, beyond missing annotations

| Location | Error | Assessment |
|---|---|---|
| `kb4it/core/main.py:51` | `params: argparse.Namespace = None` | Real typing gap (implicit Optional); harmless at runtime |
| `kb4it/core/main.py:70` | `__class__` not defined | False positive: `__class__` is valid inside a method |
| `kb4it/core/version.py:28` | `Match | None` has no `.groups()` | False positive in practice: clauses are stripped and non-empty (`version.py:21`), and `CLAUSE_RE` (`version.py:8`) ends in `(.+)$`, so it always matches |
| `apphelp/logic/apphelp_checks.py:57` | Too many arguments for `_target_exists` | False positive: `*url.partition("#")[::2]` expands to exactly two arguments |
| `kb4it/core/env.py:111`, `kb4it/core/log.py:46` | `None` used as a string/path | Values that are `None` only before setup; Needs verification in Phase 2 |
| `kb4it/services/database.py:140` | Returns `None` for `-> str` | Real typing gap; callers must handle `None` (Phase 2) |
| `kb4it/services/processor.py:214-215` | `object` not indexable | Typing gap from an untyped dict; harmless |

### bandit

| ID | Location | Assessment |
|---|---|---|
| B602 high | `kb4it/core/util.py:219-220` | Real: `subprocess.Popen([cmd], shell=True)` in `exec_cmd`; see BASE-01 |
| B702 medium | `kb4it/services/builder.py:197` | Real lead: Mako `Template(...)` with no escaping filters; Phase 3 |
| B104 medium | `kb4it/core/webserver.py:159` | False positive: compares a host string for display, binds nothing |
| B406 low (2) | `kb4it/core/publish.py:40`, `:78` | False positive: `xml.sax.saxutils` used to escape output, no XML parsing |
| B110/B112 low (9) | Same places as ruff S110/S112 | Phase 2 |
| B404/B603/B607 low | `core/version.py:39`, `tui/app.py:204` | Argument lists, no shell; acceptable |

### vulture

Of 155 candidates, 87 are "unused methods"; most are called dynamically
(Textual `on_*`, `compose`, `action_*` handlers, theme hooks called by name, and
methods called from Mako templates), so they are not reported. The unused
module-level functions were cross-checked with a search over `kb4it/`, `tests/`
and `scripts/`, templates included:

| Function | Location | Used by |
|---|---|---|
| `exec_cmd` | `kb4it/core/util.py:210` | Tests only (`tests/core/test_util.py:66-67`) |
| `delete_files` | `kb4it/core/util.py:283` | Tests only |
| `get_hash_from_file` | `kb4it/core/util.py:312` | Tests only |
| `get_year`, `get_month`, `get_day` | `kb4it/core/util.py:486-496` | Tests, and unused imports in `themes/techdoc/logic/theme.py:24-27` |
| `log_timestamp`, `kb4it_timestamp`, `get_timestamp_yyyymmdd` | `kb4it/core/util.py:501-590` | Nothing found |
| `_start_project_server` | `kb4it/tui/app.py:172` | Nothing found |
| `DocumentMeta` | `kb4it/core/types.py:47` | Nothing found |

Custom themes in `~/.kb4it/opt/resources/themes/` may import `kb4it.core.util`
functions; whether any of these are a public API for themes is Needs
verification before removal.

### radon, rank D (complexity 21 to 30)

| CC | Function |
|---|---|
| 30 | `themes/apphelp/logic/apphelp_meta.py:117` `validate_all` |
| 25 | `services/deployer.py:140` `Deployer.step_08_copy_global_resources_to_target` |
| 24 | `themes/techdoc/logic/theme.py:492` `Theme.build_events` |
| 23 | `services/workflow.py:126` `Workflow.verify_sources` |
| 23 | `services/processor.py:86` `Processor.step_00_extraction` |
| 23 | `services/builder.py:366` `Builder.write_feed` |
| 22 | `themes/blog/logic/theme.py:186` `Theme.build_events` |

`build_events` (techdoc and blog) and `build_datatable` (techdoc `:91`, blog `:34`,
bookshelf `:671`, all rank C) appear in more than one theme: a duplication lead
for Phase 4.

### pip-audit

No known vulnerabilities. pip-audit resolved the newest versions allowed by
`requirements.txt` (only `Mako==1.3.12` is pinned), so this covers a fresh
install, not older versions already installed on a machine or the `pixi.lock`
environment (Phase 5).

### Phase 1 findings

**BASE-01** | Severity: Medium
Location: `kb4it/core/util.py:210-224`
Evidence:
```python
def exec_cmd(data):
    doc, cmd, num = data
    process = subprocess.Popen(
        [cmd], shell=True,
```
Why it matters: a helper that runs an arbitrary string through the shell, with no
caller in the package (only `tests/core/test_util.py:66-67`). It is not exploitable
today, but it is an easy way to add command injection later, and it keeps a bandit
high finding open.
Recommended fix: delete `exec_cmd` and its test; if a command runner is ever
needed, take an argument list and no shell.
Effort: S

**BASE-02** | Severity: Low
Location: `kb4it/core/main.py:67-69`
Evidence:
```python
if "log_level" not in self.params:
    self.params["LOGLEVEL"] = "INFO"
setup_logging(self.params["log_level"], self.log_file)
```
Why it matters: the fallback writes a different key (`LOGLEVEL`) from the one read
(`log_level`), so the fallback can never work; a caller without `log_level` gets a
`KeyError`. Today every caller passes it (`main.py:249` argparse option,
`tui/app.py:322-331`, `tui/app.py:1022-1030`, `core/serve.py:96-98`), so it is
latent.
Recommended fix: set `self.params["log_level"]`, or read with
`self.params.get("log_level", "INFO")`.
Effort: S

**BASE-03** | Severity: Low
Location: `kb4it/core/util.py:210-590`, `kb4it/core/types.py:47`, `kb4it/tui/app.py:172`, plus ruff F401/F841 (28 places, for example `themes/blog/logic/theme.py:189-421`, `services/processor.py:88`)
Evidence: see the vulture table; `themes/blog/logic/theme.py:339-348` assigns
`ecats`, `event_types`, `category` and `title` and never uses them.
Why it matters: dead code hides the real data flow, keeps unused imports alive in
themes and makes reviews slower. Unused locals inside `build_events` may also mean
a half-finished feature.
Recommended fix: remove after confirming which `util` functions themes may use
(Needs verification); run `ruff check --select F401,F841 --fix` for the safe part.
Effort: S

**BASE-04** | Severity: Info
Location: `pyproject.toml` (no `[tool.ruff]`, `[tool.mypy]`); `.github/workflows/kb4it.yml`
Evidence: no lint or type-check step in CI; ruff reports 261 issues and mypy 33.
Why it matters: nothing stops new broad excepts, unused code or type errors.
Recommended fix: add a `[tool.ruff]` section with a chosen rule set (start with
`E,F,B,BLE,S` and grow), fix or baseline the current issues, and run
`ruff check` in CI; add `mypy` later, per package.
Effort: M

**BASE-05** | Severity: Info
Location: 7 functions of rank D, listed above (for example `apphelp_meta.py:117`, `deployer.py:140`)
Evidence: radon complexity 22 to 30.
Why it matters: these are the hardest functions to test and change; three of them
are on the main build path (`processor.py:86`, `deployer.py:140`, `builder.py:366`).
Recommended fix: split when they are next changed, guided by the Phase 2 and 4
findings; no change on its own.
Effort: M

### Phase 1 top 5

| # | ID | Why |
|---|---|---|
| 1 | B702, `services/builder.py:197` | Mako without escaping: the main security question, carried to Phase 3 |
| 2 | BASE-01 | `shell=True` helper with no caller; trivial to remove |
| 3 | Broad excepts (BLE001 45, S110 8), worst in `tui/app.py` | Swallowed errors hide build failures; reviewed one by one in Phase 2 |
| 4 | BASE-04 | No linter or type checker in CI, so the numbers above will grow |
| 5 | BASE-02 and the mypy `None` cases (`env.py:111`, `log.py:46`, `database.py:140`) | Latent crashes; checked for reachability in Phase 2 |

Phase 1 is complete. Stopped here, waiting for your go-ahead before Phase 2.

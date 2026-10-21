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
| 2 Correctness and robustness | Done |
| 3 Security | Done |
| 4 Architecture and maintainability | Done |
| 5 Dependencies and packaging | Done |
| 6 Tests and HTML output quality | Done |

The High and Medium findings were fixed by patches 0080 to 0105 (`responses/KB4IT-0.9-AUDIT-FIX-PLAN.md`); the architecture findings, ARC-01 to ARC-08, by the architecture series, patches 0111 to 0133 (`responses/KB4IT-0.9-ARCHITECTURE-PLAN.md`). Each finding in scope carries a `Status:` line.

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
Status: Fixed in patch 0086 (FS-03).
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


---

## Phase 2: Correctness and robustness

Method: the 45 broad `except` clauses and 9 `except: pass/continue` from Phase 1
were read one by one with their context. Each suspected failure was then
reproduced with throwaway knowledge bases created with `kb4it create` in a scratch
folder outside the repository (`KB4IT_HOME` pointed there too). "Reproduced" below
means the behaviour was observed, with the command outcome quoted.

### Summary

| Area | Result |
|---|---|
| Error handling | Page compile and render failures are logged but never fail the build (COR-01); a template syntax error is hidden (COR-06); several theme `except: pass` blocks (COR-10) |
| Incremental cache | The new cache is saved before compilation, so a failed build leaves stale pages (COR-02); settings shown on every page do not trigger a rebuild (COR-05) |
| File I/O and paths | The target folder is not checked, and the stale-page sweep deletes user files (COR-03); JSON files are not written atomically and a corrupt registry is silently replaced (COR-04); `copydir` builds paths with `str.replace` (COR-11) |
| YAML | `yaml.safe_load` is the only YAML loader (`kb4it/core/util.py:362`); no `yaml.load` anywhere in `kb4it/`. Nested mappings become text (COR-12) |
| Encodings | Every text open passes an encoding; enforced by `tests/core/test_encoding_rule.py`. No finding |
| Concurrency | Worker threads write into shared dictionaries (COR-13); per-repository lock in place |
| Phase 1 leads | `env.py:111`, `log.py:46`: false positives. `database.py:140` returns `None`, but every caller handles it (`database.py:113`, `:279`, `themes/blog/logic/theme.py:80-81`, `:193-195`, `themes/bookshelf/logic/theme.py:143`): typing gap only. BASE-02 stays latent |

### Findings

**COR-01** | Severity: High
Status: Fixed in patch 0080 (BO-01); exit status documented in 0082 (BO-03).
Location: `kb4it/services/compiler.py:208-220`, `kb4it/core/main.py:202`
Evidence:
```python
            if rc is True:
                try:
                    self.srvthm.build_page(path_hdoc)
                ...
                except Exception as error:
                    self.log.error(f"[COMPILER] ERROR {error}")
                    self.print_traceback()
                return x
            else:
                self.log.error(f"[COMPILER] COMPILE_FAILED doc={basename}")
                return x
```
Reproduced: blog sample with `tagline` removed from `repo.json`: 9 `[COMPILER] ERROR 'tagline'` lines, exit status 0, and the summary says `invalid=0`.
Why it matters: a build whose pages failed reports success. CI, the GitHub Action
and scripts publish a broken or partial site; `fail_on_invalid` does not cover it.
Recommended fix: collect failed documents in the `Compiler` (both the `rc is False`
branch and `build_page` exceptions), add them to the summary as `failed=`, and
raise `CompilationError` after the pool finishes, so `KB4IT.run()` returns
`False` and the process exits 1. A failing theme can stay non-fatal under
`kb4it serve` by catching it there.
Effort: M

**COR-02** | Severity: High
Status: Fixed in patch 0081 (BO-02).
Location: `kb4it/services/processor.py:187` (in `step_00_extraction`; saved again at `:301` after analysis), `kb4it/services/backend.py:300-304`
Evidence:
```python
        # Save new kbdict
        self.srvbes.save_kbdict(self.kbdict_new)
```
This runs at the end of extraction (stage 3), before compilation (stage 5) and deployment (stage 7).
Reproduced: techdoc sample with a hook that fails once for `page.md`:
build 1 `rc=0` "Version one"; body changed to "Version two" and build 2 fails
(`rc=1`); build 3 `rc=0`, `compiled=0 skipped=1`, and `target/page.html` still
says "Version one".
Why it matters: after any failed or interrupted build (hook error, crash,
Ctrl+C, full disk), incremental builds keep serving stale pages until someone
runs `--force`, and nothing tells them to.
Recommended fix: write the new `kbdict.json` only after a successful deploy, or
keep the previous hashes for every document that was not compiled and deployed
in this run. Combine with COR-01, so failed documents are never marked done.
Effort: M

**COR-03** | Severity: Medium
Status: Fixed in patches 0083 (target check) and 0084 (owned pages) (FS-01).
Location: `kb4it/services/deployer.py:130-134`, `kb4it/services/backend.py:346-348`
Evidence:
```python
        for filename in os.listdir(dir_target):
            if not filename.endswith('.html'):
                continue
            if filename not in expected:
                os.unlink(os.path.join(dir_target, filename))
```
Reproduced: `"target": "."` (the repository root) with a user file `notes.html`
there: the build exits 0 and `notes.html` is deleted; the root fills with
generated pages, `resources/` and `sources/`.
Why it matters: one wrong `target` value (`.`, the source folder, an existing
web folder) deletes user HTML files without a warning. Stage 1 only creates the
target folder (`backend.py:346-348`); nothing checks it against the repository
root, `source/`, `config/` or the home folder.
Recommended fix: in stage 1, refuse a target that equals or contains the
repository root, the source folder, `config/` or `$HOME`; and limit the stale
sweep to files KB4IT wrote in an earlier build (keep the list in `kbdict.json`).
Effort: M

**COR-04** | Severity: Medium
Status: Fixed in patch 0085 (FS-02).
Location: `kb4it/services/workflow.py:89-94`, `kb4it/core/util.py:301-304`
Evidence:
```python
        if os.path.exists(projects_file):
            try:
                data = json_load(projects_file)
                projects = data.get("projects", [])
            except Exception:
                pass
```
```python
def json_save(filepath: str, adict: dict) -> None:
    with open(filepath, "w", encoding="utf-8") as fout:
        json.dump(adict, fout, sort_keys=True, indent=4)
```
Reproduced: a truncated `projects.json` listing projects A and B, then
`kb4it create techdoc ...`: exit 0, nothing logged, and the file now lists only
the new project.
Why it matters: the project list of the TUI is lost silently. Because `json_save`
truncates the file and then writes, a crash or a full disk during any save can
produce exactly that truncated file; for `kbdict.json` it turns the next builds
into `KBDICT_LOAD_FAIL` errors (`backend.py:294-296`) until `--force`.
Recommended fix: write JSON atomically (temporary file in the same folder, then
`os.replace`). On a parse error of `projects.json`, log it, keep a copy
(`projects.json.bak`) and do not overwrite it. On a corrupt `kbdict.json`,
rebuild from scratch with a warning instead of failing.
Effort: S

**COR-05** | Severity: Medium
Status: Fixed in patch 0087 (OC-01).
Location: `kb4it/services/processor.py:190-198`, `kb4it/services/builder.py:135-140`
Evidence:
```python
        return {"markdown": repo.get("markdown") or {}, "search": repo.get("search", True),
                "site_url": repo.get("site_url"), "og_image": repo.get("og_image"), "feed": repo.get("feed"),
                "overrides": ..., "hooks": ..., "backlinks": repo.get("backlinks", True)}
```
and the default `site_signature()` returns `""`; only apphelp overrides it.
Reproduced: techdoc sample, build with `"title": "Old Site Name"`, change it to
"New Site Name", build again: `index.html` has the new name 6 times,
`page.html` keeps the old name (2 times, 0 for the new one).
Why it matters: a change to `title`, `tagline`, `logo` or any theme option in
`repo.json` leaves every unchanged document page with the old header in
techdoc, blog and bookshelf, until `--force`.
Recommended fix: hash the whole `repo.json` (minus keys that do not reach pages,
such as `workers` and `force`) into `signature_parts()`, or give each theme a
`site_signature()` that covers the keys its templates read.
Effort: S

**COR-06** | Severity: Medium
Status: Fixed in patch 0088 (OC-02).
Location: `kb4it/services/builder.py:195-207`
Evidence:
```python
            for template_path in candidates:
                try:
                    tpl = Template(filename=template_path)
                    ...
                    return tpl
                except Exception as err:
                    self.log.debug(f"[BUILDER] TEMPLATE_CANDIDATE_SKIP path={template_path} reason={err}")
                    continue
            self.log.error(f"[BUILDER] TEMPLATE_NOT_FOUND name={template}")
```
Why it matters: the same `except` covers "file does not exist" (the normal case
for override and theme candidates) and "Mako syntax error". A syntax error in an
`overrides/` template is logged at DEBUG only, and the theme's template is used
instead, so the user's change silently does nothing. A syntax error in a theme
template ends as "Template not found", which points the wrong way. Behaviour
derived from the code; Needs verification with a deliberately broken override.
Recommended fix: skip candidates with `os.path.exists()`, and let a
`mako.exceptions.SyntaxException` (or any compile error) raise `ThemeError` with
the file and line.
Effort: S

**COR-07** | Severity: Medium
Status: Fixed in patch 0089 (OC-03).
Location: `kb4it/core/util.py:368`
Evidence:
```python
        title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
```
Reproduced: a document with a fenced `bash` block containing `# install the tool`
before its `# Real title` heading gets the title `install the tool`.
Why it matters: shell, Python and YAML comments inside code blocks are common in
technical documents; the wrong title appears in navigation, indexes, search
and the feed.
Recommended fix: ignore lines inside fenced code blocks (track ```` ``` ```` and
`~~~` fences) when looking for the first H1, or take the title from
python-markdown's `toc_tokens` after conversion.
Effort: S

**COR-08** | Severity: Medium
Status: Fixed in patch 0090 (OC-04).
Location: `kb4it/resources/themes/blog/logic/theme.py:169`
Evidence:
```python
            timestamp = var['post'][sort_by][0]
```
Reproduced: blog sample plus one post without `Date`: exit 1, and the only message
is `Error: 'Date'` (from `kb4it/core/main.py:369-370`); traceback
`build_page_index` -> `KeyError: 'Date'`.
Why it matters: one post stops the whole blog, and the message names neither the
document nor the cause. `Date` is documented as optional elsewhere, and
`get_doc_timestamp` already returns `None` for it.
Recommended fix: skip or sort undated posts last (`var['post'].get(sort_by)`), and
report them with a `DOC_*` warning; in `main.py:369` print the exception type
and suggest the log file.
Effort: S

**COR-09** | Severity: Low
Status: Fixed in patch 0080 (BO-01).
Location: `kb4it/services/deployer.py:125-128`
Evidence:
```python
            except FileNotFoundError as error:
                self.log.error(f"[DEPLOYER] ERROR {error}")
                self.log.error("[DEPLOYER] HINT rerun with -force")
                return
```
Why it matters: when one compiled page is missing from the cache (the usual
result of COR-01 or COR-02), the deploy stops copying the remaining pages and
skips the stale sweep, but the build still exits 0. The hint also names a flag
that does not exist (`-force` instead of `--force`).
Recommended fix: copy every other page, collect the missing ones, and fail the
build with their names; fix the hint text.
Effort: S

**COR-10** | Severity: Low
Location: `kb4it/resources/themes/blog/logic/theme.py:665-674`, `:690-693`; `themes/techdoc/logic/theme.py:945-948`; `themes/bookshelf/logic/theme.py:494-497`; `kb4it/tui/app.py:94-97`, `:159-162`, `:236-239`
Evidence (blog, `:690-693`):
```python
        except Exception:
            BODY = HTML_BODY.render(var=var)
```
Why it matters: when the post template fails, the blog silently renders the page
with a different template, and the error is never logged. The other places drop
an error with `pass` (page title, theme list, notifications). The remaining
broad excepts (in `tui/app.py`, `frontend.py`, `workflow.py:113`,
`processor.py:219`) log the error and are acceptable at a UI or per-item
boundary.
Recommended fix: log every swallowed exception at WARNING with the document id;
in the blog, let a template error reach COR-01's failure path.
Effort: S

**COR-11** | Severity: Low
Location: `kb4it/core/util.py:189`, `kb4it/core/util.py:270-274`
Evidence:
```python
            rel_path = root.replace(source, "").lstrip(os.sep)
```
```python
                if os.path.isfile(file_object_path):
                    os.unlink(file_object_path)
                else:
                    shutil.rmtree(file_object_path)
```
Why it matters: `str.replace` removes every occurrence of the source path, not
only the prefix, so a path that repeats it (or a source given with a trailing
separator) lands in the wrong folder. In `delete_target_contents`, a symbolic
link to a folder is not a file, and `shutil.rmtree` refuses symbolic links with
`OSError`, which stops the build. Both derived from the code; Needs verification
for a real layout that triggers them.
Recommended fix: `os.path.relpath(root, source)`; unlink symbolic links
(`os.path.islink`) before the file/folder test.
Effort: S

**COR-12** | Severity: Low
Location: `kb4it/core/util.py:380-388`
Evidence:
```python
            else:
                keys[k] = [str(v).strip()]
```
Reproduced: `Meta: {a: 1}` in frontmatter becomes the property value `"{'a': 1}"`,
and `Author: Virseda, Tomas` becomes two authors.
Why it matters: nested YAML produces Python-repr text on pages and odd property
pages; the comma rule is documented, but surprising for names.
Recommended fix: report nested mappings as `DOC_INVALID reason=nested_mapping`
(or a warning) instead of stringifying them; document how to keep a comma inside
a value (a YAML list).
Effort: S

**COR-13** | Severity: Low
Location: `kb4it/services/builder.py:221-237`, `kb4it/services/database.py:218-222`, `kb4it/services/compiler.py:110`
Evidence:
```python
        theme_var["repo"] = self.srvbes.get_dict("repo")
        ...
        theme_var["kb"]["keys"] = self.srvdtb.get_keys()
        theme_var["repo"]["updated"] = get_human_datetime(datetime.now())
        ...
        theme_var["kb"]["keys"]["menu"] = sorted(...)
```
`get_dict("repo")` and `get_keys()` return the shared objects, and
`get_theme_var()` runs from `compilation_finished`, a future callback that
executes in the worker threads.
Why it matters: every worker writes into the repository settings and the
database's key cache at the same time. The values written are the same today,
so no wrong output was seen, but any per-page value put there later would leak
between pages. Needs verification under load.
Recommended fix: build `theme_var["repo"]` and `theme_var["kb"]["keys"]` as
copies (`dict(...)`) inside `get_theme_var`.
Effort: S

**COR-14** | Severity: Low
Location: `kb4it/core/publish.py:69-73`
Evidence:
```python
def atom_date(value) -> str:
    """'2026-10-08' or '2026-10-08 14:30:00' as an Atom timestamp (UTC)."""
    text = str(value).strip().replace("T", " ")
    date, _, time = text.partition(" ")
    return f"{date}T{(time or '00:00:00')[:8]}Z"
```
Why it matters: a local time is labelled UTC (`Z`), and a `Date` with an offset
(`2026-10-08T14:30:00+02:00`) loses the offset, so feed readers show posts hours
off.
Recommended fix: keep a given offset; for naive values, either take a `timezone`
from `repo.json` or write the local offset.
Effort: S

### Phase 2 top 5

| # | ID | Why |
|---|---|---|
| 1 | COR-01 | Failed pages exit 0: CI and the GitHub Action publish broken sites |
| 2 | COR-02 | A failed build leaves pages stale for good, with nothing pointing to `--force` |
| 3 | COR-03 | A wrong `target` deletes user HTML files |
| 4 | COR-04 | Non-atomic JSON writes and a silently replaced project registry |
| 5 | COR-05 and COR-07 | Stale headers after a settings change, and wrong titles from code-block comments: both visible on real sites |


---

## Phase 3: Security

Threat model used: the person who runs `kb4it build` trusts `repo.json`, the
theme and any hooks (they are code they chose to run). Document content
(frontmatter and Markdown) may come from other people: several authors, merged
pull requests, imported notes. Readers of the generated site are the victims of
anything that runs in their browser. Payloads were tested by building throwaway
sites in a scratch folder with the bundled themes; "Reproduced" quotes the
generated HTML.

### Summary

| Area | Result |
|---|---|
| Mako autoescaping | No default filter (`Template(filename=...)` at `kb4it/services/builder.py:197`). apphelp escapes 100 of 115 expressions with `\| h`; techdoc 0 of 219, blog 0 of 202, bookshelf 0 of 170; common templates 11 of 19. No `\| n` anywhere, because nothing is escaped by default (SEC-01) |
| Markdown raw HTML | Passed through: `<script>`, `on*=` attributes and `javascript:` links reach the page (SEC-02) |
| Path traversal from properties | Not possible: `valid_filename` (`kb4it/core/util.py:444-456`) removes `/` and `\`; a property named `../../escaped` produced `....escaped`, and no file was written outside the target. But a name starting with a dot empties the site (SEC-03) |
| subprocess / shell | One `shell=True`, in unused `exec_cmd` (BASE-01). Other calls use argument lists: `core/version.py:39`, `tui/app.py:204`. The generated `compile.sh` quotes the path with `shlex.quote` (`kb4it/services/workflow.py:36`) |
| Untrusted YAML | `yaml.safe_load` only (`kb4it/core/util.py:362`): no object construction. Alias expansion is not limited (SEC-07) |
| Code execution by design | Hooks and theme logic are Python run in-process (SEC-04) |
| Escaped correctly | `HTML_HEAD_META.tpl` (`\| h` on every user value), Atom feed and sitemap (`xml.sax.saxutils.escape`, `kb4it/core/publish.py:40-95`), search results (`textContent` only, `kb4it/resources/common/js/kb4it-search-ui.js:15`), search index (JSON in a separate `.js` file, `kb4it/core/search.py:70-73`), the source viewer (`&lt;` in `xss.html`), and the GitHub Action (inputs reach scripts through `env:`, never `${{ }}` inside `run:`, `action.yml`) |
| Local web server | Standard library handler with its path normalisation; binds `127.0.0.1` by default and warns for other hosts (SEC-08) |

### Findings

**SEC-01** | Severity: High
Status: Fixed in patches 0094 (switch, common templates) and 0095 to 0098 (apphelp, techdoc, blog, bookshelf) (SC-01).
Location: `kb4it/services/builder.py:197`; for example `kb4it/resources/themes/techdoc/templates/METADATA_VALUE_LINK.tpl:1`
Evidence:
```python
                    tpl = Template(filename=template_path)
```
```mako
<a class="kb-meta-val" href="${var['link_url']}">${var['link_name']}</a>
```
Reproduced (techdoc, `target/xss.html` and `target/Author.html`), from the frontmatter
`Tag: <script>alert("tag")</script>` and `Author: Eve" onmouseover="alert(1)`:
```html
<a class="kb-meta-val" href="Tag_scriptalerttagscript.html"><script>alert("tag")</script></a>
<span class="kb-cloud-word">Eve" onmouseover="alert(1)</span>
```
The same payloads appear unescaped in 7 pages of techdoc, 13 of blog and 10 of
bookshelf (document page, `properties.html`, key and key/value pages, blog
index and event pages). In blog, the title lands inside an attribute:
`<div uk-tooltip="Title <svg onload=alert("title")>">`.
Why it matters: anyone who can add or edit one document can run script in the
browser of every reader, on every page that lists that property. Static sites
are often hosted on a shared origin (GitHub Pages `user.github.io`), so the
script runs with that origin's rights.
Recommended fix: compile templates with escaping on by default, through one
`TemplateLookup(..., default_filters=["h"])` (or `["str", "h"]`) shared by
`Builder.template`, and mark the expressions that carry ready-made HTML (page
bodies, rendered fragments) with `| n`. Then review the 591 expressions of
techdoc, blog and bookshelf; apphelp shows the target state. Add a test that
builds every theme with an HTML payload in each property and title and fails on
raw `<script>`.
Effort: L

**SEC-02** | Severity: Medium
Status: Fixed in patch 0099: trust model documented, optional `markdown.sanitize` with nh3, `DOC_RAW_SCRIPT` in verify (SC-02).
Location: `kb4it/core/mdconfig.py:51-52`
Evidence:
```python
    def new_markdown(self):
        return markdown.Markdown(extensions=self.all_extensions(), extension_configs=self.all_configs())
```
Reproduced (techdoc, `target/dot.html`): the body lines `[raw](javascript:alert(1))`,
`<script>alert("body")</script>` and `<div onclick="alert(2)">x</div>` appear
unchanged as `href="javascript:alert(1)"`, `<script>alert("body")</script>` and
`<div onclick="alert(2)">`.
Why it matters: python-markdown passes raw HTML by design, and for a single
author it is a feature (the help documents embedding Mermaid this way). For a
knowledge base with several contributors it is the same stored XSS as SEC-01,
and the documentation does not say so.
Recommended fix: document the trust model in the help ("documents can contain
HTML and scripts; review contributions"). Optionally add `"markdown":
{"sanitize": true}` that cleans the compiled HTML with an allow-list (for
example `nh3`, a binary wheel with no Node, or `lxml_html_clean`, which is no
longer part of lxml), off by default for compatibility. Always drop
`javascript:` URLs from links generated by KB4IT itself.
Effort: M

**SEC-03** | Severity: Medium
Status: Fixed in patch 0093 (SC-03).
Location: `kb4it/services/processor.py:468`, `kb4it/core/util.py:202-207`, `kb4it/services/deployer.py:125-128`
Evidence:
```python
            docId = f"{valid_filename(key)}.md"
```
```python
    for ext in ("*.md", "*.markdown"):
        docs.extend(glob.glob(os.path.join(path, ext)))
```
Reproduced: one document with the frontmatter key `.note: a` (or `../../escaped: a`,
which becomes `....escaped`): the build exits 0, `target/index.html` does not
exist, and the log ends with `[DEPLOYER] ERROR [Errno 2] No such file or
directory: '.../var/cache/....escaped.html'`.
Why it matters: the key page gets a name starting with a dot; `glob` skips hidden
files, so the page is never compiled; the deployer stops at the missing file
(COR-09), so no page reaches the target, and the build still reports success
(COR-01). A single crafted or mistyped property name takes the published site
down.
Recommended fix: make `valid_filename` strip leading dots and return a fallback
for empty results, or reject property names without a letter or digit as
`DOC_INVALID`; fixing COR-01 and COR-09 turns the remaining cases into a visible
failure.
Effort: S

**SEC-04** | Severity: Low
Location: `kb4it/core/hooks.py:43-50`, `action.yml` (no option to disable hooks), `help/source/reference-github-action.md`
Evidence:
```python
        spec = importlib.util.spec_from_file_location(f"kb4it_repo_hooks_{digest}", path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
```
Why it matters: building a repository runs its `hooks` file and the Python logic of
its theme (`theme_path` or a user theme). `help/source/howto-hooks.md:18` warns
about hooks; the GitHub Action reference does not. A workflow that builds pull
requests runs code from the pull request. On `pull_request` from a fork GitHub
gives a read-only token and no secrets, which limits the damage, but
`pull_request_target` or self-hosted runners would not.
Recommended fix: add a sentence to the action reference and to "Publish on GitHub
Pages"; add a `--no-hooks` option (and a `hooks` input to the action) for
building untrusted changes.
Effort: S

**SEC-05** | Severity: Low
Location: `kb4it/core/util.py:210-224`
Evidence: `subprocess.Popen([cmd], shell=True, ...)` (see BASE-01).
Why it matters: the only shell invocation in the package; unused, so not
reachable today.
Recommended fix: delete it (BASE-01).
Effort: S

**SEC-06** | Severity: Low
Location: `kb4it/core/publish.py:81`, `:85-86`, `:93`, `:95`
Evidence:
```python
           f'<feed xmlns="http://www.w3.org/2005/Atom" xml:base="{escape(base)}">',
                f'    <link href="{escape(e["url"])}"/>',
                f"    <updated>{e['updated']}</updated>"]
```
Why it matters: `xml.sax.saxutils.escape` does not escape `"`, so a `site_url`
or document URL containing `"` breaks out of the attribute; and `<updated>` is
written from the document's `Date` without escaping. `site_url` comes from
`repo.json` (trusted) and URLs are built from sanitised file names, so the
practical risk is a malformed feed. Whether a crafted `Date` reaches
`<updated>` unchanged depends on `string_timestamp` (`kb4it/services/processor.py:124`):
Needs verification.
Recommended fix: use `xml.sax.saxutils.quoteattr` for attribute values and
`escape` for `<updated>`, or build the feed with `xml.etree.ElementTree`.
Effort: S

**SEC-07** | Severity: Low
Location: `kb4it/core/util.py:362`
Evidence:
```python
        fm = yaml.safe_load(fm_text) if fm_text else {}
```
Why it matters: `safe_load` constructs no objects, but it still expands YAML
aliases, so a few hundred bytes of nested anchors ("billion laughs") can use a
large amount of memory and time while parsing one document. This matters only
for documents from untrusted sources. Not reproduced; Needs verification of the
actual cost with the installed PyYAML.
Recommended fix: reject frontmatter that contains anchors or aliases (`&`, `*`
tokens), or cap the frontmatter size (for example 64 KB) before parsing.
Effort: S

**SEC-08** | Severity: Info
Location: `kb4it/core/webserver.py:104-107`, `kb4it/core/serve.py:152-154`
Evidence:
```python
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)
```
Why it matters: the preview server relies on the standard library for path
handling (it normalises `..`), binds to `127.0.0.1` unless `--host` is given,
and warns for other addresses. It also lists folder contents and follows
symbolic links inside the target, which is acceptable for a local preview.
Recommended fix: none needed; keep the warning, and mention in the `serve` help
that `--host 0.0.0.0` exposes the site without authentication.
Effort: S

### Phase 3 top 5

| # | ID | Why |
|---|---|---|
| 1 | SEC-01 | Stored XSS from any frontmatter value or title, on every page that lists it, in three of four themes |
| 2 | SEC-02 | Raw HTML and scripts in Markdown, undocumented as a trust decision |
| 3 | SEC-03 | One property name empties the published site while the build reports success |
| 4 | SEC-04 | Hooks and theme code run during CI builds of pull requests; undocumented in the action |
| 5 | SEC-06 and SEC-07 | Feed attribute escaping and YAML alias expansion: small fixes that close the remaining input paths |


---

## Phase 4: Architecture and maintainability

Method: service dependencies were taken from `get_service("...")` calls; the import
graph and class sizes from an `ast` walk of `kb4it/`; theme duplication by comparing
methods of the same name across the four `theme.py` files with `difflib`
(similarity ratio) and templates by SHA-256; template use by searching every
`.py` and `.tpl` for each template name (including the transformation names built
with f-strings in `builder.py`).

### Summary

| Area | Result |
|---|---|
| Coupling | Service locator; Backend is a hub with two-way links to six services (ARC-03) |
| Circular imports | None at module level. 22 imports inside functions; three of them make `core` depend on `services` (ARC-04) |
| God classes | techdoc `Theme` 1,187 lines / 40 methods; blog `Theme` 926 / 27; bookshelf 681 / 33; `Builder` 467 / 36; `tui/app.py` 1,449 lines (ARC-02) |
| Duplicated logic | 19 methods exist in three or more themes; several pairs are 93 to 100% identical; 51 duplicate template files (ARC-01) |
| Dead code | 62 bundled templates never referenced; 12 of 24 page transformations can never match (ARC-05); dead functions in BASE-03 |
| Type hints | 39% of functions (251 of 632) carry any annotation; 25% of parameters (132 of 525) (ARC-07) |
| Config sprawl | Contained: 40 `repo.json` keys read, all documented in `help/source/reference-repo-json.md` except the runtime `updated` (COR-13) and apphelp's `version` (documented in its theme reference). Global `ENV` dict: 95 references, read-mostly |
| Testability | 316 test functions; `KB4IT_HOME` isolates per-user files; services can only be tested through a full `KB4IT` app (ARC-03); module-level state (ARC-06) |

Service dependencies (`get_service` calls):

| Service | Asks for |
|---|---|
| Backend (`services/backend.py`) | Builder, Compiler, Deployer, Frontend, Processor, Theme |
| Processor | Backend, DB, Theme |
| Compiler | Backend, DB, Processor, Theme |
| Builder (and every Theme) | Backend, DB |
| Deployer | Backend, Theme |
| Frontend | Backend, Theme |
| Workflow | Backend, Frontend, Theme |
| Database | Backend |

### Findings

**ARC-01** | Severity: Medium
Status: Fixed in patches 0115 to 0122 (AR-01): `DocumentTheme` in `kb4it/services/themekit/` and the `uikit` template base.
Location: `kb4it/resources/themes/blog/logic/theme.py` and `kb4it/resources/themes/techdoc/logic/theme.py` (pairs below); templates under `kb4it/resources/themes/*/templates/`
Evidence (similarity of same-named methods):

| Method | Lines | Similarity | Locations |
|---|---|---|---|
| `get_labels` | 11 | 100% | blog `:828`, techdoc `:1060` |
| `get_html_values_from_key` | 9 | 100% | blog `:840`, techdoc `:1072` |
| `extract_toc` | 31 | 97% | bookshelf `:636`, techdoc `:855` |
| `build_metadata_section` | 25 | 96% | blog `:850`, techdoc `:1082` |
| `build_events` | 132 | 95% | blog `:186`, techdoc `:492` |
| `build_page_key` | 24 | 95% | blog `:704`, techdoc `:972` |
| `build_page_key_value` | 26 | 93% | blog `:729`, techdoc `:999` |
| `build_datatable` | 84 | 81% | blog `:34`, techdoc `:91` (and bookshelf `:671`) |

19 methods appear in three or more themes (`build_page`, `build_page_key`,
`build_page_key_value`, `build_page_properties`, `build_page_stats`,
`build_datatable`, `build_tagcloud_from_key`, `extract_toc`, `get_labels`, and 10
more). Templates: 47 groups of byte-identical `.tpl` files, 51 redundant copies.
Why it matters: every fix must be made two or three times. The Phase 2 and 3
findings show it: COR-08 (blog only, but `build_events` is shared logic), SEC-01
(the same unescaped templates in three themes).
Recommended fix: move the shared methods into `Builder` (or a mixin such as
`services/themekit.py`) and keep only real differences in each theme; move
identical templates to `resources/common/templates/`, which
`_template_candidates` already falls back to. Do it after SEC-01, so escaping is
fixed once.
Effort: L

**ARC-02** | Severity: Medium
Status: Fixed in patches 0123 to 0125 (AR-02): no module over 600 lines, enforced by a test.
Location: `kb4it/resources/themes/techdoc/logic/theme.py:82`, `kb4it/resources/themes/blog/logic/theme.py:24`, `kb4it/resources/themes/bookshelf/logic/theme.py:80`, `kb4it/services/builder.py:67`, `kb4it/tui/app.py`
Evidence: class sizes from `ast`: techdoc `Theme` 1,187 lines and 40 methods,
blog `Theme` 926 and 27, bookshelf `Theme` 681 and 33, `Builder` 467 and 36;
`tui/app.py` is one 1,449-line module with 15 screen and widget classes. Five
of the seven rank-D functions of Phase 1 live in these classes.
Why it matters: each theme class mixes page assembly, the events calendar,
datatables, tag clouds and statistics; changes need a full build to test, and
reviews of one feature drag in the whole file.
Recommended fix: after ARC-01, split by concern (calendar, tables, page
builders) into small modules; split `tui/app.py` into one module per screen.
Effort: L

**ARC-03** | Severity: Medium
Status: Fixed in patches 0129 and 0130 (AR-03): `backend.pipeline`; the old lookups are deprecated until 0.10.0.
Location: `kb4it/core/service.py:82`, `kb4it/services/backend.py:315`, `:447`, `:454`, `kb4it/services/frontend.py:163`
Evidence:
```python
    def get_services(self):
        """Get services needed."""
        self.srvbld = self.get_service("Builder")
        self.app.register_service("Processor", Processor())
```
(`backend.py:312-315`), and the table above.
Why it matters: any service can reach any other by name, Backend both owns and
depends on the pipeline services, and four services are registered in the
middle of a build. The order in which things exist is implicit, and no service
can be tested without a whole `KB4IT` app; the tests in `tests/` drive full
builds through subprocesses or the controller for that reason.
Recommended fix: keep the registry for application-level services (Backend, DB,
Workflow), but pass the pipeline's collaborators explicitly
(`Processor(backend, db, theme)`, `Compiler(...)`), created once in stage 1;
document the lifecycle in `AGENTS.md`.
Effort: L

**ARC-04** | Severity: Low
Status: Fixed in patch 0083 (`kb4it/core/paths.py`); `core` imports services only in `main.py`, the controller.
Location: `kb4it/core/hooks.py:76`, `kb4it/core/serve.py:43`, `:51`, `kb4it/services/backend.py:38`
Evidence:
```python
def load_hooks(repo: dict, root) -> Hooks:
    from kb4it.services.backend import resolve_repo_path
```
Why it matters: `core` is the lower layer, but two `core` modules import a
service module (inside functions, to avoid a cycle) only to reach a pure path
helper. It invites real cycles later.
Recommended fix: move `resolve_repo_path` to `kb4it/core/util.py` (or a new
`core/paths.py`) and import it from there everywhere.
Effort: S

**ARC-05** | Severity: Low
Status: Fixed in patches 0100 (`HTML_TAG_A`), 0112 (13 transformation pairs) and 0113 (63 templates) (AR-04).
Location: `kb4it/services/builder.py:74-87`, `:117-120`; `kb4it/resources/common/templates/HTML_TAG_*_MD.tpl`; `kb4it/services/compiler.py:251-295`
Evidence:
```python
        for old, new in self._xform_pairs:
            if old:
                content = content.replace(old, new)
```
Of the 24 transformation sources, 12 are Asciidoctor markup that python-markdown
never produces: `HTML_TAG_PRE_MD` is `<pre class="CodeRay highlight">`,
`HTML_TAG_TABLE_MD` is `<table class="tableblock frame-all grid-all spread">`,
the five `HTML_TAG_ADMONITION_*_MD` are `<div class="admonitionblock ...`, and
the five `HTML_TAG_ADMONITION_ICON_*_MD` are `<i class="fa icon-...`.
python-markdown 3 emits `<pre><code>`, `<table>` and `<div class="admonition note">`
(checked with `extra` and `admonition`). Separately, 62 bundled templates are
never referenced by name: techdoc 16 (for example `EVENTCAL_TABLE_YEAR`,
`TABLE_EVENT`), blog 45 (for example `CARD_DOC`, `PAGINATION_PAGE_ACTIVE`,
`TIMELINEJS`, `HTML_TAG_TABLE_OLD_2`), bookshelf 1. No `<%include>`,
`<%namespace>` or `<%inherit>` exists in any template.
Why it matters: dead templates and transformations make the themes look bigger
and more fragile than they are, and every page pays 24 string replacements. The
compiler also rewrites python-markdown output into AsciiDoc-style
`sect1`/`sectionbody` blocks (`compiler.py:251-295`) only to keep the old
transformations and CSS working: legacy coupling between the compiler and the
themes. Whether a custom theme or override relies on these names is Needs
verification.
Recommended fix: remove the 12 dead pairs and the unreferenced templates, checking
the output with `scripts/devel/theme_snapshot.py` before and after; in the long
run, style python-markdown's own markup with CSS instead of string replacement.
Effort: M

**ARC-06** | Severity: Low
Status: Fixed in patches 0126 to 0128 (AR-05).
Location: `kb4it/services/builder.py:70`, `kb4it/services/compiler.py:28-53`, `kb4it/services/backend.py:290`
Evidence:
```python
class Builder(Service):
    theme_var = {}
```
```python
_progress_callback = None
_compile_start_callback = None
```
```python
                self.params["force"] = True
```
Why it matters: a class-level dict shared by every `Builder` and theme instance,
module-level callbacks set by the TUI that every later build in the same process
sees, and runtime decisions written back into the parameters and settings (also
`repo["updated"]`, COR-13). Builds in one process (the TUI, `kb4it serve`) can
leak state into each other.
Recommended fix: make `theme_var` an instance attribute, pass callbacks through
the `KB4IT` parameters or the `Compiler` constructor, and keep runtime flags in
the runtime dict, not in `params` or `repo`.
Effort: S

**ARC-07** | Severity: Low
Status: In part, as scoped by AR-06: patch 0131 annotates the seams, which pass `mypy --strict` in CI; the rest of the package is not annotated.
Location: whole package; for example `kb4it/services/database.py` (10 mypy errors, Phase 1)
Evidence: 251 of 632 functions (39%) have any annotation; 132 of 525
parameters (25%); no mypy step in CI (BASE-04).
Why it matters: the service-locator design (ARC-03) hides types already; without
annotations, tools cannot follow a value from `get_service` to its use.
Recommended fix: annotate `core/` and the public methods of `services/` first,
with typed returns for `get_service` (overloads or a typed registry), and run
mypy on those packages in CI.
Effort: M

**ARC-08** | Severity: Info
Status: Fixed in patch 0114 (AR-07).
Location: `index.html` (repository root), `pypi/README.rst`, `tests/conftest.py:8`
Evidence: `index.html` is a redirect to `https://t00m.github.io/KB4IT/demo/index.html`,
last changed in `d0e2862`; GitHub Pages is now published by
`.github/workflows/help.yml` with "GitHub Actions" as the source, so the file is
not served. `pypi/README.rst` is not referenced (`pyproject.toml:7` uses
`readme = "README.md"`). The comment at `tests/conftest.py:8` says
`kb4it.core.env` creates its folder at import time; `core/env.py` no longer calls
`makedirs` (folders are created by `KB4IT.__setup_environment`, `core/main.py:100-104`).
Why it matters: leftovers mislead contributors and reviewers.
Recommended fix: delete `index.html` and `pypi/` after confirming nothing external
links to them; update the comment.
Effort: S

### Phase 4 top 5

| # | ID | Why |
|---|---|---|
| 1 | ARC-01 | Duplicated theme code: every fix (SEC-01, COR-08) has to be made two or three times |
| 2 | ARC-03 | Service locator and hub: hard to test and to reason about build order |
| 3 | ARC-05 | 62 dead templates and 12 transformations that never match: cheap to remove with the snapshot tool |
| 4 | ARC-02 | God classes in the themes and the TUI, to split after ARC-01 |
| 5 | ARC-04 and ARC-06 | Small, safe fixes: move the path helper down, remove shared class and module state |


---

## Phase 5: Dependencies and packaging

Method: third-party imports found with an `ast` walk of `kb4it/` and compared with
`pyproject.toml:44-56` and `requirements.txt:1-7`; resolved versions taken from a
fresh `uv` environment built from `requirements.txt` (the same resolution
`scripts/devel/test.sh` uses); the wheel `dist/kb4it-0.8.0-py3-none-any.whl` built
from this tree in Phase 1 was listed with `zipfile`; built sites from the Phase 3
tests were measured with `du`.

### Summary

| Area | Result |
|---|---|
| Declared vs used | All 7 runtime dependencies are imported: `mako` (`core/env.py`, `services/builder.py`), `markdown`, `yaml`, `pygments`, `lxml`, `rich`, `textual`. Nothing undeclared (the `theme` import in `services/frontend.py` is the theme module loaded at runtime). `pymdown-extensions` is an optional extra and is only loaded by name through `markdown.extensions` |
| pyproject vs requirements.txt | Identical (enforced by `tests/core/test_requirements.py`). Two more copies are not checked (DEP-02) |
| Pins | `Mako==1.3.12` exact (kept current by Dependabot, commit `34dbf8b`); `lxml` unbounded; the rest lower bounds only, no upper bounds (DEP-03) |
| Resolved today | Mako 1.3.12, Markdown 3.11.1, PyYAML 6.0.3, Pygments 2.21.0, lxml 6.1.3, rich 15.0.0, textual 8.2.8, pymdown-extensions 12.2; the full suite passes with them (Phase 2 runs) |
| Node toolchain | None in the build: no `node_modules`, no bundler config, no `.ts` sources. The wheel and every built site carry vendored, pre-built JavaScript, including four `package.json` files and two `.map` files (DEP-04) |
| Licences | Project: GPL-3.0-or-later, consistent in `pyproject.toml:6`, `:19` and `LICENSE`. Vendored: UIkit 3.21.13 (MIT, header in each file), DataTables 1.11.3 (MIT, header), jQuery 3.5.1 (MIT, header), Highlight.js 11.11.1 (BSD-3-Clause, `LICENSE` file). TimelineJS refers to a licence file that is not shipped (DEP-05) |
| Python versions | `python = ">=3.11,<4.0"` (`pyproject.toml:45`); classifiers 3.11 to 3.14; CI runs 3.11, 3.13 and 3.14 on three systems. 3.12 is not in the CI matrix (DEP-07) |
| Third dependency source | `pixi.toml` and `pixi.lock` are stale and unused (DEP-01) |
| Build backend | `poetry-core>=1.5.0` with metadata in `[tool.poetry]` (`pyproject.toml:1-63`). It works today (wheel built in Phase 1); see DEP-06 |

### Findings

**DEP-01** | Severity: Low
Location: `pixi.lock:100-104`, `pixi.toml:14-24`
Evidence:
```yaml
  name: kb4it
  version: 0.7.20+build.18
  sha256: caea46b923a9e2fa07193c81cdc62e3440a96c5609eb06d614249961bf1359d9
  requires_python: '>=3.12'
  editable: true
```
```toml
[tasks]
check = "kb4it --version"
build = "python -m build"
```
Why it matters: the lock was last changed on 2025-12-20 (`5bcf187`), records
KB4IT 0.7.20 with `requires_python >=3.12` (the project says `>=3.11`), and holds
no entry for any runtime dependency (only 2 `pypi:` lines). The `build` task needs
the `build` package, which is not declared. No workflow, README or help page uses
pixi, so it is a third dependency source that nobody checks.
Recommended fix: remove `pixi.toml` and `pixi.lock`, or regenerate the lock, add
`build` to it and test `pixi run check` in CI.
Effort: S

**DEP-02** | Severity: Low
Location: `scripts/devel/test.sh:12-13`, `scripts/devel/check_themes.sh:6-7`
Evidence:
```bash
    --with pytest --with "Mako==1.3.12" --with "Markdown>=3.5" --with "PyYAML>=6.0" --with "Pygments>=2.15" \
    --with lxml --with "rich>=13.0" --with "textual>=0.47.0" \
```
Why it matters: the dependency list exists four times. `tests/core/test_requirements.py`
keeps `requirements.txt` equal to `pyproject.toml`, but not these two scripts. The
last Mako bump (`34dbf8b`) changed `requirements.txt` and `setup.py` only: when
the next bump lands, the tests and the theme check will keep running the old
version without anyone noticing.
Recommended fix: use `uv run --no-project --with-requirements requirements.txt`
in both scripts (as the GitHub Action steps already do), or extend
`test_requirements.py` to read them.
Effort: S

**DEP-03** | Severity: Low
Location: `pyproject.toml:46-52`, `requirements.txt:1-7`
Evidence:
```toml
Mako = "1.3.12"
lxml = "*"
rich = ">=13.0"
textual = ">=0.47.0"
```
Why it matters: lower bounds only mean a new major version of `textual` (8.x
today, from 0.47 when the bound was written) or `Markdown` can break the TUI or
the compiler on a fresh install with no code change; the exact Mako pin makes
KB4IT hard to install next to other packages in one environment. For an
application installed with uv, pipx or the Linux packages, the risk is the
first one.
Recommended fix: keep lower bounds, add tested upper bounds on the next major
(`textual>=0.47,<9`, `Markdown>=3.5,<4`, `lxml>=5,<7`), relax Mako to
`>=1.3.12,<2`, and let Dependabot raise them; or publish a constraints file used
by CI and the packages.
Effort: S

**DEP-04** | Severity: Low
Location: `kb4it/resources/themes/techdoc/framework/Highlight/package.json:2`, `kb4it/resources/themes/techdoc/templates/HTML_HEADER_COMMON.tpl`, `kb4it/services/deployer.py:140-209`
Evidence: the templates load only `Highlight/highlight.js` and
`Highlight/styles/github-dark.css` (2 references each), but each of techdoc and
blog ships the whole Highlight.js CDN package (6.4 MB): the `es/` module build
(2.1 MB, with its own `package.json`), `languages/` (1.5 MB), `highlight.min.js`
and every style. The wheel is 15.9 MB uncompressed, 14.9 MB of it under
`framework/` (1,868 files). The deployer copies the framework into every site:
the Phase 3 techdoc site was 9.8 MB and blog 12 MB, both with
`resources/themes/.../Highlight/package.json`.
Why it matters: no Node is involved, so the hard constraint holds, but
`package.json` files in published sites suggest an npm toolchain, and every user
downloads and publishes megabytes of unused files.
Recommended fix: keep only `highlight.min.js`, the styles in use and `LICENSE` in
each theme (or one shared copy in `resources/common/`), and drop `es/`,
`languages/` and `package.json`; with `markdown.highlight: pygments` the theme
could skip Highlight.js entirely.
Effort: S

**DEP-05** | Severity: Low
Location: `kb4it/resources/themes/blog/framework/TimelineJS/js/timeline.js:1`, `kb4it/resources/themes/blog/templates/TIMELINEJS.tpl`
Evidence:
```js
/*! For license information please see timeline.js.LICENSE.txt */
```
`kb4it/resources/themes/blog/framework/TimelineJS/js/` contains only
`timeline.js` and `timeline.js.map`.
Why it matters: TimelineJS 3 is distributed under the Mozilla Public License 2.0,
which asks that the licence notice travel with the code; the file the header
points to is missing from the repository, the wheel and every published blog
site. TimelineJS (1.5 MB) is also only used by `TIMELINEJS.tpl`, which nothing
references (ARC-05). The licence of the shipped build is Needs verification
against the upstream release.
Recommended fix: remove TimelineJS with the dead template; if it stays, add the
upstream `timeline.js.LICENSE.txt` and a `LICENSE` file. Add a
`THIRD-PARTY-NOTICES` file listing every vendored library, version and licence.
Effort: S

**DEP-06** | Severity: Info
Location: `pyproject.toml:1-63`
Evidence: `[tool.poetry]` holds name, version, dependencies, extras and scripts;
there is no `[project]` table; `[build-system] requires = ["poetry-core>=1.5.0"]`.
Why it matters: poetry-core 2 accepts the standard `[project]` table (PEP 621),
which other tools read directly (uv, pip, Dependabot, pip-audit, the
`test_requirements.py` parser). The `tool.poetry` form still builds, so there is
no defect today.
Recommended fix: move the metadata to `[project]` in a later release, keep
`poetry-core>=2` as the backend, and simplify `test_requirements.py`.
Effort: M

**DEP-07** | Severity: Info
Location: `.github/workflows/kb4it.yml:16`
Evidence:
```yaml
        python: ["3.11", "3.13", "3.14"]
```
Why it matters: Python 3.12 is declared (`pyproject.toml:24`) and is the
`python3` of Ubuntu 24.04, but only the `.deb` install test exercises it.
Recommended fix: add 3.12 to the matrix on Linux only, or accept the gap and say
so in `AGENTS.md`.
Effort: S

### Phase 5 top 5

| # | ID | Why |
|---|---|---|
| 1 | DEP-02 | Tests and the theme check use their own copy of the pins and will silently drift after the next bump |
| 2 | DEP-05 | A licence notice the shipped TimelineJS refers to is missing from every published blog |
| 3 | DEP-04 | About 5 MB of unused Highlight.js per theme, with `package.json`, copied into every site |
| 4 | DEP-03 | No upper bounds on fast-moving dependencies such as textual |
| 5 | DEP-01 | Stale pixi files: a third, unchecked dependency source |


---

## Phase 6: Tests and HTML output quality

Method:
- Coverage: the full suite (455 tests, all passing) ran under `coverage` 7 with
  subprocess measurement enabled (`COVERAGE_PROCESS_START` and a temporary `.pth`
  hook in the throwaway uv environment), so builds started by the tests in a
  separate process are counted.
- HTML: one site per bundled theme was created with `kb4it create` in a scratch
  folder, plus one document using lists, a task list, a table, an admonition, a
  code block and an image; the `target/*.html` pages were checked with the Nu
  HTML Checker (`vnu.jar` through `uvx html5validator`, Java 21) and with an
  `lxml` script for `lang`, `<h1>`, `alt` and `<main>`.
- Markdown: extension combinations were rendered with `MarkdownSettings` from
  `kb4it/core/mdconfig.py`, with and without `pymdown-extensions` 12.2.

### Summary

| Area | Result |
|---|---|
| Coverage | 85% of 5,739 statements. Lowest: `themes/techdoc/logic/theme.py` 60% (354 of 888 missed), `themes/apphelp/logic/apphelp_versions.py` 27%, `core/serve.py` 76%. `core/types.py` shows 0% because it only holds type aliases imported under `TYPE_CHECKING` |
| Critical paths without tests | Page compile and render failures, the deploy abort, the cache after a failed build, escaping, title extraction (TST-01, TST-02) |
| HTML validity | apphelp: 0 errors on 14 pages. bookshelf: 6 errors. techdoc: 353 (73 not UIkit-related). blog: 384 (97 not UIkit-related) (HTML-01, HTML-03) |
| Accessibility basics | `lang` present on every page of every theme. blog: no `<h1>` and an image without `alt` on all 17 pages; techdoc and blog: placeholder `alt` text, no `<main>` landmark (HTML-02) |
| Markdown extensions | A fenced code block inside an admonition breaks with the default extensions (MD-01); `sane_lists` swallows a list that directly follows a list of the other type (MD-02); `pymdownx.superfences` in the default highlight mode produces unstyled Pygments markup (MD-03). `sane_lists` with `pymdownx.tasklist` renders task items and nested ordered lists correctly |

### Findings

**TST-01** | Severity: High
Status: Fixed in patches 0080, 0081 and 0105 (TS-01); coverage 91% with subprocess builds counted.
Location: `kb4it/services/compiler.py:191-193`, `:211-216`, `:219-220`; `kb4it/services/deployer.py:125-128`
Evidence: coverage report, missing lines:
```
kb4it/services/compiler.py   196   23   88%   77-78, 93-94, 121, 170, 191-193, 206-207, 211-216, 219-220, ...
kb4it/services/deployer.py   175   12   93%   57-58, 99, 125-128, 147-148, ...
```
Why it matters: these are exactly the branches behind COR-01 (a failed page
exits 0), COR-09 (the deploy stops copying) and SEC-03 (one property name empties
the site). No test makes a page fail and checks the exit status, the summary or
the next incremental build (COR-02), which is why those defects went unnoticed.
Recommended fix: add tests that make one document fail to compile and to render
(a hook or a broken template in `overrides/`), and assert: exit status 1, a
`failed=` count in the summary, every other page still deployed, and the failed
page rebuilt by the next incremental build.
Effort: M

**TST-02** | Severity: Medium
Status: Fixed in patches 0087, 0089, 0095 to 0098 (output tests) and 0104 (HTML validation in CI) (TS-02).
Location: `tests/themes/test_techdoc.py`, `tests/themes/test_blog.py`, `tests/themes/test_bookshelf.py`; `kb4it/resources/themes/techdoc/logic/theme.py` (60% covered); `kb4it/core/util.py:368`
Evidence: no test feeds HTML in frontmatter or titles to the themes (SEC-01); no
test covers a `# comment` in a code block before the H1 (COR-07); no test changes
`repo.json` between two builds (COR-05); no generated page is checked for valid
HTML. The largest theme module is the least covered.
Why it matters: the themes are where users see defects, and the tests check that
pages exist more than what is in them.
Recommended fix: one parametrised test over the four bundled themes that builds a
document with hostile values and asserts no raw `<script>` and no `on*=` in any
page; a title extraction test; a settings-change test; and, in the CI `package`
job, run `html5validator` on the smoke-build output of apphelp and bookshelf
(already nearly clean) to keep them valid.
Effort: M

**HTML-01** | Severity: Medium
Status: Fixed in patches 0100 to 0102 (HT-01); the Nu HTML Checker reports 0 errors besides `uk-*` on every sample site.
Location: `kb4it/resources/themes/techdoc/templates/HTML_TAG_A_NEW.tpl:1`, `kb4it/resources/themes/blog/templates/HTML_TAG_A_NEW.tpl:1`, `kb4it/resources/themes/bookshelf/templates/HTML_TAG_A_NEW.tpl:1`, `kb4it/resources/themes/blog/templates/HTML_TAG_SECT1_NEW.tpl:1`, `kb4it/resources/themes/blog/templates/HTML_TAG_SECTIONBODY_NEW.tpl:1`
Evidence:
```html
<a class="" target="" href=
```
(techdoc and blog), `<a class="bk-link" href=` (bookshelf), and
```html
<div id="kb-sect1" class="uk-margin-small-bottom uk-card ...">
<div id="kb-section-body" class="uk-container">
```
vnu results: techdoc `rich.html:275` "Bad value '' for attribute 'target'" (31
times in techdoc, 29 in blog); bookshelf `properties.html:66` "Duplicate attribute
'class'" (6), from `WORDCLOUD.tpl:3` links that already have a class; blog
`rich.html:220`, `:222` "Duplicate ID 'kb-sect1'", "Duplicate ID 'kb-section-body'";
blog `rich.html:330` "Stray end tag 'div'" (34); techdoc `all.html:204` "Element
'div' not allowed as child of element 'span'"; techdoc `rich.html:193` "Element 'ul'
not allowed as child of element 'ul'".
Why it matters: the string-replacement transformations (ARC-05) rewrite every
`<a href=` on the page, including links that templates already styled, so the
second `class` is ignored and the styling is lost; repeated IDs break in-page
anchors and scripts that look up an element by id; stray end tags change the
layout depending on how the browser recovers.
Recommended fix: drop the `HTML_TAG_A` transformation (style links with CSS
instead), use classes instead of fixed IDs in the section templates, and fix the
templates behind the stray `</div>` (blog `rich.html:330`) and the block elements
inside `<span>`; validate in CI (TST-02).
Effort: M

**HTML-02** | Severity: Medium
Status: Fixed in patch 0103 (HT-02).
Location: `kb4it/resources/themes/blog/templates/HTML_FOOTER.tpl:67`, `kb4it/resources/themes/techdoc/apps/default/config/repo.json:22-32`, `kb4it/resources/themes/blog/apps/default/config/repo.json:10-20`, `kb4it/resources/themes/techdoc/apps/sapbasis/config/repo.json:26-32`
Evidence:
```html
<img src="resources/common/images/kb4it-badge-built-with.svg">
```
```json
    "git": false,
    "git_server": "{https://{server.fqdn}",
    "logo_alt": "{alternative_text}",
```
Checked on the built sample sites: blog 17 of 17 pages have no `<h1>` and an
image without `alt`; techdoc 16 of 16 pages have `alt="{alternative_text}"` on the
logo; blog `rich.html:187` links to
`{https://{server.fqdn}/{username}/{repository_name}/edit/...}` although
`"git": false`; techdoc and blog pages have no `<main>` landmark (apphelp and
bookshelf pass all four checks).
Why it matters: screen readers announce the placeholder text or the file name of
the image; pages without a main heading or landmark are hard to navigate; a
placeholder edit link is a broken link on every page of every new blog. These
values come from the sample configuration that `kb4it create` copies.
Recommended fix: use real defaults in the sample `repo.json` (`"logo_alt": ""` or
the site title, no git placeholders), skip the edit link in blog when `git` is
false, add `alt` to the badge, give each page one `<h1>` and wrap the content in
`<main>`.
Effort: S

**MD-01** | Severity: Medium
Status: Fixed in patch 0092: documented, `MD_FENCE_IN_BLOCK` in verify; three help pages corrected (OC-05).
Location: `kb4it/core/mdconfig.py:21`
Evidence:
```python
BASE_EXTENSIONS = ["extra", "admonition", "toc", "sane_lists"]
```
Rendered with the defaults:
```
!!! note
    ```python
    y = 2
    ```
```
gives `<div class="admonition note"> <p class="admonition-title">Note</p> <p><code>python y = 2</code></p> </div>`:
the fence is not recognised inside the admonition, and the code block becomes
inline code with the language name in it.
Why it matters: code inside a note or warning is common in technical
documentation, which is what techdoc targets; the output is silently wrong.
Recommended fix: document the limitation (indent code blocks inside admonitions,
or enable `pymdownx.superfences`), or make `pymdownx.superfences` a default when
`KB4IT[extras]` is installed, with MD-03 fixed first.
Effort: S

**MD-02** | Severity: Low
Location: `kb4it/core/mdconfig.py:21` (`sane_lists`)
Evidence: `1. one\n2. two\n- bullet\n- [ ] task` renders as
`<ol><li>one</li><li>two- bullet- [ ] task</li></ol>`.
Why it matters: with `sane_lists`, a list of the other type needs a blank line
before it, otherwise its items are swallowed into the last item as text. This is
documented python-markdown behaviour, but not in the KB4IT help. Task lists
themselves work with `sane_lists` and `pymdownx.tasklist`, including nested
ordered lists.
Recommended fix: add one line to the Markdown section of the help.
Effort: S

**MD-03** | Severity: Low
Status: Fixed in patch 0091 (OC-05).
Location: `kb4it/core/mdconfig.py:37-49`
Evidence: with `"extensions": ["pymdownx.superfences"]` and the default
`highlight: "client"`, a fenced block renders as
`<div class="highlight"><pre><span></span><code><span class="n">x</span> ...`
(Pygments markup), but `pygments.css` is only written in `pygments` mode and
highlight.js is still loaded.
Why it matters: code blocks lose their colours, or get both systems at once,
depending on the theme CSS.
Recommended fix: when `pymdownx.superfences` or `pymdownx.highlight` is enabled,
set `pymdownx.highlight: {"use_pygments": highlight == "pygments"}` in
`all_configs()`, so client mode gets plain `language-*` classes.
Effort: S

**HTML-03** | Severity: Info
Location: UIkit markup in techdoc and blog templates (for example `kb4it/resources/themes/techdoc/templates/HTML_HEADER_COMMON.tpl`)
Evidence: vnu reports 280 techdoc and 287 blog errors of the form "Attribute
'uk-icon' not allowed on element 'span'", and the same for `uk-grid`, `uk-sticky`,
`uk-navbar`, `uk-dropdown`, `uk-tooltip`.
Why it matters: browsers ignore unknown attributes, so nothing breaks, but the
noise hides the real errors of HTML-01 in any validator run.
Recommended fix: use the equivalent `data-uk-*` attributes, which UIkit accepts and
HTML5 allows, when templates are next touched.
Effort: M

**TST-03** | Severity: Info
Location: `tests/blog/post1.adoc`
Evidence: an AsciiDoc file in a folder with no tests; KB4IT no longer reads
AsciiDoc (`kb4it/core/util.py:410-414` accepts `.md` and `.markdown` only).
Why it matters: a leftover from the AsciiDoc era.
Recommended fix: delete it.
Effort: S
Status: Fixed in commit ff02094 (TST-03).

### Phase 6 top 5

| # | ID | Why |
|---|---|---|
| 1 | TST-01 | The failure branches are untested, which hid the two High correctness findings |
| 2 | HTML-01 | Link rewriting and fixed IDs produce invalid HTML and lose styling in three themes |
| 3 | MD-01 | Code inside admonitions renders wrong with the default extensions |
| 4 | HTML-02 | Placeholder `alt` text and edit links shipped by `kb4it create`, missing `<h1>` in blog |
| 5 | TST-02 | No escaping, title or settings-change tests; no HTML validation in CI |

---

## Overall priorities

The audit is complete. Across the six phases, in the order I would fix them:

| # | Finding | Severity | Effort | Why first |
|---|---|---|---|---|
| 1 | SEC-01 | High | L | Stored XSS from any frontmatter value in three of four themes |
| 2 | COR-01 + TST-01 | High | M | Failed pages exit 0; CI and the GitHub Action publish broken sites |
| 3 | COR-02 | High | M | A failed build leaves stale pages until `--force` |
| 4 | COR-03 | Medium | M | A wrong `target` deletes user files |
| 5 | SEC-03 | Medium | S | One property name empties the published site |
| 6 | COR-04 | Medium | S | Non-atomic JSON writes; registry silently replaced |
| 7 | COR-05, COR-07, COR-08, MD-01 | Medium | S | Wrong output visible to readers: stale headers, wrong titles, blog stopped by one post, broken code in notes |
| 8 | SEC-02, SEC-04 | Medium/Low | S | Document the trust model for Markdown HTML and hooks |
| 9 | ARC-01, ARC-05, HTML-01 | Medium | L | Deduplicate the themes and remove the string-replacement layer; fixes many HTML errors at once |
| 10 | BASE-04, DEP-02, TST-02 | Info/Low/Medium | M | Lint, pinned dependencies and HTML checks in CI so the fixes stay fixed |

51 findings in total: 4 High (COR-01, COR-02, SEC-01, TST-01), 16 Medium,
23 Low and 8 Info. Each phase section lists them with location, evidence and fix.

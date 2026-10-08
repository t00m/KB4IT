---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-08
DocType: How-to guide
OS: Linux, macOS, Windows
Product: KB4IT
Scope: Development
Status: Done
Tag: implementation-plan, roadmap, cross-platform
Topic: Architecture, Development
---

# KB4IT 0.9 implementation plan

## Problem

`responses/KB4IT-0.9-SPEC.md` (approved 2026-10-08) defines 38 requirements in 10 phases. This plan turns them into an ordered series of commits that can be delivered as one zipped `git am` patch series, applied without a terminal session on my side, and verified on Linux, macOS and Windows.

## Prerequisites

- Base: commit `d026df3` (release 0.8.0) on `master`.
- Working branch here: `ccr-271d5ff1-h0hh01`. It already holds the comparison report and the specification.
- Tools in this environment: Python 3.11+, `uv` and `git`; no macOS or Windows machine.
- Your side: a clone of KB4IT, `git` 2.30+, and permission to push a branch so the CI matrix can run on macOS and Windows.

## Procedure

### Working rules for every commit

1. One commit per requirement, or per clean part of one. Message: one line, Conventional Commits, lower case, imperative, no trailers. The requirement ID goes in the CHANGELOG entry, not in the message.
2. Each commit contains its code, its tests, the matching help page update (`help/source/`), and its `CHANGELOG.md` entry under `## [Unreleased]`.
3. Before each commit:
    - `./scripts/devel/test.sh` passes (full suite, Linux).
    - `./scripts/devel/check_themes.sh` passes when a theme changed.
    - `kb4it verify help/config/repo.json` passes when a help page changed.
    - A smoke build of each bundled theme passes when the build pipeline changed (`scripts/devel/smoke_build.py`, added in commit 17).
4. Code that only runs on Windows or macOS (lock, clipboard, script names) is written behind `sys.platform` checks and unit tested on Linux with `monkeypatch` (fake `msvcrt`, fake `sys.platform`, fake `PATH`). The real run happens in CI after you push.
5. No em dashes in code, comments, docs or messages.

### Commit series

The numbers are the order of the patch files (`0001-...patch`, `0002-...patch`). Counts are estimates; a requirement may need one more commit if a clean split appears.

#### Phase 0: documents and foundation fixes

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 1 | `docs: add comparison report of markdown static site generators` | | `responses/KB4IT-SSG-COMPARISON.md` | |
| 2 | `docs: add specification for kb4it 0.9` | | `responses/KB4IT-0.9-SPEC.md` | |
| 3 | `docs: add implementation plan for kb4it 0.9` | | `responses/KB4IT-0.9-PLAN.md` | |
| 4 | `fix(builder): reset template caches for each build` | FX-01 | `services/builder.py`, `services/workflow.py` | `tests/core/test_template_cache.py`: template edited between two builds; two themes sharing a template name |
| 5 | `fix(themes): read and write text files as utf-8` | FX-02 | `themes/{techdoc,blog,bookshelf}/logic/theme.py` | `tests/core/test_encoding_rule.py` (AST scan of `kb4it/`); build under `LC_ALL=C` |
| 6 | `build: sync requirements.txt and pixi platforms` | FX-03 | `requirements.txt`, `pixi.toml` | `tests/core/test_requirements.py` |

Commits 1 and 2 already exist locally (`5f3e0f7`, `eee52ac`); the spec commit will be amended to its approved text before the series is cut.

#### Phase 1: cross-platform support

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 7 | `feat(env): detect the platform without exiting outside linux` | CP-01 | `core/env.py`, `core/util.py` | fallback when os-release is missing; `FAMILY` values |
| 8 | `feat(env): add KB4IT_HOME to relocate per-user data` | CP-03 | `core/env.py`, `tests/conftest.py` | nothing written under `Path.home()` |
| 9 | `feat(core): add a cross-platform file lock` | CP-02 | new `core/lock.py` | busy lock, PID, release after kill; `msvcrt` path with a fake module |
| 10 | `refactor(main): lock each repository instead of the whole user` | CP-02 | `core/main.py`, `services/workflow.py`, `tui/app.py` | two repositories build in parallel; same repository refused with exit 1; registry lock around `projects.json` |
| 11 | `feat(workflow): write compile.cmd on windows and quote the config path` | CP-04 | `services/workflow.py` | file name per platform; quoted path with spaces |
| 12 | `feat(tui): copy to clipboard on macos and windows` | CP-05 | `tui/app.py` | order of tools per platform |
| 13 | `fix(processor): report case clashes and windows reserved names` | CP-06 | `services/processor.py`, `core/util.py` | `Foo.md`/`foo.md`; `con.md`; `copydir` with `ntpath` |
| 14 | `fix(util): give crlf and lf sources the same body hash` | CP-07 | `core/util.py`, `.gitattributes` | LF and CRLF copies give equal metadata and hash |
| 15 | `test: make the suite run on macos and windows` | CP-10 | `tests/**` | the suite itself |
| 16 | `build: declare kb4it os independent` | CP-08 | `pyproject.toml` | existing packaging tests |
| 17 | `ci: run tests and smoke builds on linux, macos and windows` | CP-09 | `.github/workflows/kb4it.yml`, `scripts/devel/test.sh`, new `scripts/devel/smoke_build.py` | CI matrix |

Help pages in phase 1: `howto-install.md` (Windows, macOS, WSL), `troubleshooting.md` (lock busy, case clash, reserved names), `reference-command-line.md` (lock behaviour).

#### Phase 2: live preview

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 18 | `refactor(core): move the local web server out of the tui` | SV-01 | new `core/webserver.py`, `tui/app.py` | existing TUI tests; port scan |
| 19 | `feat(core): add a polling file watcher` | SV-01 | new `core/watch.py` | detects add, change, delete; debounce |
| 20 | `feat(cli): add kb4it serve with live reload` | SV-01 | `core/main.py`, `services/workflow.py`, `core/webserver.py` | new `tests/serve/`: serve, edit, status endpoint, injected script, error banner |
| 21 | `feat(tui): live reload in the web server action` | SV-02 | `tui/app.py` | status endpoint exposed |

Help pages: `reference-command-line.md`, new `howto-preview.md`, `howto-use-tui.md`.

#### Phase 3: Markdown pipeline

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 22 | `refactor(processor): combine theme and core build signatures` | MD-01, CU-01, CU-02 | `services/processor.py`, `core/types.py` | a core signature change forces a full rebuild |
| 23 | `feat(compiler): configurable markdown extensions` | MD-01 | `services/compiler.py`, `services/backend.py`, `services/workflow.py` (verify), `pyproject.toml` (extra) | tasklist output; missing extension hint; block change recompiles all |
| 24 | `feat(compiler): highlight code at build time with pygments` | MD-02 | `services/compiler.py`, `services/deployer.py`, `pyproject.toml`, `requirements.txt`, theme heads and footers | `pygments` output; `client` output unchanged |
| 25 | `fix(compiler): accept spaces after the closing frontmatter line` | MD-03 | `services/compiler.py` | `--- ` closing line |

Help pages: `reference-repo-json.md` (`markdown`), `reference-document-format.md`.

#### Phase 4: full-text search

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 26 | `refactor(search): share the apphelp search engine` | SR-01 | new `core/search.py`, new `resources/common/js/kb4it-search.js`, `themes/apphelp/logic/apphelp_search.py` | all `tests/apphelp/test_search_*` unchanged and passing |
| 27 | `feat(techdoc): add full-text search` | SR-02 | techdoc `theme.py`, `HTML_HEADER_COMMON.tpl`, new `PAGE_SEARCH.tpl` | index content; system pages absent; `search: false` |
| 28 | `feat(blog): add full-text search` | SR-02 | blog theme | same |
| 29 | `feat(bookshelf): add full-text search` | SR-02 | bookshelf theme | same |
| 30 | `perf(search): cache section extraction per page` | SR-03 | `core/search.py` | unchanged page not re-parsed |

Help pages: `reference-theme-techdoc.md`, `reference-theme-blog.md`, `reference-theme-bookshelf.md`, `reference-repo-json.md` (`search`).

#### Phase 5: publishing metadata

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 31 | `feat(backend): add the site_url setting` | PB-01 | `services/backend.py` | trailing slash; skip logs |
| 32 | `feat(deployer): write sitemap.xml and robots.txt` | PB-02 | new `core/sitemap.py`, `services/deployer.py` | valid XML; user `robots.txt` wins; `sitemap: false` |
| 33 | `feat: add an atom feed` | PB-03 | new `core/feeds.py`, blog, techdoc and bookshelf themes | entries, order, category filter, head link |
| 34 | `feat(templates): add description and open graph tags` | PB-04 | new `common/templates/HTML_HEAD_META.tpl`, four theme heads | tags with and without `site_url`; `Summary` and first-paragraph fallback |

Help pages: `reference-repo-json.md`, `howto-publish-github-pages.md`, `howto-publish-web-server.md`.

#### Phase 6: customization and extension

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 35 | `feat(builder): per-repository template and static overrides` | CU-01 | `services/builder.py`, `services/frontend.py`, `services/deployer.py`, `services/processor.py` | override used; removal restores; static file copied; required templates |
| 36 | `feat: add build hooks` | CU-02 | new `core/hooks.py`, `services/backend.py`, `services/compiler.py`, `services/builder.py`, `services/workflow.py` | each hook; failure path; signature change |

Help pages: new `howto-customize-templates.md` (with the Mermaid example), new `howto-hooks.md`, `explanation-themes.md`.

#### Phase 7: backlinks and link checks

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 37 | `feat(processor): track links between documents` | KG-01 | `services/processor.py`, `core/mdlinks.py`, `core/types.py` | links stored; backlink change marks the target for recompile; unchanged docs skipped |
| 38 | `feat(themes): show which documents link to a page` | KG-01 | the four themes' page templates | "Linked from" section; `backlinks: false` |
| 39 | `feat(verify): report broken links and anchors` | KG-02 | `services/workflow.py` | exit 1 with source and target named |

Help pages: `reference-theme-*.md`, `reference-command-line.md` (`verify`).

#### Phase 8: versioned help

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 40 | `feat(apphelp): build each help version into its own folder` | VH-01 | apphelp `theme.py`, `apphelp_config.py`, `services/backend.py` (target sub-folder hook) | two versions kept; `versions.json`; `latest/`; root redirect |
| 41 | `feat(apphelp): add a version switcher` | VH-02 | apphelp templates and `apphelp.js` | switcher markup; same page kept when present |
| 42 | `ci(help): keep earlier help versions when publishing` | VH-03 | `.github/workflows/help.yml` | workflow syntax check |

Help pages: `reference-theme-apphelp.md`, `howto-publish-github-pages.md`.

#### Phase 9: documentation

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 43 | `docs(help): review the help site for 0.9` | DOC-01 | `help/source/*` | `kb4it verify help/config/repo.json` |
| 44 | `docs: update the readme for 0.9` | DOC-02 | `README.md` | new `tests/core/test_readme.py`: every CLI subcommand appears in the Usage block |
| 45 | `docs: update agents.md for 0.9` | DOC-03 | `AGENTS.md` | |
| 46 | `docs(release): raise theme requirements at release time` | DOC-04 | `RELEASING.md` | see open question Q-1 |

DOC-05 (CHANGELOG) is satisfied commit by commit. DOC-06 (release) is your step after the merge.

### Delivery package

At the end I build `kb4it-0.9-series.zip` in the repository folder `responses/` (so the app can open it) containing:

- `0001-*.patch` to `0046-*.patch` from `git format-patch d026df3..HEAD`.
- `README-APPLY.md`: how to apply (below), the commit list, and what to check.
- `SERIES.sha256`: checksums of the patch files.

How you apply it:

```bash
git fetch origin
git switch -c feature/0.9 d026df3
unzip kb4it-0.9-series.zip -d /tmp/kb4it-0.9
git am --3way /tmp/kb4it-0.9/*.patch
./scripts/devel/test.sh
git push -u origin feature/0.9
```

The push starts the CI matrix (commit 17) on Linux, macOS and Windows. If any job fails, send me the job log and I will deliver a follow-up patch on top of the series.

### Progress reporting

- After each phase I send a short status message: commits done, tests passing, anything that changed from the plan.
- After phase 1 I can deliver an interim zip with phases 0 and 1 only, so you can push it and get the macOS and Windows CI results early. The final zip then contains the whole series again from commit 1. See Q-2.

## Verification

| Check | Where | When |
|---|---|---|
| Full test suite | Here, Linux, Python 3.11 | Before every commit |
| Theme check | Here | Every commit touching a theme |
| Help site verify | Here | Every commit touching `help/source/` |
| Smoke build of the four themes | Here | Every commit touching the pipeline |
| Byte-identical output for 0.8.0 settings | Here, with `scripts/devel/theme_snapshot.py` | End of each phase |
| `git am` of the full series on a clean `d026df3` checkout | Here | Before building the zip |
| macOS and Windows | GitHub Actions on your push | After you apply the series |

## Troubleshooting

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Windows keeps files open (antivirus, Explorer preview) and `os.unlink`/`shutil.rmtree` fail during deploy | Build fails on Windows | Retry with short back-off in `core/util.py` file removal helpers; clear error naming the file |
| `msvcrt.locking` behaves differently from `flock` (byte ranges, no shared locks) | Lock bugs on Windows | Lock one byte at offset 0; tests with a fake module here and real runs in CI |
| Textual differences on Windows terminals | TUI rendering issues | Out of scope for fixes beyond CP-05 unless CI or you report one |
| Pygments HTML interacts with the theme transformation pipeline (`HTML_TAG_PRE_*` pairs) | Broken code block styling with `pygments` | Transformation pairs target AsciiDoc-era markup that python-markdown never emits; test the techdoc and blog output explicitly |
| Search index size on large sites | Slow page loads | 5 MB warning; `search: false`; sections capped at 5000 characters as in apphelp |
| Backlinks need link data before compilation | Extra parse cost in stage 3 | Parse only changed documents; links of unchanged documents come from `kbdict.json` |
| Versioned apphelp changes where the deployer writes | Regression in apphelp | Behind `apphelp.versions.enabled`; existing apphelp tests must pass unchanged |
| The series is long (about 46 commits) | Review effort | Each commit is small and self-contained; interim zip after phase 1 |

## Open questions

Answered on 2026-10-08: the recommendation was chosen for each one.

| # | Question | Decision |
|---|---|---|
| Q-1 | Themes that use 0.9 features should declare `"kb4it": ">=0.9.0"`. But `kb4it/VERSION` stays `0.8.0` until you run `scripts/release.sh`, and KB4IT refuses a theme whose requirement it does not meet, so the tests would fail inside the series. | Keep the bundled themes at their current requirement inside the series, and add a step to `RELEASING.md` (commit 46): raise the bundled themes to `>=0.9.0` in the release commit. Alternative: bump `kb4it/VERSION` to `0.9.0` at the start of the series, which departs from the rule that only `release.sh` changes it. |
| Q-2 | Interim delivery after phase 1? | Yes: one interim zip after phase 1 so macOS and Windows CI results arrive early, then the final zip. |
| Q-3 | The series includes my two analysis documents and this plan under `responses/`. | Keep them: they record why each change was made. Alternative: leave `responses/` out of the series. |

## Implementation notes

Differences between this plan and the delivered series, decided while implementing:

| Item | Plan | Delivered | Why |
|---|---|---|---|
| CP-02 | `create` locks `<new repo>/var/kb4it.lock` | `create` locks `~/.kb4it/var/create-<hash>.lock` | A lock inside the new folder created the folder before the theme was checked, so a failed `create` left it behind |
| CP-07 | LF/CRLF only | Also the UTF-8 byte order mark, in sources and `repo.json` | Found while testing: Windows editors write it, and it hid the opening `---` |
| SV-02 | Rebuilds shown in the Build screen log | Rebuilds shown as notifications | The web server keeps running after the Project screen closes; a notification reaches the user on any screen |
| SR-02, SR-03 | One commit per theme, then a caching commit | One commit; the index is built by the core from the HTML the compiler produces, cached per document | No per-theme indexing code; caching comes for free |
| SR-02 | Search parses pages in worker threads | Sections are parsed on the main thread (separate fix commit) | One full test run crashed with `free(): invalid pointer`; keeping lxml on one thread avoids the risk |
| PB-04 | Themes include `HTML_HEAD_META.tpl` | The deployer inserts it before `</head>` of each page built in the run | Works for all four themes without editing their page logic; a theme can still override the template |
| KG-01 | apphelp shows backlinks in "Related" | All four themes show the same "Linked from" block at the end of the article | One code path, from the compiler |
| VH-01 | `apphelp.version` | The existing top-level `version` key | apphelp already reads it for the footer |
| VH-03 | Change `help.yml` | Documented pattern only; `help.yml` unchanged | Turning versions on changes the published help URLs (root redirects to `latest/`); that is your decision |
| Plan, verification | Byte-identical comparison with 0.8.0 per phase | Not run | Most phases change the output on purpose (search box, page metadata, backlinks); each change is covered by its own tests instead |

Pre-existing problems found while testing, not fixed (outside the specification):

- blog: a post without `Date` stops the build with `Error: 'Date'`, although `Date` is optional.
- blog: a `repo.json` without `tagline` or the `git` keys makes every page fail to render (`[COMPILER] ERROR 'tagline'`), yet the build exits with status 0.


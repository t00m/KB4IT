---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-14
DocType: How-to guide
OS: Linux, macOS, Windows
Product: KB4IT
Scope: Development
Status: Done
Tag: implementation-plan, audit, security, correctness, html
Topic: Architecture, Development
---

# KB4IT 0.9 audit fix implementation plan

## Problem

`responses/KB4IT-0.9-AUDIT-FIX-SPEC.md` (approved 2026-10-14, recommended answer for D-1 to
D-6) defines 18 requirements in groups A to F for the High and Medium findings of
`AUDIT.md`; group G (AR-01 to AR-03) moves to a separate series (D-6). This plan
turns groups A to F into an ordered series of commits, delivered as a zipped
`git am` series on top of patch 0077.

## Prerequisites

- Base: the branch after patch 0077 (`docs: approve the audit fix specification`),
  with `AUDIT.md` and the specification.
- Working branch here: `ccr-271d5ff1-h0hh01`.
- Tools in this session, checked on 2026-10-14: Python 3.11 to 3.14 through uv,
  Java 21 with the Nu HTML Checker (`uvx html5validator`), Docker, shellcheck and
  actionlint through `uvx`. `nh3` 0.3.7 installs from PyPI with abi3 wheels for
  Linux (x86_64, aarch64), macOS and Windows; it removed `<script>`, `onclick` and a
  `javascript:` link in a first test.
- Your side: as before, `git am`, a push for CI on macOS and Windows.

## Procedure

### Working rules for every commit

1. One commit per requirement or clean part of one; one-line Conventional Commits
   message without trailers; the requirement and finding IDs go in the
   `CHANGELOG.md` entry.
2. Each commit holds its code, tests, help pages and changelog entry.
3. Before each commit: `./scripts/devel/test.sh` passes; the help site verifies when
   a help page changed; ruff reports no new issue in the changed files.
4. Every audit reproduction in scope becomes a test that failed before the commit
   and passes after it. The test is written first and run against the old code.
5. Theme changes are checked with the content snapshot (commit 79) before and after:
   any difference other than the intended one is investigated before committing.
6. No em dashes.

### Design choices inside the spec

| Topic | Choice |
|---|---|
| Content snapshot | `scripts/devel/theme_snapshot.py` gains `--content DIR`: it builds the sample app of every theme plus a fixture set (rich document, hostile values, undated post) and writes each page, normalised (build timestamps and version strings removed), to `DIR`. `diff -r` of two runs shows every output change. |
| Failed pages (BO-01) | `Compiler` keeps `self.failed: list[tuple[str, str]]`, appended under a lock from `_compile_md` and `compilation_finished`. After the pool, a non-empty list raises `CompilationError`. The summary reads `len(compiler.failed)`. The Deployer collects missing pages the same way and raises after copying the rest. |
| Cache commit (BO-02) | `Processor` stores the new dictionary in `self.kbdict_new` only; `Backend.stage_06_deploy` calls `commit_kbdict()` after the Deployer returns. Backlink data written today by the second save at `processor.py:301` is kept in memory until the commit. |
| Target check (FS-01) | A helper `check_target(target, root, source, home)` in `kb4it/core/paths.py` (new; ARC-04's `resolve_repo_path` moves there too, since the same commit touches it). Paths are compared with `os.path.realpath` and `os.path.commonpath`, case-insensitively on Windows and macOS. |
| Owned files (FS-01) | `kbdict["deployed"]`: sorted list of target-relative paths written by `step_07` and `step_08`. The sweep deletes `previous_deployed - current_deployed`, only for `.html` pages (resources are rewritten, not swept, as today). |
| Atomic JSON (FS-02) | `json_save` uses `tempfile.NamedTemporaryFile(dir=..., delete=False)`, `flush` and `os.fsync`, then `os.replace`. On Windows `os.replace` is atomic for files on the same volume. |
| Settings signature (OC-01) | `signature_parts()["repo"] = get_hash_from_dict({k: v for k, v in repo.items() if k not in NON_PAGE_KEYS})`, with `NON_PAGE_KEYS = {"workers", "force", "fail_on_invalid", "source", "target"}` in `processor.py`. |
| Title rule (OC-03) | One function `first_heading(body) -> (title, line_index)` in `kb4it/core/util.py` that walks lines, tracks fence state (backtick or tilde, length at least 3, indent at most 3) and skips indented code; used by `get_markdown_attributes` and `get_hash_from_body`. |
| Autoescape (SC-01, D-1) | `Builder.template` reads `theme["autoescape"]`; when true, `Template(filename=..., default_filters=["h"])`. Common templates (`resources/common/templates`) always compile with `["h"]`; their expressions that hold HTML get `\| n`, and their 11 explicit `\| h` become plain expressions. A small script, `scripts/devel/escape_audit.py`, lists every `${...}` of a theme with the variable it prints, to drive the review of the 591 expressions; it is committed so later theme work can reuse it. |
| Which expressions get `\| n` | Those that print values built as HTML in Python (page bodies, `var['content']`, rendered fragments such as `search_box`, `metadata_section`, datatables, tag clouds, menus) or that come from `theme_var` keys documented as HTML. Every other expression (titles, property values, URLs, ids, counters) is escaped. Each `\| n` is listed in the commit's notes. |
| Sanitiser (SC-02, D-2) | `nh3` added as an optional dependency in the `extras` group (`pyproject.toml`), loaded only when `"markdown": {"sanitize": true}`; a missing package stops the build with the same hint pattern as missing Markdown extensions (`MD_EXTENSION_MISSING`). The allow-list is built from what python-markdown, the bundled extensions and PyMdown emit (headings with `id`, tables, code with `class`, admonitions, task-list `input` with `type`, `disabled`, `checked`). `test.sh` installs `nh3` and `pymdown-extensions` so these paths run in CI. |
| Section ids (HT-01) | `kb-sect1` and `kb-section-body` become classes `kb-sect1` and `kb-section-body`; the blog CSS selectors change from `#` to `.`; the TOC keeps using the heading ids python-markdown creates. |
| Validation in CI (TS-02) | `scripts/devel/validate_html.py` runs `html5validator` on a target folder and fails on any message not matching `Attribute "uk-[a-z-]+" not allowed`; the `package` job in `kb4it.yml` runs it on the four smoke-build sites. |

### Commit series

Numbers continue after 0077. Counts are estimates.

#### Phase A: plan and tooling

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 78 | `docs: add implementation plan for the audit fixes` | | this file | |
| 79 | `build(devel): snapshot the content of every theme's pages` | (support) | `scripts/devel/theme_snapshot.py`, `tests/fixtures/audit/` | run twice on the same tree gives no diff |

#### Phase B: build outcome

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 80 | `fix(compiler): fail the build when a page fails` | BO-01 (COR-01, COR-09) | `services/compiler.py`, `services/deployer.py`, `services/workflow.py` (summary), `core/main.py` | `tests/core/test_build_failures.py`: failing hook, blog without `tagline`, missing cached page; exit 1, `failed=`, other pages deployed |
| 81 | `fix(processor): write the cache only after a successful deploy` | BO-02 (COR-02) | `services/processor.py`, `services/backend.py` | the hook-fails-once scenario; an interrupted build (exception in stage 6) keeps the old `kbdict.json` |
| 82 | `docs: document when kb4it build fails` | BO-03 | `help/source/reference-command-line.md`, `help/source/reference-github-action.md` | help verify |

#### Phase C: files and data

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 83 | `fix(backend): refuse a target that overlaps the repository` | FS-01 (COR-03) | new `core/paths.py`, `services/backend.py`, `core/hooks.py`, `core/serve.py` | each forbidden target refused with both paths in the message; a nested valid target accepted |
| 84 | `fix(deployer): remove only pages kb4it wrote` | FS-01 (COR-03) | `services/deployer.py`, `services/processor.py` | user `notes.html` survives; deleted document's page removed; first build after upgrade deletes nothing |
| 85 | `fix(util): write json files atomically and keep corrupt ones` | FS-02 (COR-04) | `core/util.py`, `services/workflow.py`, `services/backend.py` | truncated `projects.json` kept as `.corrupt-*`; truncated `kbdict.json` gives a full rebuild; failure between write and replace leaves the old file |
| 86 | `refactor(util): remove the unused shell helper` | FS-03 (BASE-01) | `core/util.py`, `tests/core/test_util.py` | no `shell=True` in `kb4it/` (scan test) |

#### Phase D: output correctness

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 87 | `fix(processor): rebuild every page when site settings change` | OC-01 (COR-05) | `services/processor.py` | title change rebuilds `page.html`; `workers` change rebuilds nothing |
| 88 | `fix(builder): report template compile errors` | OC-02 (COR-06) | `services/builder.py` | broken override: exit 1, file and line in the message |
| 89 | `fix(util): ignore code blocks when finding the title` | OC-03 (COR-07) | `core/util.py` | fences with backticks and tildes, indented code, title after a code block; help site unchanged (snapshot) |
| 90 | `fix(blog): build with posts that have no date` | OC-04 (COR-08) | `themes/blog/logic/theme.py`, `core/main.py` | undated post listed last with `DOC_UNDATED`; error line shows type and log path |
| 91 | `fix(markdown): plain highlight classes with superfences in client mode` | OC-05 (MD-03) | `core/mdconfig.py` | superfences in `client` gives `language-*` classes; in `pygments` mode, Pygments markup and CSS |
| 92 | `feat(verify): warn about fences inside indented blocks` | OC-05 (MD-01) | `services/workflow.py`, `help/source/` Markdown page | warning present without superfences, absent with it |

#### Phase E: security

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 93 | `fix(util): page names never start with a dot` | SC-03 (SEC-03) | `core/util.py`, `services/processor.py` | `.note: a` builds `note.html` and `index.html`; `"...": a` reported invalid, site built |
| 94 | `feat(builder): escape template output for themes that opt in` | SC-01 (SEC-01) | `services/builder.py`, `resources/common/templates/*.tpl`, new `scripts/devel/escape_audit.py`, theme authoring help | common templates escape hostile values; custom theme without the flag warns once and renders as before |
| 95 | `fix(apphelp): escape template output by default` | SC-01 | `themes/apphelp/theme.json`, `themes/apphelp/templates/*.tpl` | new `tests/themes/test_escaping.py` with apphelp; snapshot unchanged except intended |
| 96 | `fix(techdoc): escape template output by default` | SC-01 | `themes/techdoc/theme.json`, templates, `logic/theme.py` where it builds HTML strings | `test_escaping.py` extended to techdoc |
| 97 | `fix(blog): escape template output by default` | SC-01 | same for blog | extended to blog |
| 98 | `fix(bookshelf): escape template output by default` | SC-01 | same for bookshelf | extended to bookshelf: the four themes are covered |
| 99 | `feat(markdown): optional html cleaning with nh3` | SC-02 (SEC-02, D-2) | `core/mdconfig.py`, `services/compiler.py`, `services/workflow.py` (`DOC_RAW_SCRIPT`), `pyproject.toml`, `scripts/devel/test.sh`, help (trust model) | sanitize on: script, handler, `javascript:` removed, tables, code, admonitions and task lists kept; off: unchanged, `verify` lists the document; missing `nh3`: clear error |

#### Phase F: HTML and accessibility

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 100 | `fix(themes): drop the link rewriting transformation` | HT-01 (HTML-01, ARC-05 in part) | `services/builder.py`, `HTML_TAG_A_*` templates, theme CSS | no `target=""`, no duplicate `class` on any sample page |
| 101 | `fix(blog): use classes for section blocks` | HT-01 | blog `HTML_TAG_SECT*_NEW.tpl`, blog CSS | no duplicate id on the rich document page |
| 102 | `fix(themes): valid markup in techdoc and blog pages` | HT-01 | the templates behind stray `</div>`, `div` in `span`, nested `ul`, `width="24px"` | vnu: 0 errors other than `uk-*` on the four sample sites (run locally) |
| 103 | `fix(themes): accessible defaults for new sites` | HT-02 (HTML-02) | sample `repo.json` files, header and footer templates, blog page templates | `lxml` checks: `lang`, one `h1`, `alt` without placeholders, `main`, no `href="{` |

#### Phase G: tests and CI, notes

| # | Commit message | Spec | Main files | Tests |
|---|---|---|---|---|
| 104 | `ci: validate the html of the sample sites` | TS-02 | new `scripts/devel/validate_html.py`, `.github/workflows/kb4it.yml` | the step itself; actionlint |
| 105 | `test: cover the failure branches` | TS-01 | any test still missing after 80 to 86 | coverage of `compiler.py:191-193`, `:211-216`, `:219-220`, `deployer.py:125-128` |
| 106 | `docs: update agents.md for the audit fixes` | | `AGENTS.md` (exit status, cache commit, autoescape, sanitize, target rule) | |
| 107 | `docs: record implementation notes in the audit fix plan` | | this file, `AUDIT.md` status column | |

`AUDIT.md` gains a "Status" line for each finding in scope in commit 107 (fixed in
commit N), so the audit stays the reference.

### Delivery package

`kb4it-0.9-audit-fix-series.zip`: patches 0077 to 0107 from
`git format-patch <0076>..HEAD --start-number 77`, `README-APPLY.md` and
`SERIES.sha256`. Applied on the branch after 0076:

```bash
git am --3way /tmp/kb4it-audit-fix/00*.patch
./scripts/devel/test.sh
git push
```

### Progress reporting

A short status after each phase. One interim zip after Phase E (security), so the
escaping can be reviewed on CI before the HTML work, if you want it.

## Verification

| Check | Where | When |
|---|---|---|
| Full test suite | Here, Python 3.11 | Every commit |
| Audit reproductions now passing | Here (tests) | Commits 80 to 99 |
| Content snapshot diff | Here | Every theme or template commit |
| Nu HTML Checker on the four sample sites | Here and CI | Commits 100 to 104 |
| Coverage of the failure branches | Here | Commit 105 |
| `bandit -r kb4it` without B602 | Here | Commit 86 |
| `git am` of 0077 to 0107 on a clean checkout of 0076 | Here | Before the zip |
| macOS and Windows (paths, atomic replace, case-insensitive target check) | CI after you push | After applying |

## Implementation notes

The series is patches 0079 to 0107, as planned: the snapshot tool, 26 commits for the requirements in groups A to F, the `AGENTS.md` update and these notes. Patches 0079 to 0099 went out first as `kb4it-audit-fix-interim.zip`. Differences from the plan, decided while implementing:

| Item | Plan | Delivered | Why |
|---|---|---|---|
| Common templates (SC-01) | Spec: escaped like the theme that uses them | Always escaped, as the plan's design table says | Their explicit `\| h` filters are gone; "like the theme" would have printed those values raw for a custom theme without the flag |
| `THEME_AUTOESCAPE_OFF` | Warned for every theme without the flag | Custom themes only (the spec's wording) | No intermediate commit warned about a bundled theme still being converted |
| Python-built HTML | Commits 96 to 98 | Datatable titles, tooltips and dates in techdoc, blog and bookshelf escape their values; the JSON in the techdoc "Add" page writes `<` as `\u003c` | Found with an instrumented build that records every escaped value looking like HTML, with its template and line |
| Entities in expressions | Not foreseen | bookshelf printed `&middot;` and `&#9656;` inside `${...}`; the separators are now raw and the values beside them escaped | Escaping would have shown the entity text |
| `pymdown-extensions` in `test.sh` | Commit 99 | Commit 91; `nh3` in 99 | The superfences tests of 91 run in CI from that commit on |
| `nh3` version | Any | `>=0.3.0` | `filter_style_properties`, used to keep only `text-align` in table cells, arrived in 0.3.0 |
| Title rule (OC-03) | `get_markdown_attributes` and `get_hash_from_body` | Also the line the compiler leaves out of the page body | One definition of the title line everywhere |
| Blog system pages (OC-04) | Not foreseen | Rendered with the plain body template explicitly | They reached it only because the post template failed on their missing `Date`; tolerating undated posts would have turned them into post cards |
| SC-03 | Property names | Also property values that clean to nothing (`bad_property_value`) | They made pages such as `Tag_.html` shared by unrelated values |
| MD-01 | Help page and warning | Also three help pages ("Customize templates", "Create a theme", "Release") converted from fenced to indented code | The new warning found them: their commands rendered as inline code |
| Template errors (OC-02) | Raise | Raise, logged once per build with the error on one line | A broken footer otherwise logged one multi-line error per page |
| Duplicate `class` (HT-01) | `HTML_TAG_A` only | Also the blog key modal title, now a `div` with `uk-h2` | The `HTML_TAG_H2` pair adds a `class` to every `<h2 `; changing the shared pattern would break custom themes |
| Blog home ids (HT-01) | Not listed | The metadata and source dialogs of each post carry the post name in their ids | The home page repeats them per post |
| `h1` (HT-02) | Techdoc and blog | Blog posts use their title as `h1`; other blog pages get a visually hidden `h1`; bookshelf pages without a heading get a visible one | Acceptance covers all four themes |
| `git_path` (HT-02) | Every `git_*` key set | Server, user, repository and branch set; `git_path` may be empty | Documents at the repository root, as apphelp already allows |
| Windows `os.replace` retry | Risk table: retry three times | Not done | No failure seen; it waits for CI on Windows |
| `validate_html.py` | Runs on the smoke-build sites | Builds the sample site of every bundled theme itself (five sites with techdoc's sapbasis), with the audit documents | One command here and in CI; checks only pages, not third-party demo files such as TimelineJS's `icons.html` |

Raw expressions (`| n`) per theme after the series: apphelp 3, techdoc 33, blog 24, bookshelf 18 (`scripts/devel/escape_audit.py <theme> --raw`).

What ran here and what only CI can show:

- Ran here: the full test suite at every commit (569 tests at the end, Python 3.11); the content snapshot before and after every theme commit; the Nu HTML Checker on the five sample sites (118 pages, 0 errors besides `uk-*`; 437 before Phase F); coverage with subprocess builds counted (91%, 85% at the audit); `git am` of the interim series on a clean checkout of 0078; shellcheck and actionlint.
- Only CI: macOS and Windows (case-insensitive target check, atomic replace, file modes), the other Python versions of the matrix, and the HTML validation step on GitHub's runner.

Follow-ups outside this series:

- Pages left in a target by a build older than this series stay there, since no record says KB4IT wrote them; delete them by hand, or empty the target once.
- The bookshelf help promises edit links, but the theme never prints its page actions.
- AR-01 to AR-03 (decision D-6).

## Troubleshooting

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| A template prints HTML built in Python without being marked `\| n` | Escaped markup visible on pages (`&lt;div&gt;`) | `escape_audit.py` lists every expression; the content snapshot shows every change; the vnu run catches visible tags in attributes; one theme per commit |
| Double escaping where Python already escaped a value (apphelp, head metadata) | `&amp;lt;` on pages | Those `\| h` become plain expressions in the same commit; snapshot diff |
| Theme logic builds HTML strings with values inside (for example datatables, tag clouds) | Escaping in templates does not cover them | `escape_audit.py` also lists f-strings that build HTML in `logic/theme.py`; those values get `html.escape` in Python (commits 96 to 98) |
| Owned-files list missing for repositories built before the upgrade | Old orphan pages stay | Documented in the release notes: one `--force` cleans them |
| Atomic replace on Windows when the file is open (antivirus, editor) | `PermissionError` | Retry three times with a short delay, then a clear error naming the file |
| `nh3` allow-list too strict | Lost formatting with `sanitize` on | Tests cover every structure the bundled extensions emit; the option is off by default |
| Size of the series (about 30 commits) and the escaping review | Review effort | Interim zip after Phase E; each theme in its own commit |

## Open questions

None. If the escaping review shows that a theme cannot be converted without visible
changes beyond escaped characters, I will stop and ask before going on.

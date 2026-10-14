---
Author: Tomás Vírseda
Category: Change
Date: 2026-10-14
DocType: Reference
OS: Linux, macOS, Windows
Product: KB4IT
Scope: Development
Status: Approved
Tag: specification, audit, security, correctness, html
Topic: Architecture, Development
---

# KB4IT 0.9 audit fix specification: High and Medium findings

## Overview

`AUDIT.md` (patches 0069 to 0075) reports 51 findings. This specification covers
the 20 rated High or Medium:

| Severity | Findings |
|---|---|
| High (4) | COR-01, COR-02, SEC-01, TST-01 |
| Medium (16) | BASE-01, COR-03, COR-04, COR-05, COR-06, COR-07, COR-08, SEC-02, SEC-03, ARC-01, ARC-02, ARC-03, TST-02, HTML-01, HTML-02, MD-01 |

Three Low findings are pulled in because a Medium fix depends on them: COR-09
(deploy abort, fixed with COR-01), MD-03 (superfences highlighting, needed by
MD-01) and ARC-05 (the link transformation removed by HTML-01). The remaining Low
and Info findings stay in `AUDIT.md` for later.

The base is the branch after patch 0075. The work follows the usual cycle:
this specification (approved 2026-10-14), then an implementation plan, then a `git am` patch series.

### Requirement groups

| Group | Requirements | Findings |
|---|---|---|
| A. Build outcome | BO-01 to BO-03 | COR-01, COR-09, COR-02 |
| B. Files and data safety | FS-01 to FS-03 | COR-03, COR-04, BASE-01 |
| C. Output correctness | OC-01 to OC-05 | COR-05, COR-06, COR-07, COR-08, MD-01 (with MD-03) |
| D. Security | SC-01 to SC-03 | SEC-01, SEC-02, SEC-03 |
| E. HTML and accessibility | HT-01, HT-02 | HTML-01 (with ARC-05 in part), HTML-02 |
| F. Tests and CI | TS-01, TS-02 | TST-01, TST-02 |
| G. Architecture | AR-01 to AR-03 | ARC-01, ARC-02, ARC-03 |

## Conventions

Same as the 0.9 specifications: one-line Conventional Commits without trailers;
code, tests, help pages and `CHANGELOG.md` entry in the same commit;
`[<COMPONENT>] EVENT key=value` logging; UTF-8 for every file; no em dashes. Each
requirement names its acceptance test. Every behaviour change that a user can
notice gets a line in the help and in the release notes.

## A. Build outcome

### BO-01 A failed page fails the build (COR-01, COR-09)

**Requirement.**

- The `Compiler` records every document whose Markdown compilation fails
  (`compiler.py:219`) or whose page rendering raises (`compiler.py:211-216`), with
  the reason.
- After the pool finishes, if any document failed, the compiler logs
  `[COMPILER] PAGES_FAILED n=<n> docs=<names>` and raises `CompilationError`, so
  `KB4IT.run()` returns `False` and `kb4it build` exits with status 1.
- The build summary gains `failed=<n>` (`workflow.py:381`), shown in the GitHub
  Action job summary too.
- The `Deployer` no longer stops at the first missing page (`deployer.py:125-128`):
  it copies every page it has, collects the missing ones, and raises
  `CompilationError` naming them. The hint says `--force`.
- `kb4it serve` and the TUI keep running after a failed build and show the first
  error, as they do for other build errors today.

**Acceptance.** A techdoc build where one document's `on_page` hook raises, and a
blog build without `tagline`, both exit 1 with `failed=` greater than 0; every
other page is still deployed.

### BO-02 The cache is written only after a successful build (COR-02)

**Requirement.**

- `Processor` keeps the new `kbdict` in memory. The two writes in
  `processor.py:187` and `:301` are removed.
- `Backend` writes `kbdict.json` once, after stage 7 (deploy) succeeds, through a
  new `Backend.commit_kbdict()`.
- A build that fails or is interrupted at any stage leaves the previous
  `kbdict.json` untouched, so the next incremental build compiles every document
  that changed since the last successful build.

**Acceptance.** The scenario of COR-02 (hook fails once for a changed document):
the third build compiles the page (`compiled=1`) and `target/page.html` holds the
new text.

### BO-03 Exit status documented

**Requirement.** `reference-command-line.md` lists when `build` exits 1: settings
error, invalid documents with `fail_on_invalid`, a failed page (new), a busy
lock. The GitHub Action reference says the step fails on any of them.

**Acceptance.** Help verify passes; the statement matches the code.

## B. Files and data safety

### FS-01 The target folder is checked, and the sweep deletes only KB4IT's files (COR-03)

**Requirement.**

- Stage 1 (`backend.py:331`) refuses, with `ConfigError` and a message naming both
  paths, a `target` that is equal to, or contains, any of: the repository root,
  the source folder, `config/`, `var/`, the user's home folder, or a filesystem
  root. A target inside the source folder is also refused.
- `kbdict.json` keeps the list of files KB4IT wrote into the target
  (`deployed`). The stale sweep in `deployer.py:130-134` deletes only files from
  that list that the current build did not produce. The first build after an
  upgrade has no list and therefore deletes nothing.

**Acceptance.** `"target": "."` stops with the new error and deletes nothing; a
user file `notes.html` placed in a valid target survives any number of builds; a
deleted document's page is still removed.

### FS-02 JSON files are written atomically; corrupt files are kept (COR-04)

**Requirement.**

- `json_save` (`util.py:301`) writes to a temporary file in the same folder and
  replaces the target with `os.replace`.
- A `projects.json` that cannot be parsed is renamed to
  `projects.json.corrupt-<timestamp>` with a warning
  (`[WORKFLOW] PROJECTS_CORRUPT`), and the registry starts empty. It is never
  overwritten in place.
- A `kbdict.json` that cannot be parsed logs `[BACKEND] KBDICT_CORRUPT` and the
  build continues as a full rebuild, instead of failing with `KBDICT_LOAD_FAIL`.

**Acceptance.** The COR-04 reproduction keeps the original file as
`projects.json.corrupt-*`; a truncated `kbdict.json` gives a successful full build;
a test interrupts `json_save` between write and replace and finds the old file
intact.

### FS-03 Remove the shell helper (BASE-01)

**Requirement.** `exec_cmd` (`util.py:210-224`) and its test
(`tests/core/test_util.py:66-67`) are deleted. No `shell=True` remains in
`kb4it/`.

**Acceptance.** `bandit -r kb4it` reports no B602; a test scans `kb4it/` for
`shell=True`.

## C. Output correctness

### OC-01 Site settings shown on every page trigger a rebuild (COR-05)

**Requirement.** `Processor.signature_parts()` (`processor.py:190-198`) includes a
hash of the whole `repo.json`, minus keys that never reach a page: `workers`,
`force`, `fail_on_invalid`, `source`, `target`. Changing any other key rebuilds
every page.

**Acceptance.** The COR-05 reproduction: after the title change, `page.html` shows
the new name; changing `workers` does not rebuild anything.

### OC-02 Template errors are reported, not skipped (COR-06)

**Requirement.** `Builder.template` (`builder.py:178-208`) skips only candidates that
do not exist (`os.path.exists`). A candidate that exists but fails to compile
raises `ThemeError("Template <name> at <path>: <Mako error with line>")`. The
message for a missing template stays as it is.

**Acceptance.** A test puts a template with a Mako syntax error in `overrides/`; the
build exits 1 and the message names the file and line.

### OC-03 The title ignores code blocks (COR-07)

**Requirement.** The H1 search in `get_markdown_attributes` (`util.py:368`) skips
lines inside fenced code blocks (opened by three or more backticks or tildes,
indented up to three spaces) and indented code blocks. The same rule is used
wherever the leading H1 is found (`get_hash_from_body`, `util.py:322-338`).

**Acceptance.** The COR-07 document gets the title "Real title"; existing documents
keep their titles (the full test suite and the help site build unchanged).

### OC-04 A blog post without Date does not stop the blog (COR-08)

**Requirement.**

- The blog index (`themes/blog/logic/theme.py:169`) and every other place in the
  blog theme that reads `Date` handle a missing value: undated posts are listed
  after the dated ones and logged once with `[THEME] DOC_UNDATED doc=<name>`.
- `main.py:369` prints the exception type and the log file path, instead of the
  bare message.

**Acceptance.** The COR-08 reproduction exits 0, the post appears in the index, and
the warning is logged; a forced error prints `Error: KeyError: 'Date' (see
<repo>/var/log/kb4it.log)`.

### OC-05 Code blocks inside admonitions (MD-01, with MD-03)

**Requirement.**

- The help page on Markdown says that with the default extensions a code block
  inside an admonition must be indented, and that `pymdownx.superfences` (from
  `KB4IT[extras]`) allows fences there.
- MD-03: when `pymdownx.superfences` or `pymdownx.highlight` is enabled,
  `MarkdownSettings.all_configs()` (`mdconfig.py:45-49`) sets
  `pymdownx.highlight: {"use_pygments": <highlight == "pygments">}`, so the
  default `client` mode produces plain `language-*` classes for highlight.js.
- `kb4it verify` warns `MD_FENCE_IN_BLOCK doc=<name>` when a fence line appears
  inside an indented block and superfences is not enabled (see Decision D-5).

**Acceptance.** With superfences enabled, the MD-01 example renders a real code
block in both `client` and `pygments` modes; without it, `verify` prints the
warning.

## D. Security

### SC-01 Template output is escaped by default (SEC-01)

**Requirement.**

- `Builder.template` compiles every template with
  `Template(filename=..., default_filters=["h"])` when the theme opts in with
  `"autoescape": true` in `theme.json` (see Decision D-1).
- In each bundled theme, the expressions that carry ready-made HTML (page bodies,
  rendered fragments, the search box, metadata sections) are marked `| n`. The
  explicit `| h` in apphelp and in the common templates become plain
  expressions, so nothing is escaped twice.
- All four bundled themes turn `autoescape` on. A custom theme without the key
  keeps today's behaviour and gets one warning per build:
  `[BUILDER] THEME_AUTOESCAPE_OFF theme=<id>`.
- The common templates (`resources/common/templates`) are escaped like the theme
  that uses them.
- The theme authoring help explains `| n` and the flag.

**Acceptance.** A test builds every bundled theme with the SEC-01 payloads in each
property, in a property name and in the title, and finds no raw `<script`, no
`onerror=` or `onmouseover=` and no unescaped `"` inside an attribute in any page.
`scripts/devel/theme_snapshot.py` shows no other change in the output of the
sample sites, apart from characters that are now escaped.

### SC-02 Raw HTML in Markdown: documented, and optionally cleaned (SEC-02)

**Requirement.**

- The help states the trust model: documents may contain HTML and scripts, which
  reach the page as written; review contributions from others, or turn cleaning
  on.
- A new setting `"markdown": {"sanitize": true}` cleans the compiled HTML of each
  document with an allow-list (elements and attributes that python-markdown and
  the bundled extensions produce; no `script`, `style`, `on*` attributes,
  `javascript:` or `data:` URLs except images). Off by default (see Decision D-2
  for the library).
- `kb4it verify` reports `DOC_RAW_SCRIPT doc=<name>` for documents with `<script>`
  or `on*=` attributes when sanitising is off, as information.

**Acceptance.** With `sanitize` on, the SEC-02 document renders without the script,
the handler and the `javascript:` link, and its text, tables, code and admonitions
are unchanged; with it off, the output is as today and `verify` lists the
document.

### SC-03 Property names that cannot make a page name (SEC-03)

**Requirement.** `valid_filename` (`util.py:444-456`) strips leading dots. A
property name or value whose cleaned name is empty is reported as
`DOC_INVALID reason=bad_property_name key=<key>` (so `fail_on_invalid` applies)
and left out of the navigation, instead of producing a page that is never
compiled.

**Acceptance.** A document with `.note: a` builds a site with `index.html` and a
`note.html` key page; a document with `"...": a` is reported invalid and the rest
of the site is built.

## E. HTML and accessibility

### HT-01 Valid HTML in techdoc, blog and bookshelf (HTML-01)

**Requirement.**

- The `HTML_TAG_A` transformation pair is removed (`builder.py:74-87` and the
  `HTML_TAG_A_MD/NEW` templates); link styling moves to CSS rules on the
  document container. This removes the empty `target=""` and the duplicate
  `class` attributes.
- `HTML_TAG_SECT1_NEW.tpl` and `HTML_TAG_SECTIONBODY_NEW.tpl` (blog, and the same
  pattern elsewhere) use classes instead of fixed `id`s; CSS and scripts that
  select `#kb-sect1` or `#kb-section-body` are updated.
- The templates behind the stray `</div>` (blog document page), the `<div>` inside
  `<span>` (techdoc and blog tooltips), the nested `<ul>` (techdoc navigation) and
  `width="24px"` (techdoc header logo) are fixed.
- UIkit `uk-*` attributes (HTML-03, Info) are out of scope; the validator check in
  TS-02 filters them.

**Acceptance.** On the sample sites of Phase 6 plus the COR-07 and MD-01 documents,
the Nu HTML Checker reports 0 errors other than `uk-*` attributes for all four
themes.

### HT-02 Accessible defaults (HTML-02)

**Requirement.**

- The sample `repo.json` files of techdoc (default, sapbasis) and blog drop the
  `{...}` placeholders: `logo_alt` empty and the `git_*` keys absent.
- Templates use the site title as the logo `alt` when `logo_alt` is empty.
- The blog renders the edit link only when `git` is true and every `git_*` key is
  set.
- The "built with KB4IT" badge has `alt="Built with KB4IT"`.
- Every page of techdoc and blog has exactly one `<h1>` and wraps its content in
  `<main>`.

**Acceptance.** The `lxml` checks of Phase 6 pass for every page of the four sample
sites: `lang` present, one `<h1>`, every `<img>` with a non-placeholder `alt`, a
`<main>` element, no `href="{`.

## F. Tests and CI

### TS-01 Tests for the failure paths (TST-01)

**Requirement.** Tests that cover `compiler.py:191-193`, `:211-216`, `:219-220` and
`deployer.py:125-128`, through the acceptance cases of BO-01, BO-02, FS-01, FS-02
and SC-03. Coverage of those lines is reported in the plan's verification.

**Acceptance.** The listed lines are covered (coverage run as in Phase 6 of the
audit).

### TS-02 Output tests and HTML validation in CI (TST-02)

**Requirement.**

- The tests named in SC-01, OC-01, OC-03 and HT-02 exist and run on Linux, macOS
  and Windows.
- A new CI step in the `package` job of `kb4it.yml` builds the four sample sites
  and runs `html5validator` (Python package bundling the Nu checker; Java is
  preinstalled on `ubuntu-latest`), failing on any error that is not a `uk-*`
  attribute. No Node is involved.

**Acceptance.** The CI step is green on the commit that adds it and red when a
template error from HT-01 is put back.

## G. Architecture

These three are refactors with no change in behaviour. They are specified here so
the plan can schedule them, but Decision D-6 asks whether they belong in this
series.

### AR-01 Shared theme code (ARC-01)

**Requirement.** The methods that are identical or nearly identical across themes
(`get_labels`, `get_html_values_from_key`, `extract_toc`,
`build_metadata_section`, `build_page_key`, `build_page_key_value`,
`build_events`, `build_datatable`; see the ARC-01 table) move to `Builder` or to a
mixin module `kb4it/services/themekit.py`; themes keep only real differences.
Byte-identical templates move to `resources/common/templates/`.

**Acceptance.** `theme_snapshot.py` output of the four sample sites is identical
before and after; each moved method has one definition.

### AR-02 Smaller modules (ARC-02)

**Requirement.** After AR-01, the techdoc, blog and bookshelf theme classes are split
by concern (events calendar, tables, page builders), and `tui/app.py` into one
module per screen. No public name used by custom themes changes without an alias.

**Acceptance.** No module over 600 lines in `kb4it/` (excluding tests); snapshot
identical; the TUI tests pass.

### AR-03 Explicit pipeline collaborators (ARC-03)

**Requirement.** `Processor`, `Compiler` and `Deployer` receive their collaborators
(backend, database, theme) in their constructor, created once in stage 1; the
registry keeps the application-level services. The lifecycle is described in
`AGENTS.md`.

**Acceptance.** Each of the three services is constructed in a unit test with
stand-in collaborators, without a `KB4IT` app; snapshot identical.

## Compatibility

| Change | Who notices | How |
|---|---|---|
| BO-01 exit status 1 on a failed page | Scripts and CI that ignored page errors | Their build now fails, as it should; release notes |
| FS-01 target check | Repositories whose `target` is `.`, the source or home | Build stops with a clear error; release notes say how to move the target |
| FS-01 sweep limited to KB4IT's files | Nobody, except that orphan pages from builds before the upgrade stay until `--force` once | Release notes |
| SC-01 autoescape | Custom themes that turn it on and print HTML through `${...}` | They mark those expressions `\| n`; custom themes without the flag are unchanged |
| OC-01 settings in the signature | Everyone, once | The first build after any settings change rebuilds every page |
| HT-01 link and section markup | Custom CSS that targets `a[target]`, `#kb-sect1` or `#kb-section-body` | Release notes list the changed selectors |
| HT-02 sample configs | New repositories only | Existing `repo.json` files are not touched |

## Decisions for review

Answered on 2026-10-14: the recommendation was chosen for each one, and the specification was approved. AR-01 to AR-03 move to a separate series (D-6).

| # | Decision | Recommendation | Alternative |
|---|---|---|---|
| D-1 | Escaping switch (SC-01) | Per-theme `"autoescape": true` in `theme.json`; bundled themes on, custom themes warned | Global default on for every theme, breaking custom themes that print HTML |
| D-2 | Sanitiser library (SC-02) | `nh3` as part of `KB4IT[extras]`: binary wheels, no Node, maintained | `lxml_html_clean` (pure Python on lxml, also an extra); or documentation only, no `sanitize` option |
| D-3 | Release vehicle | Part of 0.9.0, before the first tag; the High fixes are security and data-loss issues | A 0.9.1 release after 0.9.0 |
| D-4 | Failed page (BO-01) | Always fails the build | A `repo.json` option to keep today's behaviour |
| D-5 | Fences in admonitions (OC-05) | Document, add the `verify` warning, fix MD-03 | Enable superfences automatically when `pymdown-extensions` is installed |
| D-6 | Architecture (AR-01 to AR-03) | A separate series after this one, once SC-01 and HT-01 have changed the same files | In this series, after groups A to F |

## Testing summary

| Check | Where |
|---|---|
| Full test suite with the new tests, Linux | Here, every commit |
| Reproductions of every audit finding in scope, now passing | Here, in the tests |
| Coverage of the failure branches (TS-01) | Here, at the end |
| Nu HTML Checker on the four sample sites (HT-01, TS-02) | Here (Java and `html5validator` work in this session) and CI |
| `theme_snapshot.py` before and after AR-01 to AR-03 | Here |
| macOS and Windows | CI after you push |

## Related Topics

- `AUDIT.md`: the findings, their evidence and the reproductions referenced here.
- `responses/KB4IT-0.9-SPEC.md`, `responses/KB4IT-0.9-DISTRIBUTION-SPEC.md`: the earlier 0.9 work this builds on.
